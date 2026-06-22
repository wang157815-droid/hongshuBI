import pandas as pd

from app.redbook.constants.source_type import SOURCE_XIAOHONGXING_ORDER
from app.schemas.redbook import ParseResult

from .base import BaseRedbookParser, clean_text, compact_raw, to_date, to_decimal, to_int


class XiaohongxingOrderParser(BaseRedbookParser):
    source_type = SOURCE_XIAOHONGXING_ORDER

    FIELD_MAP = {
        "日期": ("stat_date", to_date),
        "订单ID": ("order_id", clean_text),
        "流量类型": ("traffic_type", clean_text),
        "归因周期": ("attribution_window", to_int),
        "阅读/播放UV": ("read_play_uv", to_int),
        "点赞UV": ("like_uv", to_int),
        "评论UV": ("comment_uv", to_int),
        "收藏UV": ("collect_uv", to_int),
        "转发UV": ("share_uv", to_int),
        "互动UV": ("interaction_uv", to_int),
        "内容互动率": ("content_interaction_rate", lambda v: to_decimal(v, is_percent=True)),
        "搜索曝光UV": ("search_exposure_uv", to_int),
        "搜索进店UV": ("search_visit_uv", to_int),
        "进店UV": ("shop_visit_uv", to_int),
        "新客进店uv": ("new_customer_visit_uv", to_int),
        "商品收藏UV": ("product_collect_uv", to_int),
        "商品加购UV": ("product_cart_uv", to_int),
        "关注店铺UV": ("shop_follow_uv", to_int),
        "店铺会员UV": ("shop_member_uv", to_int),
        "成交UV": ("deal_uv", to_int),
        "商家GMV": ("merchant_gmv", to_decimal),
        "订单商品成交GMV": ("order_product_gmv", to_decimal),
        "非订单商品成交GMV": ("non_order_product_gmv", to_decimal),
        "新客成交UV": ("new_customer_deal_uv", to_int),
        "订单商品新客成交GMV": ("order_product_new_customer_gmv", to_decimal),
        "预售付定GMV": ("presale_deposit_gmv", to_decimal),
        "预售整单预估GMV": ("presale_estimated_gmv", to_decimal),
        "预售付定UV": ("presale_deposit_uv", to_int),
        "成交转化率": ("deal_conversion_rate", lambda v: to_decimal(v, is_percent=True)),
    }
    REQUIRED_HEADERS = {"日期", "订单ID", "阅读/播放UV", "进店UV", "商家GMV"}

    def parse(self) -> ParseResult:
        dataframe = pd.read_csv(self.file_path, encoding="utf-8-sig", dtype=str)
        missing = sorted(self.REQUIRED_HEADERS - set(dataframe.columns))
        if missing:
            for header in missing:
                self.error(1, header, None, "missing_header", f"缺少必填字段：{header}")
            return ParseResult(source_type=self.source_type, total_rows=len(dataframe), errors=self.errors)

        records = []
        for index, row in dataframe.iterrows():
            row_number = int(index) + 2
            raw = row.where(pd.notna(row), None).to_dict()
            record = {"row_number": row_number}
            for source_header, (target_field, converter) in self.FIELD_MAP.items():
                if source_header in raw:
                    record[target_field] = converter(raw[source_header])
            if not record.get("order_id"):
                self.warn(row_number, "订单ID", None, "missing_order_id", "订单ID为空")
            record["raw_json"] = compact_raw(raw)
            records.append(record)

        return ParseResult(
            source_type=self.source_type,
            total_rows=len(dataframe),
            data_rows=len(records),
            success_rows=len(records),
            failed_rows=len(self.errors),
            warnings=self.warnings,
            errors=self.errors,
            records=records,
            summary={"columns": list(dataframe.columns)},
        )
