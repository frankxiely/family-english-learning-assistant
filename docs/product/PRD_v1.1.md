# PRD v1.1

## 版本定义

v1.1 是本地网页版：本机运行 API 和 Web，手机浏览器访问。首位用户为妈妈，管理员为你。系统先不依赖外部模型 API。

## AI / Provider 职责边界

内容生成 provider 只负责两类结构化草稿：

- 学习前：`lesson_plan_json`
- 学习后：`learning_review_json`

provider 不负责前端展示、完成判定、测试计分、数据库写入和发布状态变更。

## 标准资产

- 标准 lesson JSON 是正式备课素材。
- 标准 learning review JSON 是正式复盘素材。
- 管理员备注归属管理员管理模块，可写可不写；转译器读取，有值写入标准 JSON，无值写 `null`。
