# Debug Guide

## 模块 Debug

```bash
scripts/debug_modules.sh
```

## API Debug

FastAPI 安装后：

```bash
uvicorn services.api.app.main:app --reload --host 127.0.0.1 --port 8000
```

可用接口：

- `GET /api/health`
- `GET /api/debug/modules`
- `GET /api/learning/today?user_id=user_mom`
- `POST /api/admin/generate/today`

## 数据库 Debug

```bash
scripts/init_db.sh
scripts/generate_today.sh
scripts/debug_modules.sh
```
