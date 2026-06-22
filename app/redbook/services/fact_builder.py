from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.models.redbook import (
    RedbookFactNoteDaily,
    RedbookFactTaskDaily,
    RedbookMartProjectDaily,
    RedbookNoteMapping,
    RedbookRawJuguang,
    RedbookRawPgy,
    RedbookRawXiaohongxingOrderDaily,
    RedbookTaskMapping,
)


def dec(value) -> Decimal:
    return Decimal("0") if value is None else Decimal(str(value))


def div(numerator, denominator, multiplier=Decimal("1")):
    denominator = dec(denominator)
    if denominator == 0:
        return None
    return dec(numerator) / denominator * multiplier


def add_int(target, key, value):
    target[key] += int(value or 0)


def add_dec(target, key, value):
    target[key] += dec(value)


def in_date_range(value: date | None, date_start: date | None = None, date_end: date | None = None):
    if not value:
        return False
    if date_start and value < date_start:
        return False
    if date_end and value > date_end:
        return False
    return True


async def latest_pgy_by_note(project_id: int):
    latest = {}
    for item in await RedbookRawPgy.filter(project_id=project_id).order_by("note_id", "-update_date"):
        if item.note_id and item.note_id not in latest:
            latest[item.note_id] = item
    return latest


async def rebuild_redbook_facts(
    project_id: int,
    date_start: date | None = None,
    date_end: date | None = None,
    build_note_daily: bool = True,
    build_task_daily: bool = True,
    build_project_daily: bool = True,
):
    result = {}
    if build_note_daily:
        result["note_daily"] = await rebuild_note_daily(project_id, date_start, date_end)
    if build_task_daily:
        result["task_daily"] = await rebuild_task_daily(project_id, date_start, date_end)
    if build_project_daily:
        result["project_daily"] = await rebuild_project_daily(project_id, date_start, date_end)
    return result


async def rebuild_note_daily(project_id: int, date_start: date | None = None, date_end: date | None = None):
    delete_query = RedbookFactNoteDaily.filter(project_id=project_id)
    raw_query = RedbookRawJuguang.filter(project_id=project_id)
    if date_start:
        delete_query = delete_query.filter(stat_date__gte=date_start)
        raw_query = raw_query.filter(stat_date__gte=date_start)
    if date_end:
        delete_query = delete_query.filter(stat_date__lte=date_end)
        raw_query = raw_query.filter(stat_date__lte=date_end)
    await delete_query.delete()

    mappings = {item.note_id: item for item in await RedbookNoteMapping.filter(project_id=project_id)}
    pgy_latest = await latest_pgy_by_note(project_id)

    raw_rows = await raw_query
    grouped = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    first_stat_date_by_note = {}
    for row in raw_rows:
        if not row.stat_date or not row.note_id:
            continue
        if row.note_id not in first_stat_date_by_note or row.stat_date < first_stat_date_by_note[row.note_id]:
            first_stat_date_by_note[row.note_id] = row.stat_date
        key = (row.stat_date, row.note_id)
        add_dec(grouped[key], "ad_cost", row.cost)
        for field in ("impressions", "clicks", "interactions", "search_component_clicks", "offsite_active_uv_30d", "new_seed_users", "new_deep_seed_users"):
            add_int(grouped[key], field, getattr(row, field))

    rows = []
    for (stat_date, note_id), values in grouped.items():
        mapping = mappings.get(note_id)
        pgy = pgy_latest.get(note_id)
        publish_date = (mapping.publish_date if mapping else None) or (pgy.publish_date if pgy else None)
        fee_date = publish_date or first_stat_date_by_note.get(note_id)
        is_fee_day = fee_date == stat_date
        rows.append(
            RedbookFactNoteDaily(
                project_id=project_id,
                stat_date=stat_date,
                note_id=note_id,
                blogger_name=(mapping.blogger_name if mapping else None) or (pgy.blogger_name if pgy else None),
                blogger_type=mapping.blogger_type if mapping else None,
                note_type=(mapping.note_type if mapping else None) or (pgy.note_type if pgy else None),
                product_name=mapping.product_name if mapping else None,
                product_category=mapping.product_category if mapping else None,
                content_direction=mapping.content_direction if mapping else None,
                publish_date=publish_date,
                note_fee=pgy.blogger_quote_amount if pgy and is_fee_day else None,
                service_fee=pgy.service_fee_amount if pgy and is_fee_day else None,
                ad_cost=values["ad_cost"],
                impressions=values["impressions"],
                clicks=values["clicks"],
                interactions=values["interactions"],
                search_component_clicks=values["search_component_clicks"],
                offsite_active_uv_30d=values["offsite_active_uv_30d"],
                new_seed_users=values["new_seed_users"],
                new_deep_seed_users=values["new_deep_seed_users"],
                pgy_exposure=pgy.exposure if pgy else None,
                pgy_read_count=pgy.read_count if pgy else None,
                pgy_interaction_count=pgy.interaction_count if pgy else None,
                ctr=div(values["clicks"], values["impressions"]),
                cpc=div(values["ad_cost"], values["clicks"]),
                cpm=div(values["ad_cost"], values["impressions"], Decimal("1000")),
                cpe=div(values["ad_cost"], values["interactions"]),
            )
        )
    if rows:
        await RedbookFactNoteDaily.bulk_create(rows)
    return {"created": len(rows)}


async def rebuild_task_daily(project_id: int, date_start: date | None = None, date_end: date | None = None):
    delete_query = RedbookFactTaskDaily.filter(project_id=project_id)
    raw_query = RedbookRawXiaohongxingOrderDaily.filter(project_id=project_id)
    if date_start:
        delete_query = delete_query.filter(stat_date__gte=date_start)
        raw_query = raw_query.filter(stat_date__gte=date_start)
    if date_end:
        delete_query = delete_query.filter(stat_date__lte=date_end)
        raw_query = raw_query.filter(stat_date__lte=date_end)
    await delete_query.delete()

    mappings = {item.order_id: item for item in await RedbookTaskMapping.filter(project_id=project_id)}
    grouped = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    task_int_fields = (
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
    )
    task_decimal_fields = (
        "merchant_gmv",
        "order_product_gmv",
        "non_order_product_gmv",
        "order_product_new_customer_gmv",
        "presale_deposit_gmv",
        "presale_estimated_gmv",
    )
    for row in await raw_query:
        if not row.stat_date or not row.order_id:
            continue
        key = (row.stat_date, row.order_id)
        for field in task_int_fields:
            add_int(grouped[key], field, getattr(row, field))
        for field in task_decimal_fields:
            add_dec(grouped[key], field, getattr(row, field))

    rows = []
    for (stat_date, order_id), values in grouped.items():
        mapping = mappings.get(order_id)
        rows.append(
            RedbookFactTaskDaily(
                project_id=project_id,
                stat_date=stat_date,
                order_id=order_id,
                task_id=mapping.task_id if mapping else None,
                task_name=mapping.task_name if mapping else "未归类",
                task_type=mapping.task_type if mapping else "未匹配订单",
                product_name=mapping.product_name if mapping else None,
                product_category=mapping.product_category if mapping else None,
                blogger_type=mapping.blogger_type if mapping else None,
                read_play_uv=values["read_play_uv"],
                like_uv=values["like_uv"],
                collect_uv=values["collect_uv"],
                comment_uv=values["comment_uv"],
                share_uv=values["share_uv"],
                interaction_uv=values["interaction_uv"],
                content_interaction_rate=div(values["interaction_uv"], values["read_play_uv"]),
                search_exposure_uv=values["search_exposure_uv"],
                search_visit_uv=values["search_visit_uv"],
                shop_visit_uv=values["shop_visit_uv"],
                new_customer_visit_uv=values["new_customer_visit_uv"],
                product_collect_uv=values["product_collect_uv"],
                product_cart_uv=values["product_cart_uv"],
                shop_follow_uv=values["shop_follow_uv"],
                shop_member_uv=values["shop_member_uv"],
                deal_uv=values["deal_uv"],
                merchant_gmv=values["merchant_gmv"],
                order_product_gmv=values["order_product_gmv"],
                non_order_product_gmv=values["non_order_product_gmv"],
                new_customer_deal_uv=values["new_customer_deal_uv"],
                order_product_new_customer_gmv=values["order_product_new_customer_gmv"],
                presale_deposit_gmv=values["presale_deposit_gmv"],
                presale_estimated_gmv=values["presale_estimated_gmv"],
                presale_deposit_uv=values["presale_deposit_uv"],
                deal_conversion_rate=div(values["deal_uv"], values["shop_visit_uv"]),
            )
        )
    if rows:
        await RedbookFactTaskDaily.bulk_create(rows)
    return {"created": len(rows)}


async def rebuild_project_daily(project_id: int, date_start: date | None = None, date_end: date | None = None):
    delete_query = RedbookMartProjectDaily.filter(project_id=project_id)
    note_query = RedbookFactNoteDaily.filter(project_id=project_id)
    task_query = RedbookFactTaskDaily.filter(project_id=project_id)
    if date_start:
        delete_query = delete_query.filter(stat_date__gte=date_start)
        note_query = note_query.filter(stat_date__gte=date_start)
        task_query = task_query.filter(stat_date__gte=date_start)
    if date_end:
        delete_query = delete_query.filter(stat_date__lte=date_end)
        note_query = note_query.filter(stat_date__lte=date_end)
        task_query = task_query.filter(stat_date__lte=date_end)
    await delete_query.delete()

    grouped = defaultdict(lambda: defaultdict(lambda: Decimal("0")))
    note_sets = defaultdict(set)
    blogger_sets = defaultdict(set)
    for row in await note_query:
        if not row.stat_date:
            continue
        if row.note_id:
            note_sets[row.stat_date].add(row.note_id)
        if row.blogger_name:
            blogger_sets[row.stat_date].add(row.blogger_name)
        add_dec(grouped[row.stat_date], "ad_cost", row.ad_cost)
        for field in ("impressions", "clicks", "interactions", "search_component_clicks", "offsite_active_uv_30d"):
            add_int(grouped[row.stat_date], field, getattr(row, field))

    mappings = {item.note_id: item for item in await RedbookNoteMapping.filter(project_id=project_id)}
    for pgy in (await latest_pgy_by_note(project_id)).values():
        mapping = mappings.get(pgy.note_id)
        fee_date = (mapping.publish_date if mapping else None) or pgy.publish_date or pgy.update_date
        if not in_date_range(fee_date, date_start, date_end):
            continue
        if pgy.note_id:
            note_sets[fee_date].add(pgy.note_id)
        if pgy.blogger_name:
            blogger_sets[fee_date].add(pgy.blogger_name)
        add_dec(grouped[fee_date], "note_fee", pgy.blogger_quote_amount)
        add_dec(grouped[fee_date], "service_fee", pgy.service_fee_amount)
        add_int(grouped[fee_date], "pgy_exposure", pgy.exposure)
        add_int(grouped[fee_date], "pgy_read_count", pgy.read_count)
        add_int(grouped[fee_date], "pgy_interaction_count", pgy.interaction_count)

    for row in await task_query:
        if not row.stat_date:
            continue
        for source, target in (
            ("read_play_uv", "task_read_play_uv"),
            ("like_uv", "task_like_uv"),
            ("collect_uv", "task_collect_uv"),
            ("comment_uv", "task_comment_uv"),
            ("share_uv", "task_share_uv"),
            ("interaction_uv", "task_interaction_uv"),
            ("search_exposure_uv", "task_search_exposure_uv"),
            ("search_visit_uv", "task_search_visit_uv"),
            ("shop_visit_uv", "task_shop_visit_uv"),
            ("new_customer_visit_uv", "task_new_customer_visit_uv"),
            ("product_collect_uv", "task_product_collect_uv"),
            ("product_cart_uv", "task_product_cart_uv"),
            ("shop_follow_uv", "task_shop_follow_uv"),
            ("shop_member_uv", "task_shop_member_uv"),
            ("deal_uv", "task_deal_uv"),
            ("new_customer_deal_uv", "task_new_customer_deal_uv"),
            ("presale_deposit_uv", "task_presale_deposit_uv"),
        ):
            add_int(grouped[row.stat_date], target, getattr(row, source))
        add_dec(grouped[row.stat_date], "task_merchant_gmv", row.merchant_gmv)
        add_dec(grouped[row.stat_date], "task_order_product_gmv", row.order_product_gmv)
        add_dec(grouped[row.stat_date], "task_non_order_product_gmv", row.non_order_product_gmv)
        add_dec(grouped[row.stat_date], "task_order_product_new_customer_gmv", row.order_product_new_customer_gmv)
        add_dec(grouped[row.stat_date], "task_presale_deposit_gmv", row.presale_deposit_gmv)
        add_dec(grouped[row.stat_date], "task_presale_estimated_gmv", row.presale_estimated_gmv)

    rows = []
    for stat_date, values in grouped.items():
        total_cost = values["note_fee"] + values["ad_cost"]
        rows.append(
            RedbookMartProjectDaily(
                project_id=project_id,
                stat_date=stat_date,
                note_count=len(note_sets[stat_date]),
                blogger_count=len(blogger_sets[stat_date]),
                note_fee=values["note_fee"],
                service_fee=values["service_fee"],
                ad_cost=values["ad_cost"],
                total_cost=total_cost,
                total_cost_with_service=total_cost + values["service_fee"],
                impressions=values["impressions"],
                clicks=values["clicks"],
                interactions=values["interactions"],
                search_component_clicks=values["search_component_clicks"],
                offsite_active_uv_30d=values["offsite_active_uv_30d"],
                pgy_exposure=values["pgy_exposure"],
                pgy_read_count=values["pgy_read_count"],
                pgy_interaction_count=values["pgy_interaction_count"],
                task_read_play_uv=values["task_read_play_uv"],
                task_like_uv=values["task_like_uv"],
                task_collect_uv=values["task_collect_uv"],
                task_comment_uv=values["task_comment_uv"],
                task_share_uv=values["task_share_uv"],
                task_interaction_uv=values["task_interaction_uv"],
                task_search_exposure_uv=values["task_search_exposure_uv"],
                task_search_visit_uv=values["task_search_visit_uv"],
                task_shop_visit_uv=values["task_shop_visit_uv"],
                task_new_customer_visit_uv=values["task_new_customer_visit_uv"],
                task_product_collect_uv=values["task_product_collect_uv"],
                task_product_cart_uv=values["task_product_cart_uv"],
                task_shop_follow_uv=values["task_shop_follow_uv"],
                task_shop_member_uv=values["task_shop_member_uv"],
                task_deal_uv=values["task_deal_uv"],
                task_new_customer_deal_uv=values["task_new_customer_deal_uv"],
                task_merchant_gmv=values["task_merchant_gmv"],
                task_order_product_gmv=values["task_order_product_gmv"],
                task_non_order_product_gmv=values["task_non_order_product_gmv"],
                task_order_product_new_customer_gmv=values["task_order_product_new_customer_gmv"],
                task_presale_deposit_gmv=values["task_presale_deposit_gmv"],
                task_presale_estimated_gmv=values["task_presale_estimated_gmv"],
                task_presale_deposit_uv=values["task_presale_deposit_uv"],
                cpc=div(values["ad_cost"], values["clicks"]),
                cpm=div(values["ad_cost"], values["impressions"], Decimal("1000")),
                cpe=div(values["ad_cost"], values["interactions"]),
                search_component_cost=div(values["ad_cost"], values["search_component_clicks"]),
                visit_uv_cost=div(total_cost, values["task_shop_visit_uv"]),
                roi=div(values["task_merchant_gmv"], total_cost),
            )
        )
    if rows:
        await RedbookMartProjectDaily.bulk_create(rows)
    return {"created": len(rows)}
