# 音频策略 v1

## 当前问题

浏览器 Web Speech API 可以快速播放单词和句子，但它不是稳定的课程音频方案：

- 不同系统、浏览器和设备可用 voice 不一致。
- 主要控制项是 voice、lang、rate、pitch、volume。
- 很难稳定控制感情、角色、停顿和课文整体节奏。
- 播放时临时合成，不便于复现、缓存和质量审核。

因此 v1.1 可以继续保留 Web Speech API 作为 fallback，但课文音频要逐步转为“生成后入库的音频资产”。

## 推荐架构

### 1. audio provider 接口

后端预留统一接口：

- `web_speech_runtime`：前端临时朗读，当前默认 fallback。
- `local_tts_provider`：本机生成音频文件，可考虑 Piper 或 macOS 系统 TTS。
- `cloud_neural_tts_provider`：后续可选，接 Azure / Google / ElevenLabs 等神经网络 TTS。
- `manual_audio_provider`：管理员手工上传或录制音频。

所有 provider 输出都必须登记到 `asset_sources`，不能只把 URL 写在前端。

### 2. 音频资产目录

建议目录：

```text
apps/web/public/generated/audio/
  words/
  passage_lines/
  passages/
  manifests/
```

命名建议：

```text
audio_{target_type}_{content_hash}_{voice_key}_{rate_key}.mp3
```

例如：

```text
audio_word_see_enus_female_normal.mp3
audio_passage_line_i_see_it_teacher_normal.mp3
audio_passage_i_see_it_dialogue_slow.mp3
```

### 3. lesson JSON 音频字段

建议新增：

```json
{
  "audio_assets": [
    {
      "audio_id": "audio_word_see_enus_female_normal",
      "target_type": "word",
      "target_ref": "word_see",
      "text": "see",
      "provider": "web_speech_runtime",
      "voice_key": "en-US-female-default",
      "locale": "en-US",
      "rate": 0.9,
      "pitch": 1,
      "style": "neutral",
      "local_url": null,
      "content_hash": "pending",
      "duration_ms": null
    }
  ]
}
```

课文行应有：

```json
{
  "role": "Teacher",
  "text": "See the seat.",
  "audio_ref": "audio_line_teacher_see_the_seat_normal",
  "slow_audio_ref": "audio_line_teacher_see_the_seat_slow"
}
```

## 让课文音频更自然

### v1.1 立即可做

- 选取设备上最自然的 `en-US` voice，并记录 voice 名称。
- 单词正常语速 `rate = 0.82` 到 `0.9`。
- 课文正常语速 `rate = 0.88` 到 `0.95`。
- 慢速版本 `rate = 0.65` 到 `0.72`。
- 对话按句子分开朗读，不把角色名读出来。
- 整篇播放时句间插入短停顿，角色切换处停顿更明显。

### v1.1 已实现的本地 TTS

- 管理员可以在后台对未发布草稿生成音频。
- provider 为 `macos_say_tts`，使用 macOS `say` 生成 AIFF，再用 `afconvert` 转成 WAV。
- 音频写入 `apps/web/public/generated/audio/`，通过 `audio_assets.local_url` 暴露给前端。
- 单词、课文行、慢速课文行、听音测试题都能生成音频。
- 前端正常/慢速整段播放会优先按逐句缓存音频顺序播放。
- 如果本地音频缺失或播放失败，前端回退到 Web Speech。

### v1.2 推荐

- 后台增加音频审核队列，支持试听、重生成、手工上传和发布。
- 同一个角色固定 voice，Teacher、Vi、Mom、Bank Staff 等角色有稳定声音。
- 接入支持 SSML 的 provider 后，使用停顿、重音和发音词典进一步优化。
- 每次生成音频记录 provider、voice、rate、pitch、style、source_text、content_hash。

### v1.3 之后

- 使用支持 SSML 的神经网络 TTS。
- 通过 SSML 控制停顿、语速、重音、角色声音和自定义发音。
- 对音标课重点词使用 `<phoneme>` 或发音词典保证读音准确。
- 对对话课使用多角色 voice，分别生成正常语速和慢速版本。

## provider 选择

### Web Speech API

优点：

- 免费。
- 不需要 API key。
- 前端立刻可用。

缺点：

- 音质和 voice 由设备决定。
- 情绪和停顿控制弱。
- 无法稳定复现同一份音频。

定位：v1.1 fallback。

### Piper 本地 TTS

优点：

- 本地生成，不依赖云 API。
- 可生成可缓存音频文件。
- 适合没有 OpenAI API 的阶段做本地实验。

缺点：

- 需要安装模型和命令行工具。
- 英语 voice 自然度要实际听选。
- 对话情绪控制有限。

定位：v1.2 本地音频 provider 候选。

### Azure / Google Cloud TTS

优点：

- 支持 SSML、神经网络声音、停顿、语速、部分自定义发音。
- 更适合课文和对话音频。

缺点：

- 需要云账号和费用控制。
- 需要 provider 抽象和缓存，避免每次前端播放都调用 API。

定位：后续可选高质量 provider。

## v1.1 决策

短期不直接接付费 API，但前端不能继续只假设 Web Speech 是唯一音源。先做四件事：

1. 把音频策略和 lesson JSON 字段写清楚。
2. 前端优先播放 lesson JSON 中 `audio_assets.local_url` 指向的缓存音频；没有缓存音频时才使用 Web Speech API。
3. 后端继续写入 `audio_assets`，并为单词、课文行、慢速课文行和听音测试题生成稳定 `audio_ref`。
4. `audio_assets` 增加 `style`、`emphasis_words`、`pause_after_ms`，为后续有感情、重音和停顿的 TTS provider 留出数据位。

## 课文和测试音频目标

课文音频不能只是“把文字念出来”。每个音频资产应记录：

- `target_type`：word、passage_line、passage_line_slow、quiz_question。
- `style`：例如 neutral、slow_clear、quiz_prompt、warm_teacher、bank_service。
- `emphasis_words`：当天要强调的词或音，例如 see、sit、bank。
- `pause_after_ms`：句后停顿，角色切换可更长。
- `local_url`：生成完成后的缓存文件路径。

后台后续需要提供音频生成/审核队列：

- 生成：为已发布或待发布 lesson JSON 批量生成音频。
- 试听：管理员在后台逐条听单词、课文行和测试题音频。
- 替换：不满意时重新生成或手工上传。
- 发布：只有通过审核的音频写入 `local_url`，前端才优先播放。
