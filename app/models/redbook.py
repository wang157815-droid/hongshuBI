from tortoise import fields

from .base import BaseModel, TimestampMixin


class RedbookProject(BaseModel, TimestampMixin):
    project_code = fields.CharField(max_length=64, unique=True, description="项目编码", index=True)
    project_name = fields.CharField(max_length=128, description="项目名称", index=True)
    brand_name = fields.CharField(max_length=128, null=True, description="品牌名", index=True)
    project_period = fields.CharField(max_length=64, null=True, description="项目周期", index=True)
    start_date = fields.DateField(null=True, description="开始日期", index=True)
    end_date = fields.DateField(null=True, description="结束日期", index=True)
    status = fields.CharField(max_length=32, default="active", description="状态", index=True)
    remark = fields.TextField(null=True, description="备注")
    created_by = fields.BigIntField(null=True, description="创建人")

    class Meta:
        table = "redbook_project"


class RedbookFileUpload(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_type = fields.CharField(max_length=64, description="数据源类型", index=True)
    original_file_name = fields.CharField(max_length=255, description="原始文件名")
    stored_file_path = fields.CharField(max_length=512, description="存储路径")
    file_ext = fields.CharField(max_length=16, null=True, description="文件扩展名")
    file_size = fields.BigIntField(default=0, description="文件大小")
    file_hash = fields.CharField(max_length=128, null=True, description="文件哈希", index=True)
    sheet_names = fields.JSONField(null=True, description="Excel sheet列表")
    upload_user_id = fields.BigIntField(null=True, description="上传人")
    upload_time = fields.DatetimeField(auto_now_add=True, description="上传时间", index=True)
    parse_status = fields.CharField(max_length=32, default="pending", description="解析状态", index=True)
    parser_version = fields.CharField(max_length=32, null=True, description="解析器版本")
    total_rows = fields.IntField(default=0, description="总行数")
    data_rows = fields.IntField(default=0, description="明细行数")
    success_rows = fields.IntField(default=0, description="成功行数")
    failed_rows = fields.IntField(default=0, description="失败行数")
    warning_count = fields.IntField(default=0, description="警告数")
    unmatched_note_count = fields.IntField(default=0, description="未匹配note数")
    unmatched_order_count = fields.IntField(default=0, description="未匹配order数")
    error_message = fields.TextField(null=True, description="错误摘要")
    summary_json = fields.JSONField(null=True, description="解析摘要")
    parsed_at = fields.DatetimeField(null=True, description="解析时间", index=True)

    class Meta:
        table = "redbook_file_upload"


class RedbookParseError(BaseModel, TimestampMixin):
    file_id = fields.BigIntField(description="文件ID", index=True)
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_type = fields.CharField(max_length=64, description="数据源类型", index=True)
    sheet_name = fields.CharField(max_length=128, null=True, description="sheet名")
    row_number = fields.IntField(null=True, description="行号", index=True)
    column_name = fields.CharField(max_length=128, null=True, description="列名")
    raw_value = fields.TextField(null=True, description="原始值")
    error_code = fields.CharField(max_length=64, description="错误码", index=True)
    error_level = fields.CharField(max_length=32, default="error", description="错误级别", index=True)
    error_message = fields.TextField(null=True, description="错误信息")

    class Meta:
        table = "redbook_parse_error"


class RedbookNoteMapping(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    note_id = fields.CharField(max_length=128, description="笔记ID", index=True)
    blogger_name = fields.CharField(max_length=128, null=True, description="达人名称", index=True)
    blogger_type = fields.CharField(max_length=64, null=True, description="达人类型", index=True)
    note_type = fields.CharField(max_length=64, null=True, description="笔记类型", index=True)
    product_name = fields.CharField(max_length=128, null=True, description="产品名称", index=True)
    product_category = fields.CharField(max_length=128, null=True, description="产品分类", index=True)
    content_direction = fields.CharField(max_length=128, null=True, description="内容方向", index=True)
    note_url = fields.CharField(max_length=512, null=True, description="笔记链接")
    publish_date = fields.DateField(null=True, description="发布时间", index=True)
    status = fields.CharField(max_length=32, default="active", description="状态", index=True)
    source_file_id = fields.BigIntField(null=True, description="来源文件ID", index=True)

    class Meta:
        table = "redbook_note_mapping"
        unique_together = (("project_id", "note_id"),)


class RedbookTaskMapping(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    order_id = fields.CharField(max_length=128, description="订单ID", index=True)
    task_id = fields.CharField(max_length=128, null=True, description="任务ID", index=True)
    task_name = fields.CharField(max_length=128, null=True, description="任务名称", index=True)
    task_type = fields.CharField(max_length=64, null=True, description="任务类型", index=True)
    product_name = fields.CharField(max_length=128, null=True, description="产品名称", index=True)
    product_category = fields.CharField(max_length=128, null=True, description="产品分类", index=True)
    blogger_type = fields.CharField(max_length=64, null=True, description="达人类型", index=True)
    cooperation_mode = fields.CharField(max_length=128, null=True, description="合作模式")
    status = fields.CharField(max_length=32, default="active", description="状态", index=True)
    source_file_id = fields.BigIntField(null=True, description="来源文件ID", index=True)

    class Meta:
        table = "redbook_task_mapping"
        unique_together = (("project_id", "order_id"),)


class RedbookTaskNoteBridge(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    task_id = fields.CharField(max_length=128, null=True, description="任务ID", index=True)
    order_id = fields.CharField(max_length=128, null=True, description="订单ID", index=True)
    note_id = fields.CharField(max_length=128, description="笔记ID", index=True)
    relation_type = fields.CharField(max_length=64, default="manual", description="关系来源")
    weight = fields.DecimalField(max_digits=18, decimal_places=6, default=1, description="权重")

    class Meta:
        table = "redbook_task_note_bridge"


class RedbookDimensionDict(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(null=True, description="项目ID", index=True)
    dict_type = fields.CharField(max_length=64, description="字典类型", index=True)
    dict_code = fields.CharField(max_length=128, description="编码", index=True)
    dict_label = fields.CharField(max_length=128, description="展示名")
    sort_order = fields.IntField(default=0, description="排序")
    status = fields.CharField(max_length=32, default="active", description="状态", index=True)

    class Meta:
        table = "redbook_dimension_dict"


class RedbookKeywordConfig(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    keyword = fields.CharField(max_length=128, description="搜索词", index=True)
    product_category = fields.CharField(max_length=128, null=True, description="品类", index=True)
    keyword_type = fields.CharField(max_length=64, default="custom", description="搜索词类型", index=True)
    is_brand_keyword = fields.BooleanField(default=False, description="是否品牌词")
    is_product_keyword = fields.BooleanField(default=False, description="是否产品词")
    is_competitor_keyword = fields.BooleanField(default=False, description="是否竞品词")
    is_default_selected = fields.BooleanField(default=False, description="是否默认展示")
    is_kpi_keyword = fields.BooleanField(default=False, description="是否KPI关键词")
    kpi_name = fields.CharField(max_length=128, null=True, description="KPI名称")
    sort_order = fields.IntField(default=0, description="排序")
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "redbook_keyword_config"
        unique_together = (("project_id", "keyword"),)


class RedbookKpiConfig(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    kpi_code = fields.CharField(max_length=64, description="KPI编码", index=True)
    kpi_name = fields.CharField(max_length=128, description="KPI名称")
    metric_code = fields.CharField(max_length=64, description="绑定指标")
    target_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="目标值")
    weight_score = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="权重分")
    direction = fields.CharField(max_length=32, default="higher_better", description="方向")
    cap_at_full_score = fields.BooleanField(default=True, description="是否封顶")
    formula_version = fields.CharField(max_length=32, default="v1", description="公式版本")
    cost_scope = fields.CharField(max_length=64, default="exclude_service_fee", description="费用口径")
    status = fields.CharField(max_length=32, default="active", description="状态", index=True)

    class Meta:
        table = "redbook_kpi_config"


class RedbookRawJuguang(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_file_id = fields.BigIntField(description="来源文件ID", index=True)
    row_number = fields.IntField(null=True, description="原始行号")
    stat_date = fields.DateField(null=True, description="统计日期", index=True)
    creative_name = fields.CharField(max_length=255, null=True, description="创意名称")
    creative_id = fields.CharField(max_length=128, null=True, description="创意ID", index=True)
    note_id = fields.CharField(max_length=128, null=True, description="笔记/素材ID", index=True)
    note_url = fields.CharField(max_length=1024, null=True, description="笔记链接")
    unit_name = fields.CharField(max_length=255, null=True, description="单元名称")
    unit_id = fields.CharField(max_length=128, null=True, description="单元ID", index=True)
    plan_name = fields.CharField(max_length=255, null=True, description="计划名称")
    plan_id = fields.CharField(max_length=128, null=True, description="计划ID", index=True)
    creator_name = fields.CharField(max_length=128, null=True, description="创作者", index=True)
    placement = fields.CharField(max_length=128, null=True, description="投放位置", index=True)
    optimize_goal = fields.CharField(max_length=128, null=True, description="优化目标", index=True)
    cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="消费")
    impressions = fields.BigIntField(null=True, description="展现量")
    clicks = fields.BigIntField(null=True, description="点击量")
    ctr = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="点击率")
    cpc = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="平均点击成本")
    cpm = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="平均千次展现费用")
    likes = fields.BigIntField(null=True, description="点赞")
    collects = fields.BigIntField(null=True, description="收藏")
    comments = fields.BigIntField(null=True, description="评论")
    follows = fields.BigIntField(null=True, description="关注")
    shares = fields.BigIntField(null=True, description="分享")
    interactions = fields.BigIntField(null=True, description="互动量")
    cpe = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="平均互动成本")
    action_button_clicks = fields.BigIntField(null=True, description="行动按钮点击量")
    action_button_ctr = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="行动按钮点击率")
    screenshots = fields.BigIntField(null=True, description="截图")
    save_images = fields.BigIntField(null=True, description="保存图片")
    search_component_clicks = fields.BigIntField(null=True, description="搜索组件点击量")
    search_component_ctr = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="搜索组件点击转化率")
    post_search_reads = fields.BigIntField(null=True, description="搜后阅读量")
    offsite_active_uv_30d = fields.BigIntField(null=True, description="站外活跃UV")
    offsite_active_cost_30d = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="站外活跃成本")
    new_seed_users = fields.BigIntField(null=True, description="新增种草人群")
    new_seed_user_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="新增种草人群成本")
    new_deep_seed_users = fields.BigIntField(null=True, description="新增深度种草人群")
    new_deep_seed_user_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="新增深度种草人群成本")
    raw_json = fields.JSONField(null=True, description="原始行")

    class Meta:
        table = "redbook_raw_juguang"


class RedbookRawPgyWide(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_file_id = fields.BigIntField(description="来源文件ID", index=True)
    row_number = fields.IntField(null=True, description="原始行号")
    update_date = fields.DateField(null=True, description="更新日期", index=True)
    note_id = fields.CharField(max_length=128, null=True, description="笔记ID", index=True)
    raw_json = fields.JSONField(null=True, description="原始宽表行")

    class Meta:
        table = "redbook_raw_pgy_wide"


class RedbookRawPgy(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_file_id = fields.BigIntField(description="来源文件ID", index=True)
    row_number = fields.IntField(null=True, description="原始行号")
    update_date = fields.DateField(null=True, description="数据更新日期", index=True)
    blogger_name = fields.CharField(max_length=128, null=True, description="博主昵称", index=True)
    blogger_home_url = fields.CharField(max_length=512, null=True, description="主页链接")
    fans_count = fields.BigIntField(null=True, description="粉丝量")
    health_level = fields.CharField(max_length=64, null=True, description="健康等级")
    note_title = fields.CharField(max_length=512, null=True, description="笔记标题")
    note_url = fields.CharField(max_length=1024, null=True, description="笔记链接")
    note_type = fields.CharField(max_length=64, null=True, description="笔记类型", index=True)
    publish_date = fields.DateField(null=True, description="发布日期", index=True)
    note_source = fields.CharField(max_length=128, null=True, description="笔记来源")
    note_id = fields.CharField(max_length=128, null=True, description="笔记ID", index=True)
    content_tag = fields.CharField(max_length=128, null=True, description="内容标签")
    order_id = fields.CharField(max_length=128, null=True, description="订单ID", index=True)
    task_id = fields.CharField(max_length=128, null=True, description="任务ID", index=True)
    cooperation_name = fields.CharField(max_length=128, null=True, description="合作名称")
    brand_name = fields.CharField(max_length=128, null=True, description="品牌")
    account_name = fields.CharField(max_length=128, null=True, description="下单账号")
    blogger_quote_amount = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="博主报价")
    service_fee_amount = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="服务费")
    is_effective_mode = fields.CharField(max_length=32, null=True, description="是否优效")
    spu_name = fields.CharField(max_length=255, null=True, description="SPU名称")
    exposure = fields.BigIntField(null=True, description="曝光量")
    read_count = fields.BigIntField(null=True, description="阅读量")
    read_uv = fields.BigIntField(null=True, description="阅读UV")
    interaction_count = fields.BigIntField(null=True, description="互动量")
    interaction_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="互动率")
    like_count = fields.BigIntField(null=True, description="点赞量")
    collect_count = fields.BigIntField(null=True, description="收藏量")
    comment_count = fields.BigIntField(null=True, description="评论量")
    share_count = fields.BigIntField(null=True, description="分享量")
    follow_count = fields.BigIntField(null=True, description="关注量")
    natural_exposure = fields.BigIntField(null=True, description="自然曝光")
    natural_read_count = fields.BigIntField(null=True, description="自然阅读")
    promotion_exposure = fields.BigIntField(null=True, description="推广曝光")
    promotion_read_count = fields.BigIntField(null=True, description="推广阅读")
    heat_exposure = fields.BigIntField(null=True, description="加热曝光")
    heat_read_count = fields.BigIntField(null=True, description="加热阅读")
    raw_json = fields.JSONField(null=True, description="标准字段原始值")

    class Meta:
        table = "redbook_raw_pgy"


class RedbookRawXiaohongxingOrderDaily(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_file_id = fields.BigIntField(description="来源文件ID", index=True)
    row_number = fields.IntField(null=True, description="原始行号")
    stat_date = fields.DateField(null=True, description="统计日期", index=True)
    order_id = fields.CharField(max_length=128, null=True, description="订单ID", index=True)
    traffic_type = fields.CharField(max_length=64, null=True, description="流量类型")
    attribution_window = fields.IntField(null=True, description="归因周期")
    read_play_uv = fields.BigIntField(null=True, description="阅读播放UV")
    like_uv = fields.BigIntField(null=True, description="点赞UV")
    comment_uv = fields.BigIntField(null=True, description="评论UV")
    collect_uv = fields.BigIntField(null=True, description="收藏UV")
    share_uv = fields.BigIntField(null=True, description="转发UV")
    interaction_uv = fields.BigIntField(null=True, description="互动UV")
    content_interaction_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="内容互动率")
    search_exposure_uv = fields.BigIntField(null=True, description="搜索曝光UV")
    search_visit_uv = fields.BigIntField(null=True, description="搜索进店UV")
    shop_visit_uv = fields.BigIntField(null=True, description="进店UV")
    new_customer_visit_uv = fields.BigIntField(null=True, description="新客进店UV")
    product_collect_uv = fields.BigIntField(null=True, description="商品收藏UV")
    product_cart_uv = fields.BigIntField(null=True, description="商品加购UV")
    shop_follow_uv = fields.BigIntField(null=True, description="关注店铺UV")
    shop_member_uv = fields.BigIntField(null=True, description="店铺会员UV")
    deal_uv = fields.BigIntField(null=True, description="成交UV")
    merchant_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="商家GMV")
    order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="订单商品GMV")
    non_order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="非订单商品GMV")
    new_customer_deal_uv = fields.BigIntField(null=True, description="新客成交UV")
    order_product_new_customer_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="订单商品新客GMV")
    presale_deposit_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售付定GMV")
    presale_estimated_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售预估GMV")
    presale_deposit_uv = fields.BigIntField(null=True, description="预售付定UV")
    deal_conversion_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="成交转化率")
    raw_json = fields.JSONField(null=True, description="原始行")

    class Meta:
        table = "redbook_raw_xiaohongxing_order_daily"


class RedbookRawKeywordSearch(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    source_file_id = fields.BigIntField(description="来源文件ID", index=True)
    row_number = fields.IntField(null=True, description="原始行号")
    column_number = fields.IntField(null=True, description="原始列号")
    stat_date = fields.DateField(null=True, description="搜索指数日期", index=True)
    keyword = fields.CharField(max_length=128, description="搜索词", index=True)
    product_category = fields.CharField(max_length=128, null=True, description="品类", index=True)
    keyword_type = fields.CharField(max_length=64, default="custom", description="搜索词类型", index=True)
    raw_value = fields.CharField(max_length=64, null=True, description="原始值")
    search_index = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="可确定的搜索指数")
    is_less_than_threshold = fields.BooleanField(default=False, description="是否小于阈值", index=True)
    threshold_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="阈值")
    estimate_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="可选估算值")
    raw_json = fields.JSONField(null=True, description="原始单元格信息")

    class Meta:
        table = "redbook_raw_keyword_search"


class RedbookFactNoteDaily(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    stat_date = fields.DateField(null=True, description="日期", index=True)
    note_id = fields.CharField(max_length=128, null=True, description="笔记ID", index=True)
    blogger_name = fields.CharField(max_length=128, null=True, description="达人", index=True)
    blogger_type = fields.CharField(max_length=64, null=True, description="达人类型", index=True)
    note_type = fields.CharField(max_length=64, null=True, description="笔记类型", index=True)
    product_name = fields.CharField(max_length=128, null=True, description="产品")
    product_category = fields.CharField(max_length=128, null=True, description="品类", index=True)
    content_direction = fields.CharField(max_length=128, null=True, description="内容方向", index=True)
    publish_date = fields.DateField(null=True, description="发布时间")
    note_fee = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="笔记费用")
    service_fee = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="服务费")
    ad_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="投流费用")
    impressions = fields.BigIntField(null=True, description="展现")
    clicks = fields.BigIntField(null=True, description="点击")
    interactions = fields.BigIntField(null=True, description="互动")
    search_component_clicks = fields.BigIntField(null=True, description="搜索组件点击")
    offsite_active_uv_30d = fields.BigIntField(null=True, description="站外活跃UV")
    new_seed_users = fields.BigIntField(null=True, description="新增种草")
    new_deep_seed_users = fields.BigIntField(null=True, description="新增深度种草")
    pgy_exposure = fields.BigIntField(null=True, description="蒲公英曝光")
    pgy_read_count = fields.BigIntField(null=True, description="蒲公英阅读")
    pgy_interaction_count = fields.BigIntField(null=True, description="蒲公英互动")
    ctr = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="CTR")
    cpc = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPC")
    cpm = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPM")
    cpe = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPE")

    class Meta:
        table = "redbook_fact_note_daily"


class RedbookFactTaskDaily(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    stat_date = fields.DateField(null=True, description="日期", index=True)
    order_id = fields.CharField(max_length=128, null=True, description="订单ID", index=True)
    task_id = fields.CharField(max_length=128, null=True, description="任务ID", index=True)
    task_name = fields.CharField(max_length=128, null=True, description="任务名称", index=True)
    task_type = fields.CharField(max_length=64, null=True, description="任务类型", index=True)
    product_name = fields.CharField(max_length=128, null=True, description="产品")
    product_category = fields.CharField(max_length=128, null=True, description="品类", index=True)
    blogger_type = fields.CharField(max_length=64, null=True, description="达人类型", index=True)
    read_play_uv = fields.BigIntField(null=True, description="阅读播放UV")
    like_uv = fields.BigIntField(null=True, description="点赞UV")
    collect_uv = fields.BigIntField(null=True, description="收藏UV")
    comment_uv = fields.BigIntField(null=True, description="评论UV")
    share_uv = fields.BigIntField(null=True, description="转发UV")
    interaction_uv = fields.BigIntField(null=True, description="互动UV")
    content_interaction_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="内容互动率")
    search_exposure_uv = fields.BigIntField(null=True, description="搜索曝光UV")
    search_visit_uv = fields.BigIntField(null=True, description="搜索进店UV")
    shop_visit_uv = fields.BigIntField(null=True, description="进店UV")
    new_customer_visit_uv = fields.BigIntField(null=True, description="新客进店UV")
    product_collect_uv = fields.BigIntField(null=True, description="商品收藏UV")
    product_cart_uv = fields.BigIntField(null=True, description="商品加购UV")
    shop_follow_uv = fields.BigIntField(null=True, description="关注店铺UV")
    shop_member_uv = fields.BigIntField(null=True, description="店铺会员UV")
    deal_uv = fields.BigIntField(null=True, description="成交UV")
    merchant_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="商家GMV")
    order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="订单商品GMV")
    non_order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="非订单商品GMV")
    new_customer_deal_uv = fields.BigIntField(null=True, description="新客成交UV")
    order_product_new_customer_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="订单商品新客GMV")
    presale_deposit_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售付定GMV")
    presale_estimated_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售预计GMV")
    presale_deposit_uv = fields.BigIntField(null=True, description="预售付定UV")
    deal_conversion_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="成交转化率")
    visit_uv_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="进店成本")
    roi = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="ROI")

    class Meta:
        table = "redbook_fact_task_daily"


class RedbookMartProjectDaily(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    stat_date = fields.DateField(null=True, description="日期", index=True)
    note_count = fields.IntField(default=0, description="笔记数")
    blogger_count = fields.IntField(default=0, description="达人数")
    note_fee = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="笔记费用")
    service_fee = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="服务费")
    ad_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="投流费用")
    total_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="总花费")
    total_cost_with_service = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="含服务费总花费")
    impressions = fields.BigIntField(null=True, description="展现")
    clicks = fields.BigIntField(null=True, description="点击")
    interactions = fields.BigIntField(null=True, description="互动")
    search_component_clicks = fields.BigIntField(null=True, description="搜索组件点击")
    offsite_active_uv_30d = fields.BigIntField(null=True, description="站外活跃UV")
    pgy_exposure = fields.BigIntField(null=True, description="蒲公英曝光")
    pgy_read_count = fields.BigIntField(null=True, description="蒲公英阅读")
    pgy_interaction_count = fields.BigIntField(null=True, description="蒲公英互动")
    task_read_play_uv = fields.BigIntField(null=True, description="任务阅读UV")
    task_like_uv = fields.BigIntField(null=True, description="任务点赞UV")
    task_collect_uv = fields.BigIntField(null=True, description="任务收藏UV")
    task_comment_uv = fields.BigIntField(null=True, description="任务评论UV")
    task_share_uv = fields.BigIntField(null=True, description="任务转发UV")
    task_interaction_uv = fields.BigIntField(null=True, description="任务互动UV")
    task_search_exposure_uv = fields.BigIntField(null=True, description="搜索曝光UV")
    task_search_visit_uv = fields.BigIntField(null=True, description="搜索进店UV")
    task_shop_visit_uv = fields.BigIntField(null=True, description="进店UV")
    task_new_customer_visit_uv = fields.BigIntField(null=True, description="新客进店UV")
    task_product_collect_uv = fields.BigIntField(null=True, description="商品收藏UV")
    task_product_cart_uv = fields.BigIntField(null=True, description="商品加购UV")
    task_shop_follow_uv = fields.BigIntField(null=True, description="关注店铺UV")
    task_shop_member_uv = fields.BigIntField(null=True, description="店铺会员UV")
    task_deal_uv = fields.BigIntField(null=True, description="成交UV")
    task_new_customer_deal_uv = fields.BigIntField(null=True, description="新客成交UV")
    task_merchant_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="商家GMV")
    task_order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="任务商品成交GMV")
    task_non_order_product_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="非任务商品成交GMV")
    task_order_product_new_customer_gmv = fields.DecimalField(
        max_digits=20, decimal_places=6, null=True, description="任务商品新客成交GMV"
    )
    task_presale_deposit_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售付定GMV")
    task_presale_estimated_gmv = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="预售预计GMV")
    task_presale_deposit_uv = fields.BigIntField(null=True, description="预售付定UV")
    cpc = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPC")
    cpm = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPM")
    cpe = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="CPE")
    search_component_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="搜索组件成本")
    visit_uv_cost = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="进店成本")
    roi = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="ROI")

    class Meta:
        table = "redbook_mart_project_daily"


class RedbookKpiResult(BaseModel, TimestampMixin):
    project_id = fields.BigIntField(description="项目ID", index=True)
    kpi_config_id = fields.BigIntField(null=True, description="KPI配置ID", index=True)
    kpi_code = fields.CharField(max_length=64, description="KPI编码", index=True)
    kpi_name = fields.CharField(max_length=128, description="KPI名称")
    actual_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="实际值")
    target_value = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="目标值")
    weight_score = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="权重分")
    achievement_rate = fields.DecimalField(max_digits=20, decimal_places=8, null=True, description="达成率")
    actual_score = fields.DecimalField(max_digits=20, decimal_places=6, null=True, description="实际得分")
    formula_version = fields.CharField(max_length=32, default="v1", description="公式版本")
    stat_date = fields.DateField(null=True, description="计算日期", index=True)

    class Meta:
        table = "redbook_kpi_result"
