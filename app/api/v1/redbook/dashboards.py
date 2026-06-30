import asyncio
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Query

from app.models.redbook import (
    RedbookFileUpload,
    RedbookFactNoteDaily,
    RedbookFactTaskDaily,
    RedbookKpiConfig,
    RedbookMartProjectDaily,
    RedbookNoteMapping,
    RedbookRawJuguang,
    RedbookRawKeywordSearch,
    RedbookRawPgy,
    RedbookRawXiaohongxingOrderDaily,
    RedbookTaskMapping,
    RedbookTaskNoteBridge,
)
from app.redbook.constants.source_type import (
    SOURCE_JUGUANG,
    SOURCE_KEYWORD_SEARCH,
    SOURCE_NOTE_MAPPING,
    SOURCE_PGY,
    SOURCE_TASK_MAPPING,
    SOURCE_XIAOHONGXING_ORDER,
)
from app.redbook.services.fact_builder import dec, div, in_date_range, latest_pgy_by_note, rebuild_redbook_facts
from app.schemas.base import Success

router = APIRouter()
_rebuild_locks: dict[int, asyncio.Lock] = {}


def apply_date_range(query, date_start: date | None, date_end: date | None):
    if date_start:
        query = query.filter(stat_date__gte=date_start)
    if date_end:
        query = query.filter(stat_date__lte=date_end)
    return query


def get_rebuild_lock(project_id: int):
    if project_id not in _rebuild_locks:
        _rebuild_locks[project_id] = asyncio.Lock()
    return _rebuild_locks[project_id]


async def has_note_source_data(project_id: int, date_start: date | None, date_end: date | None):
    has_juguang = await apply_date_range(RedbookRawJuguang.filter(project_id=project_id), date_start, date_end).exists()
    has_pgy = await RedbookRawPgy.filter(project_id=project_id).exists()
    return has_juguang or has_pgy


async def has_task_source_data(project_id: int, date_start: date | None, date_end: date | None):
    return await apply_date_range(
        RedbookRawXiaohongxingOrderDaily.filter(project_id=project_id), date_start, date_end
    ).exists()


async def has_dashboard_source_data(project_id: int, date_start: date | None, date_end: date | None, model):
    if model is RedbookFactNoteDaily:
        return await has_note_source_data(project_id, date_start, date_end)
    if model is RedbookFactTaskDaily:
        return await has_task_source_data(project_id, date_start, date_end)
    return await has_note_source_data(project_id, date_start, date_end) or await has_task_source_data(
        project_id, date_start, date_end
    )


async def ensure_dashboard_data(project_id: int, date_start: date | None, date_end: date | None, model):
    query = apply_date_range(model.filter(project_id=project_id), date_start, date_end)
    if await query.exists():
        return
    if not await has_dashboard_source_data(project_id, date_start, date_end, model):
        return

    async with get_rebuild_lock(project_id):
        query = apply_date_range(model.filter(project_id=project_id), date_start, date_end)
        if await query.exists():
            return
        await rebuild_redbook_facts(project_id=project_id, date_start=date_start, date_end=date_end)


def add_int(target, key, value):
    target[key] += int(value or 0)


def add_dec(target, key, value):
    target[key] += dec(value)


def blank_metrics():
    return defaultdict(lambda: Decimal("0"))


def add_ad_metrics(target, row):
    add_dec(target, "ad_cost", row.ad_cost)
    for field in (
        "impressions",
        "clicks",
        "interactions",
        "search_component_clicks",
        "offsite_active_uv_30d",
        "new_seed_users",
        "new_deep_seed_users",
    ):
        add_int(target, field, getattr(row, field))


def add_pgy_metrics(target, pgy):
    add_dec(target, "note_fee", pgy.blogger_quote_amount)
    add_dec(target, "service_fee", pgy.service_fee_amount)
    add_int(target, "pgy_exposure", pgy.exposure)
    add_int(target, "pgy_read_count", pgy.read_count)
    add_int(target, "pgy_interaction_count", pgy.interaction_count)


def raw_decimal(row, *keys):
    raw = row.raw_json or {}
    for key in keys:
        value = raw.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            value = value.strip().replace(",", "").replace("¥", "").replace("￥", "")
            if value in {"", "-"}:
                continue
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError):
            continue
    return Decimal("0")


def pgy_ad_amount(pgy):
    return raw_decimal(pgy, "广告金额", "广告费", "投流费用")


def metrics_payload(metrics, note_ids=None, bloggers=None):
    ad_cost = metrics["ad_cost"]
    note_fee = metrics["note_fee"]
    service_fee = metrics["service_fee"]
    total_cost = note_fee + ad_cost
    return {
        "note_count": len(note_ids or []),
        "blogger_count": len(bloggers or []),
        "note_fee": note_fee,
        "service_fee": service_fee,
        "ad_cost": ad_cost,
        "total_cost": total_cost,
        "total_cost_with_service": total_cost + service_fee,
        "impressions": metrics["impressions"],
        "clicks": metrics["clicks"],
        "interactions": metrics["interactions"],
        "search_component_clicks": metrics["search_component_clicks"],
        "offsite_active_uv_30d": metrics["offsite_active_uv_30d"],
        "new_seed_users": metrics["new_seed_users"],
        "new_deep_seed_users": metrics["new_deep_seed_users"],
        "pgy_exposure": metrics["pgy_exposure"],
        "pgy_read_count": metrics["pgy_read_count"],
        "pgy_interaction_count": metrics["pgy_interaction_count"],
        "ctr": div(metrics["clicks"], metrics["impressions"]),
        "cpc": div(ad_cost, metrics["clicks"]),
        "cpm": div(ad_cost, metrics["impressions"], Decimal("1000")),
        "cpe": div(ad_cost, metrics["interactions"]),
        "search_component_cost": div(ad_cost, metrics["search_component_clicks"]),
        "offsite_active_cost": div(ad_cost, metrics["offsite_active_uv_30d"]),
    }


def context_for_note(note_id, mappings, pgy_latest, fact_contexts):
    mapping = mappings.get(note_id)
    pgy = pgy_latest.get(note_id)
    fact = fact_contexts.get(note_id)
    return {
        "note_id": note_id,
        "blogger_name": (mapping.blogger_name if mapping else None)
        or (pgy.blogger_name if pgy else None)
        or (fact.blogger_name if fact else None),
        "blogger_type": (mapping.blogger_type if mapping else None) or (fact.blogger_type if fact else None),
        "note_type": (mapping.note_type if mapping else None)
        or (pgy.note_type if pgy else None)
        or (fact.note_type if fact else None),
        "product_name": (mapping.product_name if mapping else None)
        or (fact.product_name if fact else None)
        or (pgy.spu_name if pgy else None),
        "product_category": (mapping.product_category if mapping else None)
        or (fact.product_category if fact else None)
        or (pgy.spu_name if pgy else None),
        "content_direction": (mapping.content_direction if mapping else None)
        or (fact.content_direction if fact else None)
        or (pgy.content_tag if pgy else None),
        "publish_date": (mapping.publish_date if mapping else None)
        or (fact.publish_date if fact else None)
        or (pgy.publish_date if pgy else None),
        "note_url": (mapping.note_url if mapping else None) or (pgy.note_url if pgy else None),
    }


def as_product_filter_set(product_filter):
    if not product_filter:
        return set()
    if isinstance(product_filter, str):
        values = [product_filter]
    else:
        values = product_filter
    return {normalized_option(value) for value in values if normalized_option(value)}


def product_matches(value, product_filter):
    candidate = normalized_option(value)
    product_values = as_product_filter_set(product_filter)
    if not product_values:
        return True
    return candidate in product_values


def context_matches_product(ctx, product_filter):
    product_values = as_product_filter_set(product_filter)
    if not product_values:
        return True
    return product_matches(ctx.get("product_category"), product_values)


def matches_filters(ctx, product_category, blogger_type, note_type, content_direction, keyword):
    if not context_matches_product(ctx, product_category):
        return False
    if blogger_type and ctx["blogger_type"] != blogger_type:
        return False
    if note_type and ctx["note_type"] != note_type:
        return False
    if content_direction and ctx["content_direction"] != content_direction:
        return False
    if keyword:
        lower_keyword = keyword.lower()
        haystack = " ".join(str(ctx.get(key) or "") for key in ("note_id", "blogger_name", "product_category", "content_direction"))
        if lower_keyword not in haystack.lower():
            return False
    return True


def option_values(contexts, key):
    return sorted({ctx[key] for ctx in contexts if ctx.get(key)})


def normalized_option(value):
    if value is None:
        return ""
    return str(value).strip()


def add_product_option(options, value, source):
    label = normalized_option(value)
    if label:
        options[label].add(source)


async def resolve_product_filter_values(project_id: int, product_category: str):
    selected = normalized_option(product_category)
    if not selected:
        return set()

    pgy_rows = await RedbookRawPgy.filter(project_id=project_id).values("spu_name", "note_id")
    note_mapping_rows = await RedbookNoteMapping.filter(project_id=project_id).values("product_category", "note_id")
    values = {selected}
    related_note_ids = {
        normalized_option(row.get("note_id"))
        for row in pgy_rows
        if normalized_option(row.get("spu_name")) == selected and normalized_option(row.get("note_id"))
    }
    related_note_ids.update(
        normalized_option(row.get("note_id"))
        for row in note_mapping_rows
        if normalized_option(row.get("product_category")) == selected and normalized_option(row.get("note_id"))
    )
    for row in pgy_rows:
        if normalized_option(row.get("note_id")) in related_note_ids:
            value = normalized_option(row.get("spu_name"))
            if value:
                values.add(value)
    for row in note_mapping_rows:
        if normalized_option(row.get("note_id")) in related_note_ids:
            value = normalized_option(row.get("product_category"))
            if value:
                values.add(value)

    return values


async def resolve_task_filter_context(project_id: int, task_id: str):
    selected = normalized_option(task_id)
    context = {"task_id": selected, "order_ids": set(), "note_ids": set()}
    if not selected:
        return context

    mapping_rows = await RedbookTaskMapping.filter(project_id=project_id, task_id=selected).values("order_id")
    context["order_ids"] = {
        normalized_option(row.get("order_id")) for row in mapping_rows if normalized_option(row.get("order_id"))
    }

    pgy_rows = await RedbookRawPgy.filter(project_id=project_id, task_id=selected).values("note_id", "order_id")
    for row in pgy_rows:
        note_id = normalized_option(row.get("note_id"))
        order_id = normalized_option(row.get("order_id"))
        if note_id:
            context["note_ids"].add(note_id)
        if order_id:
            context["order_ids"].add(order_id)

    bridge_rows = await RedbookTaskNoteBridge.filter(project_id=project_id, task_id=selected).values(
        "note_id", "order_id"
    )
    if context["order_ids"]:
        bridge_rows.extend(
            await RedbookTaskNoteBridge.filter(
                project_id=project_id,
                order_id__in=context["order_ids"],
            ).values("note_id", "order_id")
        )
    for row in bridge_rows:
        note_id = normalized_option(row.get("note_id"))
        order_id = normalized_option(row.get("order_id"))
        if note_id:
            context["note_ids"].add(note_id)
        if order_id:
            context["order_ids"].add(order_id)
    return context


def task_row_matches(task_id, order_id, task_filter):
    selected = task_filter.get("task_id") if task_filter else ""
    if not selected:
        return True
    return normalized_option(task_id) == selected or normalized_option(order_id) in task_filter["order_ids"]


def fee_date_for_note(ctx, pgy):
    return ctx.get("publish_date") or (pgy.publish_date if pgy else None) or (pgy.update_date if pgy else None)


def build_breakdowns(note_rows, key):
    groups = {}
    for row in note_rows:
        label = row.get(key) or "未填写"
        if label not in groups:
            groups[label] = {"metrics": blank_metrics(), "note_ids": set(), "bloggers": set()}
        group = groups[label]
        group["note_ids"].add(row["note_id"])
        if row.get("blogger_name"):
            group["bloggers"].add(row["blogger_name"])
        for metric in (
            "note_fee",
            "service_fee",
            "ad_cost",
            "impressions",
            "clicks",
            "interactions",
            "search_component_clicks",
            "offsite_active_uv_30d",
            "new_seed_users",
            "new_deep_seed_users",
            "pgy_exposure",
            "pgy_read_count",
            "pgy_interaction_count",
        ):
            add_dec(group["metrics"], metric, row.get(metric)) if metric in {"note_fee", "service_fee", "ad_cost"} else add_int(
                group["metrics"], metric, row.get(metric)
            )
    return sorted(
        [{"name": label, **metrics_payload(item["metrics"], item["note_ids"], item["bloggers"])} for label, item in groups.items()],
        key=lambda item: dec(item["total_cost"]),
        reverse=True,
    )


async def build_planting_dashboard(
    project_id: int,
    date_start: date | None,
    date_end: date | None,
    product_category: str,
    blogger_type: str,
    note_type: str,
    content_direction: str,
    keyword: str,
    task_id: str = "",
):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookFactNoteDaily)
    product_filter = await resolve_product_filter_values(project_id, product_category)
    task_filter = await resolve_task_filter_context(project_id, task_id)
    fact_query = apply_date_range(RedbookFactNoteDaily.filter(project_id=project_id), date_start, date_end)
    fact_rows = await fact_query.order_by("stat_date", "note_id")
    mappings = {item.note_id: item for item in await RedbookNoteMapping.filter(project_id=project_id)}
    pgy_latest = await latest_pgy_by_note(project_id)

    fact_contexts = {}
    for row in fact_rows:
        if row.note_id and row.note_id not in fact_contexts:
            fact_contexts[row.note_id] = row

    all_note_ids = set(mappings) | set(pgy_latest) | set(fact_contexts)
    all_contexts = [context_for_note(note_id, mappings, pgy_latest, fact_contexts) for note_id in all_note_ids]

    note_metrics = {}
    daily_metrics = defaultdict(blank_metrics)
    active_note_ids = set()

    for row in fact_rows:
        if not row.note_id:
            continue
        if task_filter["task_id"] and normalized_option(row.note_id) not in task_filter["note_ids"]:
            continue
        ctx = context_for_note(row.note_id, mappings, pgy_latest, fact_contexts)
        if not matches_filters(ctx, product_filter, blogger_type, note_type, content_direction, keyword):
            continue
        active_note_ids.add(row.note_id)
        note_metrics.setdefault(row.note_id, blank_metrics())
        add_ad_metrics(note_metrics[row.note_id], row)
        if row.stat_date:
            add_ad_metrics(daily_metrics[row.stat_date], row)

    for note_id, pgy in pgy_latest.items():
        if task_filter["task_id"] and normalized_option(note_id) not in task_filter["note_ids"]:
            continue
        ctx = context_for_note(note_id, mappings, pgy_latest, fact_contexts)
        if not matches_filters(ctx, product_filter, blogger_type, note_type, content_direction, keyword):
            continue
        pgy_fee_date = fee_date_for_note(ctx, pgy)
        should_include_pgy = note_id in active_note_ids or in_date_range(pgy_fee_date, date_start, date_end)
        if not should_include_pgy:
            continue
        note_metrics.setdefault(note_id, blank_metrics())
        add_pgy_metrics(note_metrics[note_id], pgy)
        if in_date_range(pgy_fee_date, date_start, date_end):
            add_dec(daily_metrics[pgy_fee_date], "note_fee", pgy.blogger_quote_amount)
            add_dec(daily_metrics[pgy_fee_date], "service_fee", pgy.service_fee_amount)

    note_rows = []
    total_metrics = blank_metrics()
    total_note_ids = set()
    total_bloggers = set()
    for note_id, metrics in note_metrics.items():
        ctx = context_for_note(note_id, mappings, pgy_latest, fact_contexts)
        row_payload = {**ctx, **metrics_payload(metrics, {note_id}, {ctx["blogger_name"]} if ctx.get("blogger_name") else set())}
        note_rows.append(row_payload)
        total_note_ids.add(note_id)
        if ctx.get("blogger_name"):
            total_bloggers.add(ctx["blogger_name"])
        for metric, value in metrics.items():
            total_metrics[metric] += value

    trend = [{"stat_date": day, **metrics_payload(metrics)} for day, metrics in sorted(daily_metrics.items())]
    note_rows.sort(key=lambda item: dec(item["total_cost"]), reverse=True)

    return {
        "totals": metrics_payload(total_metrics, total_note_ids, total_bloggers),
        "trend": trend,
        "breakdowns": {
            "product_category": build_breakdowns(note_rows, "product_category"),
            "blogger_type": build_breakdowns(note_rows, "blogger_type"),
            "note_type": build_breakdowns(note_rows, "note_type"),
            "content_direction": build_breakdowns(note_rows, "content_direction"),
        },
        "notes": note_rows[:500],
        "filters": {
            "product_category": option_values(all_contexts, "product_category"),
            "blogger_type": option_values(all_contexts, "blogger_type"),
            "note_type": option_values(all_contexts, "note_type"),
            "content_direction": option_values(all_contexts, "content_direction"),
        },
    }


def sum_int(rows, field):
    return sum(int(getattr(row, field) or 0) for row in rows)


def sum_dec(rows, field):
    return sum(dec(getattr(row, field)) for row in rows)


def add_task_metrics(target, row):
    for field in (
        "read_play_uv",
        "like_uv",
        "collect_uv",
        "comment_uv",
        "share_uv",
        "interaction_uv",
        "search_exposure_uv",
        "search_visit_uv",
        "shop_visit_uv",
        "new_customer_visit_uv",
        "product_collect_uv",
        "product_cart_uv",
        "shop_follow_uv",
        "shop_member_uv",
        "deal_uv",
        "new_customer_deal_uv",
        "presale_deposit_uv",
    ):
        add_int(target, field, getattr(row, field))
    for field in (
        "merchant_gmv",
        "order_product_gmv",
        "non_order_product_gmv",
        "order_product_new_customer_gmv",
        "presale_deposit_gmv",
        "presale_estimated_gmv",
    ):
        add_dec(target, field, getattr(row, field))


def xiaohongxing_summary(rows):
    note_fee = sum_dec(rows, "note_fee")
    service_fee = sum_dec(rows, "service_fee")
    ad_cost = sum_dec(rows, "ad_cost")
    total_cost = note_fee + ad_cost
    impressions = sum_int(rows, "impressions")
    clicks = sum_int(rows, "clicks")
    interactions = sum_int(rows, "interactions")
    search_component_clicks = sum_int(rows, "search_component_clicks")
    read_play_uv = sum_int(rows, "task_read_play_uv")
    interaction_uv = sum_int(rows, "task_interaction_uv")
    search_exposure_uv = sum_int(rows, "task_search_exposure_uv")
    search_visit_uv = sum_int(rows, "task_search_visit_uv")
    shop_visit_uv = sum_int(rows, "task_shop_visit_uv")
    collect_cart_uv = sum_int(rows, "task_product_collect_uv") + sum_int(rows, "task_product_cart_uv")
    deal_uv = sum_int(rows, "task_deal_uv")
    merchant_gmv = sum_dec(rows, "task_merchant_gmv")
    return {
        "note_count": sum_int(rows, "note_count"),
        "blogger_count": sum_int(rows, "blogger_count"),
        "note_fee": note_fee,
        "service_fee": service_fee,
        "ad_cost": ad_cost,
        "total_cost": total_cost,
        "total_cost_with_service": total_cost + service_fee,
        "content_exposure": sum_int(rows, "pgy_exposure"),
        "pgy_read_count": sum_int(rows, "pgy_read_count"),
        "pgy_interaction_count": sum_int(rows, "pgy_interaction_count"),
        "impressions": impressions,
        "clicks": clicks,
        "interactions": interactions,
        "search_component_clicks": search_component_clicks,
        "offsite_active_uv_30d": sum_int(rows, "offsite_active_uv_30d"),
        "read_play_uv": read_play_uv,
        "like_uv": sum_int(rows, "task_like_uv"),
        "collect_uv": sum_int(rows, "task_collect_uv"),
        "comment_uv": sum_int(rows, "task_comment_uv"),
        "share_uv": sum_int(rows, "task_share_uv"),
        "interaction_uv": interaction_uv,
        "search_exposure_uv": search_exposure_uv,
        "search_visit_uv": search_visit_uv,
        "shop_visit_uv": shop_visit_uv,
        "new_customer_visit_uv": sum_int(rows, "task_new_customer_visit_uv"),
        "product_collect_uv": sum_int(rows, "task_product_collect_uv"),
        "product_cart_uv": sum_int(rows, "task_product_cart_uv"),
        "collect_cart_uv": collect_cart_uv,
        "shop_follow_uv": sum_int(rows, "task_shop_follow_uv"),
        "shop_member_uv": sum_int(rows, "task_shop_member_uv"),
        "deal_uv": deal_uv,
        "new_customer_deal_uv": sum_int(rows, "task_new_customer_deal_uv"),
        "merchant_gmv": merchant_gmv,
        "order_product_gmv": sum_dec(rows, "task_order_product_gmv"),
        "non_order_product_gmv": sum_dec(rows, "task_non_order_product_gmv"),
        "order_product_new_customer_gmv": sum_dec(rows, "task_order_product_new_customer_gmv"),
        "presale_deposit_gmv": sum_dec(rows, "task_presale_deposit_gmv"),
        "presale_estimated_gmv": sum_dec(rows, "task_presale_estimated_gmv"),
        "presale_deposit_uv": sum_int(rows, "task_presale_deposit_uv"),
        "ctr": div(clicks, impressions),
        "cpc": div(ad_cost, clicks),
        "cpm": div(ad_cost, impressions, Decimal("1000")),
        "cpe": div(ad_cost, interactions),
        "search_component_cost": div(ad_cost, search_component_clicks),
        "interaction_rate": div(interaction_uv, read_play_uv),
        "search_visit_rate": div(search_visit_uv, search_exposure_uv),
        "shop_visit_rate": div(shop_visit_uv, read_play_uv),
        "collect_cart_rate": div(collect_cart_uv, shop_visit_uv),
        "deal_conversion_rate": div(deal_uv, shop_visit_uv),
        "roi": div(merchant_gmv, total_cost),
        "gmv_per_read_uv": div(merchant_gmv, read_play_uv),
    }


def xiaohongxing_daily_row(row):
    collect_cart_uv = int(row.task_product_collect_uv or 0) + int(row.task_product_cart_uv or 0)
    return {
        "stat_date": row.stat_date,
        "note_fee": row.note_fee,
        "service_fee": row.service_fee,
        "ad_cost": row.ad_cost,
        "total_cost": row.total_cost,
        "total_cost_with_service": row.total_cost_with_service,
        "content_exposure": row.pgy_exposure,
        "impressions": row.impressions,
        "clicks": row.clicks,
        "interactions": row.interactions,
        "search_component_clicks": row.search_component_clicks,
        "read_play_uv": row.task_read_play_uv,
        "like_uv": row.task_like_uv,
        "collect_uv": row.task_collect_uv,
        "comment_uv": row.task_comment_uv,
        "share_uv": row.task_share_uv,
        "interaction_uv": row.task_interaction_uv,
        "search_exposure_uv": row.task_search_exposure_uv,
        "search_visit_uv": row.task_search_visit_uv,
        "shop_visit_uv": row.task_shop_visit_uv,
        "new_customer_visit_uv": row.task_new_customer_visit_uv,
        "product_collect_uv": row.task_product_collect_uv,
        "product_cart_uv": row.task_product_cart_uv,
        "collect_cart_uv": collect_cart_uv,
        "shop_follow_uv": row.task_shop_follow_uv,
        "shop_member_uv": row.task_shop_member_uv,
        "deal_uv": row.task_deal_uv,
        "new_customer_deal_uv": row.task_new_customer_deal_uv,
        "merchant_gmv": row.task_merchant_gmv,
        "order_product_gmv": row.task_order_product_gmv,
        "non_order_product_gmv": row.task_non_order_product_gmv,
        "order_product_new_customer_gmv": row.task_order_product_new_customer_gmv,
        "ctr": div(row.clicks, row.impressions),
        "cpc": div(row.ad_cost, row.clicks),
        "cpm": div(row.ad_cost, row.impressions, Decimal("1000")),
        "cpe": div(row.ad_cost, row.interactions),
        "interaction_rate": div(row.task_interaction_uv, row.task_read_play_uv),
        "search_visit_rate": div(row.task_search_visit_uv, row.task_search_exposure_uv),
        "shop_visit_rate": div(row.task_shop_visit_uv, row.task_read_play_uv),
        "new_customer_visit_rate": div(row.task_new_customer_visit_uv, row.task_shop_visit_uv),
        "collect_cart_rate": div(collect_cart_uv, row.task_shop_visit_uv),
        "deal_conversion_rate": div(row.task_deal_uv, row.task_shop_visit_uv),
        "new_customer_deal_rate": div(row.task_new_customer_deal_uv, row.task_deal_uv),
        "roi": row.roi,
    }


def blank_xiaohongxing_daily(stat_date):
    return {
        "stat_date": stat_date,
        "note_fee": Decimal("0"),
        "service_fee": Decimal("0"),
        "ad_cost": Decimal("0"),
        "total_cost": Decimal("0"),
        "total_cost_with_service": Decimal("0"),
        "content_exposure": 0,
        "pgy_read_count": 0,
        "pgy_interaction_count": 0,
        "impressions": 0,
        "clicks": 0,
        "interactions": 0,
        "search_component_clicks": 0,
        "read_play_uv": 0,
        "like_uv": 0,
        "collect_uv": 0,
        "comment_uv": 0,
        "share_uv": 0,
        "interaction_uv": 0,
        "search_exposure_uv": 0,
        "search_visit_uv": 0,
        "shop_visit_uv": 0,
        "new_customer_visit_uv": 0,
        "product_collect_uv": 0,
        "product_cart_uv": 0,
        "collect_cart_uv": 0,
        "shop_follow_uv": 0,
        "shop_member_uv": 0,
        "deal_uv": 0,
        "new_customer_deal_uv": 0,
        "merchant_gmv": Decimal("0"),
        "order_product_gmv": Decimal("0"),
        "non_order_product_gmv": Decimal("0"),
        "order_product_new_customer_gmv": Decimal("0"),
        "presale_deposit_gmv": Decimal("0"),
        "presale_estimated_gmv": Decimal("0"),
        "presale_deposit_uv": 0,
    }


def finalize_xiaohongxing_daily(row):
    row["total_cost"] = dec(row["note_fee"]) + dec(row["ad_cost"])
    row["total_cost_with_service"] = row["total_cost"] + dec(row["service_fee"])
    row["collect_cart_uv"] = int(row["product_collect_uv"] or 0) + int(row["product_cart_uv"] or 0)
    row["ctr"] = div(row["clicks"], row["impressions"])
    row["cpc"] = div(row["ad_cost"], row["clicks"])
    row["cpm"] = div(row["ad_cost"], row["impressions"], Decimal("1000"))
    row["cpe"] = div(row["ad_cost"], row["interactions"])
    row["search_component_cost"] = div(row["ad_cost"], row["search_component_clicks"])
    row["interaction_rate"] = div(row["interaction_uv"], row["read_play_uv"])
    row["search_visit_rate"] = div(row["search_visit_uv"], row["search_exposure_uv"])
    row["shop_visit_rate"] = div(row["shop_visit_uv"], row["read_play_uv"])
    row["new_customer_visit_rate"] = div(row["new_customer_visit_uv"], row["shop_visit_uv"])
    row["collect_cart_rate"] = div(row["collect_cart_uv"], row["shop_visit_uv"])
    row["deal_conversion_rate"] = div(row["deal_uv"], row["shop_visit_uv"])
    row["new_customer_deal_rate"] = div(row["new_customer_deal_uv"], row["deal_uv"])
    row["roi"] = div(row["merchant_gmv"], row["total_cost"])
    row["gmv_per_read_uv"] = div(row["merchant_gmv"], row["read_play_uv"])
    return row


def sum_daily_int(rows, field):
    return sum(int(row.get(field) or 0) for row in rows)


def sum_daily_dec(rows, field):
    return sum(dec(row.get(field)) for row in rows)


def xiaohongxing_summary_from_daily_rows(rows, planting_totals=None):
    planting_totals = planting_totals or {}
    note_fee = sum_daily_dec(rows, "note_fee")
    service_fee = sum_daily_dec(rows, "service_fee")
    ad_cost = sum_daily_dec(rows, "ad_cost")
    total_cost = note_fee + ad_cost
    impressions = sum_daily_int(rows, "impressions")
    clicks = sum_daily_int(rows, "clicks")
    interactions = sum_daily_int(rows, "interactions")
    search_component_clicks = sum_daily_int(rows, "search_component_clicks")
    read_play_uv = sum_daily_int(rows, "read_play_uv")
    interaction_uv = sum_daily_int(rows, "interaction_uv")
    search_exposure_uv = sum_daily_int(rows, "search_exposure_uv")
    search_visit_uv = sum_daily_int(rows, "search_visit_uv")
    shop_visit_uv = sum_daily_int(rows, "shop_visit_uv")
    collect_cart_uv = sum_daily_int(rows, "collect_cart_uv")
    deal_uv = sum_daily_int(rows, "deal_uv")
    merchant_gmv = sum_daily_dec(rows, "merchant_gmv")
    return {
        "note_count": planting_totals.get("note_count", 0),
        "blogger_count": planting_totals.get("blogger_count", 0),
        "note_fee": note_fee,
        "service_fee": service_fee,
        "ad_cost": ad_cost,
        "total_cost": total_cost,
        "total_cost_with_service": total_cost + service_fee,
        "content_exposure": sum_daily_int(rows, "content_exposure"),
        "pgy_read_count": sum_daily_int(rows, "pgy_read_count"),
        "pgy_interaction_count": sum_daily_int(rows, "pgy_interaction_count"),
        "impressions": impressions,
        "clicks": clicks,
        "interactions": interactions,
        "search_component_clicks": search_component_clicks,
        "offsite_active_uv_30d": planting_totals.get("offsite_active_uv_30d", 0),
        "read_play_uv": read_play_uv,
        "like_uv": sum_daily_int(rows, "like_uv"),
        "collect_uv": sum_daily_int(rows, "collect_uv"),
        "comment_uv": sum_daily_int(rows, "comment_uv"),
        "share_uv": sum_daily_int(rows, "share_uv"),
        "interaction_uv": interaction_uv,
        "search_exposure_uv": search_exposure_uv,
        "search_visit_uv": search_visit_uv,
        "shop_visit_uv": shop_visit_uv,
        "new_customer_visit_uv": sum_daily_int(rows, "new_customer_visit_uv"),
        "product_collect_uv": sum_daily_int(rows, "product_collect_uv"),
        "product_cart_uv": sum_daily_int(rows, "product_cart_uv"),
        "collect_cart_uv": collect_cart_uv,
        "shop_follow_uv": sum_daily_int(rows, "shop_follow_uv"),
        "shop_member_uv": sum_daily_int(rows, "shop_member_uv"),
        "deal_uv": deal_uv,
        "new_customer_deal_uv": sum_daily_int(rows, "new_customer_deal_uv"),
        "merchant_gmv": merchant_gmv,
        "order_product_gmv": sum_daily_dec(rows, "order_product_gmv"),
        "non_order_product_gmv": sum_daily_dec(rows, "non_order_product_gmv"),
        "order_product_new_customer_gmv": sum_daily_dec(rows, "order_product_new_customer_gmv"),
        "presale_deposit_gmv": sum_daily_dec(rows, "presale_deposit_gmv"),
        "presale_estimated_gmv": sum_daily_dec(rows, "presale_estimated_gmv"),
        "presale_deposit_uv": sum_daily_int(rows, "presale_deposit_uv"),
        "ctr": div(clicks, impressions),
        "cpc": div(ad_cost, clicks),
        "cpm": div(ad_cost, impressions, Decimal("1000")),
        "cpe": div(ad_cost, interactions),
        "search_component_cost": div(ad_cost, search_component_clicks),
        "interaction_rate": div(interaction_uv, read_play_uv),
        "search_visit_rate": div(search_visit_uv, search_exposure_uv),
        "shop_visit_rate": div(shop_visit_uv, read_play_uv),
        "collect_cart_rate": div(collect_cart_uv, shop_visit_uv),
        "deal_conversion_rate": div(deal_uv, shop_visit_uv),
        "roi": div(merchant_gmv, total_cost),
        "gmv_per_read_uv": div(merchant_gmv, read_play_uv),
    }


async def build_filtered_xiaohongxing_daily_rows(project_id, date_start, date_end, product_category, task_id=""):
    product_filter = await resolve_product_filter_values(project_id, product_category)
    task_filter = await resolve_task_filter_context(project_id, task_id)
    planting_dashboard = await build_planting_dashboard(
        project_id=project_id,
        date_start=date_start,
        date_end=date_end,
        product_category=product_category,
        blogger_type="",
        note_type="",
        content_direction="",
        keyword="",
        task_id=task_id,
    )
    daily_rows = {}

    def daily_for(stat_date):
        if stat_date not in daily_rows:
            daily_rows[stat_date] = blank_xiaohongxing_daily(stat_date)
        return daily_rows[stat_date]

    for row in planting_dashboard.get("trend") or []:
        stat_date = row.get("stat_date")
        if not stat_date:
            continue
        daily = daily_for(stat_date)
        daily["note_fee"] += dec(row.get("note_fee"))
        daily["service_fee"] += dec(row.get("service_fee"))
        daily["ad_cost"] += dec(row.get("ad_cost"))
        daily["content_exposure"] += int(row.get("pgy_exposure") or 0)
        daily["pgy_read_count"] += int(row.get("pgy_read_count") or 0)
        daily["pgy_interaction_count"] += int(row.get("pgy_interaction_count") or 0)
        daily["impressions"] += int(row.get("impressions") or 0)
        daily["clicks"] += int(row.get("clicks") or 0)
        daily["interactions"] += int(row.get("interactions") or 0)
        daily["search_component_clicks"] += int(row.get("search_component_clicks") or 0)

    await ensure_dashboard_data(project_id, date_start, date_end, RedbookFactTaskDaily)
    task_query = apply_date_range(RedbookFactTaskDaily.filter(project_id=project_id), date_start, date_end)
    task_rows = await task_query.order_by("stat_date", "task_id", "order_id")
    for row in task_rows:
        if not row.stat_date:
            continue
        if not task_row_matches(row.task_id, row.order_id, task_filter):
            continue
        if not product_matches(row.product_category, product_filter):
            continue
        daily = daily_for(row.stat_date)
        daily["read_play_uv"] += int(row.read_play_uv or 0)
        daily["like_uv"] += int(row.like_uv or 0)
        daily["collect_uv"] += int(row.collect_uv or 0)
        daily["comment_uv"] += int(row.comment_uv or 0)
        daily["share_uv"] += int(row.share_uv or 0)
        daily["interaction_uv"] += int(row.interaction_uv or 0)
        daily["search_exposure_uv"] += int(row.search_exposure_uv or 0)
        daily["search_visit_uv"] += int(row.search_visit_uv or 0)
        daily["shop_visit_uv"] += int(row.shop_visit_uv or 0)
        daily["new_customer_visit_uv"] += int(row.new_customer_visit_uv or 0)
        daily["product_collect_uv"] += int(row.product_collect_uv or 0)
        daily["product_cart_uv"] += int(row.product_cart_uv or 0)
        daily["shop_follow_uv"] += int(row.shop_follow_uv or 0)
        daily["shop_member_uv"] += int(row.shop_member_uv or 0)
        daily["deal_uv"] += int(row.deal_uv or 0)
        daily["new_customer_deal_uv"] += int(row.new_customer_deal_uv or 0)
        daily["presale_deposit_uv"] += int(row.presale_deposit_uv or 0)
        daily["merchant_gmv"] += dec(row.merchant_gmv)
        daily["order_product_gmv"] += dec(row.order_product_gmv)
        daily["non_order_product_gmv"] += dec(row.non_order_product_gmv)
        daily["order_product_new_customer_gmv"] += dec(row.order_product_new_customer_gmv)
        daily["presale_deposit_gmv"] += dec(row.presale_deposit_gmv)
        daily["presale_estimated_gmv"] += dec(row.presale_estimated_gmv)

    return [finalize_xiaohongxing_daily(row) for _, row in sorted(daily_rows.items())], planting_dashboard


async def build_source_status(project_id: int):
    source_labels = {
        SOURCE_PGY: "蒲公英笔记批量数据",
        SOURCE_JUGUANG: "聚光投流原始数据",
        SOURCE_XIAOHONGXING_ORDER: "小红星订单每日数据",
        SOURCE_KEYWORD_SEARCH: "小红书搜索日报",
        SOURCE_NOTE_MAPPING: "笔记映射",
    }
    files = await RedbookFileUpload.filter(project_id=project_id, source_type__in=list(source_labels)).order_by(
        "source_type", "-upload_time"
    )
    grouped = {}
    for row in files:
        grouped.setdefault(row.source_type, []).append(row)

    status_rows = []
    for source_type, label in source_labels.items():
        rows = grouped.get(source_type, [])
        latest = rows[0] if rows else None
        status_rows.append(
            {
                "source_type": source_type,
                "label": label,
                "file_count": len(rows),
                "success_file_count": sum(1 for item in rows if item.parse_status == "success"),
                "latest_file_name": latest.original_file_name if latest else None,
                "latest_parse_status": latest.parse_status if latest else "missing",
                "latest_upload_time": latest.upload_time if latest else None,
                "latest_parsed_at": latest.parsed_at if latest else None,
                "data_rows": latest.data_rows if latest else 0,
            }
        )

    task_mapping_count = await RedbookTaskMapping.filter(project_id=project_id).count()
    status_rows.append(
        {
            "source_type": SOURCE_TASK_MAPPING,
            "label": "任务映射",
            "file_count": task_mapping_count,
            "success_file_count": task_mapping_count,
            "latest_file_name": None,
            "latest_parse_status": "success" if task_mapping_count else "missing",
            "latest_upload_time": None,
            "latest_parsed_at": None,
            "data_rows": task_mapping_count,
        }
    )
    return status_rows


async def build_missing_mappings(project_id: int, date_start: date | None, date_end: date | None):
    raw_order_query = apply_date_range(RedbookRawXiaohongxingOrderDaily.filter(project_id=project_id), date_start, date_end)
    raw_note_query = apply_date_range(RedbookRawJuguang.filter(project_id=project_id), date_start, date_end)
    raw_orders = {
        item
        for item in await raw_order_query.exclude(order_id=None).distinct().values_list("order_id", flat=True)
        if item
    }
    mapped_orders = {
        item for item in await RedbookTaskMapping.filter(project_id=project_id).values_list("order_id", flat=True) if item
    }
    raw_notes = {
        item
        for item in await raw_note_query.exclude(note_id=None).distinct().values_list("note_id", flat=True)
        if item
    }
    mapped_notes = {
        item for item in await RedbookNoteMapping.filter(project_id=project_id).values_list("note_id", flat=True) if item
    }
    unmatched_orders = sorted(raw_orders - mapped_orders)
    unmatched_notes = sorted(raw_notes - mapped_notes)
    return {
        "unmatched_order_count": len(unmatched_orders),
        "unmatched_note_count": len(unmatched_notes),
        "unmatched_orders": unmatched_orders[:100],
        "unmatched_notes": unmatched_notes[:100],
    }


async def build_dashboard_kpis(project_id: int, summary):
    configs = await RedbookKpiConfig.filter(project_id=project_id, status="active").order_by("id")
    if not configs:
        return {"configured": False, "items": [], "total_score": None}

    metric_values = {
        "total_cost": summary["total_cost"],
        "total_cost_with_service": summary["total_cost_with_service"],
        "note_fee": summary["note_fee"],
        "ad_cost": summary["ad_cost"],
        "service_fee": summary["service_fee"],
        "content_exposure": summary["content_exposure"],
        "read_play_uv": summary["read_play_uv"],
        "interaction_uv": summary["interaction_uv"],
        "search_exposure_uv": summary["search_exposure_uv"],
        "search_visit_uv": summary["search_visit_uv"],
        "shop_visit_uv": summary["shop_visit_uv"],
        "collect_cart_uv": summary["collect_cart_uv"],
        "deal_uv": summary["deal_uv"],
        "merchant_gmv": summary["merchant_gmv"],
        "roi": summary["roi"],
    }
    items = []
    total_score = Decimal("0")
    for config in configs:
        actual_value = metric_values.get(config.metric_code)
        target_value = dec(config.target_value)
        weight_score = dec(config.weight_score)
        achievement_rate = None
        actual_score = None
        if actual_value is not None and target_value != 0:
            if config.direction == "lower_better":
                achievement_rate = div(target_value, actual_value)
            else:
                achievement_rate = div(actual_value, target_value)
            if achievement_rate is not None:
                score_rate = min(dec(achievement_rate), Decimal("1")) if config.cap_at_full_score else dec(achievement_rate)
                actual_score = score_rate * weight_score
                total_score += actual_score
        items.append(
            {
                "kpi_code": config.kpi_code,
                "kpi_name": config.kpi_name,
                "metric_code": config.metric_code,
                "actual_value": actual_value,
                "target_value": config.target_value,
                "weight_score": config.weight_score,
                "achievement_rate": achievement_rate,
                "actual_score": actual_score,
                "direction": config.direction,
            }
        )
    return {"configured": True, "items": items, "total_score": total_score}


def add_keyword_metrics(target, row):
    add_int(target, "record_count", 1)
    if row.is_less_than_threshold:
        add_int(target, "less_than_threshold_count", 1)
    if row.search_index is not None:
        add_dec(target, "search_index", row.search_index)
        add_int(target, "known_value_count", 1)


def keyword_metrics_payload(metrics):
    return {
        "search_index": metrics["search_index"],
        "known_value_count": metrics["known_value_count"],
        "less_than_threshold_count": metrics["less_than_threshold_count"],
        "record_count": metrics["record_count"],
        "avg_search_index": div(metrics["search_index"], metrics["known_value_count"]),
    }


def split_selected_keywords(value: str | None):
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


async def default_keyword_search_keywords(project_id: int, limit: int = 5):
    rows = await RedbookRawKeywordSearch.filter(project_id=project_id).order_by("row_number", "keyword").values("keyword")
    keywords = []
    seen = set()
    for row in rows:
        keyword = row.get("keyword")
        if not keyword or keyword in seen:
            continue
        seen.add(keyword)
        keywords.append(keyword)
        if len(keywords) >= limit:
            break
    return keywords


async def build_keyword_search_dashboard(
    project_id: int,
    date_start: date | None,
    date_end: date | None,
    selected_keywords: str,
    keyword: str,
    use_default_keywords: bool = False,
):
    selected_keyword_list = split_selected_keywords(selected_keywords)
    if not selected_keyword_list and use_default_keywords:
        selected_keyword_list = await default_keyword_search_keywords(project_id)
    selected_keyword_set = set(selected_keyword_list)

    keyword_query = apply_date_range(RedbookRawKeywordSearch.filter(project_id=project_id), date_start, date_end)
    if keyword:
        keyword_query = keyword_query.filter(keyword__contains=keyword)
    keyword_rows_source = await keyword_query.order_by("keyword", "stat_date")

    metric_query = apply_date_range(RedbookRawKeywordSearch.filter(project_id=project_id), date_start, date_end)
    if selected_keyword_list:
        metric_query = metric_query.filter(keyword__in=selected_keyword_list)
        metric_rows = await metric_query.order_by("stat_date", "keyword")
    else:
        metric_rows = []

    total_metrics = blank_metrics()
    daily_metrics = defaultdict(blank_metrics)
    daily_keyword_metrics = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    metric_dates = set()
    for row in metric_rows:
        add_keyword_metrics(total_metrics, row)
        if row.stat_date:
            metric_dates.add(row.stat_date)
            add_keyword_metrics(daily_metrics[row.stat_date], row)
            if row.search_index is not None:
                daily_keyword_metrics[row.stat_date][row.keyword] += dec(row.search_index)

    keyword_groups = {}
    latest_by_keyword = {}
    available_keywords = set()
    for row in keyword_rows_source:
        if row.keyword:
            available_keywords.add(row.keyword)
        if row.keyword not in keyword_groups:
            keyword_groups[row.keyword] = {
                "keyword": row.keyword,
                "metrics": blank_metrics(),
            }
        add_keyword_metrics(keyword_groups[row.keyword]["metrics"], row)
        if row.stat_date and (row.keyword not in latest_by_keyword or row.stat_date > latest_by_keyword[row.keyword].stat_date):
            latest_by_keyword[row.keyword] = row

    keyword_rows = []
    for item in keyword_groups.values():
        latest = latest_by_keyword.get(item["keyword"])
        keyword_rows.append(
            {
                "keyword": item["keyword"],
                "latest_date": latest.stat_date if latest else None,
                "latest_raw_value": latest.raw_value if latest else None,
                "latest_search_index": latest.search_index if latest else None,
                **keyword_metrics_payload(item["metrics"]),
            }
        )

    keyword_rows.sort(key=lambda item: dec(item["search_index"]), reverse=True)
    all_rows = await apply_date_range(RedbookRawKeywordSearch.filter(project_id=project_id), date_start, date_end).distinct().values(
        "keyword"
    )
    all_keywords = sorted({row.get("keyword") for row in all_rows if row.get("keyword")})

    return {
        "summary": {
            **keyword_metrics_payload(total_metrics),
            "keyword_count": len(available_keywords),
            "available_keyword_count": len(all_keywords),
            "selected_keyword_count": len(selected_keyword_list),
            "date_count": len(metric_dates),
            "selected_keywords": selected_keyword_list,
        },
        "trend": [
            {
                "stat_date": stat_date,
                **keyword_metrics_payload(metrics),
                "keyword_values": [
                    {"keyword": item, "search_index": daily_keyword_metrics[stat_date][item]}
                    for item in selected_keyword_list
                ],
            }
            for stat_date, metrics in sorted(daily_metrics.items())
        ],
        "keywords": [{**row, "selected": row["keyword"] in selected_keyword_set} for row in keyword_rows[:500]],
        "filters": {
            "keyword": all_keywords,
            "selected_keywords": selected_keyword_list,
        },
    }


async def build_task_groups(
    project_id: int,
    date_start: date | None,
    date_end: date | None,
    product_category: str = "",
    task_id: str = "",
):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookFactTaskDaily)
    product_filter = await resolve_product_filter_values(project_id, product_category)
    task_filter = await resolve_task_filter_context(project_id, task_id)
    task_query = apply_date_range(RedbookFactTaskDaily.filter(project_id=project_id), date_start, date_end)
    task_rows = await task_query.order_by("task_id", "order_id")
    mapping_rows = await RedbookTaskMapping.filter(project_id=project_id)
    mappings = {item.order_id: item for item in mapping_rows}
    mappings_by_task_id = {item.task_id: item for item in mapping_rows if item.task_id}
    groups = {}

    def group_for(task_id, task_name=None, task_type=None, product_name=None, product_value=None, blogger_type=None):
        key = task_id or "__unmapped__"
        if key not in groups:
            groups[key] = {
                "task_id": None if key == "__unmapped__" else key,
                "task_name": task_name or ("未归类" if key == "__unmapped__" else key),
                "task_type": task_type,
                "product_name": product_name,
                "product_category": product_value or product_name,
                "blogger_type": blogger_type,
                "order_ids": set(),
                "note_ids": set(),
                "has_xiaohongxing_data": False,
                "metrics": blank_metrics(),
            }
        return groups[key]

    for row in task_rows:
        if not task_row_matches(row.task_id, row.order_id, task_filter):
            continue
        if not product_matches(row.product_category, product_filter):
            continue
        group = group_for(
            row.task_id,
            row.task_name,
            row.task_type,
            row.product_name,
            row.product_category,
            row.blogger_type,
        )
        group["has_xiaohongxing_data"] = True
        if row.order_id:
            group["order_ids"].add(row.order_id)
        add_task_metrics(group["metrics"], row)

    for pgy in (await latest_pgy_by_note(project_id)).values():
        fee_date = pgy.publish_date or pgy.update_date
        if not in_date_range(fee_date, date_start, date_end):
            continue
        if not task_row_matches(pgy.task_id, pgy.order_id, task_filter):
            continue
        mapping = mappings_by_task_id.get(pgy.task_id)
        pgy_product = (mapping.product_category if mapping else None) or pgy.spu_name
        if not product_matches(pgy_product, product_filter):
            continue
        if not pgy.task_id or pgy.task_id not in groups:
            continue
        group = group_for(
            pgy.task_id or (mapping.task_id if mapping else None),
            mapping.task_name if mapping else pgy.cooperation_name,
            mapping.task_type if mapping else None,
            mapping.product_name if mapping else pgy.spu_name,
            pgy_product,
            mapping.blogger_type if mapping else None,
        )
        if pgy.note_id:
            group["note_ids"].add(pgy.note_id)
        if pgy.order_id:
            group["order_ids"].add(pgy.order_id)
        add_dec(group["metrics"], "note_fee", pgy.blogger_quote_amount)
        add_dec(group["metrics"], "service_fee", pgy.service_fee_amount)
        add_dec(group["metrics"], "ad_cost", pgy_ad_amount(pgy))
        add_int(group["metrics"], "content_exposure", pgy.exposure)

    bridges = {item.note_id: item for item in await RedbookTaskNoteBridge.filter(project_id=project_id)}
    for row in await apply_date_range(RedbookFactNoteDaily.filter(project_id=project_id), date_start, date_end):
        bridge = bridges.get(row.note_id)
        if not bridge:
            continue
        if not task_row_matches(bridge.task_id, bridge.order_id, task_filter):
            continue
        mapping = mappings.get(bridge.order_id) if bridge.order_id else None
        bridge_product = (mapping.product_category if mapping else None) or row.product_category
        if not product_matches(bridge_product, product_filter):
            continue
        task_id = bridge.task_id or (mapping.task_id if mapping else None)
        group = group_for(
            task_id,
            mapping.task_name if mapping else None,
            mapping.task_type if mapping else None,
            mapping.product_name if mapping else row.product_name,
            bridge_product,
        )
        add_dec(group["metrics"], "ad_cost", dec(row.ad_cost) * dec(bridge.weight))

    payload = []
    for item in groups.values():
        if not item["has_xiaohongxing_data"]:
            continue
        metrics = item["metrics"]
        collect_cart_uv = metrics["product_collect_uv"] + metrics["product_cart_uv"]
        total_cost = metrics["note_fee"] + metrics["ad_cost"]
        note_count = len(item["note_ids"])
        total_interaction = metrics["like_uv"] + metrics["collect_uv"] + metrics["comment_uv"]
        payload.append(
            {
                "task_id": item["task_id"],
                "task_name": item["task_name"],
                "task_type": item["task_type"],
                "product_name": item["product_name"],
                "product_category": item["product_category"],
                "blogger_type": item["blogger_type"],
                "order_count": len(item["order_ids"]),
                "note_count": note_count,
                "note_fee": metrics["note_fee"],
                "service_fee": metrics["service_fee"],
                "ad_cost": metrics["ad_cost"],
                "total_cost": total_cost,
                "content_exposure": metrics["content_exposure"],
                "read_play_uv": metrics["read_play_uv"],
                "like_uv": metrics["like_uv"],
                "collect_uv": metrics["collect_uv"],
                "comment_uv": metrics["comment_uv"],
                "share_uv": metrics["share_uv"],
                "interaction_uv": metrics["interaction_uv"],
                "total_interaction": total_interaction,
                "search_exposure_uv": metrics["search_exposure_uv"],
                "search_visit_uv": metrics["search_visit_uv"],
                "shop_visit_uv": metrics["shop_visit_uv"],
                "new_customer_visit_uv": metrics["new_customer_visit_uv"],
                "product_collect_uv": metrics["product_collect_uv"],
                "product_cart_uv": metrics["product_cart_uv"],
                "collect_cart_uv": collect_cart_uv,
                "shop_follow_uv": metrics["shop_follow_uv"],
                "shop_member_uv": metrics["shop_member_uv"],
                "deal_uv": metrics["deal_uv"],
                "new_customer_deal_uv": metrics["new_customer_deal_uv"],
                "merchant_gmv": metrics["merchant_gmv"],
                "order_product_gmv": metrics["order_product_gmv"],
                "non_order_product_gmv": metrics["non_order_product_gmv"],
                "order_product_new_customer_gmv": metrics["order_product_new_customer_gmv"],
                "avg_interaction_per_note": div(metrics["interaction_uv"], note_count),
                "cpm": div(total_cost, metrics["content_exposure"], Decimal("1000")),
                "cpv": div(total_cost, metrics["read_play_uv"]),
                "cpe": div(total_cost, metrics["interaction_uv"]),
                "interaction_rate": div(metrics["interaction_uv"], metrics["read_play_uv"]),
                "search_visit_rate": div(metrics["search_visit_uv"], metrics["search_exposure_uv"]),
                "collect_cart_rate": div(collect_cart_uv, metrics["shop_visit_uv"]),
                "interaction_visit_rate": div(metrics["shop_visit_uv"], metrics["interaction_uv"]),
                "read_visit_rate": div(metrics["shop_visit_uv"], metrics["read_play_uv"]),
                "read_search_exposure_rate": div(metrics["search_exposure_uv"], metrics["read_play_uv"]),
                "interaction_search_exposure_rate": div(metrics["search_exposure_uv"], metrics["interaction_uv"]),
                "visit_uv_cost": div(total_cost, metrics["shop_visit_uv"]),
                "deal_conversion_rate": div(metrics["deal_uv"], metrics["shop_visit_uv"]),
                "roi": div(metrics["merchant_gmv"], total_cost),
                "full_shop_gmv": metrics["merchant_gmv"],
                "full_shop_roi": div(metrics["merchant_gmv"], total_cost),
            }
        )
    return sorted(payload, key=lambda row: dec(row["merchant_gmv"]), reverse=True)


async def load_xiaohongxing_mart_rows(project_id: int, date_start: date | None, date_end: date | None):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookMartProjectDaily)
    rows = await apply_date_range(RedbookMartProjectDaily.filter(project_id=project_id), date_start, date_end).order_by("stat_date")
    if rows and await has_dashboard_source_data(project_id, date_start, date_end, RedbookMartProjectDaily):
        is_stale = all(row.pgy_exposure is None and row.task_interaction_uv is None for row in rows)
        if is_stale:
            await rebuild_redbook_facts(project_id=project_id, date_start=date_start, date_end=date_end)
            rows = await apply_date_range(
                RedbookMartProjectDaily.filter(project_id=project_id), date_start, date_end
            ).order_by("stat_date")
    return rows


async def build_product_options(project_id: int):
    options = defaultdict(set)
    pgy_rows = await RedbookRawPgy.filter(project_id=project_id).values("spu_name", "note_id")
    pgy_products = sorted({normalized_option(row.get("spu_name")) for row in pgy_rows if normalized_option(row.get("spu_name"))})
    pgy_products_by_note = defaultdict(set)
    for row in pgy_rows:
        note_id = normalized_option(row.get("note_id"))
        product = normalized_option(row.get("spu_name"))
        if note_id and product:
            pgy_products_by_note[note_id].add(product)
    for value in pgy_products:
        add_product_option(options, value, "pgy")

    mapping_rows = await RedbookNoteMapping.filter(project_id=project_id).values("product_category", "note_id")
    mapping_products = set()
    linked_pgy_products = defaultdict(set)
    for row in mapping_rows:
        product = normalized_option(row.get("product_category"))
        if not product:
            continue
        mapping_products.add(product)
        note_id = normalized_option(row.get("note_id"))
        if note_id:
            linked_pgy_products[product].update(pgy_products_by_note.get(note_id, set()))
    for product in mapping_products:
        linked_products = linked_pgy_products.get(product)
        if linked_products:
            for linked_product in linked_products:
                add_product_option(options, linked_product, "note_mapping")
        else:
            add_product_option(options, product, "note_mapping")
    return [
        {"label": label, "value": label, "sources": sorted(sources)}
        for label, sources in sorted(options.items(), key=lambda item: item[0])
    ]


async def build_task_group_options(project_id: int, product_category: str = ""):
    await ensure_dashboard_data(project_id, None, None, RedbookFactTaskDaily)
    selected_product = normalized_option(product_category)
    product_filter = await resolve_product_filter_values(project_id, selected_product)
    fact_rows = await RedbookFactTaskDaily.filter(project_id=project_id).values("task_id", "order_id")
    fact_task_ids = {
        normalized_option(row.get("task_id")) for row in fact_rows if normalized_option(row.get("task_id"))
    }
    fact_order_ids = {
        normalized_option(row.get("order_id")) for row in fact_rows if normalized_option(row.get("order_id"))
    }
    mapping_rows = await RedbookTaskMapping.filter(project_id=project_id, status="active").values(
        "task_id",
        "task_name",
        "order_id",
        "product_category",
        "product_name",
    )
    options = {}
    for row in mapping_rows:
        task_id = normalized_option(row.get("task_id"))
        if not task_id:
            continue
        order_id = normalized_option(row.get("order_id"))
        if task_id not in fact_task_ids and order_id not in fact_order_ids:
            continue
        if selected_product and not product_matches(row.get("product_category"), product_filter):
            continue
        task_name = normalized_option(row.get("task_name")) or task_id
        current = options.get(task_id)
        if not current or current["label"] == task_id:
            options[task_id] = {
                "label": task_name,
                "value": task_id,
                "task_id": task_id,
                "task_name": task_name,
            }
    return sorted(options.values(), key=lambda item: (item["task_name"], item["task_id"]))


def xiaohongxing_response_payload(summary, daily_rows, task_groups, source_status, missing_mappings, kpis):
    return {
        "summary": summary,
        "cost_trend": [
            {
                "stat_date": row["stat_date"],
                "note_fee": row["note_fee"],
                "service_fee": row["service_fee"],
                "ad_cost": row["ad_cost"],
                "total_cost": row["total_cost"],
            }
            for row in daily_rows
        ],
        "search_trend": [
            {
                "stat_date": row["stat_date"],
                "search_exposure_uv": row["search_exposure_uv"],
                "search_visit_uv": row["search_visit_uv"],
                "shop_visit_uv": row["shop_visit_uv"],
                "search_component_clicks": row["search_component_clicks"],
            }
            for row in daily_rows
        ],
        "gmv_trend": [
            {
                "stat_date": row["stat_date"],
                "merchant_gmv": row["merchant_gmv"],
                "deal_uv": row["deal_uv"],
                "roi": row["roi"],
            }
            for row in daily_rows
        ],
        "daily_rows": daily_rows,
        "task_groups": task_groups,
        "source_status": source_status,
        "missing_mappings": missing_mappings,
        "kpis": kpis,
    }


async def build_xiaohongxing_dashboard_payload(
    project_id: int,
    date_start: date | None,
    date_end: date | None,
    product_category: str = "",
    task_id: str = "",
):
    if product_category or task_id:
        daily_rows, planting_dashboard = await build_filtered_xiaohongxing_daily_rows(
            project_id,
            date_start,
            date_end,
            product_category,
            task_id,
        )
        summary = xiaohongxing_summary_from_daily_rows(daily_rows, planting_dashboard.get("totals") or {})
    else:
        rows = await load_xiaohongxing_mart_rows(project_id, date_start, date_end)
        summary = xiaohongxing_summary(rows)
        daily_rows = [xiaohongxing_daily_row(row) for row in rows]
    return xiaohongxing_response_payload(
        summary=summary,
        daily_rows=daily_rows,
        task_groups=await build_task_groups(project_id, date_start, date_end, product_category, task_id),
        source_status=await build_source_status(project_id),
        missing_mappings=await build_missing_mappings(project_id, date_start, date_end),
        kpis=await build_dashboard_kpis(project_id, summary),
    )


@router.get("/product-options", summary="Redbook dashboard product options")
async def product_options(project_id: int = Query(...)):
    return Success(data=await build_product_options(project_id))


@router.get("/task-group-options", summary="Redbook dashboard task group options")
async def task_group_options(
    project_id: int = Query(...),
    product_category: str = Query(""),
):
    return Success(data=await build_task_group_options(project_id, product_category))


@router.get("/keyword-search", summary="Redbook keyword search dashboard")
async def keyword_search_dashboard(
    project_id: int = Query(...),
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    selected_keywords: str = Query(""),
    keyword: str = Query(""),
    use_default_keywords: bool = Query(False),
):
    return Success(
        data=await build_keyword_search_dashboard(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
            selected_keywords=selected_keywords,
            keyword=keyword,
            use_default_keywords=use_default_keywords,
        )
    )


@router.get("/xiaohongxing", summary="Redbook xiaohongxing dashboard")
async def xiaohongxing_dashboard(
    project_id: int = Query(...),
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    product_category: str = Query(""),
    task_id: str = Query(""),
):
    return Success(
        data=await build_xiaohongxing_dashboard_payload(project_id, date_start, date_end, product_category, task_id)
    )


@router.get("/overview", summary="Redbook dashboard overview")
async def overview(
    project_id: int = Query(...),
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    product_category: str = Query(""),
    task_id: str = Query(""),
):
    if product_category or task_id:
        payload = await build_xiaohongxing_dashboard_payload(
            project_id,
            date_start,
            date_end,
            product_category,
            task_id,
        )
        summary = payload["summary"]
        totals = {
            "note_count": summary["note_count"],
            "blogger_count": summary["blogger_count"],
            "note_fee": summary["note_fee"],
            "service_fee": summary["service_fee"],
            "ad_cost": summary["ad_cost"],
            "total_cost": summary["total_cost"],
            "impressions": summary["impressions"],
            "clicks": summary["clicks"],
            "interactions": summary["interactions"],
            "search_component_clicks": summary["search_component_clicks"],
            "task_shop_visit_uv": summary["shop_visit_uv"],
            "task_deal_uv": summary["deal_uv"],
            "task_merchant_gmv": summary["merchant_gmv"],
        }
        return Success(data={"totals": totals, "trend": payload["daily_rows"]})

    await ensure_dashboard_data(project_id, date_start, date_end, RedbookMartProjectDaily)
    rows = await apply_date_range(RedbookMartProjectDaily.filter(project_id=project_id), date_start, date_end).order_by("stat_date")
    totals = {
        "note_count": sum(row.note_count or 0 for row in rows),
        "blogger_count": sum(row.blogger_count or 0 for row in rows),
        "note_fee": sum(row.note_fee or 0 for row in rows),
        "service_fee": sum(row.service_fee or 0 for row in rows),
        "ad_cost": sum(row.ad_cost or 0 for row in rows),
        "total_cost": sum(row.total_cost or 0 for row in rows),
        "impressions": sum(row.impressions or 0 for row in rows),
        "clicks": sum(row.clicks or 0 for row in rows),
        "interactions": sum(row.interactions or 0 for row in rows),
        "search_component_clicks": sum(row.search_component_clicks or 0 for row in rows),
        "task_shop_visit_uv": sum(row.task_shop_visit_uv or 0 for row in rows),
        "task_deal_uv": sum(row.task_deal_uv or 0 for row in rows),
        "task_merchant_gmv": sum(row.task_merchant_gmv or 0 for row in rows),
    }
    return Success(data={"totals": totals, "trend": [await row.to_dict() for row in rows]})


@router.get("/ads-efficiency", summary="Redbook ads efficiency")
async def ads_efficiency(
    project_id: int = Query(...),
    date_start: date | None = Query(None),
    date_end: date | None = Query(None),
    product_category: str = Query(""),
    blogger_type: str = Query(""),
    note_type: str = Query(""),
    content_direction: str = Query(""),
    keyword: str = Query(""),
    task_id: str = Query(""),
):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookFactNoteDaily)
    return Success(
        data=await build_planting_dashboard(
            project_id=project_id,
            date_start=date_start,
            date_end=date_end,
            product_category=product_category,
            blogger_type=blogger_type,
            note_type=note_type,
            content_direction=content_direction,
            keyword=keyword,
            task_id=task_id,
        )
    )


@router.get("/search-funnel", summary="Redbook search funnel")
async def search_funnel(project_id: int = Query(...), date_start: date | None = Query(None), date_end: date | None = Query(None)):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookMartProjectDaily)
    rows = await apply_date_range(RedbookMartProjectDaily.filter(project_id=project_id), date_start, date_end).order_by("stat_date")
    return Success(
        data=[
            {
                "stat_date": row.stat_date,
                "search_component_clicks": row.search_component_clicks,
                "task_search_exposure_uv": row.task_search_exposure_uv,
                "task_search_visit_uv": row.task_search_visit_uv,
                "search_component_cost": row.search_component_cost,
            }
            for row in rows
        ]
    )


@router.get("/conversion-funnel", summary="Redbook conversion funnel")
async def conversion_funnel(project_id: int = Query(...), date_start: date | None = Query(None), date_end: date | None = Query(None)):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookMartProjectDaily)
    rows = await apply_date_range(RedbookMartProjectDaily.filter(project_id=project_id), date_start, date_end).order_by("stat_date")
    return Success(
        data={
            "read_play_uv": sum(row.task_read_play_uv or 0 for row in rows),
            "search_exposure_uv": sum(row.task_search_exposure_uv or 0 for row in rows),
            "search_visit_uv": sum(row.task_search_visit_uv or 0 for row in rows),
            "shop_visit_uv": sum(row.task_shop_visit_uv or 0 for row in rows),
            "collect_cart_uv": sum((row.task_product_collect_uv or 0) + (row.task_product_cart_uv or 0) for row in rows),
            "deal_uv": sum(row.task_deal_uv or 0 for row in rows),
            "merchant_gmv": sum(row.task_merchant_gmv or 0 for row in rows),
        }
    )


@router.get("/task-performance", summary="Redbook task performance")
async def task_performance(project_id: int = Query(...), date_start: date | None = Query(None), date_end: date | None = Query(None)):
    await ensure_dashboard_data(project_id, date_start, date_end, RedbookFactTaskDaily)
    rows = await apply_date_range(RedbookFactTaskDaily.filter(project_id=project_id), date_start, date_end).order_by("-stat_date")
    return Success(data=[await row.to_dict() for row in rows])
