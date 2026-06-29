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

每天必须像一个小教材课时，而不是孤立的词表和干对话。最低内容密度：

- 一个成人能理解的微场景钩子，例如上班前英语角、桌面物品、通勤、银行前台。
- 3 到 4 个新词，最多 2 个复习词；新词和复习词在 `vocabulary.learning_role` 中区分。
- 4 到 6 句有情节推进的短课文，句子可以简单，但不能只是 Teacher/learner 重复同一句。
- 3 到 5 张知识卡，每张只讲一个小点，允许把旧词复习穿插进去。
- 4 到 5 道检索测试，至少 1 道检查课文理解，至少 1 道检查旧内容回顾。

知识讲解必须讲“今天需要掌握的知识”，不能写成课程设计说明。每课至少覆盖：

- 发音或语音点：今天要听清/读准什么，拿当天词举例。
- 单词：核心词义、词性或最小用法，不写词典式长释义。
- 句型或语法：当天课文里出现的固定结构，例如 `Please + verb`、`I can ...`、`My name is ...`。
- 场景用法：这个句子在什么真实场景里说，什么表达更自然。

课文必须像真实人会说的话。允许为零基础简化句子，但不允许为了塞词生成不自然句子，例如 “I see the bank.” 这种没有真实交际目的的句子。银行场景优先使用 “Welcome to the bank.”、 “I can help.”、 “Please sit here.” 这类自然短句。

测试必须测掌握，不测课程元信息。禁止把“今天主要练什么？”作为常规测试题。推荐题型：

- `sound_choice`：听音选词，用来测听辨。
- `meaning_choice`：看词选中文核心意思。
- `cloze`：在当天句型里补词。
- `sentence_meaning`：看英文短句选中文意思。
- `scenario_choice`：给场景，选择自然回应。
- `review_choice`：从旧词或旧句中做检索复习。

## 一周生成和复习

管理员可以一次生成未来 7 天 lesson JSON 草稿。生成时必须按用户当前 `learning_days` 加周内偏移选择路线项，不能 7 天重复同一课。

复习不单独增加模块。系统从 `review_queue` 中取旧词或旧知识点，均匀分配到未来一周，并放入：

- `vocabulary`：标记 `learning_role: "review"` 和 `is_review: true`。
- `passage`：在新课文里自然出现，前端用复习色高亮。
- `knowledge_note`：用“复习回顾”卡片说明旧内容，不占新知识点。
- `quiz`：至少用一道题确认旧内容是否能认出或读出。

显式规则：`on`、`the`、`a`、`in` 等功能词通常不作为零基础阶段的新词；需要解释时放在 `passage.difficult_words`，用点按释义处理。

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
