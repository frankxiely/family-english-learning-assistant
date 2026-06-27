# 内容数据合同

## lesson_plan_json

`lesson_plan_json` 是 provider 输出的学习计划草稿。它必须同时具备机器可解析字段和人类可读文本。

生成前必须读取内容知识库、用户画像、学习状态、课程路线图和管理员备注。provider 只能在路线图给定的知识点、场景、时长和素材约束内填充当天课程。

关键字段：

- `schema_version`
- `user_id`
- `lesson_date`
- `human_readable_text`
- `theme`
- `objectives`
- `sections`
- `vocabulary`
- `passage`
- `knowledge_note`
- `quiz`
- `asset_requirements`
- `admin_note`
- `admin_instruction`
- `admin_revision_note`

管理员字段由管理员管理模块写入。没有内容时写 `null`。

## lesson JSON

lesson JSON 是入库目标和前端数据源。它由转译器从 `lesson_plan_json` 标准化得到。

lesson JSON 应保留 `route_basis`、`teaching_knowledge_id`、`progress_summary` 和素材需求，方便后续追溯“这一天为什么学这些内容”。

## learning_review_json

`learning_review_json` 来自真实学习记录，描述当天学得怎么样，以及明天怎么调。
