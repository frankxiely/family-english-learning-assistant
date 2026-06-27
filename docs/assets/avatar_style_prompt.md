# 对话角色头像风格 Prompt

用途：为英语学习助手生成同一风格的对话角色头像，供课文中的老师、医生、妈妈、客户、银行职员等角色使用。

## 风格总结

这组头像是温和、亲切的半写实卡通肖像。人物为正面或轻微三分之二角度的上半身构图，头部较大，五官柔和，眼睛明亮，微笑自然。线条干净但不过度扁平，面部和头发使用柔和渐变与分层阴影，整体质感接近现代移动应用中的高质量人物插画。

背景为纯净的柔和渐变色，不出现复杂场景。职业身份通过服装和手持物表达，例如医生穿白大褂和听诊器，老师可持书本或笔记本，家庭角色可穿日常外套。整体要成熟、可信、温暖，适合中年学习者使用，避免幼稚、夸张、商业 IP 化或玩具化。

## 推荐生成 Prompt

```text
Create a friendly semi-realistic cartoon portrait for a mobile English learning app. Show a warm, approachable adult character from the chest up, facing forward with a slight three-quarter angle, gentle smile, bright expressive eyes, clean facial features, and soft layered shading. Use smooth vector-like illustration with subtle gradients, polished hair shapes, natural skin tones, and a calm pastel gradient background. The character should look mature, trustworthy, and kind, suitable for an adult learner interface. Use clothing and simple props to clearly indicate the role: [ROLE AND OCCUPATION]. Keep the composition centered, high resolution, square format, no text, no logo, no brand character, no exaggerated toy style.
```

## 负面约束

```text
No text, no watermark, no logo, no famous character, no brand IP, no childish mascot, no exaggerated chibi proportions, no harsh shadows, no busy background, no photorealistic face, no scary expression, no distorted hands, no cropped head.
```

## 当前本地素材

- `apps/web/public/assets/avatars/roles/mom2.png`：妈妈角色备用头像。
- `apps/web/public/assets/avatars/roles/doctor-female.png`：女性医生头像。
- `apps/web/public/assets/avatars/roles/doctor-male.png`：男性医生头像。
- `apps/web/public/assets/avatars/roles/teacher-female.png`：女性老师头像。
- `apps/web/public/assets/avatars/roles/admin-male.png`：男性管理员测试账号头像，也可作为课文中的 administrator/admin 角色头像。
- `apps/web/public/assets/avatars/role-avatars.json`：角色名、职业、性别与头像路径映射。
