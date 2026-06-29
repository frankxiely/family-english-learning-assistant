# GitHub 公开网页部署

本项目不能只用 GitHub Pages 完成完整部署。GitHub Pages 只能发布静态前端；登录、课程生成、发布、复盘、数据库和生成音频都需要后端 API。

当前免费试用方案采用：

- GitHub Pages：发布 `apps/web` 静态网页。
- 本机 FastAPI：运行后端 API。
- 本机 SQLite：保存账号、课程、学习进度和草稿数据。
- Cloudflare Quick Tunnel：把本机 API 临时转发到公网。

长期稳定方案可以改为云服务器或 Render 等平台运行后端。

## 当前公开地址

- 前端页面：`https://frankxiely.github.io/family-english-learning-assistant/`
- 当前 API tunnel：`https://enclosure-affordable-contents-racial.trycloudflare.com`

Cloudflare Quick Tunnel 的地址不是永久地址。只要 tunnel 重启后地址变化，就要更新 GitHub 仓库变量并重新部署 Pages。

## 1. 推送到 GitHub

仓库：`frankxiely/family-english-learning-assistant`

仓库里已经包含：

- `.github/workflows/pages.yml`：GitHub Pages 构建与发布。
- `Dockerfile`：后端 API 容器，供长期云部署使用。
- `render.yaml`：Render Blueprint，供长期云部署使用。

GitHub 仓库设置里把 Pages Source 设为 `GitHub Actions`。

## 2. 启动本机后端

在项目根目录运行：

```bash
env MOMO_CORS_ORIGINS=https://frankxiely.github.io,http://127.0.0.1:5173,http://localhost:5173 .venv/bin/uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
```

确认 API 在线：

```bash
curl -s http://127.0.0.1:8000/api/health
```

预期返回：

```json
{"status":"ok","version":"1.1.0"}
```

## 3. 启动 Cloudflare Quick Tunnel

另开一个终端，在项目根目录运行：

```bash
/Users/xielingyun/.local/bin/cloudflared tunnel --url http://127.0.0.1:8000
```

命令输出里会出现一个 `https://*.trycloudflare.com` 地址。记录这个地址，并验证：

```bash
curl -s https://你的-tunnel.trycloudflare.com/api/health
```

## 4. 配置 GitHub Pages 前端

进入 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `Variables`，设置：

- `VITE_API_BASE_URL=https://你的-tunnel.trycloudflare.com`

也可以用 GitHub CLI：

```bash
/Users/xielingyun/.local/bin/gh variable set VITE_API_BASE_URL --repo frankxiely/family-english-learning-assistant --body https://你的-tunnel.trycloudflare.com
/Users/xielingyun/.local/bin/gh workflow run "Deploy web to GitHub Pages" --repo frankxiely/family-english-learning-assistant
```

可选变量：

- `VITE_BASE_PATH=/family-english-learning-assistant/`

如果不填 `VITE_BASE_PATH`，工作流会自动判断：普通仓库使用 `/${repo}/`，`用户名.github.io` 仓库使用 `/`。

## 5. 验证公开页面

打开：

```text
https://frankxiely.github.io/family-english-learning-assistant/
```

接口验证：

```bash
curl -s -i https://你的-tunnel.trycloudflare.com/api/health
curl -s -i -X OPTIONS https://你的-tunnel.trycloudflare.com/api/auth/login \
  -H 'Origin: https://frankxiely.github.io' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type'
```

CORS 预检应该返回 `access-control-allow-origin: https://frankxiely.github.io`。

## 6. 免费方案限制

- 电脑必须保持开机和联网。
- FastAPI 后端进程必须保持运行。
- `cloudflared tunnel` 进程必须保持运行。
- Quick Tunnel 地址可能在重启后变化；地址变化后必须更新 `VITE_API_BASE_URL` 并重新部署 GitHub Pages。
- 数据库保存在本机 `data/sqlite/app.db`；公开网页实际读写的就是这份本机数据。

## 7. 音频说明

本地高质量音频使用 macOS `say` + `afconvert` 生成，并写入 `apps/web/public/generated/audio/`。

公开网页的音频逻辑：

- 如果 lesson JSON 里已有可访问的 `audio_assets.local_url`，前端会播放缓存音频。
- 如果没有缓存音频，前端会回退到浏览器 Web Speech。
- 当前 Quick Tunnel 方案可以访问本机后端挂载的 `/generated` 资源。
- 后续如果改成长期云后端，需要同步迁移音频生成能力或把生成音频作为静态资源发布。

## 8. 长期云部署备选

如果后续需要 24 小时稳定公网访问，可以把后端迁到云服务器或 Render。

Render 方案大致结构：

- Render Docker Web Service：运行 FastAPI 后端。
- Render Disk + SQLite：保存账号、课程、学习进度和草稿数据。
- 后端环境变量：
  - `MOMO_DB_PATH=/var/data/app.db`
  - `MOMO_AUTO_SEED_TEST_DATA=0`
  - `MOMO_CORS_ORIGINS=https://frankxiely.github.io`
- GitHub 变量：
  - `VITE_API_BASE_URL=https://你的-render-api.onrender.com`

当前阶段因为没有可用国际信用卡，优先使用免费的 GitHub Pages + Cloudflare Quick Tunnel 方案。

## 官方参考

- GitHub Pages custom workflow: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Vite env variables: https://vite.dev/guide/env-and-mode
- Vite static deploy: https://vite.dev/guide/static-deploy
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/
- Render Blueprint spec: https://render.com/docs/blueprint-spec
- Render Disks: https://render.com/docs/disks
