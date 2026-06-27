# API Contract

## Auth

### POST /api/auth/login

本地主机登录接口。v1.1 使用预置学习者账号，不做正式公网账号体系。

请求体：

- `login_account`
- `password`
- `remember`

返回的 `session.username` 是可重复的用户展示名；`session.login_account` 是唯一登录账号。
登录成功后返回 `session.session_token` 和 `session.expires_at`。管理员端调用 `/api/admin/*` 和 `/api/debug/modules` 时必须使用：

- `Authorization: Bearer <session_token>`

当前预置账号：

- 登录账号：`ViZhang`
- 用户名/展示名：`Vi`
- `Frank1229`

当前本地管理员账号：

- 登录账号：`admin_xly`
- `Admin1229`

## Learning

### GET /api/learning/today

查询学习者当天已发布的标准 lesson JSON。若当天还没有发布内容，系统会用本地模板生成一个可用版本。

参数：

- `user_id`
- `date` 可选，默认当天

### POST /api/learning/complete

提交真实学习记录，并生成 `learning_review_json`。

请求体核心字段：

- `lesson_asset_id`
- `completed_sections`
- `word_mastery`：每个单词的 `known`、`fuzzy` 或 `unknown`
- `quiz_answers`：题干和用户选择
- `difficulty_notes`
- `self_rating`
- `learning_minutes`

### GET /api/learning/state

查询用户画像、学习状态、知识点进度、场景进度、词汇掌握和复习队列。

### GET /api/learning/review

查询某天的学习复盘 JSON。

### GET /api/learning/weekly-summary

查询最近 7 天简版进度分析，并写入 RAG 来源表。

## Admin

### GET /api/admin/users

需要管理员 token。

返回学习者目录，用于管理员选择用户。

### GET /api/admin/users/{user_id}/workspace

需要管理员 token。

返回单个用户工作台数据：用户信息、登录账号、最新未发布草稿、当天已发布课程、学习画像概览和管理员反馈日志。

### GET /api/admin/users/{user_id}/learning-overview

需要管理员 token。

根据 `learning_review_assets`、`vocabulary_mastery` 和 `learning_status` 汇总学习天数、词汇量估计、薄弱项、下一步建议和近期复盘。

### GET /api/admin/dashboard

需要管理员 token。

管理员工作台聚合接口，返回画像、学习状态、当前 lesson 资产、版本、备注、调整日志、最近复盘和最近进度。
其中 `user.nickname` 是可重复用户名，`login_accounts[].login_account` 是唯一登录账号。
该接口保留为兼容接口；v1.1 新管理员主界面优先使用 `/api/admin/users` 和 `/api/admin/users/{user_id}/workspace`。

### PUT /api/admin/users/{user_id}/profile

需要管理员 token。

管理员修改学习者画像，包括目标、每天学习时长、场景偏好和备注。
也可传入 `username` 或 `display_username` 修改用户展示名；该字段允许重复，不作为登录凭证。

### POST /api/admin/notes

需要管理员 token。

保存管理员备注。备注属于管理员管理模块，生成器会在下次生成草稿时抽取；无备注时标准 JSON 中对应字段为 `null`。

### POST /api/admin/generate/today

需要管理员 token。

根据数据库上下文生成今日 lesson 草稿。草稿写入 `lesson_draft_workspaces`，不会进入正式 `lesson_json_assets`。

### POST /api/admin/drafts/generate

需要管理员 token。

按 `user_id`、`lesson_date` 和可选 `admin_instruction` 生成未发布课程草稿。

### PUT /api/admin/drafts/{draft_id}/note

需要管理员 token。

把管理员备注写入草稿 JSON 的 `admin_note`。

### POST /api/admin/drafts/{draft_id}/ai-adjust

需要管理员 token。

根据管理员调整指令重新生成未发布草稿。v1.1 无 OpenAI API 时由本地模板 provider 记录并生成结构化 JSON。

### PUT /api/admin/drafts/{draft_id}

需要管理员 token。

保存人工编辑后的完整 lesson JSON 草稿，并为“还原上一步”写入快照。

### POST /api/admin/drafts/{draft_id}/undo

需要管理员 token。

把未发布草稿恢复到上一步；可连续调用，直到没有更早快照。

### POST /api/admin/drafts/{draft_id}/publish

需要管理员 token。

发布未发布草稿。发布后才写入正式 `lesson_json_assets` 并派生结构化课程表。

### POST /api/admin/feedback

需要管理员 token。

记录管理员对生成质量或后台体验的反馈，写入 `admin_feedback_logs`，不混入学习者 lesson JSON。

### PUT /api/admin/lessons/{lesson_asset_id}/draft

需要管理员 token。

保存管理员修改后的 lesson JSON 草稿，并写入版本和修订记录。

### POST /api/admin/lessons/{lesson_asset_id}/publish

需要管理员 token。

发布草稿，派生 `daily_plans`、`lesson_sections`、`vocabulary_items`、`quizzes` 等结构化表。

### POST /api/admin/lessons/{lesson_asset_id}/rollback

需要管理员 token。

按 `version_id` 回滚并重新发布。

### PUT /api/admin/route/{route_item_id}

需要管理员 token。

调整课程路线图优先级和目标时长。

### GET /api/admin/exports/learning-log

需要管理员 token。

导出某天完整学习包。

参数：

- `user_id`
- `date` 可选
- `format`：`markdown` 或 `csv`

## Debug

### GET /api/debug/modules

需要管理员 token。

返回模块自检结果，包括数据库、lesson JSON、学习复盘、进度、错误、难点和 RAG 来源表计数。
