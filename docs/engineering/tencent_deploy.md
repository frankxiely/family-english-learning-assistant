# 腾讯云版本更新

当前腾讯云试运行入口：

- 页面：`http://175.24.179.41/`
- API 健康检查：`http://175.24.179.41/api/health`

本项目在腾讯云上建议采用：

- Nginx：托管 `apps/web/dist` 静态前端，并把 `/api`、`/generated` 转发给后端。
- FastAPI：通过 systemd 常驻运行，监听 `127.0.0.1:8000`。
- SQLite：保存在线学习数据，默认路径 `data/sqlite/app.db`。
- Git：只更新代码和可提交的静态素材，不管理线上 SQLite 数据库。

## 核心原则

1. 发布前先在本地验证，再推送 GitHub。
2. 服务器更新前先备份线上 SQLite。
3. 线上环境不要执行 `scripts/seed_test_data.sh`。
4. 线上 `MOMO_AUTO_SEED_TEST_DATA` 必须保持为 `0`。
5. 如果生成音频只存在服务器本地，要确认 Nginx 代理 `/generated` 到后端，或在构建前保留 `apps/web/public/generated/audio/`。

## 本地发版

在本地项目根目录：

```bash
cd "/Users/xielingyun/Desktop/家庭英语学习助手"

.venv/bin/ruff check services/api/app tests
.venv/bin/python -m pytest
npm --prefix apps/web run build
npm run test:e2e
```

更新版本号和变更记录：

- `package.json`
- `apps/web/package.json`
- `pyproject.toml`
- `services/api/app/main.py`
- `CHANGELOG.md`

提交并打标签：

```bash
git add .
git commit -m "Release v1.2.0"
git tag v1.2.0
git push origin main --tags
```

## 首次服务器配置参考

以下路径和服务名是推荐值，可以按服务器实际情况调整：

- 项目目录：`/opt/family-english-learning-assistant`
- 前端目录：`/var/www/family-english`
- systemd 服务名：`family-english-api`
- 后端端口：`127.0.0.1:8000`

systemd 示例：

```ini
[Unit]
Description=Family English Learning Assistant API
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/family-english-learning-assistant
Environment=MOMO_DB_PATH=data/sqlite/app.db
Environment=MOMO_AUTO_SEED_TEST_DATA=0
Environment=MOMO_CORS_ORIGINS=http://175.24.179.41
ExecStart=/opt/family-english-learning-assistant/.venv/bin/uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Nginx 示例：

```nginx
server {
    listen 80;
    server_name 175.24.179.41;

    root /var/www/family-english;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /generated/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 使用发布脚本

脚本位置：

```bash
scripts/deploy_tencent.sh
```

在腾讯云服务器的项目根目录运行：

```bash
WEB_ROOT=/var/www/family-english \
SERVICE_NAME=family-english-api \
PUBLIC_HEALTH_URL=http://175.24.179.41/api/health \
RELOAD_NGINX=1 \
scripts/deploy_tencent.sh v1.2.0
```

脚本会依次执行：

1. 检查服务器是否有未提交的 tracked 代码改动。
2. 备份 `data/sqlite/app.db` 到 `data/sqlite/backups/`。
3. `git fetch --tags` 并切换到指定版本。
4. 安装 Python 依赖。
5. 运行 `init_db`，只做建表或迁移，不灌测试数据。
6. 安装前端依赖并构建 `apps/web/dist`。
7. 如果设置了 `WEB_ROOT`，同步前端到 Nginx 静态目录。
8. 重启 systemd API 服务。
9. 可选 reload Nginx。
10. 检查本机和公网 `/api/health`。

常用参数：

| 变量 | 默认值 | 说明 |
| --- | --- | --- |
| `WEB_ROOT` | 空 | 设置后同步 `apps/web/dist/` 到该目录 |
| `SERVICE_NAME` | `family-english-api` | systemd 服务名 |
| `WEB_API_BASE_URL` | 空 | 同源部署时留空；跨域 API 时填完整 API 地址 |
| `WEB_BASE_PATH` | `/` | Vite base path |
| `PYTHON_BIN` | 自动优先 `.venv/bin/python` | 指定发布时使用的 Python |
| `HEALTH_URL` | `http://127.0.0.1:8000/api/health` | 本机健康检查 |
| `PUBLIC_HEALTH_URL` | 空 | 公网健康检查 |
| `RELOAD_NGINX` | `0` | 设为 `1` 时执行 `nginx -t` 和 reload |
| `ALLOW_DIRTY_DEPLOY` | `0` | 设为 `1` 时允许服务器 tracked 改动 |
| `INSTALL_PYTHON_DEPS` | `1` | 设为 `0` 跳过 Python 依赖安装 |
| `INSTALL_NODE_DEPS` | `1` | 设为 `0` 跳过 `npm ci` |
| `BUILD_WEB` | `1` | 设为 `0` 跳过前端构建 |
| `RESTART_SERVICE` | `1` | 设为 `0` 跳过 API 重启 |
| `SKIP_HEALTH_CHECK` | `0` | 设为 `1` 跳过健康检查 |

同源部署时，前端请求 `/api` 即可，`WEB_API_BASE_URL` 留空：

```bash
WEB_ROOT=/var/www/family-english \
WEB_API_BASE_URL= \
SERVICE_NAME=family-english-api \
scripts/deploy_tencent.sh v1.2.0
```

如果前端和 API 分开部署，构建时指定 API 地址：

```bash
WEB_API_BASE_URL=http://175.24.179.41 \
scripts/deploy_tencent.sh v1.2.0
```

## 手动发布步骤

如果不使用脚本，可以在服务器上手动执行：

```bash
cd /opt/family-english-learning-assistant

mkdir -p data/sqlite/backups
sqlite3 data/sqlite/app.db "PRAGMA wal_checkpoint(FULL);"
cp data/sqlite/app.db "data/sqlite/backups/app-before-v1.2.0-$(date +%Y%m%d_%H%M%S).db"

git fetch --tags origin
git checkout v1.2.0

python3 -m pip install -e .
MOMO_DB_PATH=data/sqlite/app.db MOMO_AUTO_SEED_TEST_DATA=0 PYTHONPATH=. python3 services/api/app/tools/init_db.py

npm --prefix apps/web ci
VITE_BASE_PATH=/ VITE_API_BASE_URL= npm --prefix apps/web run build

sudo rsync -a --delete apps/web/dist/ /var/www/family-english/
sudo systemctl restart family-english-api
sudo nginx -t
sudo systemctl reload nginx
```

验证：

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s http://175.24.179.41/api/health
```

## 回滚

优先只回滚代码：

```bash
WEB_ROOT=/var/www/family-english \
SERVICE_NAME=family-english-api \
PUBLIC_HEALTH_URL=http://175.24.179.41/api/health \
RELOAD_NGINX=1 \
scripts/deploy_tencent.sh v1.1.0
```

不要默认恢复数据库。只有在新版本迁移或写入导致数据损坏时，才恢复发布前备份：

```bash
sudo systemctl stop family-english-api
cp data/sqlite/backups/app-before-v1.2.0-YYYYMMDD_HHMMSS.db data/sqlite/app.db
sudo systemctl start family-english-api
```

恢复数据库会丢失备份之后产生的学习记录、草稿、发布记录和账号设置，执行前要确认影响范围。

## 发布后检查

- `http://175.24.179.41/api/health` 返回新版本号。
- 学习者账号可以登录。
- 管理员后台可以进入用户工作台。
- 今日课程可以打开并完成提交。
- `/generated` 下的图片和音频可以访问。
- `data/sqlite/backups/` 中存在本次发布前备份。
