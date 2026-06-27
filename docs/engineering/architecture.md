# 架构说明

```text
用户画像 + 学习状态 + 课程路线图 + 复习队列 + 管理员备注
  -> provider 生成 lesson_plan_json
  -> 转译器生成标准 lesson JSON
  -> lesson_json_assets 入库
  -> API 读取已发布 lesson JSON
  -> 前端统一组件渲染
  -> 用户学习记录
  -> learning_review_json
  -> 回写学习状态和复习队列
```

数据库是唯一事实来源。前端不直接消费 provider 原始输出。
