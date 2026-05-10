# HoteLink 部署说明（源码对齐版）

> 仅记录仓库中已存在且可执行的部署能力

## 1. 先按场景找答案

- 只想本地直接跑后端和前端：看“7. 本地运行（无 Docker）”
- 只想用 Docker 起完整开发环境：看“4. 开发环境（docker-compose.dev.yml）”
- 只想看生产部署入口和服务构成：看“5. 生产环境（docker-compose.prod.yml）”
- 只想知道环境变量和安全基线：看“6. 环境变量文件”和“10. 当前安全基线”
- 只想知道推送后 GitHub 会自动跑什么：看“11. CI 与本地质量门禁”

## 2. 相关文件

- 开发编排：[`../docker-compose.dev.yml`](../docker-compose.dev.yml)
- 生产编排：[`../docker-compose.prod.yml`](../docker-compose.prod.yml)
- Windows 脚本：[`../scripts/docker.ps1`](../scripts/docker.ps1)
- Unix 脚本：[`../scripts/docker.sh`](../scripts/docker.sh)
- 后端镜像：
  - 开发：[`../backend/Dockerfile.dev`](../backend/Dockerfile.dev)
  - 生产：[`../backend/Dockerfile`](../backend/Dockerfile)
- 前端镜像：
  - 开发：[`../frontend/Dockerfile.dev`](../frontend/Dockerfile.dev)
  - 生产：[`../frontend/Dockerfile`](../frontend/Dockerfile)
- 网关配置：
  - 开发：[`../frontend/docker/nginx.dev.conf`](../frontend/docker/nginx.dev.conf)
  - 生产：[`../frontend/docker/nginx.conf`](../frontend/docker/nginx.conf)

---

## 3. 统一脚本能力

`scripts/docker.ps1` 与 `scripts/docker.sh` 支持：

- `up`
- `down`
- `ps`
- `logs`
- `build`
- `restart`
- `check`（仅 dev）
- `migrate`

示例：

```powershell
.\scripts\docker.ps1 dev up
.\scripts\docker.ps1 dev check
.\scripts\docker.ps1 prod up
```

```bash
sh ./scripts/docker.sh dev up
sh ./scripts/docker.sh prod migrate
```

---

## 4. 开发环境（docker-compose.dev.yml）

### 4.1 服务

- `mysql`
- `redis`
- `backend-dev`
- `backend-check`（profile: checks）
- `user-web-dev`
- `admin-web-dev`
- `frontend-gateway-dev`
- `celery-worker-dev`
- `celery-beat-dev`

### 4.2 默认端口

- `3306` MySQL
- `6379` Redis
- `8000` Django
- `8088` Nginx 开发网关（统一入口）

### 4.3 访问地址

- 用户端：`http://localhost:8088`
- 管理端：`http://localhost:8088/admin/`
- 后端：`http://localhost:8000`

---

## 5. 生产环境（docker-compose.prod.yml）

### 5.1 服务

- `mysql`
- `redis`
- `backend`
- `celery-worker`
- `celery-beat`
- `web`

### 5.2 对外入口

- `web` 暴露 `80` 端口
- Nginx 转发：
  - `/` -> 用户端静态站点
  - `/admin/` -> 管理端静态站点
  - `/api/` -> Django API
  - `/docs/` `/redoc/` `/schema/` -> 后端 API 文档（仅在 `ENABLE_API_DOCS=1` 时启用）

---

## 6. 环境变量文件

- 开发示例：[`../.env.docker.dev.example`](../.env.docker.dev.example)
- 生产示例：[`../.env.docker.example`](../.env.docker.example)
- 后端本地示例：[`../backend/.env.example`](../backend/.env.example)

关键配置域：

- Django：`DJANGO_*`
- DB：`DB_*` 与 `MYSQL_*`
- Redis/Celery：`REDIS_URL` `CELERY_BROKER_URL` `CELERY_RESULT_BACKEND`
- AI：`AI_*`
- 安全增强：`ENABLE_API_DOCS`、`JWT_*`、`API_THROTTLE_*`
- 支付回调：真实支付异步通知使用支付网关运行时配置中的 `notify_secret`，限流可通过 `API_THROTTLE_PAYMENT_NOTIFY` 覆盖

---

## 7. 本地运行（无 Docker）

### 7.1 后端

```bash
cd backend
poetry install
python manage.py migrate
python manage.py runserver
python manage.py test apps.api.tests
```

> 当前测试入口：`apps.api.tests` 覆盖后端接口、权限、订单、支付、发票、AI 等核心 API 行为。

### 7.2 前端

```bash
cd frontend
npm install
npm run dev
npm run build
npm run type-check
```

---

## 8. 数据初始化脚本

已存在并可用：

- 演示数据：[`../scripts/generate/seed_demo_data.py`](../scripts/generate/seed_demo_data.py)
- 批量酒店种子：[`../scripts/generate/seed_hotels_bulk.py`](../scripts/generate/seed_hotels_bulk.py)
- 从酒店图片池导入酒店：[`../scripts/generate/import_hotels_from_dist_images.py`](../scripts/generate/import_hotels_from_dist_images.py)

示例：

```bash
python scripts/generate/seed_demo_data.py
python scripts/generate/seed_hotels_bulk.py --count 200 --overwrite --images-dir dist/hotel_photo_crawler/photos
python scripts/generate/import_hotels_from_dist_images.py --count 200 --images-dir dist/hotel_photo_crawler/photos
```

---

## 9. 注意事项

1. `check` 动作仅在开发编排可用（调用 `backend-check`）。
2. 生产容器默认会在 `web` 角色下自动执行迁移与 `collectstatic`（可通过环境变量关闭）。
3. AI、数据库、Redis 密钥不要写入仓库，只保留在 `.env` 或部署平台密钥管理中。

---

## 10. 当前安全基线

### 10.1 后端

- 生产环境默认启用 `SECURE_SSL_REDIRECT`
- 默认启用 HSTS、`Referrer-Policy`、`X-Frame-Options`、`nosniff`
- JWT 刷新默认开启轮换与黑名单，部署后需执行迁移以创建 `token_blacklist` 表
- DRF 已启用全局限流，并对登录、刷新、上传、支付回调、AI 接口配置更严格速率
- 当前限流速率（可通过 `API_THROTTLE_*` 环境变量覆盖）：`anon` 600/min、`user` 1500/min、`auth_login` 15/min、`auth_register` 9/min、`auth_refresh` 100/min、`auth_logout` 150/min、`system_init` 15/hour、`upload` 100/hour、`payment_notify` 600/hour、`ai_user` 150/hour、`ai_admin` 300/hour

### 10.2 网关

- `frontend/docker/nginx.conf` 已补充 CSP、`Permissions-Policy`、`Referrer-Policy`、`X-Frame-Options` 等基础响应头
- 若 TLS 在外层负载均衡终止，HSTS 应由最外层 HTTPS 入口统一下发，避免仅在纯 HTTP 容器内配置失效

### 10.3 运维建议

1. 生产环境保持 `ENABLE_API_DOCS=0`，仅在内网排障或受控环境下临时开启。
2. 上线本次改动后执行 `python manage.py migrate`，确保 JWT 黑名单表落库。
3. 若部署为多实例，建议将 Django cache/throttle 后端切换到共享缓存（如 Redis），以获得跨实例一致的限流效果。

---

## 11. CI 与本地质量门禁

- GitHub Actions 工作流：[`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)
- Push 和 Pull Request 会触发后端与前端两组任务
- 后端任务执行 `poetry run python manage.py check` 和 `poetry run python manage.py test apps.api.tests -v 2`
- 前端任务执行 `npm run type-check` 和 `npm run test:unit:ci`
- 本地提交前可使用根目录 `pre-commit`；`pre-commit` 阶段做格式与仓库基础检查，`pre-push` 阶段执行前后端单元测试
