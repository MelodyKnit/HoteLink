# HoteLink 部署说明

## 1. 文档目标

本文件用于说明 HoteLink 项目在两种场景下的部署方式：

- 开发环境部署
- 生产环境部署

当前项目已经提供了两套 Docker 编排文件：

- [`../docker-compose.dev.yml`](../docker-compose.dev.yml)
- [`../docker-compose.prod.yml`](../docker-compose.prod.yml)

它们的目标不同：

- 开发环境：方便本地开发，支持挂载源码、热更新，不需要本机单独安装 MySQL 和 Redis
- 生产环境：面向正式部署，使用构建后的前端静态资源、Gunicorn、Nginx、Celery、MySQL、Redis

## 1.1 一键部署入口

项目根目录已经补充统一 Docker 启动脚本：

- [`../scripts/docker.ps1`](../scripts/docker.ps1)
- [`../scripts/docker.sh`](../scripts/docker.sh)

建议以后统一通过脚本管理 Docker 环境，而不是每次手写完整的 `docker compose` 命令。

PowerShell：

```powershell
.\scripts\docker.ps1 dev up
.\scripts\docker.ps1 prod up
```

macOS / Linux / Git Bash：

```bash
sh ./scripts/docker.sh dev up
sh ./scripts/docker.sh prod up
```

脚本支持的动作：

- `up`
- `down`
- `ps`
- `logs`
- `build`
- `restart`
- `check`，仅开发环境可用

## 2. 前置要求

无论开发环境还是生产环境，都建议先准备：

- Docker
- Docker Compose

建议版本：

- Docker Engine 24+
- Docker Compose v2+

## 3. 当前项目状态说明

当前仓库中：

- 前端双应用已经初始化完成
- 前端镜像可以正常构建
- 后端依赖已经准备好
- 后端生产镜像和开发镜像也已经准备好

当前仓库中已完成：

- `manage.py`
- `config/settings/dev.py`
- `config/settings/prod.py`
- `config/urls.py`
- `config/wsgi.py`
- `config/asgi.py`
- `config/celery.py`
- 基础 app 与初始迁移

所以当前阶段：

- 前端容器可以运行
- `mysql` 和 `redis` 可以作为开发和生产基础设施使用
- 后端容器已经具备启动 Django 服务的基础

当前真正缺少的不是部署基础，而是更完整的业务实现。

## 3.1 文档同步约定

- 新增部署相关配置时，必须同步更新本文件
- 新增环境变量时，必须同步更新 `.env` 示例文件和本文件
- 新增 AI 配置时，必须同步更新 [`ai-integration.md`](./ai-integration.md)
- 若部署方案与论文基线实现产生差异，必须同步更新 [`thesis-alignment.md`](./thesis-alignment.md)

## 4. 开发环境部署

### 4.1 目的

开发环境的设计目标：

- 不在本机额外安装 MySQL
- 不在本机额外安装 Redis
- 用容器承载后端运行环境
- 用容器直接启动用户端和管理端 Vite 开发服务
- 改代码后使用挂载目录与热更新，不必重复部署生产镜像

### 4.2 相关文件

- [`../docker-compose.dev.yml`](../docker-compose.dev.yml)
- [`../.env.docker.dev.example`](../.env.docker.dev.example)
- [`../backend/Dockerfile.dev`](../backend/Dockerfile.dev)
- [`../backend/docker/entrypoint.dev.sh`](../backend/docker/entrypoint.dev.sh)
- [`../frontend/Dockerfile.dev`](../frontend/Dockerfile.dev)

### 4.3 开发环境服务组成

- `mysql`
- `redis`
- `backend-dev`
- `user-web-dev`
- `admin-web-dev`

### 4.4 默认端口

- `3306`：MySQL
- `6379`：Redis
- `8000`：后端开发服务
- `5173`：用户端开发服务
- `5174`：管理端开发服务

### 4.5 开发环境启动步骤

1. 根据你的本地需求修改 `.env.docker.dev`

重点可调整：

- MySQL 账号密码
- Redis 连接地址
- Django 调试配置
- 前后端暴露端口
- `AI_API_KEY`
- `AI_MODEL`

如果 `.env.docker.dev` 不存在，首次执行脚本时会自动根据 `.env.docker.dev.example` 创建。

2. 一键启动开发环境：

```powershell
.\scripts\docker.ps1 dev up
```

或：

```bash
sh ./scripts/docker.sh dev up
```

3. 查看容器状态：

```powershell
.\scripts\docker.ps1 dev ps
```

或：

```bash
sh ./scripts/docker.sh dev ps
```

4. 查看日志：

```powershell
.\scripts\docker.ps1 dev logs
```

或：

```bash
sh ./scripts/docker.sh dev logs
```

### 4.6 开发环境访问地址

- 用户端：[http://localhost:5173](http://localhost:5173)
- 管理端：[http://localhost:5174/admin/](http://localhost:5174/admin/)
- 后端：[http://localhost:8000](http://localhost:8000)

### 4.7 开发环境如何工作

#### 前端

- `frontend` 目录通过 volume 挂载进容器
- Vite 开发服务在容器中运行
- 本地修改前端源码后，容器内开发服务会进行热更新
- 开发环境默认启用 `CHOKIDAR_USEPOLLING=true`，用于兼容 Windows + Docker Desktop 的文件变更监听

#### 后端

- `backend` 目录通过 volume 挂载进容器
- 容器内使用 Poetry 安装依赖
- 容器可直接运行 `python manage.py runserver 0.0.0.0:8000`

#### AI

- DeepSeek 相关配置通过 `.env.docker.dev` 注入
- 后端统一通过 `openai` SDK 调用 AI
- 不要在前端容器中放置真实 AI 密钥

#### 数据

- MySQL 和 Redis 使用 Docker volume 持久化
- 即使重启容器，数据不会直接丢失

### 4.8 开发环境停止与清理

停止容器：

```powershell
.\scripts\docker.ps1 dev down
```

或：

```bash
sh ./scripts/docker.sh dev down
```

停止并删除数据卷：

```bash
docker compose --env-file .env.docker.dev -f docker-compose.dev.yml down -v
```

注意：

- `down -v` 会删除 MySQL 和 Redis 的开发数据
- 一般只在你确认要重置开发数据时使用

### 4.9 当前阶段的已知行为

当前开发环境中，`backend-dev` 会：

- 安装 Poetry 依赖
- 执行 Django `check`
- 执行 Django 迁移
- 启动 Django 开发服务

后续你继续补代码时，不需要重新部署整套生产环境。

### 4.10 开发环境中的后端检查与测试

如果你希望直接在 Docker 开发环境中检查后端，可使用：

```powershell
.\scripts\docker.ps1 dev check
```

或：

```bash
sh ./scripts/docker.sh dev check
```

该命令会在开发环境容器中执行：

- `python manage.py check`
- `python manage.py test apps.api`

补充说明：

- `backend-check` 服务会临时使用 MySQL `root` 账号创建 Django 测试库
- `backend-dev` 业务容器仍然连接普通业务开发库
- 这样既能保留 Django 标准测试流程，也避免把创建数据库权限开放给普通业务账号

如果只想进入开发后端容器手动执行命令，可使用：

```bash
docker compose --env-file .env.docker.dev -f docker-compose.dev.yml exec backend-dev sh
```

进入后可继续运行：

```bash
python manage.py check
python manage.py test apps.api
python manage.py seed_demo_data
```

## 5. 生产环境部署

### 5.1 目的

生产环境的设计目标：

- 使用构建后的前端静态资源
- 使用 Nginx 承担静态文件托管与反向代理
- 使用 Gunicorn 运行 Django
- 使用 Celery Worker 和 Celery Beat
- 使用 MySQL 和 Redis 作为正式基础设施

### 5.2 相关文件

- [`../docker-compose.prod.yml`](../docker-compose.prod.yml)
- [`../.env.docker.example`](../.env.docker.example)
- [`../backend/Dockerfile`](../backend/Dockerfile)
- [`../backend/docker/entrypoint.sh`](../backend/docker/entrypoint.sh)
- [`../frontend/Dockerfile`](../frontend/Dockerfile)
- [`../frontend/docker/nginx.conf`](../frontend/docker/nginx.conf)

### 5.3 生产环境服务组成

- `mysql`
- `redis`
- `backend`
- `celery-worker`
- `celery-beat`
- `web`

### 5.4 生产环境访问路径

- `/`：用户端前端
- `/admin/`：酒店管理端前端
- `/api/`：后端接口
- `/docs/`：Swagger 或 API 文档入口
- `/redoc/`：ReDoc
- `/schema/`：OpenAPI schema
- `/static/`：Django collectstatic 静态资源
- `/media/`：上传文件

### 5.5 生产环境启动步骤

1. 修改 `.env.docker`

至少应检查：

- 数据库账号密码
- Django Secret Key
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- Gunicorn worker 数量
- Celery app 配置
- `AI_API_KEY`
- `AI_MODEL`
- `AI_REASONING_MODEL`

如果 `.env.docker` 不存在，首次执行脚本时会自动根据 `.env.docker.example` 创建。

2. 一键启动生产环境：

```powershell
.\scripts\docker.ps1 prod up
```

或：

```bash
sh ./scripts/docker.sh prod up
```

3. 查看运行状态：

```powershell
.\scripts\docker.ps1 prod ps
```

或：

```bash
sh ./scripts/docker.sh prod ps
```

4. 查看日志：

```powershell
.\scripts\docker.ps1 prod logs
```

或：

```bash
sh ./scripts/docker.sh prod logs
```

### 5.6 生产环境如何工作

#### 前端

- 使用 `frontend/Dockerfile` 进行多阶段构建
- 在构建阶段完成 `npm ci` 和 `npm run build`
- 构建结果复制到 Nginx 镜像中

#### 网关

- `web` 容器使用 Nginx
- 用户端挂载在 `/`
- 管理端挂载在 `/admin/`
- `/api/`、`/docs/` 等路径反向代理到 Django

#### 后端

- 使用 `backend/Dockerfile`
- 启动脚本为 [`../backend/docker/entrypoint.sh`](../backend/docker/entrypoint.sh)
- 默认可在启动时执行迁移和 `collectstatic`
- 正式 Web 服务通过 Gunicorn 运行

#### AI

- 生产环境中的 `AI_API_KEY` 必须通过 `.env.docker` 或部署平台环境变量注入
- 禁止把真实密钥写进镜像、源码和示例文件
- 建议为 AI 调用添加监控与审计日志

#### 异步任务

- `celery-worker` 执行异步任务
- `celery-beat` 执行定时任务

#### 数据持久化

生产环境使用以下 volume：

- `mysql_data`
- `redis_data`
- `static_data`
- `media_data`

### 5.7 生产环境停止与更新

停止服务：

```powershell
.\scripts\docker.ps1 prod down
```

或：

```bash
sh ./scripts/docker.sh prod down
```

重新构建并启动：

```powershell
.\scripts\docker.ps1 prod restart
```

或：

```bash
sh ./scripts/docker.sh prod restart
```

拉起单个服务：

```bash
docker compose --env-file .env.docker -f docker-compose.prod.yml up -d backend
```

### 5.8 当前阶段的已知行为

当前生产环境已经具备完整的基础部署骨架：

- 前端镜像可以构建
- Nginx 配置已经就绪
- MySQL、Redis、Celery 编排结构已经就绪
- Django 项目骨架已经就绪

当前仍需随着业务开发继续补充的，是后端业务代码而不是 Docker 部署结构。

## 6. 开发环境与生产环境的区别

### 开发环境

- 强调热更新
- 使用源码挂载
- 前端直接跑 Vite dev server
- 后端直接跑 Django 开发服务
- 便于频繁修改和调试

### 生产环境

- 强调稳定性
- 使用构建产物
- 前端通过 Nginx 提供静态资源
- 后端通过 Gunicorn 提供服务
- 增加 Celery Worker 和 Beat

## 7. 常用命令速查

### 开发环境

启动：

```powershell
.\scripts\docker.ps1 dev up
```

查看状态：

```powershell
.\scripts\docker.ps1 dev ps
```

查看日志：

```powershell
.\scripts\docker.ps1 dev logs
```

停止：

```powershell
.\scripts\docker.ps1 dev down
```

### 生产环境

启动：

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

停止：

```powershell
.\scripts\docker.ps1 prod down
```

## 8. 推荐后续动作

为了让这两套 Docker 部署都真正完整可用，建议下一步优先完成：

1. 继续细化 Django 业务模型
2. 设计用户端与管理端接口
3. 补充认证、权限和菜单体系
4. 补充 Celery 任务实现
5. 为 Docker 环境增加更细致的健康检查与初始化脚本
