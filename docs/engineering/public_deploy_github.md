# GitHub 公开网页部署

本项目不能只用 GitHub Pages 完成完整部署。GitHub Pages 只能发布静态前端；登录、课程生成、发布、复盘、数据库和生成音频都需要后端 API。因此公开访问采用：

- GitHub Pages：发布 `apps/web` 静态网页。
- Render Docker Web Service：运行 FastAPI 后端。
- Render Disk + SQLite：保存账号、课程、学习进度和草稿数据。

## 1. 推送到 GitHub

在 GitHub 创建仓库后，把当前项目推到 `main` 分支。仓库里已经包含：

- `.github/workflows/pages.yml`：GitHub Pages 构建与发布。
- `Dockerfile`：后端 API 容器。
- `render.yaml`：Render Blueprint。

GitHub 仓库设置里把 Pages Source 设为 `GitHub Actions`。

## 2. 部署后端 API

在 Render 里选择 `New` -> `Blueprint`，连接这个 GitHub 仓库。Render 会读取根目录 `render.yaml`。

需要改的环境变量：

- `MOMO_DB_PATH=/var/data/app.db`
- `MOMO_AUTO_SEED_TEST_DATA=1`
- `MOMO_CORS_ORIGINS=https://你的GitHub用户名.github.io`

如果使用 GitHub 项目页，例如 `https://你的GitHub用户名.github.io/仓库名/`，CORS origin 仍然只填协议和域名：`https://你的GitHub用户名.github.io`。

Render 服务创建后，记录后端地址，例如：

```text
https://family-english-api.onrender.com
```

打开下面地址确认 API 在线：

```text
https://family-english-api.onrender.com/api/health
```

## 3. 配置 GitHub Pages 前端

进入 GitHub 仓库 `Settings` -> `Secrets and variables` -> `Actions` -> `Variables`，添加：

- `VITE_API_BASE_URL=https://family-english-api.onrender.com`

可选变量：

- `VITE_BASE_PATH=/仓库名/`

如果不填 `VITE_BASE_PATH`，工作流会自动判断：普通仓库使用 `/${repo}/`，`用户名.github.io` 仓库使用 `/`。

保存变量后，推送一次 `main`，或在 Actions 里手动运行 `Deploy web to GitHub Pages`。

## 4. 第一次登录

第一次公开部署会用 `MOMO_AUTO_SEED_TEST_DATA=1` 初始化 demo 账号。先用管理员账号登录后台，并尽快修改密码：

- 管理员账号：`AdminXLY`
- 初始密码：`Frank1229`

学习者账号：

- 登录账号：`ViZhang`
- 初始密码：`Frank1229`

确认账号可用、密码已改后，可以把 Render 环境变量 `MOMO_AUTO_SEED_TEST_DATA` 改成 `0`。当前 seed 使用 `INSERT OR IGNORE`，不会覆盖已经修改过的密码，但公开服务不应长期依赖默认账号。

## 5. 音频说明

本地高质量音频当前使用 macOS `say` + `afconvert` 生成；Render 是 Linux 环境，不具备这两个命令。

公开网页仍可正常学习：

- 如果 lesson JSON 里已有可访问的 `audio_assets.local_url`，前端会播放缓存音频。
- 如果没有缓存音频，前端会回退到浏览器 Web Speech。
- 后续要在公网后台生成高质量音频，需要接云端 TTS provider，或先在本地生成音频并把生成文件提交到仓库。

## 官方参考

- GitHub Pages custom workflow: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
- Vite env variables: https://vite.dev/guide/env-and-mode
- Vite static deploy: https://vite.dev/guide/static-deploy
- Render Blueprint spec: https://render.com/docs/blueprint-spec
- Render Disks: https://render.com/docs/disks
