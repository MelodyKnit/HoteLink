# HoteLink 部署说明

## 1. 文档范围

本文只记录仓库中已经存在并可直接执行的部署能力，不描述尚未落地的方案。

部署相关事实以以下文件为准：

- [docker-compose.dev.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.dev.yml)
- [docker-compose.prod.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.prod.yml)
- [scripts/docker.ps1](D:\Nakamoto\Documents\Codes\Python\HoteLink\scripts\docker.ps1)
- [scripts/docker.sh](D:\Nakamoto\Documents\Codes\Python\HoteLink\scripts\docker.sh)
- [docs/thesis-alignment.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\thesis-alignment.md)

## 2. 已实现的部署资源

当前仓库中已经存在并可直接使用的文件：

- 开发环境编排：[docker-compose.dev.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.dev.yml)
- 生产环境编排：[docker-compose.prod.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.prod.yml)
- 开发环境变量示例：[.env.docker.dev.example](D:\Nakamoto\Documents\Codes\Python\HoteLink\.env.docker.dev.example)
- 生产环境变量示例：[.env.docker.example](D:\Nakamoto\Documents\Codes\Python\HoteLink\.env.docker.example)
- 后端开发镜像：[backend/Dockerfile.dev](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\Dockerfile.dev)
- 后端生产镜像：[backend/Dockerfile](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\Dockerfile)
- 后端开发入口：[backend/docker/entrypoint.dev.sh](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\docker\entrypoint.dev.sh)
- 后端生产入口：[backend/docker/entrypoint.sh](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\docker\entrypoint.sh)
- 前端开发镜像：[frontend/Dockerfile.dev](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\Dockerfile.dev)
- 前端生产镜像：[frontend/Dockerfile](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\Dockerfile)
- Nginx 配置：[frontend/docker/nginx.conf](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\docker\nginx.conf)

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

- [backend/apps/api/urls.py](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\apps\api\urls.py)
- [backend/apps/api/views.py](D:\Nakamoto\Documents\Codes\Python\HoteLink\backend\apps\api\views.py)

当前可以确认已经实现的能力包括：

- 系统初始化、用户登录、管理员登录、JWT 刷新与退出
- 公共酒店查询、搜索建议、房态日历、通用上传、图片缩略图、城市与字典接口
- 用户端资料、收藏、订单、评价、积分、优惠券、发票、通知、AI 对话
- 管理端经营概览、图表、酒店、房型、库存、订单、评价、用户、员工、设置、AI 配置、系统重置

系统重置接口当前已经存在：

- `POST /api/v1/admin/system/reset`

该接口的限制条件也已经在代码中实现：

- 必须登录
- 必须是 `system_admin` 或超级用户
- 必须提交确认字段 `confirm=RESET`

## 4. 开发环境部署

### 4.1 开发环境服务

[docker-compose.dev.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.dev.yml) 当前定义了以下服务：

- `mysql`
- `redis`
- `backend-dev`
- `backend-check`
- `user-web-dev`
- `admin-web-dev`

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

- [scripts/generate/seed_demo_data.py](D:\Nakamoto\Documents\Codes\Python\HoteLink\scripts\generate\seed_demo_data.py)

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

[docker-compose.prod.yml](D:\Nakamoto\Documents\Codes\Python\HoteLink\docker-compose.prod.yml) 当前定义了以下服务：

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

[frontend/docker/nginx.conf](D:\Nakamoto\Documents\Codes\Python\HoteLink\frontend\docker\nginx.conf) 当前已配置以下路径：

- `/`：用户端前端
- `/admin/`：管理端前端
- `/api/`：后端接口
- `/docs/`：Swagger UI
- `/redoc/`：ReDoc
- `/schema/`：OpenAPI Schema
- `/static/`：Django 静态资源
- `/media/`：上传文件

### 5.4 生产环境停止

```powershell
.\scripts\docker.ps1 prod down
```

## 6. 环境变量

开发环境当前示例文件为：

- [.env.docker.dev.example](D:\Nakamoto\Documents\Codes\Python\HoteLink\.env.docker.dev.example)

生产环境当前示例文件为：

- [.env.docker.example](D:\Nakamoto\Documents\Codes\Python\HoteLink\.env.docker.example)

当前已落地的 AI 相关环境变量包括：

- `AI_PROVIDER`
- `AI_ENABLED`
- `AI_BASE_URL`
- `AI_API_KEY`
- `AI_MODEL`
- `AI_REASONING_MODEL`
- `AI_TIMEOUT`

## 7. 当前未纳入本文的内容

以下内容不在本文中宣称为“已完成部署能力”：

- WebSocket 实时通知部署
- 未进入路由或未合并到工作树的前端页面
- 仓库中不存在的脚本或配置文件

如果后续新增部署能力，必须同步更新本文，并保持与实际文件一致。
