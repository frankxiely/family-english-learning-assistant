# 家庭英语学习助手

v1.1 目标：本地主机 + 网页运行。当前首位学习者是妈妈，管理员是你；系统先使用本地模板、手工录入和 mock provider 完成每日学习计划与学习复盘，不依赖 OpenAI API。正式本地使用时数据库只初始化表结构，不自动灌入测试 seed。

## 当前工作流

1. 管理员录入用户画像和学习偏好。
2. 数据库保存用户画像、学习状态、课程路线图、复习队列和每日学习事实。
3. 内容知识库提供课程分级、知识点、路线图、每日容量和素材约束。
4. 内容生成 provider 在路线图约束内生成 `lesson_plan_json` 草稿。
5. 转译器把草稿清洗、补字段、校验为标准 lesson JSON。
6. 标准 lesson JSON 入库为备课素材。
7. 管理员在网页后台预览 JSON、人类可读摘要和备注，可保存草稿、发布或回滚。
8. 前端只读取已发布的标准 lesson JSON 并统一渲染。
9. 学习结束后，根据真实学习记录生成 `learning_review_json`。
10. 复盘入库，并回写学习状态、知识点进度、场景进度、词汇掌握和复习队列。
11. 每日记录可导出为 Markdown 或 CSV，周报会整理 7 天内的学习状态。

## 本地命令

```bash
scripts/init_db.sh
scripts/seed_test_data.sh
scripts/generate_today.sh
scripts/debug_modules.sh
scripts/backup_db.sh
scripts/export_learning_log.sh markdown
scripts/export_learning_log.sh csv
sqlite3 data/sqlite/app.db ".read scripts/reset_user_mom_learning_records.sql"
```

`scripts/init_db.sh` 只创建或迁移真实本地库结构，不写入样例账号、样例课程或测试学习记录。需要测试/demo 数据时，显式执行 `scripts/seed_test_data.sh`；后端 pytest 和 Playwright E2E 会在隔离测试库中自动加载这份 seed。

验收命令：

```bash
.venv/bin/ruff check services/api/app tests
.venv/bin/python -m pytest
npm --prefix apps/web run build
npm run test:e2e
```

启动完整开发服务需要安装 Python 和 Node 依赖：

```bash
python3 -m pip install -e ".[dev]"
npm install
npm run dev
```

前端 UI：

- 学习端使用 `antd-mobile` 组件，视觉方向为清爽路径式学习体验，减少背单词卡片墙。
- 登录页以学习者登录为主，提供低强调“管理员登录”小按钮进入 `/admin`。
- 登录页使用线条风 Logo 占位稿：打开的书页、对话气泡、抽象 `M` 和右上角星标。
- 学习端不是一页拉到底网页，而是首页、学习进度、逐步学习、我的四个交互视图。
- 学习端字体面向手机阅读放大：正文、英文课文、中文词义、按钮和小标签分别使用不同字号层级。
- 长期课程路线图规定每天主题；每日 lesson JSON 负责填充当天学习内容。
- 首页鼓励语来自 lesson JSON，分英文和中文两行，不再写死机械进度文案。
- 首页展示今日任务数量，进度页可点开已完成、今日和未来课程查看不同信息。
- 首页和进度页的主按钮会按状态显示“开始今天的学习 / 继续今天的学习 / 复习今天的学习”，学习播放器返回主页后会记住当前步骤。
- 进度页详情优先读取路线图摘要字段，未来几天无需提前生成 lesson JSON 也能展示学习模块、主要知识点和课文模块；当天课程可由 lesson JSON 的 `progress_summary` 覆盖。
- 单词图片优先复用本地资产；缺失时生成本地 SVG 图并登记到 `asset_sources`。
- 单词页不默认选择掌握状态；点击“知道 / 模糊 / 不知道”后自动推进。
- 学习播放器底部用“上一模块 / 下一模块”切换主模块；课文原文/译文和知识讲解分页只翻当前卡片，并支持上一页/下一页。
- 学习端建立按钮交互体系：主行动按钮有下沉回弹，模块导航体现前后方向，单词选择、测试选项、播放按钮、原文/译文切换和工具按钮使用不同反馈层级。
- 课文是一个主模块，内部包含原文和译文两个按钮；原文页保留角色头像、逐句喇叭播放、今日词高亮和难词弹窗，译文页展示难词词义和整篇译文。
- lesson JSON 生成会读取 `data/teaching_knowledge/starter_phonics_route.v1.json` 的内容路线，并写入 `route_basis`、`progress_summary`、`source_basis` 和 `audio_assets`。
- 测试答对会自动进入下一题，答错会停留、标红、显示解析，并把错题随学习提交写入后端。
- 学习完成后先展示奖杯完成页，再进入“我的”。
- 我的页面用左上角设置按钮进入独立账号设置页，设置页提供返回和确定；我的页统计改为累计完成测试题、学习天数、完成模块和当前模块。
- 对话角色头像素材放在 `apps/web/public/assets/avatars/roles/`，风格 prompt 记录在 `docs/assets/avatar_style_prompt.md`。
- 管理端使用 `antd` 组件，走成熟后台工作台风格。
- 当前主题不直接照搬 Duolingo 品牌，只借鉴“路径、关卡、即时反馈、大按钮”的学习产品结构。

## 模块 Debug

模块 debug 入口：

```bash
scripts/debug_modules.sh
```

检查内容：

- SQLite 数据库是否可访问
- 核心表是否存在
- 当前库中的用户、课程路线图和内容知识库是否可用
- `lesson_plan_json` 是否可生成
- 标准 lesson JSON 是否可入库
- 今日学习 API 数据是否可查询
- 学习复盘、进度、错误、难点和 RAG 来源表是否可查询

## v1.1 本地页面

网页端提供三个独立入口：

- `/login`：学习者登录页。
- `/learn`：学习者页面，包含问候首页、学习进度、逐步学习播放器、完成奖杯页和我的学习总结。
- `/admin`：管理员页面；必须先用管理员账号登录，进入后先看用户目录，再进入单个用户工作台。

管理员工作台当前包含：

- 用户目录和用户选择。
- 最新未发布课程草稿 JSON。
- 草稿备注：写入 `lesson_json.admin_note`。
- AI/模板调整：根据管理员文本重新生成未发布草稿。
- 人工 JSON 编辑：保存当前编辑，并支持连续还原上一步。
- 管理员反馈：单独进入后台开发日志，不混入学习者课程内容。
- 学习结果概览：从 `learning_review_assets`、词汇掌握和学习状态汇总学习天数、词汇量估计、薄弱项和近期复盘。

课程内容边界：

- 未发布课程放在 `lesson_draft_workspaces`。
- 只有发布后的课程才进入正式 `lesson_json_assets`。
- 学习者完成课程并生成 `learning_review_json` 后，系统会生成下一天未发布草稿。

预置学习者账号：

- 登录账号：`ViZhang`
- 用户名/展示名：`Vi`，允许和其他用户重复
- 密码：`Frank1229`

当前课程路线从音标和基础拼读开始，v1.1 默认每天 30 分钟。

本地管理员账号：

- 登录账号：`admin_xly`
- 密码：`Admin1229`
- 测试管理员登录账号：`AdminXLY`
- 测试管理员用户名/展示名：`Admin_1`
- 测试管理员密码：`Frank1229`
- `AdminXLY` 同时绑定学习者身份 `user_admin_1`，可登录学习端；画像为 25 岁、硕士研究生、雅思 7.0 水平。

## 目录

- `services/api/`：后端 API 和核心业务逻辑。
- `apps/web/`：手机优先网页端。
- `db/migrations/`：数据库迁移 SQL。
- `db/seeds/`：测试/demo seed 数据；真实本地初始化不默认执行。
- `docs/content_knowledge_base/`：内容知识库说明、资料来源、路线设计、lesson JSON 写作规则和音频策略。
- `data/sqlite/`：本地 SQLite 数据库。
- `data/teaching_knowledge/`：可机器读取的资料来源目录和课程路线图草稿。
- `data/lesson_json/`：raw / normalized / validated lesson JSON 文件。
- `data/logs/`：API、内容生成、前端日志。
- `tests/`：后端 pytest 和前端 Playwright E2E 测试。
- `scripts/`：初始化、生成、校验、debug 和启动脚本。
