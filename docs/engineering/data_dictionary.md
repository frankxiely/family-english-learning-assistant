# Data Dictionary

首版数据字典以 `db/migrations/001_initial_schema.sql` 为准。核心资产：

- `learning_profiles`
- `learning_status`
- `curriculum_route_items`
- `knowledge_points`
- `teaching_knowledge_assets`
- `lesson_json_assets`
- `learning_review_assets`
- `admin_notes`
- `debug_events`

内容知识库补充资产：

- `docs/content_knowledge_base/`：资料来源、路线设计、lesson JSON 写作规则和音频策略。
- `data/teaching_knowledge/source_catalog.v1.json`：资料来源的机器可读目录。
- `data/teaching_knowledge/starter_phonics_route.v1.json`：零基础首阶段路线图初稿。
- `data/teaching_knowledge/user_routes/`：用户级路线图，供 lesson 生成和学习进度 API 优先读取。
