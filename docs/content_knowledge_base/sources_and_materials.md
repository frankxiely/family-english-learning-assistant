# 资料来源和使用边界

检索日期：2026-06-28

## 推荐作为知识库依据的资料

### CEFR 官方资料

来源：https://www.coe.int/en/web/common-european-framework-reference-languages

用途：

- 定义 Pre-A1、A1、A2 等阶段目标。
- 给课程路线图提供“能做什么”的能力描述。
- 给阶段验收和测试通过标准提供依据。

不做：

- 不把 CEFR 文本整段写进前端课程。
- 不把 CEFR 当成具体教材，它只解决分级和能力框架问题。

### British Council LearnEnglish

来源：https://learnenglish.britishcouncil.org/

重点参考：

- A1 listening / reading / speaking / vocabulary / grammar 的课型组织。
- A1 听力课常见结构：准备任务、音频、理解任务、技能练习。
- 成人学习场景，例如见面、购物、工作对话、电话留言、餐厅预订等。

不做：

- 不复制它的课文、音频和练习题。
- 只参考“课型结构”和“场景粒度”。

### Cambridge English Pre-A1 / A1

来源：https://www.cambridgeenglish.org/learning-english/parents-and-children/activities-for-children/pre-a1-level/

用途：

- 参考 Pre-A1 的小步长、低词汇负担和图文任务形式。
- 参考 Pre-A1/A1 常见词汇域，例如身体、家庭、教室、食物、地点、简单动作。
- 作为 0 基础首阶段的难度下限参考。

注意：

- Cambridge 这套页面偏儿童，我们只借鉴难度和任务类型，不复制儿童化内容。
- 对成人用户，例句和课文应改为家庭、工作、银行服务、日常购物等更自然场景。

### Oxford 3000 / Oxford 5000

来源：https://www.oxfordlearnersdictionaries.com/wordlists/oxford3000-5000

用途：

- 词汇优先级和 CEFR 词汇等级参考。
- v1.1 主要使用 A1 词，少量为了音标和拼读提前出现的词要标记为 phonics_word。
- 后续用于扩展词汇库、词性、核心词义和复习优先级。

不做：

- 不批量复制完整词表入库。
- 词义、例句、音标需要人工复核或使用许可明确的接口。

### Cambridge Dictionary / Oxford Learner's Dictionaries

来源：

- https://dictionary.cambridge.org/
- https://www.oxfordlearnersdictionaries.com/

用途：

- 核对单词拼写、词性、音标、核心词义。
- 管理员审核课程内容时作为查验资料。

不做：

- 不抓取整页词典内容。
- 不复制大量例句或释义。

### BBC Learning English

来源：https://www.bbc.co.uk/learningenglish/

用途：

- 参考发音讲解、短音频课型和实用表达粒度。
- 后续可参考 pronunciation / basic vocabulary / everyday English 的组织方法。

不做：

- 不缓存或复制 BBC 音频、视频、课文。

## 可参考但不能直接入库的教材

这些教材适合参考章节顺序、活动类型和难度推进，但属于商业教材，不能把课文、音频、题目直接搬进系统：

- English File Beginner / Elementary
- New Headway Beginner
- Interchange Intro
- Side by Side
- Cambridge English Empower Starter
- 新概念英语第一册

推荐用法：

- 管理员看目录和公开样章，总结“从什么到什么”的路线。
- 我们自己写原创短对话、讲解和测试。
- 如果购买教材并用于个人学习，也只能在本地人工备课中参考，不能作为可分发素材库。

## v1.1 推荐组合

- 分级框架：CEFR。
- 首阶段难度参考：Cambridge Pre-A1 + British Council A1。
- 词汇优先级：Oxford 3000 A1。
- 单词查验：Cambridge Dictionary / Oxford Learner's Dictionaries。
- 课型结构：British Council LearnEnglish。
- 发音讲解结构：BBC Learning English + 自编中文解释。

## 入库边界

允许入库：

- 我们原创的课程路线、课文、讲解、测试和中文说明。
- 资料来源 URL、访问日期、使用说明、许可备注。
- 单词的人工整理字段：word、phonetic、part_of_speech、core_meaning、cefr_level、topic_tag。
- 自己生成或手工授权的图片、音频、头像。

不允许入库：

- 未获授权的教材课文。
- 外部网站整套练习题。
- 外部音频、图片、插图的本地副本，除非许可明确且记录来源。
