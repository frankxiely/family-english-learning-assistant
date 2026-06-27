# lesson JSON 写作规则 v1

## 输入

每个 lesson JSON 的上游输入包括：

- 用户画像：年龄、职业、英语基础、每日学习时长、目标、兴趣偏好。
- 用户学习状态：学习天数、当前阶段、知识点进度、场景进度、复习队列、错题。
- 路线图项：今天的知识点、场景、难度、通过标准。
- 管理员备注：可为空；为空时写 `null`。
- 教学知识资产：音标、拼读、词汇、句型和测试规则。

## 输出原则

- 保留人类可读摘要，方便管理员快速审阅。
- 保留结构化字段，方便脚本入库和前端统一渲染。
- 任何素材需求要写清楚目标、类型和是否必需。
- 每个字段尽量稳定，不把前端展示逻辑混进自由文本里。

## 每日结构

推荐主模块：

1. `goal`：今日目标。
2. `vocabulary`：音标/单词。
3. `passage`：教材式短课文或短对话。
4. `knowledge_note`：知识讲解。
5. `quiz`：测试。
6. `summary`：今日总结。

## 字段要求

### route_basis

必须包含：

- `route_item_id`
- `knowledge_id`
- `knowledge_name`
- `scenario_level_id`
- `scenario_id`
- `scenario_name`
- `level_code`
- `teaching_knowledge_id`

### vocabulary

每个词必须包含：

- `word`
- `phonetic`
- `part_of_speech`
- `part_of_speech_zh`
- `meaning`
- `cefr_level`
- `is_phonics_word`
- `needs_image`
- `image_hint`
- `audio_text`

零基础阶段每个词只给一个核心词义。

### passage

对话型课文必须包含：

- `title`
- `passage_type`
- `lines`
- `difficult_words`
- `translation`
- `audio_plan`

每个 `line` 包含：

- `role`
- `role_avatar_key`
- `text`
- `translation`
- `audio_text`
- `highlight_words`

### knowledge_note

必须拆成卡片：

- `title`
- `cards`

每个 `card` 包含：

- `card_id`
- `heading`
- `body`
- `examples`
- `micro_task`

前端只展示一张卡片，通过上一页/下一页翻卡片。

### quiz

每题必须包含：

- `question_id`
- `prompt`
- `options`
- `answer`
- `explanation`
- `related_knowledge_id`
- `related_word_ids`
- `error_tag`

同一道题的统计应按 `question_id` 去重，避免重复复习导致完成题数膨胀。

### encouragement

首页鼓励语和完成页鼓励语分开：

- `home_encouragement`
- `completion_encouragement`

完成页鼓励语需要包含当天学过的至少一个词。

## 禁止

- 不生成超出路线图难度的长段课文。
- 不一天塞多个语法点。
- 不把词典式长释义放到单词页。
- 不使用未授权的外部课文、音频、图片。
- 不让 provider 原始输出直接进入前端。
