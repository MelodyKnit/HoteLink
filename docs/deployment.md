# HoteLink 部署说明

## 1. 文档范围

本文只记录仓库中已经存在并可直接执行的部署能力，不描述尚未落地的方案。

部署相关事实以以下文件为准：

- [docker-compose.dev.yml](../docker-compose.dev.yml)
- [docker-compose.prod.yml](../docker-compose.prod.yml)
- [scripts/docker.ps1](../scripts/docker.ps1)
- [scripts/docker.sh](../scripts/docker.sh)
- [docs/thesis-alignment.md](./thesis-alignment.md)

## 2. 已实现的部署资源

当前仓库中已经存在并可直接使用的文件：

- 开发环境编排：[docker-compose.dev.yml](../docker-compose.dev.yml)
- 生产环境编排：[docker-compose.prod.yml](../docker-compose.prod.yml)
- 开发环境变量示例：[.env.docker.dev.example](../.env.docker.dev.example)
- 生产环境变量示例：[.env.docker.example](../.env.docker.example)
- 后端开发镜像：[backend/Dockerfile.dev](../backend/Dockerfile.dev)
- 后端生产镜像：[backend/Dockerfile](../backend/Dockerfile)
- 后端开发入口：[backend/docker/entrypoint.dev.sh](../backend/docker/entrypoint.dev.sh)
- 后端生产入口：[backend/docker/entrypoint.sh](../backend/docker/entrypoint.sh)
- 前端开发镜像：[frontend/Dockerfile.dev](../frontend/Dockerfile.dev)
- 前端生产镜像：[frontend/Dockerfile](../frontend/Dockerfile)
- Nginx 配置：[frontend/docker/nginx.conf](../frontend/docker/nginx.conf)

统一脚本当前支持的动作如下：

- `up`
- `down`
- `ps`
- `logs`
- `build`
- `restart`
- `check`
- `migrate`

说明：

- `check` 仅开发环境可用。
- `migrate` 会进入正在运行的后端容器执行 `python manage.py migrate --noinput`。

## 3. 当前已落地的系统能力

后端路由与视图已经落地在：

- [backend/apps/api/urls.py](../backend/apps/api/urls.py)
- [backend/apps/api/views.py](../backend/apps/api/views.py)

当前可以确认已经实现的能力包括：

**系统与认证（6 个接口）**：
- 系统初始化检查、首次管理员创建
- 用户注册、用户登录、管理员登录
- JWT 刷新与退出、当前用户信息

**公共查询（6 个接口）**：
- 酒店搜索（关键词、城市、星级、价格、排序）
- 搜索建议（自动补全）
- 酒店详情（含嵌套房型）
- 酒店评价列表
- 房态日历查询
- 首页数据（Banner、推荐酒店）

**通用工具（4 个接口）**：
- 通用文件上传（按场景归档）
- 图片缩略图（含缓存）
- 城市列表
- 系统字典（枚举值）

**用户端（26 个接口）**：
- 个人资料：查看、编辑、头像上传、修改密码
- 收藏：列表、添加、移除
- 订单：列表、详情、创建（含会员折扣+优惠券）、更新、支付、取消、入住人历史
- 评价：创建/更新评价、评价列表
- 积分：积分流水
- 通知：通知列表、标记已读、删除、未读数量
- 优惠券：我的优惠券、可领取列表、领取、下单可用券
- 发票：发票列表、创建抬头、申请开票
- AI：标准聊天、流式聊天

**管理端（28 个接口）**：
- 仪表盘：今日概览、趋势图表
- 酒店：列表、创建、编辑、删除
- 房型：列表、创建、编辑、删除
- 库存：日历查询、单日更新
- 订单：列表、详情、状态变更、办理入住、办理退房
- 评价：列表、回复、删除
- 用户：列表、状态变更、会员概览
- 员工：列表、创建
- 优惠券：模板列表、创建、状态切换
- 设置：读取、更新
- AI：配置读取/更新、供应商增删改查、经营摘要、评价摘要、回复建议
- 报表：任务列表、创建任务
- 系统重置

系统重置接口限制条件：

- 必须登录
- 必须是 `system_admin` 或超级用户
- 必须提交确认字段 `confirm=RESET`

合计：**71 条 URL 路由**，**60+ 个 View 类**，**42+ 个 Serializer**。

## 4. 开发环境部署

### 4.1 开发环境服务

[docker-compose.dev.yml](../docker-compose.dev.yml) 当前定义了以下服务：

- `mysql`
- `redis`
- `backend-dev`
- `backend-check`
- `user-web-dev`
- `admin-web-dev`
- `celery-worker-dev`
- `celery-beat-dev`

对应卷与网络：

- `mysql_dev_data`
- `redis_dev_data`
- `poetry_cache`
- `frontend_node_modules`
- `hotelink-dev-net`

### 4.2 开发环境默认端口

- `3306`：MySQL
- `6379`：Redis
- `8000`：后端开发服务
- `5173`：用户端 Vite 开发服务
- `5174`：管理端 Vite 开发服务

### 4.3 开发环境启动

PowerShell：

```powershell
.\scripts\docker.ps1 dev up
```

macOS / Linux / Git Bash：

```bash
sh ./scripts/docker.sh dev up
```

查看状态：

```powershell
.\scripts\docker.ps1 dev ps
```

查看日志：

```powershell
.\scripts\docker.ps1 dev logs
```

执行检查：

```powershell
.\scripts\docker.ps1 dev check
```

执行迁移：

```powershell
.\scripts\docker.ps1 dev migrate
```

### 4.4 开发环境访问地址

- 用户端：[http://localhost:5173](http://localhost:5173)
- 管理端：[http://localhost:5174/admin/](http://localhost:5174/admin/)
- 后端：[http://localhost:8000](http://localhost:8000)

### 4.5 开发环境数据准备

当前仓库中不存在 `scripts/generate_random_data.py`。

可直接使用已经存在的 Demo 数据脚本：

- [scripts/generate/seed_demo_data.py](../scripts/generate/seed_demo_data.py)

本机执行：

```powershell
python .\scripts\generate\seed_demo_data.py
```

在 Docker 开发容器中执行：

```powershell
python .\scripts\generate\seed_demo_data.py --use-docker
```

也可以直接进入容器：

```powershell
docker compose --env-file .env.docker.dev -f docker-compose.dev.yml exec backend-dev python /scripts/generate/seed_demo_data.py
```

### 4.6 开发环境停止

```powershell
.\scripts\docker.ps1 dev down
```

如果需要删除开发数据卷：

```powershell
docker compose --env-file .env.docker.dev -f docker-compose.dev.yml down -v
```

## 5. 生产环境部署

### 5.1 生产环境服务

[docker-compose.prod.yml](../docker-compose.prod.yml) 当前定义了以下服务：

- `mysql`
- `redis`
- `backend`
- `celery-worker`
- `celery-beat`
- `web`

对应卷与网络：

- `mysql_data`
- `redis_data`
- `static_data`
- `media_data`
- `hotelink-net`

### 5.2 生产环境启动

PowerShell：

```powershell
.\scripts\docker.ps1 prod up
```

查看状态：

```powershell
.\scripts\docker.ps1 prod ps
```

查看日志：

```powershell
.\scripts\docker.ps1 prod logs
```

执行迁移：

```powershell
.\scripts\docker.ps1 prod migrate
```

重建并重启：

```powershell
.\scripts\docker.ps1 prod restart
```

### 5.3 生产环境访问路径

[frontend/docker/nginx.conf](../frontend/docker/nginx.conf) 当前已配置以下路径：

- `/`：用户端前端（SPA，fallback 到 index.html）
- `/admin/`：管理端前端（SPA，fallback 到 admin/index.html）
- `/api/`：后端接口（proxy 到 backend:8000）
- `/docs/`：Swagger UI（proxy 到 backend:8000）
- `/redoc/`：ReDoc（proxy 到 backend:8000）
- `/schema/`：OpenAPI Schema（proxy 到 backend:8000）
- `/static/`：Django 静态资源（7 天缓存）
- `/media/`：上传文件（7 天缓存）

### 5.4 生产环境默认端口

- `80`：Nginx（对外唯一入口）
- `8000`：Django Gunicorn（内部，4 workers，120s timeout）
- `3306`：MySQL（内部）
- `6379`：Redis（内部）

### 5.5 生产环境 Nginx 优化

- Gzip 压缩已开启（text/css/json/js/xml/svg，最小 1024 字节）
- 客户端最大上传体积：20MB
- 静态资源与媒体文件 7 天缓存

### 5.6 生产环境停止

```powershell
.\scripts\docker.ps1 prod down
```

## 6. 环境变量

开发环境当前示例文件为：

- [.env.docker.dev.example](../.env.docker.dev.example)

生产环境当前示例文件为：

- [.env.docker.example](../.env.docker.example)

### 6.1 Django 核心变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DJANGO_SECRET_KEY` | Django 密钥（生产必须覆盖） | 内置开发密钥 |
| `DJANGO_DEBUG` | 调试模式 | `True`（开发）/ `False`（生产） |
| `DJANGO_ALLOWED_HOSTS` | 允许的 Host | `*` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | CSRF 信任域 | — |
| `CORS_ALLOW_ALL_ORIGINS` | CORS 全放行 | `True`（开发） |
| `CORS_ALLOWED_ORIGINS` | CORS 白名单 | — |

### 6.2 数据库变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DB_HOST` | 数据库主机（空则回退 SQLite） | — |
| `DB_NAME` | 数据库名 | `hotelink` |
| `DB_USER` | 数据库用户 | `root` |
| `DB_PASSWORD` | 数据库密码 | — |
| `DB_PORT` | 数据库端口 | `3306` |

### 6.3 Redis 与 Celery 变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `REDIS_URL` | Redis 通用缓存 URL | `redis://127.0.0.1:6379/0` |
| `CELERY_BROKER_URL` | Celery Broker | `redis://127.0.0.1:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery 结果后端 | `redis://127.0.0.1:6379/2` |
| `CELERY_TIMEZONE` | Celery 时区 | `Asia/Shanghai` |

### 6.4 JWT 变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `JWT_ACCESS_MINUTES` | Access Token 有效期（分钟） | `120` |
| `JWT_REFRESH_DAYS` | Refresh Token 有效期（天） | `7` |

### 6.5 AI 相关变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_ENABLED` | AI 功能开关 | `true` |
| `AI_PROVIDER` | 默认供应商 | `deepseek` |
| `AI_BASE_URL` | API 地址 | 供应商预设 |
| `AI_API_KEY` | API 密钥 | — |
| `AI_MODEL` | 聊天模型 | 供应商预设 |
| `AI_REASONING_MODEL` | 推理模型 | — |
| `AI_TIMEOUT` | 请求超时（秒） | `60` |

### 6.6 生产部署变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CONTAINER_ROLE` | 容器角色（web/celery-worker/celery-beat） | `web` |
| `RUN_MIGRATIONS` | 启动时执行迁移 | `1` |
| `RUN_COLLECTSTATIC` | 启动时收集静态文件 | `1` |
| `DJANGO_SUPERUSER_USERNAME` | 自动创建超级用户 | — |
| `DJANGO_SUPERUSER_PASSWORD` | 超级用户密码 | — |
| `DJANGO_SUPERUSER_EMAIL` | 超级用户邮箱 | — |
| `LOG_LEVEL` | 日志级别 | `INFO` |

## 7. 本地开发（无 Docker）

除 Docker 环境外，也可以直接在本地运行：

### 7.1 后端

```bash
cd backend
# 安装依赖（需要 Poetry）
poetry install
# 数据库迁移
python manage.py migrate
# 启动开发服务
python manage.py runserver
# 运行测试
python manage.py test apps.api.tests
# 系统检查
python manage.py check
```

本地开发默认使用 SQLite（无需 MySQL），后端运行在 `http://localhost:8000`。

### 7.2 前端

```bash
cd frontend
npm install
npm run dev          # 同时启动用户端(5173) + 管理端(5174)
npm run dev:user     # 单独启动用户端
npm run dev:admin    # 单独启动管理端
npm run build        # 构建两应用
npm run type-check   # TypeScript 类型检查
```

前端 Vite 开发服务自动代理 `/api`、`/media` 等路径到后端 8000 端口。

### 7.3 数据准备

```bash
# 生成 Demo 数据（本地）
python scripts/generate/seed_demo_data.py
# 批量导入酒店（需要 dist/images 目录）
python scripts/generate/import_hotels_from_dist_images.py --count 200 --images-dir dist/images
```

## 8. 当前未纳入本文的内容

以下内容不在本文中宣称为“已完成部署能力”：

- WebSocket 实时通知部署
- 未进入路由或未合并到工作树的前端页面
- 仓库中不存在的脚本或配置文件

如果后续新增部署能力，必须同步更新本文，并保持与实际文件一致。
