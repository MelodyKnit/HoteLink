# HoteLink API 接口设计文档

## 1. 文档目标

本文件用于统一 HoteLink 酒店预订与管理平台的接口说明，服务于以下场景：

- 前后端联调
- 后端接口开发
- 数据库与业务建模
- 测试用例编写
- 已实现 HTTP 接口对齐
- 毕业论文中的接口设计说明

本文档当前遵循以下原则：

- 以论文主线功能为核心
- 采用统一的请求头、参数格式、返回格式
- 当前以已实现的 `GET`、`POST` HTTP 接口为准
- 描述尽量通俗易懂，方便前端、后端、测试共同理解
- 枚举值统一管理，避免前后端口径不一致
- 路由与行为以 `backend/apps/api/urls.py` 和 `backend/apps/api/views.py` 为准
- 未实现能力必须明确标注为“规划中”，不能写成已交付

## 2. 接口总览

### 2.1 请求方式

当前项目已实现的请求方式如下：

- `GET`：查询、获取详情、获取列表、获取统计
- `POST`：新增、修改、删除、状态流转、登录、提交表单、动作型操作
说明：

- 为保持论文和工程文档表述一致，更新和删除行为优先使用动作型 `POST`
- 当前不强制使用 `PUT`、`PATCH`、`DELETE`
- WebSocket 相关能力目前未在后端代码中落地，不作为已实现接口记录

### 2.2 接口分组

- 公共接口：`/api/v1/public/`
- 通用基础接口：`/api/v1/common/`
- 用户端接口：`/api/v1/user/`
- 管理端接口：`/api/v1/admin/`

### 2.3 角色权限

| 角色 | 说明 | 可访问范围 |
|---|---|---|
| `guest` | 未登录访客 | `public`、部分 `common` |
| `user` | 普通用户 | `public`、`common`、`user` |
| `hotel_admin` | 酒店管理员 | `public`、`common`、`admin` |
| `system_admin` | 系统管理员 | `public`、`common`、`admin` |

### 2.4 API 版本策略

- 当前统一使用 `v1`
- 版本前缀格式：`/api/v1/...`
- 后续若字段变化较大，可新增 `v2`，不直接覆盖旧版本

## 3. 通用约定

### 3.1 数据格式

- 请求体默认：`application/json`
- 文件上传：`multipart/form-data`
- 返回体统一：`application/json; charset=utf-8`
- 时间默认使用北京时间展示，后端建议内部统一使用 UTC 存储

### 3.2 字段命名规则

- JSON 字段统一使用 `snake_case`
- 布尔值字段统一使用 `is_xxx`、`has_xxx`
- 主键字段统一使用 `id`
- 关联对象字段统一使用 `xxx_id`

### 3.3 常用字段格式

| 字段类型 | 格式 | 示例 | 说明 |
|---|---|---|---|
| 日期 | `YYYY-MM-DD` | `2026-04-10` | 入住日期、离店日期 |
| 日期时间 | `YYYY-MM-DD HH:mm:ss` | `2026-04-10 14:30:00` | 展示给前端的时间 |
| 手机号 | 中国大陆 11 位 | `13800138000` | 用户手机号 |
| 金额 | `number`，保留两位小数 | `399.00` | 房价、支付金额 |
| 百分比 | `number` | `82.50` | 入住率、转化率 |
| JWT | `Bearer <token>` | `Bearer eyJ...` | 登录态校验 |

### 3.4 分页规则

列表类接口统一支持：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `page` | int | 否 | `1` | 当前页 |
| `page_size` | int | 否 | `20` | 每页数量 |

建议限制：

- `page >= 1`
- `1 <= page_size <= 100`

### 3.5 排序规则

- 查询列表时，排序优先通过 `sort` 参数表达
- 多字段排序可使用英文逗号分隔，例如：`created_at_desc,price_asc`
- 没有特殊说明时，列表默认按 `id desc` 或 `created_at desc`

## 4. 通用请求头

### 4.1 JSON 请求

```http
Content-Type: application/json
Accept: application/json
```

### 4.2 登录后请求

```http
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
```

### 4.3 文件上传请求

```http
Content-Type: multipart/form-data
Accept: application/json
Authorization: Bearer <access_token>
```

### 4.4 可选请求头

```http
X-Request-Id: 202604041200000001
X-Client-Type: web
X-App-Name: user-web
X-App-Version: 1.0.0
```

说明：

- `X-Request-Id`：用于排查日志
- `X-Client-Type`：可选值如 `web`、`h5`
- `X-App-Name`：当前前端应用名称
- `X-App-Version`：当前前端版本号

## 5. 通用返回格式

所有 HTTP 接口统一返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

字段说明：

| 字段 | 类型 | 必有 | 说明 |
|---|---|---|---|
| `code` | int | 是 | 业务状态码，`0` 表示成功 |
| `message` | string | 是 | 返回说明 |
| `data` | object/null | 是 | 返回数据体 |
| `request_id` | string | 建议 | 请求唯一标识 |
| `timestamp` | string | 建议 | 服务端返回时间 |

### 5.1 成功返回示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1
  },
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

### 5.2 分页返回示例

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  },
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

### 5.3 参数错误示例

```json
{
  "code": 4001,
  "message": "invalid parameters",
  "data": {
    "errors": {
      "mobile": [
        "手机号格式不正确"
      ]
    }
  },
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

### 5.4 无权限示例

```json
{
  "code": 4030,
  "message": "permission denied",
  "data": null,
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

## 6. 通用错误码建议

| 错误码 | 含义 |
|---|---|
| `0` | 成功 |
| `4000` | 通用请求错误 |
| `4001` | 参数错误 |
| `4002` | 缺少必填参数 |
| `4003` | 参数格式错误 |
| `4010` | 未登录 |
| `4011` | Token 无效 |
| `4012` | Token 已过期 |
| `4030` | 无权限访问 |
| `4040` | 资源不存在 |
| `4090` | 状态冲突 |
| `4091` | 库存不足 |
| `4092` | 房价已变化 |
| `4093` | 当前状态不允许该操作 |
| `4290` | 请求过于频繁 |
| `5000` | 服务端异常 |
| `5001` | 第三方服务异常 |
| `5002` | AI 服务不可用 |

## 7. 通用枚举定义

### 7.1 用户角色 `role`

## 8. 管理端扩展接口

### 8.1 AI 多供应商管理

1. 查询 AI 配置

- `GET /api/v1/admin/ai/settings`
- 权限：`hotel_admin` / `system_admin`

响应重点字段：

- `ai_enabled`
- `active_provider`
- `providers[]`
- `builtin_providers[]`

2. 更新 AI 配置

- `POST /api/v1/admin/ai/settings/update`
- 权限：`hotel_admin` / `system_admin`

请求示例：

```json
{
  "ai_enabled": true,
  "active_provider": "deepseek"
}
```

3. 添加或编辑供应商

- `POST /api/v1/admin/ai/provider/add`
- 权限：`hotel_admin` / `system_admin`

请求示例：

```json
{
  "name": "openai",
  "label": "OpenAI",
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-***",
  "chat_model": "gpt-4o-mini",
  "reasoning_model": "gpt-4o"
}
```

4. 切换活跃供应商

- `POST /api/v1/admin/ai/provider/switch`

```json
{
  "provider_name": "openai"
}
```

5. 删除供应商

- `POST /api/v1/admin/ai/provider/delete`

```json
{
  "provider_name": "openai"
}
```

注意：不能删除当前活跃供应商。

### 8.2 系统重置

1. 重置系统数据

- `POST /api/v1/admin/system/reset`
- 权限：仅 `system_admin`

请求示例：

```json
{
  "confirm": "RESET"
}
```

响应示例：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "reset": true,
    "deleted_counts": {
      "booking_orders": 120,
      "hotels": 8
    },
    "message": "系统已重置为初始状态，管理员账号已保留。"
  }
}
```

安全说明：

- 该接口为高危接口，必须进行二次确认
- 建议仅在测试环境或初始化阶段使用

| 值 | 含义 |
|---|---|
| `user` | 普通用户 |
| `hotel_admin` | 酒店管理员 |
| `system_admin` | 系统管理员 |

### 7.2 用户状态 `user_status`

| 值 | 含义 |
|---|---|
| `active` | 正常 |
| `disabled` | 禁用 |
| `locked` | 锁定 |

### 7.3 性别 `gender`

| 值 | 含义 |
|---|---|
| `unknown` | 未知 |
| `male` | 男 |
| `female` | 女 |

### 7.4 酒店状态 `hotel_status`

| 值 | 含义 |
|---|---|
| `draft` | 草稿 |
| `online` | 已上架 |
| `offline` | 已下架 |

### 7.5 酒店星级 `hotel_star`

| 值 | 含义 |
|---|---|
| `2` | 二星 |
| `3` | 三星 |
| `4` | 四星 |
| `5` | 五星 |

### 7.6 房型床型 `bed_type`

| 值 | 含义 |
|---|---|
| `single` | 单人床 |
| `double` | 双人床 |
| `queen` | 大床 |
| `twin` | 双床 |
| `family` | 家庭床 |

### 7.7 房态 `room_status`

| 值 | 含义 |
|---|---|
| `available` | 空闲可售 |
| `reserved` | 已预订 |
| `occupied` | 在住 |
| `cleaning` | 清扫中 |
| `maintenance` | 维修中 |
| `offline` | 下线不可售 |

### 7.8 订单状态 `order_status`

| 值 | 含义 |
|---|---|
| `pending_payment` | 待支付 |
| `paid` | 已支付 |
| `confirmed` | 已确认 |
| `checked_in` | 已入住 |
| `completed` | 已完成 |
| `cancelled` | 已取消 |
| `refunding` | 退款中 |
| `refunded` | 已退款 |

### 7.9 支付状态 `payment_status`

| 值 | 含义 |
|---|---|
| `unpaid` | 未支付 |
| `paid` | 已支付 |
| `failed` | 支付失败 |
| `refunded` | 已退款 |

### 7.10 支付方式 `payment_method`

| 值 | 含义 |
|---|---|
| `mock` | 模拟支付 |
| `wechat` | 微信支付 |
| `alipay` | 支付宝 |
| `cash` | 现金 |
| `card` | 银行卡 |

### 7.11 发票类型 `invoice_type`

| 值 | 含义 |
|---|---|
| `personal` | 个人发票 |
| `company` | 企业发票 |

### 7.12 会员等级 `member_level`

| 值 | 含义 |
|---|---|
| `normal` | 普通会员 |
| `silver` | 银卡会员 |
| `gold` | 金卡会员 |
| `platinum` | 白金会员 |

### 7.13 优惠券状态 `coupon_status`

| 值 | 含义 |
|---|---|
| `unused` | 未使用 |
| `used` | 已使用 |
| `expired` | 已过期 |

### 7.14 报表任务状态 `report_task_status`

| 值 | 含义 |
|---|---|
| `pending` | 待处理 |
| `running` | 执行中 |
| `success` | 成功 |
| `failed` | 失败 |

### 7.15 评价回复状态 `review_reply_status`

| 值 | 含义 |
|---|---|
| `unreplied` | 未回复 |
| `replied` | 已回复 |

### 7.16 收藏状态 `favorite_status`

| 值 | 含义 |
|---|---|
| `collected` | 已收藏 |
| `cancelled` | 已取消收藏 |

### 7.17 通知类型 `notice_type`

| 值 | 含义 |
|---|---|
| `order` | 订单通知 |
| `payment` | 支付通知 |
| `activity` | 活动通知 |
| `system` | 系统通知 |
| `review` | 评价通知 |

### 7.18 AI 场景 `ai_scene`

| 值 | 含义 |
|---|---|
| `customer_service` | 客服问答 |
| `general` | 客服问答别名（后端会规范化为 `customer_service`） |

说明：

- 当前 `ai_scene` 仅用于用户端客服问答接口
- 管理端报表总结、评价总结、回复建议使用独立接口，不通过 `ai_scene` 传值

### 7.19 AI 情感标签 `sentiment_label`（规划中）

| 值 | 含义 |
|---|---|
| `positive` | 正面 |
| `neutral` | 中立 |
| `negative` | 负面 |

### 7.20 房间状态 `room_unit_status`（规划中）

| 值 | 含义 |
|---|---|
| `vacant` | 空闲 |
| `occupied` | 在住 |
| `cleaning` | 清扫中 |
| `maintenance` | 维修中 |
| `offline` | 停用 |

### 7.21 退款单状态 `refund_status`（规划中）

| 值 | 含义 |
|---|---|
| `pending` | 待审批 |
| `approved` | 已通过 |
| `completed` | 已退款 |
| `rejected` | 已拒绝 |

### 7.22 押金状态 `deposit_status`（规划中）

| 值 | 含义 |
|---|---|
| `held` | 持有中 |
| `released` | 已退还 |
| `deducted` | 已扣除 |

### 7.23 账单状态 `bill_status`（规划中）

| 值 | 含义 |
|---|---|
| `draft` | 草稿 |
| `issued` | 已出账 |
| `settled` | 已结清 |

### 7.24 导出任务状态 `export_status`（规划中）

| 值 | 含义 |
|---|---|
| `pending` | 排队中 |
| `processing` | 生成中 |
| `done` | 已完成 |
| `failed` | 失败 |

### 7.25 活动状态 `activity_status`（规划中）

| 值 | 含义 |
|---|---|
| `draft` | 草稿 |
| `scheduled` | 定时上线 |
| `active` | 进行中 |
| `ended` | 已结束 |
| `cancelled` | 已取消 |

### 7.26 AI 调用状态 `ai_call_status`（规划中）

| 值 | 含义 |
|---|---|
| `success` | 成功 |
| `failed` | 失败 |
| `timeout` | 超时 |
| `quota_exceeded` | 配额耗尽 |

### 7.27 文案风格 `copy_style`（规划中）

| 值 | 含义 |
|---|---|
| `formal` | 正式商务 |
| `casual` | 轻松活泼 |
| `literary` | 文艺优雅 |
| `social_media` | 社交媒体短文 |

## 8. 认证与登录规则

### 8.1 Token 规则

- 登录成功后返回 `access_token` 与 `refresh_token`
- `access_token` 用于访问接口
- `refresh_token` 用于刷新登录态
- 前端应将 `access_token` 放入请求头：

```http
Authorization: Bearer <access_token>
```

### 8.2 登录态失效处理

- 当接口返回 `4011` 或 `4012` 时，前端应尝试刷新令牌
- 若刷新失败，应清空登录态并跳转登录页

### 8.3 后台权限规则

- `hotel_admin` 只允许操作自己管理范围内的数据
- `system_admin` 允许操作全部平台数据
- 后台接口需要同时校验登录态和角色权限

## 9. 通用基础接口

### 9.1 系统初始化检查

**接口**

`GET /api/v1/system/init-check`

**权限**

- 公开接口（`AllowAny`）

**说明**

判断系统中是否已存在管理员账号。前端首次访问时调用此接口，若返回 `initialized: false`，引导进入初始化页面。

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "initialized": false
  }
}
```

### 9.2 系统首次初始化

**接口**

`POST /api/v1/system/init-setup`

**权限**

- 公开接口（`AllowAny`）
- 仅当系统中无管理员时可用

**请求体**

```json
{
  "username": "admin",
  "password": "Password123"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `username` | string | 是 | 管理员用户名 |
| `password` | string | 是 | 管理员密码 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "admin",
      "role": "system_admin"
    }
  }
}
```

**错误码**

| code | 说明 |
|---|---|
| `4030` | 系统已初始化，无法重复创建 |
| `4090` | 用户名已存在 |

### 9.3 上传文件

**接口**

`POST /api/v1/common/upload`

**权限**

- `user`
- `hotel_admin`
- `system_admin`

**请求头**

```http
Content-Type: multipart/form-data
Authorization: Bearer <access_token>
```

**表单字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | file | 是 | 上传文件 |
| `scene` | string | 是 | 上传场景，如 `avatar`、`hotel`、`room_type`、`review_image` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "file_name": "avatar.png",
    "file_url": "https://cdn.example.com/uploads/avatar.png"
  }
}
```

### 9.4 图片缩略图

**接口**

`GET /api/v1/common/image-thumb`

**权限**

- 公开接口（`AllowAny`）

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `url` | string | 是 | 原图 URL（仅支持 `/media/...`） |
| `w` | int | 否 | 缩略图宽度，默认 `56`，范围 `16-512` |
| `h` | int | 否 | 缩略图高度，默认 `40`，范围 `16-512` |

**说明**

- 服务端会将原图缩放后返回 JPEG 小图并写入本地缓存目录（`media/.thumb_cache`）
- 建议管理端列表优先使用该接口返回的小图 URL，降低带宽与解码开销

### 9.5 城市列表

**接口**

`GET /api/v1/common/cities`

**说明**

- 用于前端酒店筛选、地址表单、管理端酒店编辑

### 9.6 字典数据

**接口**

`GET /api/v1/common/dicts`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `types` | string | 是 | 字典类型，多个值用英文逗号分隔 |

**示例**

```text
/api/v1/common/dicts?types=hotel_star,payment_method,bed_type
```

## 10. 认证接口

### 10.1 用户注册

**接口**

`POST /api/v1/public/auth/register`

**请求体**

```json
{
  "username": "zhangsan",
  "password": "Password123",
  "confirm_password": "Password123",
  "mobile": "13800138000",
  "email": "zhangsan@example.com"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `username` | string | 是 | 用户名，建议 4-30 位 |
| `password` | string | 是 | 登录密码 |
| `confirm_password` | string | 是 | 确认密码 |
| `mobile` | string | 是 | 手机号 |
| `email` | string | 否 | 邮箱 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 1,
    "username": "zhangsan"
  }
}
```

### 10.2 用户登录

**接口**

`POST /api/v1/public/auth/login`

**请求体**

```json
{
  "username": "zhangsan",
  "password": "Password123"
}
```

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "xxx",
    "refresh_token": "xxx",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "zhangsan",
      "role": "user"
    }
  }
}
```

### 10.3 管理员登录

**接口**

`POST /api/v1/public/auth/admin-login`

**说明**

- 用于酒店管理员和系统管理员登录后台

**请求体**

```json
{
  "username": "admin",
  "password": "Password123"
}
```

### 10.4 刷新令牌

**接口**

`POST /api/v1/public/auth/refresh`

**请求体**

```json
{
  "refresh_token": "xxx"
}
```

### 10.5 退出登录

**接口**

`POST /api/v1/user/auth/logout`

**请求体**

```json
{
  "refresh_token": "xxx"
}
```

### 10.6 获取当前登录用户信息

**接口**

`GET /api/v1/user/auth/me`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "zhangsan",
    "nickname": "张三",
    "mobile": "13800138000",
    "email": "zhangsan@example.com",
    "role": "user",
    "status": "active",
    "member_level": "gold"
  }
}
```

## 11. 公共访问接口

### 11.1 首页数据

**接口**

`GET /api/v1/public/home`

**返回内容**

- Banner
- 热门城市
- 推荐酒店
- 推荐房型
- 活动专区
- 优惠信息

### 11.2 酒店列表

**接口**

`GET /api/v1/public/hotels`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 关键词，支持酒店名、商圈、地址 |
| `city` | string | 否 | 城市 |
| `check_in_date` | string | 否 | 入住日期 |
| `check_out_date` | string | 否 | 离店日期 |
| `min_price` | number | 否 | 最低价格 |
| `max_price` | number | 否 | 最高价格 |
| `star` | int | 否 | 星级 |
| `sort` | string | 否 | 排序方式 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**排序枚举 `sort`**

| 值 | 含义 |
|---|---|
| `default` | 默认排序 |
| `price_asc` | 价格升序 |
| `price_desc` | 价格降序 |
| `rating_desc` | 评分降序 |
| `popular_desc` | 热门优先 |

### 11.3 搜索建议

**接口**

`GET /api/v1/public/hotels/search-suggest`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 是 | 搜索关键词 |

### 11.4 酒店详情

**接口**

`GET /api/v1/public/hotels/detail`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 是 | 酒店 ID |

**成功返回主要字段建议**

- 酒店基础信息
- 图片轮播
- 房型列表
- 设施服务
- 交通信息
- 评价摘要
- 入住与退房规则

### 11.5 酒店评价列表

**接口**

`GET /api/v1/public/hotels/reviews`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 是 | 酒店 ID |
| `score` | int | 否 | 评分筛选 |
| `has_image` | int | 否 | 是否仅看带图评价，`1` 表示是 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

### 11.6 房型价格日历

**接口**

`GET /api/v1/public/room-types/calendar`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `room_type_id` | int | 是 | 房型 ID |
| `start_date` | string | 是 | 开始日期，格式 `YYYY-MM-DD` |
| `end_date` | string | 是 | 结束日期，格式 `YYYY-MM-DD` |

**返回结构建议**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "room_type_id": 2001,
    "calendar": [
      {
        "date": "2026-04-10",
        "price": 399.00,
        "stock": 8,
        "status": "available"
      }
    ]
  }
}
```

## 12. 用户中心接口

### 12.1 获取个人资料

`GET /api/v1/user/profile`

### 12.2 更新个人资料

`POST /api/v1/user/profile/update`

**请求体**

```json
{
  "nickname": "张三",
  "mobile": "13800138000",
  "email": "zhangsan@example.com",
  "gender": "male",
  "birthday": "2000-01-01"
}
```

### 12.3 上传头像

`POST /api/v1/user/profile/avatar`

**请求格式**

- `multipart/form-data`

**表单字段**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `avatar` | file | 是 | 头像文件 |

### 12.4 修改密码

`POST /api/v1/user/profile/change-password`

**请求体**

```json
{
  "old_password": "OldPassword123",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

### 12.5 获取我的收藏酒店列表

`GET /api/v1/user/favorites`

### 12.6 收藏酒店

`POST /api/v1/user/favorites/add`

**请求体**

```json
{
  "hotel_id": 1001
}
```

### 12.7 取消收藏酒店

`POST /api/v1/user/favorites/remove`

**请求体**

```json
{
  "hotel_id": 1001
}
```

### 12.8 用户订单列表

`GET /api/v1/user/orders`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | 订单状态 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

### 12.9 历史入住人信息

`GET /api/v1/user/orders/guest-history`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 返回条数，默认 `6`，范围 `1-20` |

**返回示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "guest_name": "张三",
        "guest_mobile": "13800138000",
        "masked_mobile": "138***000"
      }
    ]
  }
}
```

### 12.10 用户订单详情

`GET /api/v1/user/orders/detail`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 是 | 订单 ID |

**返回字段补充**

- `original_amount`：原始订单金额
- `discount_amount`：优惠金额
- `pay_amount`：实际应付金额
- `total_amount`：兼容字段，等同于 `pay_amount`
- `payment_method`：最近一次支付记录使用的支付方式

### 12.11 创建订单

`POST /api/v1/user/orders/create`

**请求体**

```json
{
  "hotel_id": 1001,
  "room_type_id": 2001,
  "check_in_date": "2026-04-10",
  "check_out_date": "2026-04-12",
  "guest_name": "张三",
  "guest_mobile": "13800138000",
  "guest_count": 2,
  "coupon_id": 9001,
  "remark": "需要安静房间"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 是 | 酒店 ID |
| `room_type_id` | int | 是 | 房型 ID |
| `check_in_date` | string | 是 | 入住日期 |
| `check_out_date` | string | 是 | 离店日期 |
| `guest_name` | string | 是 | 入住人姓名 |
| `guest_mobile` | string | 是 | 入住人手机号 |
| `guest_count` | int | 是 | 入住人数 |
| `coupon_id` | int | 否 | 优惠券 ID |
| `remark` | string | 否 | 备注 |

### 12.11 修改订单入住信息

`POST /api/v1/user/orders/update`

**请求体**

```json
{
  "order_id": 3001,
  "guest_name": "张三",
  "guest_mobile": "13800138000",
  "remark": "晚到店，请保留房间"
}
```

### 12.12 订单支付

`POST /api/v1/user/orders/pay`

**请求体**

```json
{
  "order_id": 3001,
  "payment_method": "mock"
}
```

### 12.13 取消订单

`POST /api/v1/user/orders/cancel`

**请求体**

```json
{
  "order_id": 3001,
  "reason": "行程变化"
}
```

### 12.14 提交评价

`POST /api/v1/user/reviews/create`

**请求体**

```json
{
  "order_id": 3001,
  "score": 5,
  "content": "环境很好，服务也不错。"
}
```

**评分枚举 `score`**

| 值 | 含义 |
|---|---|
| `1` | 很差 |
| `2` | 较差 |
| `3` | 一般 |
| `4` | 满意 |
| `5` | 非常满意 |

### 12.15 积分流水

`GET /api/v1/user/points/logs`

### 12.16 用户优惠券列表

`GET /api/v1/user/coupons`

### 12.17 发票列表

`GET /api/v1/user/invoices`

### 12.18 新增发票抬头

`POST /api/v1/user/invoices/create`

**请求体**

```json
{
  "invoice_type": "company",
  "title": "北京测试科技有限公司",
  "tax_no": "91110000123456789X",
  "email": "invoice@example.com"
}
```

### 12.19 申请开票

`POST /api/v1/user/invoices/apply`

**请求体**

```json
{
  "order_id": 3001,
  "invoice_title_id": 7001
}
```

### 12.20 消息通知

#### 12.20.1 通知列表

`GET /api/v1/user/notices`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|—|——|
| `page` | int | 否 | 页码，默认 1 |
| `page_size` | int | 否 | 每页数量，默认 20 |

**返回列表元素**

| 字段 | 类型 | 说明 |
|---|---|——|
| `id` | int | 通知 ID |
| `notice_type` | string | 通知类型，见下方枚举 |
| `title` | string | 标题 |
| `content` | string | 正文内容 |
| `is_read` | bool | 是否已读 |
| `created_at` | string | 创建时间 ISO 8601 |

**`notice_type` 枚举**

| 値 | 含义 |
|---|---|
| `order` | 订单通知 |
| `payment` | 支付通知 |
| `member` | 会员通知（升级、积分） |
| `coupon` | 优惠券通知 |
| `review` | 评价积分奖励 |
| `activity` | 活动通知 |
| `system` | 系统通知 |

**额外返回字段**

```json
{
  "code": 0,
  "data": {
    "items": [...],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "unread_count": 3
  }
}
```

#### 12.20.2 未读数量

`GET /api/v1/user/notices/unread-count`

**返回示例**

```json
{ "code": 0, "data": { "unread_count": 3 } }
```

#### 12.20.3 标记已读 / 未读

`POST /api/v1/user/notices`

| 字段 | 类型 | 必填 | 说明 |
|---|---|—|——|
| `action` | string | 否 | `read`（默认）标记已读；`unread` 标记未读 |
| `ids` | array\<int\> | 否 | 指定通知 ID 列表；不传则操作全部 |

**返回示例**

```json
{ "code": 0, "data": { "unread_count": 0 } }
```

#### 12.20.4 删除通知

`DELETE /api/v1/user/notices`

| 字段 | 类型 | 必填 | 说明 |
|---|---|—|——|
| `ids` | array\<int\> | 否 | 指定通知 ID 列表；不传则删除全部 |

**返回示例**

```json
{ "code": 0, "data": { "deleted": 3, "unread_count": 0 } }
```

**前端交互设计**

- 普通模式：点击卡片即自动标记已读；`order`/`payment`/`coupon` 类型跳转对应页；其余类型以书本动画展开详情
- 管理模式（点击「管理」按鈕进入）：支持多选、全选，可批量标记已读 / 未读 / 删除、一键清空全部通知

## 13. 管理端接口

### 13.1 经营概览

`GET /api/v1/admin/dashboard/overview`

**返回内容建议**

- 今日订单数
- 今日入住数
- 今日退房数
- 今日营收
- 本月营收
- 入住率
- 待处理评价数
- 待处理报表任务数

### 13.2 经营趋势图表

`GET /api/v1/admin/dashboard/charts`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date_type` | string | 否 | 统计周期 |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |

**枚举 `date_type`**

| 值 | 含义 |
|---|---|
| `today` | 今日 |
| `week` | 本周 |
| `month` | 本月 |
| `custom` | 自定义区间 |

### 13.3 酒店列表

`GET /api/v1/admin/hotels`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 酒店名、地址关键词 |
| `status` | string | 否 | 酒店状态 |
| `ordering` | string | 否 | 排序字段，支持：`id`、`-id`、`name`、`-name`、`city`、`-city`、`star`、`-star`、`min_price`、`-min_price` |
| `thumb_mode` | string | 否 | 缩略图模式：`compact`（48x32）、`standard`（56x40） |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**返回字段补充**

- `cover_image`：原图 URL
- `cover_thumb`：缩略图 URL（管理端列表可优先使用）

### 13.4 新增酒店

`POST /api/v1/admin/hotels/create`

**请求体**

```json
{
  "name": "HoteLink 北京国贸店",
  "city": "北京",
  "address": "北京市朝阳区示例路 1 号",
  "star": 4,
  "phone": "010-88886666",
  "description": "地理位置优越，适合商务入住。",
  "cover_image": "/media/uploads/hotel/cover.jpg",
  "images": ["/media/uploads/hotel/gallery1.jpg", "/media/uploads/hotel/gallery2.jpg"],
  "status": "online"
}
```

说明：

- `cover_image`：酒店封面图 URL，通过 `/api/v1/common/upload`（scene=`hotel`）上传后获得
- `images`：酒店图片画廊 URL 列表（JSON 数组），支持多张图片

### 13.5 更新酒店

`POST /api/v1/admin/hotels/update`

**请求体**

```json
{
  "hotel_id": 1001,
  "name": "HoteLink 北京国贸旗舰店",
  "cover_image": "/media/uploads/hotel/new_cover.jpg",
  "images": ["/media/uploads/hotel/gallery1.jpg"],
  "status": "online"
}
```

### 13.6 删除酒店

`POST /api/v1/admin/hotels/delete`

**请求体**

```json
{
  "hotel_id": 1001
}
```

### 13.7 房型列表

`GET /api/v1/admin/room-types`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 按酒店筛选 |
| `ordering` | string | 否 | 排序字段，支持：`id`、`-id`、`name`、`-name`、`base_price`、`-base_price`、`bed_type`、`-bed_type` |
| `thumb_mode` | string | 否 | 缩略图模式：`compact`（48x32）、`standard`（56x40） |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**返回字段补充**

- `image`：原图 URL
- `image_thumb`：缩略图 URL（管理端列表可优先使用）

### 13.8 新增房型

`POST /api/v1/admin/room-types/create`

**请求体**

```json
{
  "hotel_id": 1001,
  "name": "豪华大床房",
  "bed_type": "queen",
  "area": 35,
  "breakfast_count": 2,
  "base_price": 399.00,
  "max_guest_count": 2,
  "image": "/media/uploads/room_type/deluxe_king.jpg",
  "status": "online"
}
```

说明：

- `image`：房型主图 URL，通过 `/api/v1/common/upload`（scene=`room_type`）上传后获得

### 13.9 更新房型

`POST /api/v1/admin/room-types/update`

### 13.10 删除房型

`POST /api/v1/admin/room-types/delete`

### 13.11 价格库存日历

`GET /api/v1/admin/inventory/calendar`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `room_type_id` | int | 是 | 房型 ID |
| `start_date` | string | 是 | 开始日期 |
| `end_date` | string | 是 | 结束日期 |

### 13.12 更新价格库存

`POST /api/v1/admin/inventory/update`

**请求体**

```json
{
  "room_type_id": 2001,
  "date": "2026-04-10",
  "price": 399.00,
  "stock": 8,
  "status": "available"
}
```

### 13.13 后台订单列表

`GET /api/v1/admin/orders`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `keyword` | string | 否 | 订单号、手机号、入住人 |
| `status` | string | 否 | 订单状态 |
| `check_in_date` | string | 否 | 入住日期 |
| `check_out_date` | string | 否 | 离店日期 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

### 13.14 后台订单详情

`GET /api/v1/admin/orders/detail`

### 13.15 后台订单状态操作

`POST /api/v1/admin/orders/change-status`

**请求体**

```json
{
  "order_id": 3001,
  "target_status": "confirmed"
}
```

### 13.16 办理入住

`POST /api/v1/admin/orders/check-in`

**请求体**

```json
{
  "order_id": 3001,
  "room_no": "1808",
  "operator_remark": "证件已核验"
}
```

### 13.17 办理退房

`POST /api/v1/admin/orders/check-out`

**请求体**

```json
{
  "order_id": 3001,
  "consume_amount": 0,
  "operator_remark": "已完成退房结算"
}
```

### 13.18 评价列表

`GET /api/v1/admin/reviews`

### 13.19 回复评价

`POST /api/v1/admin/reviews/reply`

**请求体**

```json
{
  "review_id": 5001,
  "content": "感谢您的入住，欢迎再次光临。"
}
```

### 13.20 删除评价（仅系统管理员）

`POST /api/v1/admin/reviews/delete`

**请求体**

```json
{
  "review_id": 5001
}
```

**权限**：`system_admin`

### 13.21 报表任务列表

`GET /api/v1/admin/reports/tasks`

### 13.21 创建报表任务

`POST /api/v1/admin/reports/tasks/create`

**请求体**

```json
{
  "report_type": "revenue_summary",
  "start_date": "2026-04-01",
  "end_date": "2026-04-30"
}
```

### 13.22 用户管理列表

`GET /api/v1/admin/users`

### 13.23 更新用户状态

`POST /api/v1/admin/users/change-status`

**请求体**

```json
{
  "user_id": 1,
  "status": "disabled"
}
```

### 13.24 员工账号列表

`GET /api/v1/admin/employees`

### 13.25 新增员工账号

`POST /api/v1/admin/employees/create`

**请求体**

```json
{
  "username": "frontdesk01",
  "password": "Password123",
  "name": "前台小王",
  "mobile": "13800138001",
  "role": "hotel_admin"
}
```

### 13.26 系统配置查询

`GET /api/v1/admin/settings`

### 13.27 系统配置更新

`POST /api/v1/admin/settings/update`

### 13.28 会员等级概览

`GET /api/v1/admin/members/overview`

**权限**

- `hotel_admin` / `system_admin`

**返回示例**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_users": 256,
    "levels": [
      {
        "level": "normal",
        "label": "普通会员",
        "count": 180,
        "threshold": 0,
        "discount_rate": 1.0,
        "points_multiplier": 1.0
      },
      {
        "level": "silver",
        "label": "银卡会员",
        "count": 50,
        "threshold": 500,
        "discount_rate": 0.95,
        "points_multiplier": 1.2
      }
    ]
  }
}
```

**返回字段**

| 字段 | 类型 | 说明 |
|---|---|---|
| `total_users` | int | 普通用户总数 |
| `levels[].level` | string | 等级代码 |
| `levels[].label` | string | 等级中文名 |
| `levels[].count` | int | 该等级人数 |
| `levels[].threshold` | int | 升级所需积分阈值 |
| `levels[].discount_rate` | float | 折扣率（1.0 表示无折扣） |
| `levels[].points_multiplier` | float | 积分倍率 |

### 13.29 优惠券模板列表

`GET /api/v1/admin/coupons`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | 筛选状态：`active` / `inactive` |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**返回列表元素**

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | int | 模板 ID |
| `name` | string | 优惠券名称 |
| `coupon_type` | string | 类型：`cash`（满减）/ `discount`（折扣） |
| `amount` | number | 满减金额（`cash` 类型） |
| `discount` | number | 折扣值（`discount` 类型，如 `8.5` 表示 85 折） |
| `min_amount` | number | 使用门槛金额 |
| `total_count` | int | 发放总量 |
| `claimed_count` | int | 已领取数量 |
| `remaining` | int | 剩余数量 |
| `per_user_limit` | int | 每人限领 |
| `required_level` | string | 领取所需会员等级（空表示不限） |
| `points_cost` | int | 兑换所需积分 |
| `status` | string | 状态：`active` / `inactive` |
| `valid_days` | int | 有效天数 |
| `valid_start` | string | 有效期开始日期 |
| `valid_end` | string | 有效期结束日期 |
| `created_at` | string | 创建时间 |

### 13.30 创建优惠券模板

`POST /api/v1/admin/coupons/create`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "name": "新用户满200减30",
  "coupon_type": "cash",
  "amount": 30.00,
  "discount": 10,
  "min_amount": 200.00,
  "total_count": 500,
  "per_user_limit": 1,
  "required_level": "",
  "points_cost": 0,
  "valid_days": 30,
  "valid_start": "2026-04-01",
  "valid_end": "2026-06-30"
}
```

### 13.31 更新优惠券模板状态

`POST /api/v1/admin/coupons/update`

**请求体**

```json
{
  "template_id": 1,
  "status": "inactive"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `template_id` | int | 是 | 模板 ID |
| `status` | string | 是 | 目标状态：`active`（上架）/ `inactive`（下架） |

### 13.32 系统重置

详见 [§8.2 系统重置](#82-系统重置)。

- `POST /api/v1/admin/system/reset`
- 权限：仅 `system_admin`
- 需发送 `{"confirm": "RESET"}` 确认

### 13.33 AI 供应商管理

详见 [§8.1 AI 多供应商管理](#81-ai-多供应商管理)。

- `POST /api/v1/admin/ai/provider/add` — 新增/编辑供应商
- `POST /api/v1/admin/ai/provider/switch` — 切换活跃供应商
- `POST /api/v1/admin/ai/provider/delete` — 删除供应商

## 14. AI 相关接口

说明：

- AI 是工程增强能力
- 当前建议作为辅助功能，不直接参与高风险交易最终判定
- AI 输出默认视为建议，最终决策应由业务规则或人工完成

### 14.1 用户端 AI 客服

`POST /api/v1/user/ai/chat`

**请求体**

```json
{
  "scene": "customer_service",
  "question": "这家酒店可以几点入住？",
  "hotel_id": 1001,
  "order_id": 3001,
  "booking_context": {
    "intent": "hotel_booking",
    "selected_city": "上海",
    "selected_hotel_id": 1001
  }
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scene` | string | 是 | AI 场景 |
| `question` | string | 是 | 用户问题 |
| `hotel_id` | int | 否 | 酒店相关问题时传入 |
| `order_id` | int | 否 | 订单相关问题时传入 |
| `booking_context` | object | 否 | AI 订房上下文，承载已选城市/酒店等结构化状态 |

场景约束：

- 当前仅支持：`customer_service`
- 兼容别名：`general`（服务端会自动规范化为 `customer_service`）
- 其他场景将返回参数错误（`4002`）

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "answer": "已为您切到上海，这里有 4 家当前可预订酒店。点一家，我继续把房型直接展开给您。",
    "scene": "customer_service",
    "booking_assistant": {
      "intent": "hotel_booking",
      "phase": "select_hotel",
      "context": {
        "intent": "hotel_booking",
        "selected_city": "上海",
        "selected_hotel_id": null
      },
      "options": [
        {
          "type": "select_hotel",
          "label": "外滩景观酒店",
          "value": "1001",
          "description": "上海 | 5星 | 评分4.8 | ¥899.00起",
          "payload": {
            "intent": "hotel_booking",
            "selected_city": "上海",
            "selected_hotel_id": 1001
          }
        }
      ]
    }
  }
}
```

说明：

- 当用户进入 AI 订房流程时，接口会在 `booking_assistant` 中返回结构化阶段、上下文与候选动作。
- `options[].type=select_city/select_hotel` 表示继续对话选择；`options[].type=navigate_booking` 表示可直接跳转到下单页。

### 14.2 用户端 AI 客服（流式）

`POST /api/v1/user/ai/chat/stream`

请求体与 `14.1` 相同。

响应类型：

- `text/event-stream`
- 结构化事件：`data: {"type": "meta", "scene": "customer_service", "booking_assistant": {...}}`
- 文本分块事件：`data: {"type": "chunk", "content": "...", "done": false}`
- 结束事件：`data: {"type": "done", "content": "", "done": true}`

示例：

```text
data: {"type":"meta","scene":"customer_service","booking_assistant":{"intent":"hotel_booking","phase":"select_city"}}

data: {"type":"chunk","content":"可以，我来帮您直接订酒店。","done":false}

data: {"type":"done","content":"","done":true}
```

### 14.3 管理端 AI 经营摘要

`POST /api/v1/admin/ai/report-summary`

**请求体**

```json
{
  "start_date": "2026-04-01",
  "end_date": "2026-04-30",
  "hotel_id": 1001
}
```

### 14.4 管理端 AI 评价摘要

`POST /api/v1/admin/ai/review-summary`

**请求体**

```json
{
  "hotel_id": 1001,
  "start_date": "2026-04-01",
  "end_date": "2026-04-30"
}
```

### 14.5 管理端 AI 回复建议

`POST /api/v1/admin/ai/reply-suggestion`

**请求体**

```json
{
  "review_id": 5001
}
```

### 14.6 管理端 AI 配置查询

`GET /api/v1/admin/ai/settings`

### 14.7 管理端 AI 配置更新

`POST /api/v1/admin/ai/settings/update`

说明：

- 此接口仅用于控制业务层配置，如是否启用某个 AI 场景
- 不建议通过接口直接返回真实密钥

## 15. 规划中 — AI 功能增强接口

> 以下接口均为**规划中**，标注为未来增强方向。实现后应去除标注并补充完整示例。

### 15.1 AI 智能定价建议

**接口**

`POST /api/v1/admin/ai/pricing-suggestion`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "room_type_id": 2001,
  "target_dates": ["2026-05-01", "2026-05-02", "2026-05-03"],
  "use_reasoning": false
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `room_type_id` | int | 是 | 房型 ID |
| `target_dates` | array\<string\> | 是 | 需定价的日期列表，最多 30 天 |
| `use_reasoning` | bool | 否 | 是否启用推理模型，默认 `false` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "room_type_id": 2001,
    "room_type_name": "豪华大床房",
    "hotel_name": "HoteLink 北京国贸店",
    "suggestions": [
      {
        "date": "2026-05-01",
        "current_price": 399.00,
        "suggested_min": 520.00,
        "suggested_max": 680.00,
        "suggested_price": 599.00,
        "reason": "五一假期需求高峰，建议上调价格",
        "is_holiday": true,
        "is_weekend": false,
        "historical_occupancy_rate": 95.5
      }
    ],
    "overall_analysis": "五一期间预计入住率可达 90% 以上，建议适当提价。当前定价低于同星级平均水平约 15%。",
    "ai_generated": true,
    "model_used": "deepseek-chat"
  }
}
```

**错误码**

| code | 说明 |
|---|---|
| `5002` | AI 服务不可用 |
| `4040` | 房型不存在 |
| `4001` | 日期范围超出限制 |

---

### 15.2 AI 经营分析深度报告

**接口**

`POST /api/v1/admin/ai/business-report`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "hotel_id": 1001,
  "start_date": "2026-03-01",
  "end_date": "2026-03-31",
  "dimensions": ["revenue", "occupancy", "room_type_ranking", "review_keywords", "anomaly"],
  "use_reasoning": true
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 指定酒店，不传则为全局分析 |
| `start_date` | string | 是 | 开始日期 |
| `end_date` | string | 是 | 结束日期 |
| `dimensions` | array\<string\> | 否 | 分析维度，不传则默认全部 |
| `use_reasoning` | bool | 否 | 是否使用推理模型（深度分析推荐开启） |

**dimensions 可选值**

| 值 | 含义 |
|---|---|
| `revenue` | 营收趋势与同比/环比 |
| `occupancy` | 入住率分析 |
| `room_type_ranking` | 房型收益排名 |
| `review_keywords` | 差评关键词提取 |
| `anomaly` | 异常指标高亮 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "report_markdown": "## 3月经营分析报告\n\n### 营收概览\n本月总营收 ¥128,560...",
    "summary": "3月整体营收环比增长 12%，入住率稳定在 78% 左右...",
    "highlights": [
      {"type": "positive", "text": "豪华大床房收益贡献最高，占比 42%"},
      {"type": "warning", "text": "标准间入住率仅 45%，低于平均水平"},
      {"type": "negative", "text": "差评中「隔音」关键词出现 8 次"}
    ],
    "ai_generated": true,
    "model_used": "deepseek-reasoner"
  }
}
```

---

### 15.3 AI 经营分析深度报告（流式）

**接口**

`POST /api/v1/admin/ai/business-report/stream`

请求体与 `15.2` 完全相同。

**响应类型**：`text/event-stream`

```text
data: {"type":"chunk","content":"## 3月经营分析报告\n\n","done":false}

data: {"type":"chunk","content":"### 营收概览\n本月总营收...","done":false}

data: {"type":"done","content":"","done":true}
```

---

### 15.4 AI 评价情感分析

**接口**

`POST /api/v1/admin/ai/review-sentiment`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "review_id": 5001
}
```

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "review_id": 5001,
    "sentiment_score": 0.85,
    "sentiment_label": "positive",
    "keywords": ["干净", "服务好", "交通方便"],
    "tags": ["服务", "卫生", "位置"],
    "summary": "住客对卫生与服务评价较高，交通便利为主要加分项",
    "ai_generated": true
  }
}
```

---

### 15.5 AI 评价情感批量分析

**接口**

`POST /api/v1/admin/ai/review-sentiment/batch`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "hotel_id": 1001,
  "start_date": "2026-03-01",
  "end_date": "2026-03-31"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 指定酒店 |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_202604081200",
    "message": "已提交批量分析任务，共 45 条评价待分析"
  }
}
```

说明：批量情感分析为 Celery 异步任务，前端可通过轮询或 WebSocket 获取完成通知。

---

### 15.6 AI 评价情感统计概览

**接口**

`GET /api/v1/admin/ai/review-sentiment/overview`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 指定酒店 |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total_analyzed": 120,
    "sentiment_distribution": {
      "positive": 78,
      "neutral": 30,
      "negative": 12
    },
    "top_tags": [
      {"tag": "服务", "count": 65},
      {"tag": "卫生", "count": 52},
      {"tag": "设施", "count": 41},
      {"tag": "位置", "count": 38},
      {"tag": "价格", "count": 27},
      {"tag": "餐饮", "count": 18}
    ],
    "top_keywords": [
      {"keyword": "干净", "count": 35, "sentiment": "positive"},
      {"keyword": "隔音差", "count": 8, "sentiment": "negative"},
      {"keyword": "服务态度好", "count": 22, "sentiment": "positive"}
    ],
    "trend": [
      {"date": "2026-03-01", "positive": 5, "neutral": 2, "negative": 1},
      {"date": "2026-03-02", "positive": 3, "neutral": 1, "negative": 0}
    ]
  }
}
```

---

### 15.7 AI 营销文案生成

**接口**

`POST /api/v1/admin/ai/marketing-copy`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "hotel_id": 1001,
  "copy_type": "holiday_promo",
  "style": "casual",
  "keywords": ["五一", "亲子", "早餐"],
  "target_audience": "家庭客群",
  "extra_notes": "突出亲子设施和免费早餐"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 指定酒店，传入则自动注入酒店信息 |
| `copy_type` | string | 是 | 文案类型 |
| `style` | string | 否 | 文案风格，默认 `formal`，见枚举 `copy_style` |
| `keywords` | array\<string\> | 否 | 重点关键词 |
| `target_audience` | string | 否 | 目标人群 |
| `extra_notes` | string | 否 | 额外要求 |

**copy_type 可选值**

| 值 | 含义 |
|---|---|
| `hotel_promo` | 酒店推广文案 |
| `holiday_promo` | 节假日特惠文案 |
| `member_activity` | 会员专属活动文案 |
| `seasonal_promo` | 季节性促销文案 |
| `social_media` | 社交媒体短文案 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "copies": [
      {
        "title": "五一亲子嗨住季",
        "content": "这个五一，带上宝贝来 HoteLink 北京国贸店...",
        "style": "casual"
      },
      {
        "title": "五一家庭欢享套餐",
        "content": "尊享家庭出行礼遇，入住即享双人早餐...",
        "style": "formal"
      }
    ],
    "ai_generated": true
  }
}
```

---

### 15.8 AI 酒店/房型内容生成

**接口**

`POST /api/v1/admin/ai/content-generate`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "content_type": "hotel_description",
  "context": {
    "name": "HoteLink 北京国贸店",
    "city": "北京",
    "star": 5,
    "address": "北京市朝阳区国贸大道1号"
  },
  "count": 3
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `content_type` | string | 是 | `hotel_description` / `room_description` / `seo_keywords` |
| `context` | object | 是 | 当前表单上下文数据（酒店或房型字段） |
| `count` | int | 否 | 生成候选数量，默认 `3`，范围 `1-5` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "candidates": [
      "坐落于北京CBD核心地段，HoteLink 北京国贸店以五星级标准...",
      "毗邻国贸商圈，交通便捷，HoteLink 北京国贸店为商旅精英...",
      "在繁华都市的心脏地带，HoteLink 北京国贸店将现代奢华..."
    ],
    "ai_generated": true
  }
}
```

---

### 15.9 AI 异常检测报告

**接口**

`GET /api/v1/admin/ai/anomaly-report`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 指定酒店 |
| `date` | string | 否 | 指定日期，默认今日 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "2026-04-08",
    "anomalies": [
      {
        "type": "occupancy_drop",
        "severity": "warning",
        "title": "入住率大幅下降",
        "description": "今日入住率 42%，较昨日 78% 下降 36 个百分点",
        "ai_analysis": "可能受周中工作日影响，建议关注是否有大型团队退订...",
        "suggested_actions": ["检查近期退订记录", "考虑推出周中特惠"]
      },
      {
        "type": "negative_review_spike",
        "severity": "danger",
        "title": "差评集中爆发",
        "description": "近24小时内新增 5 条1-2星差评",
        "ai_analysis": "差评集中反映隔音问题，可能与近期施工有关...",
        "suggested_actions": ["排查施工噪音源", "主动联系差评客户致歉"]
      }
    ],
    "has_anomaly": true,
    "ai_generated": true
  }
}
```

**anomaly.type 可选值**

| 值 | 含义 |
|---|---|
| `occupancy_drop` | 入住率大幅下降 |
| `cancellation_spike` | 退订率异常升高 |
| `room_idle` | 房型长期空置 |
| `negative_review_spike` | 差评集中爆发 |
| `revenue_anomaly` | 营收异常波动 |
| `overdue_checkout` | 到期未退房 |
| `overdue_checkin` | 到期未入住 |

---

### 15.10 AI 对话会话管理

#### 15.10.1 会话列表

**接口**

`GET /api/v1/user/ai/sessions`

**权限**

- `user`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "scene": "customer_service",
        "title": "关于入住时间的咨询",
        "message_count": 6,
        "last_message_at": "2026-04-08 10:30:00",
        "created_at": "2026-04-08 10:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

#### 15.10.2 会话消息列表

**接口**

`GET /api/v1/user/ai/sessions/{session_id}/messages`

**权限**

- `user`（仅自己的会话）

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量，默认 `50` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": 1,
    "items": [
      {
        "id": 1,
        "role": "user",
        "content": "这家酒店几点可以入住？",
        "created_at": "2026-04-08 10:00:00"
      },
      {
        "id": 2,
        "role": "assistant",
        "content": "一般入住时间为下午 14:00...",
        "tokens_used": 128,
        "created_at": "2026-04-08 10:00:05"
      }
    ],
    "page": 1,
    "page_size": 50,
    "total": 6,
    "total_pages": 1
  }
}
```

#### 15.10.3 删除会话

**接口**

`POST /api/v1/user/ai/sessions/delete`

**请求体**

```json
{
  "session_id": 1
}
```

#### 15.10.4 AI 对话（带会话持久化）

**接口**

`POST /api/v1/user/ai/chat`（升级原有接口）

**请求体新增参数**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `session_id` | int | 否 | 会话 ID，传入则追加到已有会话；不传则创建新会话 |

说明：升级后原有参数不变，新增 `session_id` 为可选字段，前端可选择是否携带。

---

### 15.11 AI 用量监控

#### 15.11.1 AI 调用日志列表

**接口**

`GET /api/v1/admin/ai/call-logs`

**权限**

- `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scene` | string | 否 | AI 场景筛选 |
| `provider` | string | 否 | 供应商筛选 |
| `status` | string | 否 | 调用状态筛选 |
| `user_id` | int | 否 | 用户 ID |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 10,
        "username": "zhangsan",
        "scene": "customer_service",
        "provider": "deepseek",
        "model": "deepseek-chat",
        "input_tokens": 1200,
        "output_tokens": 350,
        "total_tokens": 1550,
        "cost_estimate": 0.0023,
        "latency_ms": 2100,
        "status": "success",
        "created_at": "2026-04-08 10:30:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1200,
    "total_pages": 60
  }
}
```

#### 15.11.2 AI 用量统计概览

**接口**

`GET /api/v1/admin/ai/usage-stats`

**权限**

- `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `start_date` | string | 否 | 开始日期，默认本月初 |
| `end_date` | string | 否 | 结束日期，默认今日 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "period": {"start_date": "2026-04-01", "end_date": "2026-04-08"},
    "total_calls": 3200,
    "total_tokens": 4800000,
    "total_cost_estimate": 7.20,
    "avg_latency_ms": 1800,
    "success_rate": 98.5,
    "by_scene": [
      {"scene": "customer_service", "calls": 2500, "tokens": 3500000},
      {"scene": "report_summary", "calls": 200, "tokens": 800000},
      {"scene": "review_analysis", "calls": 500, "tokens": 500000}
    ],
    "by_provider": [
      {"provider": "deepseek", "calls": 3000, "tokens": 4500000},
      {"provider": "openai", "calls": 200, "tokens": 300000}
    ],
    "daily_trend": [
      {"date": "2026-04-01", "calls": 380, "tokens": 550000},
      {"date": "2026-04-02", "calls": 420, "tokens": 620000}
    ]
  }
}
```

#### 15.11.3 AI 配额配置查询

**接口**

`GET /api/v1/admin/ai/quota`

**权限**

- `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "daily_limit_per_user": 50,
    "monthly_token_budget": 10000000,
    "monthly_token_used": 4800000,
    "monthly_budget_usage_rate": 48.0
  }
}
```

#### 15.11.4 AI 配额配置更新

**接口**

`POST /api/v1/admin/ai/quota/update`

**权限**

- `system_admin`

**请求体**

```json
{
  "daily_limit_per_user": 100,
  "monthly_token_budget": 20000000
}
```

---

### 15.12 AI 客户画像

#### 15.12.1 查询客户 AI 画像

**接口**

`GET /api/v1/admin/customers/{user_id}/ai-portrait`

**权限**

- `hotel_admin` / `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 10,
    "ai_tags": ["商务型", "高频出行", "大床房偏好", "价格不敏感"],
    "ai_portrait": "该客户为商务差旅高频用户，过去半年入住 12 次，偏好五星级酒店大床房...",
    "last_analyzed_at": "2026-04-07 03:00:00",
    "order_count": 12,
    "total_spent": 15800.00,
    "avg_score": 4.5,
    "ai_generated": true
  }
}
```

#### 15.12.2 刷新客户 AI 画像

**接口**

`POST /api/v1/admin/customers/{user_id}/ai-portrait/refresh`

**权限**

- `hotel_admin` / `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message": "已提交画像更新任务",
    "task_id": "task_portrait_10_20260408"
  }
}
```

---

### 15.13 AI 订单异常摘要

**接口**

`GET /api/v1/admin/ai/order-anomaly-summary`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `date` | string | 否 | 指定日期，默认今日 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "date": "2026-04-08",
    "summary": "今日共检测到 3 类异常，涉及 8 个订单",
    "anomalies": [
      {
        "type": "overdue_payment",
        "count": 5,
        "description": "5 个订单超过 30 分钟未支付",
        "order_ids": [3001, 3005, 3008, 3012, 3015],
        "suggestion": "建议发送支付提醒通知"
      },
      {
        "type": "frequent_cancel_user",
        "count": 2,
        "description": "用户 zhangsan 近 7 天内取消 5 次订单",
        "user_ids": [10],
        "suggestion": "建议关注该用户行为，考虑限制短时间高频下单"
      },
      {
        "type": "overdue_checkin",
        "count": 1,
        "description": "1 个已确认订单入住日期已过但未办理入住",
        "order_ids": [3020],
        "suggestion": "建议联系客户确认是否取消"
      }
    ],
    "ai_generated": true
  }
}
```

---

### 15.14 AI 智能推荐

**接口**

`GET /api/v1/user/ai/recommendations`

**权限**

- `user`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `scene` | string | 否 | 推荐场景：`home`（首页）/ `hotel_detail`（详情页猜你喜欢）/ `search`（搜索结果增强） |
| `hotel_id` | int | 否 | 当前浏览的酒店 ID（`hotel_detail` 场景必传） |
| `keyword` | string | 否 | 搜索关键词（`search` 场景传入） |
| `limit` | int | 否 | 推荐数量，默认 `6`，范围 `1-20` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "hotel_id": 1002,
        "hotel_name": "HoteLink 上海外滩店",
        "city": "上海",
        "star": 5,
        "rating": 4.8,
        "min_price": 899.00,
        "cover_image": "/media/seed/hotels/shanghai_bund.jpg",
        "recommendation_reason": "根据您之前入住的五星级酒店偏好推荐"
      }
    ],
    "ai_generated": true
  }
}
```

---

### 15.15 AI 酒店对比分析

**接口**

`POST /api/v1/user/ai/hotel-compare`

**权限**

- `user`

**请求体**

```json
{
  "hotel_ids": [1001, 1002, 1003],
  "check_in_date": "2026-05-01",
  "check_out_date": "2026-05-03"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_ids` | array\<int\> | 是 | 酒店 ID 列表，2-3 个 |
| `check_in_date` | string | 否 | 入住日期（含价格对比时需要） |
| `check_out_date` | string | 否 | 离店日期 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "hotels": [
      {
        "hotel_id": 1001,
        "name": "HoteLink 北京国贸店",
        "star": 5,
        "rating": 4.7,
        "min_price": 599.00,
        "strengths": ["交通便利", "商务设施完善"],
        "weaknesses": ["价格偏高"]
      },
      {
        "hotel_id": 1002,
        "name": "HoteLink 北京望京店",
        "star": 4,
        "rating": 4.5,
        "min_price": 399.00,
        "strengths": ["性价比高", "房间宽敞"],
        "weaknesses": ["距离市中心较远"]
      }
    ],
    "ai_summary": "如果优先考虑交通便利和商务配套，推荐国贸店；如果注重性价比，望京店是更好的选择。",
    "ai_generated": true
  }
}
```

## 16. 规划中 — 业务功能增强接口

> 以下接口均为**规划中**，标注为未来增强方向。

### 16.1 房间管理

#### 16.1.1 房间列表

**接口**

`GET /api/v1/admin/rooms`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 否 | 酒店 ID |
| `room_type_id` | int | 否 | 房型 ID |
| `floor` | int | 否 | 楼层 |
| `status` | string | 否 | 房间状态，见枚举 `room_unit_status` |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "room_no": "1808",
        "floor": 18,
        "room_type_id": 2001,
        "room_type_name": "豪华大床房",
        "hotel_id": 1001,
        "hotel_name": "HoteLink 北京国贸店",
        "status": "vacant",
        "features": ["城市景观", "高楼层"],
        "created_at": "2026-01-01 00:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 80,
    "total_pages": 4
  }
}
```

#### 16.1.2 新增房间

**接口**

`POST /api/v1/admin/rooms/create`

**请求体**

```json
{
  "room_type_id": 2001,
  "room_no": "1808",
  "floor": 18,
  "features": ["城市景观", "高楼层"],
  "status": "vacant"
}
```

#### 16.1.3 更新房间

**接口**

`POST /api/v1/admin/rooms/update`

**请求体**

```json
{
  "room_id": 1,
  "room_no": "1808",
  "floor": 18,
  "features": ["城市景观", "高楼层", "无烟"],
  "status": "maintenance"
}
```

#### 16.1.4 删除房间

**接口**

`POST /api/v1/admin/rooms/delete`

**请求体**

```json
{
  "room_id": 1
}
```

---

### 16.2 房态总览看板

**接口**

`GET /api/v1/admin/rooms/status-board`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `hotel_id` | int | 是 | 酒店 ID |
| `date` | string | 否 | 查看日期，默认今日 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "hotel_id": 1001,
    "date": "2026-04-08",
    "summary": {
      "total": 80,
      "vacant": 35,
      "occupied": 30,
      "cleaning": 5,
      "maintenance": 5,
      "offline": 5
    },
    "floors": [
      {
        "floor": 18,
        "rooms": [
          {
            "room_id": 1,
            "room_no": "1808",
            "room_type_name": "豪华大床房",
            "status": "occupied",
            "guest_name": "张三",
            "order_id": 3001,
            "check_out_date": "2026-04-10"
          },
          {
            "room_id": 2,
            "room_no": "1809",
            "room_type_name": "标准双床房",
            "status": "vacant",
            "guest_name": null,
            "order_id": null,
            "check_out_date": null
          }
        ]
      }
    ]
  }
}
```

---

### 16.3 入住/退房记录

#### 16.3.1 入住记录列表

**接口**

`GET /api/v1/admin/check-in-records`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 否 | 订单 ID |
| `hotel_id` | int | 否 | 酒店 ID |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "order_id": 3001,
        "order_no": "HT202604100001",
        "room_no": "1808",
        "guest_name": "张三",
        "operator_name": "前台小王",
        "actual_check_in_time": "2026-04-10 14:30:00",
        "id_type": "id_card",
        "id_number_masked": "110***1234",
        "notes": "证件已核验",
        "created_at": "2026-04-10 14:30:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 50,
    "total_pages": 3
  }
}
```

#### 16.3.2 退房记录列表

**接口**

`GET /api/v1/admin/check-out-records`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

与入住记录列表相同。

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "order_id": 3001,
        "order_no": "HT202604100001",
        "room_no": "1808",
        "guest_name": "张三",
        "operator_name": "前台小王",
        "actual_check_out_time": "2026-04-12 11:00:00",
        "extra_charges": 0.00,
        "notes": "已完成退房结算",
        "created_at": "2026-04-12 11:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

---

### 16.4 续住

**接口**

`POST /api/v1/admin/orders/extend-stay`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "order_id": 3001,
  "new_check_out_date": "2026-04-14",
  "operator_remark": "客户申请续住两晚"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 是 | 订单 ID |
| `new_check_out_date` | string | 是 | 新离店日期，必须晚于当前离店日期 |
| `operator_remark` | string | 否 | 操作备注 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": 3001,
    "original_check_out_date": "2026-04-12",
    "new_check_out_date": "2026-04-14",
    "extra_nights": 2,
    "extra_amount": 798.00,
    "new_pay_amount": 1546.00,
    "message": "续住成功，需补交 ¥798.00"
  }
}
```

**错误码**

| code | 说明 |
|---|---|
| `4091` | 续住日期库存不足 |
| `4093` | 当前订单状态不支持续住（仅 `checked_in` 可续住） |

---

### 16.5 换房

**接口**

`POST /api/v1/admin/orders/change-room`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "order_id": 3001,
  "new_room_type_id": 2002,
  "new_room_no": "1910",
  "operator_remark": "客户要求升级房型"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 是 | 订单 ID |
| `new_room_type_id` | int | 否 | 新房型 ID（换房型时传入） |
| `new_room_no` | string | 是 | 新房间号 |
| `operator_remark` | string | 否 | 操作备注 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": 3001,
    "original_room_type": "标准大床房",
    "original_room_no": "1808",
    "new_room_type": "豪华大床房",
    "new_room_no": "1910",
    "price_diff": 200.00,
    "message": "换房成功，房型升级差价 ¥200.00"
  }
}
```

---

### 16.6 退款管理

#### 16.6.1 退款申请（用户端）

**接口**

`POST /api/v1/user/orders/refund`

**权限**

- `user`

**请求体**

```json
{
  "order_id": 3001,
  "reason": "行程变化，需要取消预订",
  "refund_amount": 748.00
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 是 | 订单 ID |
| `reason` | string | 是 | 退款原因 |
| `refund_amount` | number | 否 | 申请退款金额，不传则按退改规则自动计算 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "refund_id": 6001,
    "refund_no": "RF202604081200",
    "order_id": 3001,
    "refund_amount": 748.00,
    "status": "pending",
    "message": "退款申请已提交，等待审批"
  }
}
```

#### 16.6.2 退款单列表（管理端）

**接口**

`GET /api/v1/admin/refunds`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | 退款状态 |
| `keyword` | string | 否 | 订单号 / 退款单号 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 6001,
        "refund_no": "RF202604081200",
        "order_id": 3001,
        "order_no": "HT202604100001",
        "user_name": "zhangsan",
        "original_amount": 748.00,
        "refund_amount": 748.00,
        "reason": "行程变化",
        "status": "pending",
        "created_at": "2026-04-08 12:00:00",
        "processed_at": null
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 10,
    "total_pages": 1
  }
}
```

#### 16.6.3 退款审批

**接口**

`POST /api/v1/admin/refunds/process`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "refund_id": 6001,
  "action": "approve",
  "refund_amount": 748.00,
  "remark": "同意全额退款"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `refund_id` | int | 是 | 退款单 ID |
| `action` | string | 是 | `approve`（通过）/ `reject`（拒绝） |
| `refund_amount` | number | 否 | 实际退款金额（仅通过时，支持部分退款） |
| `remark` | string | 否 | 审批备注 |

---

### 16.7 押金管理

#### 16.7.1 押金收取

**接口**

`POST /api/v1/admin/deposits/create`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "order_id": 3001,
  "amount": 500.00
}
```

#### 16.7.2 押金退还

**接口**

`POST /api/v1/admin/deposits/release`

**请求体**

```json
{
  "deposit_id": 1,
  "release_amount": 500.00,
  "remark": "无损坏，全额退还"
}
```

#### 16.7.3 押金扣除

**接口**

`POST /api/v1/admin/deposits/deduct`

**请求体**

```json
{
  "deposit_id": 1,
  "deduct_amount": 200.00,
  "deduction_reason": "房间设施损坏赔偿"
}
```

#### 16.7.4 押金记录查询

**接口**

`GET /api/v1/admin/deposits`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 否 | 订单 ID |
| `status` | string | 否 | 押金状态 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

---

### 16.8 账单管理

#### 16.8.1 查询订单账单

**接口**

`GET /api/v1/admin/bills`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 否 | 订单 ID |
| `status` | string | 否 | 账单状态 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "order_id": 3001,
        "order_no": "HT202604100001",
        "total_amount": 798.00,
        "status": "issued",
        "items": [
          {"item_type": "room_charge", "description": "豪华大床房 × 2晚", "amount": 798.00},
          {"item_type": "service", "description": "迷你吧消费", "amount": 68.00},
          {"item_type": "deposit_deduction", "description": "设施损坏赔偿", "amount": 200.00}
        ],
        "created_at": "2026-04-12 11:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 1,
    "total_pages": 1
  }
}
```

#### 16.8.2 生成退房账单

**接口**

`POST /api/v1/admin/bills/generate`

**请求体**

```json
{
  "order_id": 3001,
  "extra_items": [
    {"item_type": "service", "description": "迷你吧消费", "amount": 68.00}
  ]
}
```

---

### 16.9 审计日志

**接口**

`GET /api/v1/admin/audit-logs`

**权限**

- `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `user_id` | int | 否 | 操作人 ID |
| `action` | string | 否 | 操作类型（如 `create_hotel`、`delete_order`、`system_reset`） |
| `target` | string | 否 | 操作目标（如 `hotel`、`order`、`user`） |
| `start_date` | string | 否 | 开始日期 |
| `end_date` | string | 否 | 结束日期 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "user_id": 1,
        "username": "admin",
        "action": "system_reset",
        "target": "system",
        "detail": {
          "deleted_counts": {"booking_orders": 120, "hotels": 8}
        },
        "ip_address": "192.168.1.100",
        "created_at": "2026-04-08 12:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 200,
    "total_pages": 10
  }
}
```

---

### 16.10 订单操作时间线

**接口**

`GET /api/v1/admin/orders/{order_id}/timeline`

**权限**

- `hotel_admin` / `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": 3001,
    "order_no": "HT202604100001",
    "events": [
      {
        "action": "created",
        "operator": "zhangsan（用户）",
        "description": "创建订单",
        "detail": {"room_type": "豪华大床房", "check_in": "2026-04-10"},
        "created_at": "2026-04-08 10:00:00"
      },
      {
        "action": "paid",
        "operator": "zhangsan（用户）",
        "description": "支付完成，支付方式：模拟支付",
        "detail": {"payment_no": "PAY202604081001", "amount": 748.00},
        "created_at": "2026-04-08 10:05:00"
      },
      {
        "action": "confirmed",
        "operator": "admin（管理员）",
        "description": "确认订单",
        "created_at": "2026-04-08 10:10:00"
      },
      {
        "action": "checked_in",
        "operator": "frontdesk01（管理员）",
        "description": "办理入住，房号 1808",
        "detail": {"room_no": "1808"},
        "created_at": "2026-04-10 14:30:00"
      }
    ]
  }
}
```

---

### 16.11 数据导出

#### 16.11.1 创建导出任务

**接口**

`POST /api/v1/admin/exports/create`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "export_type": "orders",
  "format": "xlsx",
  "filters": {
    "status": "completed",
    "start_date": "2026-03-01",
    "end_date": "2026-03-31"
  }
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `export_type` | string | 是 | 导出类型：`orders` / `reviews` / `users` / `revenue_report` |
| `format` | string | 否 | 导出格式：`xlsx`（默认）/ `csv` / `pdf` |
| `filters` | object | 否 | 筛选条件，按导出类型支持不同字段 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "export_20260408_001",
    "status": "pending",
    "message": "导出任务已提交，完成后将在下载中心可用"
  }
}
```

#### 16.11.2 导出任务列表

**接口**

`GET /api/v1/admin/exports`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "task_id": "export_20260408_001",
        "export_type": "orders",
        "format": "xlsx",
        "status": "done",
        "file_url": "/media/exports/orders_20260408_001.xlsx",
        "file_size": 102400,
        "record_count": 350,
        "created_at": "2026-04-08 12:00:00",
        "completed_at": "2026-04-08 12:01:30"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 5,
    "total_pages": 1
  }
}
```

#### 16.11.3 下载导出文件

**接口**

`GET /api/v1/admin/exports/{task_id}/download`

**说明**

- 返回文件流下载
- 仅 `done` 状态的任务可下载

---

### 16.12 批量操作

#### 16.12.1 订单批量操作

**接口**

`POST /api/v1/admin/orders/batch`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "order_ids": [3001, 3002, 3003],
  "action": "confirm"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_ids` | array\<int\> | 是 | 订单 ID 列表，最多 50 个 |
| `action` | string | 是 | 批量操作：`confirm` / `cancel` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 3,
    "success": 2,
    "failed": 1,
    "results": [
      {"order_id": 3001, "success": true},
      {"order_id": 3002, "success": true},
      {"order_id": 3003, "success": false, "error": "当前状态不允许该操作"}
    ]
  }
}
```

#### 16.12.2 酒店批量上下架

**接口**

`POST /api/v1/admin/hotels/batch-status`

**请求体**

```json
{
  "hotel_ids": [1001, 1002],
  "target_status": "offline"
}
```

#### 16.12.3 评价批量 AI 回复

**接口**

`POST /api/v1/admin/reviews/batch-reply`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "review_ids": [5001, 5002, 5003]
}
```

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "batch_reply_20260408",
    "message": "已提交 AI 批量回复任务，共 3 条评价"
  }
}
```

说明：此为 Celery 异步任务，AI 逐条生成回复后自动保存。

---

### 16.13 库存批量设置

**接口**

`POST /api/v1/admin/inventory/batch-update`

**权限**

- `hotel_admin` / `system_admin`

**请求体**

```json
{
  "room_type_id": 2001,
  "start_date": "2026-05-01",
  "end_date": "2026-05-07",
  "price": 599.00,
  "stock": 10,
  "status": "available",
  "apply_weekdays": true,
  "apply_weekends": true,
  "weekend_price": 699.00
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `room_type_id` | int | 是 | 房型 ID |
| `start_date` | string | 是 | 开始日期 |
| `end_date` | string | 是 | 结束日期（最大跨度 90 天） |
| `price` | number | 否 | 工作日价格 |
| `stock` | int | 否 | 库存数量 |
| `status` | string | 否 | 库存状态 |
| `apply_weekdays` | bool | 否 | 是否应用到工作日，默认 `true` |
| `apply_weekends` | bool | 否 | 是否应用到周末，默认 `true` |
| `weekend_price` | number | 否 | 周末价格（仅 `apply_weekends=true` 时生效） |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "updated_count": 7,
    "date_range": "2026-05-01 至 2026-05-07",
    "message": "已批量更新 7 天库存"
  }
}
```

---

### 16.14 客户档案

#### 16.14.1 客户档案详情

**接口**

`GET /api/v1/admin/customers/{user_id}`

**权限**

- `hotel_admin` / `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 10,
    "username": "zhangsan",
    "nickname": "张三",
    "mobile": "13800138000",
    "member_level": "gold",
    "points": 12500,
    "total_orders": 15,
    "total_spent": 18600.00,
    "avg_order_amount": 1240.00,
    "first_order_at": "2026-01-15 10:00:00",
    "last_order_at": "2026-04-05 14:00:00",
    "favorite_hotel_count": 3,
    "review_count": 8,
    "avg_review_score": 4.3,
    "ai_tags": ["商务型", "大床房偏好"],
    "ai_portrait": "该客户为商务差旅高频用户...",
    "note": "VIP 客户，注意服务质量",
    "created_at": "2026-01-10 08:00:00"
  }
}
```

#### 16.14.2 客户历史订单

**接口**

`GET /api/v1/admin/customers/{user_id}/orders`

与管理端订单列表结构相同，自动过滤为指定客户的订单。

#### 16.14.3 客户评价记录

**接口**

`GET /api/v1/admin/customers/{user_id}/reviews`

与管理端评价列表结构相同，自动过滤为指定客户的评价。

---

### 16.15 活动管理

#### 16.15.1 活动列表

**接口**

`GET /api/v1/admin/activities`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `status` | string | 否 | 活动状态 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "title": "五一亲子嗨住季",
        "description": "五一期间亲子家庭入住享八折优惠",
        "activity_type": "discount",
        "status": "active",
        "start_time": "2026-04-28 00:00:00",
        "end_time": "2026-05-05 23:59:59",
        "coupon_template_id": 5,
        "hotel_ids": [1001, 1002],
        "banner_image": "/media/uploads/activity/wuyi.jpg",
        "created_at": "2026-04-01 10:00:00"
      }
    ],
    "page": 1,
    "page_size": 20,
    "total": 3,
    "total_pages": 1
  }
}
```

#### 16.15.2 创建活动

**接口**

`POST /api/v1/admin/activities/create`

**请求体**

```json
{
  "title": "五一亲子嗨住季",
  "description": "五一期间亲子家庭入住享八折优惠",
  "activity_type": "discount",
  "start_time": "2026-04-28 00:00:00",
  "end_time": "2026-05-05 23:59:59",
  "coupon_template_id": 5,
  "hotel_ids": [1001, 1002],
  "banner_image": "/media/uploads/activity/wuyi.jpg"
}
```

**参数说明**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `title` | string | 是 | 活动标题 |
| `description` | string | 否 | 活动描述 |
| `activity_type` | string | 是 | `discount`（折扣）/ `coupon`（发券）/ `flash_sale`（限时抢购） |
| `start_time` | string | 是 | 开始时间 |
| `end_time` | string | 是 | 结束时间 |
| `coupon_template_id` | int | 否 | 关联优惠券模板 ID |
| `hotel_ids` | array\<int\> | 否 | 适用酒店 |
| `banner_image` | string | 否 | 活动 Banner 图 |

#### 16.15.3 更新活动

**接口**

`POST /api/v1/admin/activities/update`

**请求体**

```json
{
  "activity_id": 1,
  "title": "五一亲子嗨住季（加码版）",
  "status": "active"
}
```

#### 16.15.4 删除活动

**接口**

`POST /api/v1/admin/activities/delete`

**请求体**

```json
{
  "activity_id": 1
}
```

---

### 16.16 管理端通知

#### 16.16.1 管理端通知列表

**接口**

`GET /api/v1/admin/notices`

**权限**

- `hotel_admin` / `system_admin`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `notice_type` | string | 否 | 通知类型 |
| `is_read` | int | 否 | `0` 未读 / `1` 已读 |
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

#### 16.16.2 管理端未读通知数

**接口**

`GET /api/v1/admin/notices/unread-count`

#### 16.16.3 管理端通知标记已读

**接口**

`POST /api/v1/admin/notices/read`

**请求体**

```json
{
  "ids": [1, 2, 3]
}
```

---

### 16.17 浏览历史

#### 16.17.1 记录浏览

**接口**

`POST /api/v1/user/browsing-history/add`

**权限**

- `user`

**请求体**

```json
{
  "hotel_id": 1001
}
```

#### 16.17.2 浏览历史列表

**接口**

`GET /api/v1/user/browsing-history`

**权限**

- `user`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `limit` | int | 否 | 返回数量，默认 `20`，最大 `50` |

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "hotel_id": 1001,
        "hotel_name": "HoteLink 北京国贸店",
        "city": "北京",
        "star": 5,
        "rating": 4.7,
        "min_price": 599.00,
        "cover_image": "/media/seed/hotels/beijing_guomao.jpg",
        "viewed_at": "2026-04-08 10:30:00"
      }
    ]
  }
}
```

#### 16.17.3 清空浏览历史

**接口**

`POST /api/v1/user/browsing-history/clear`

---

### 16.18 订单分享

**接口**

`POST /api/v1/user/orders/share`

**权限**

- `user`

**请求体**

```json
{
  "order_id": 3001
}
```

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "share_token": "abc123def456",
    "share_url": "/order/share/abc123def456",
    "expires_at": "2026-04-15 12:00:00",
    "order_summary": {
      "hotel_name": "HoteLink 北京国贸店",
      "room_type_name": "豪华大床房",
      "check_in_date": "2026-04-10",
      "check_out_date": "2026-04-12"
    }
  }
}
```

**查看共享订单（公开）**

`GET /api/v1/public/order/share/{share_token}`

说明：仅返回脱敏后的订单摘要，不含手机号等敏感信息。

---

### 16.19 RBAC 权限管理

#### 16.19.1 角色列表

**接口**

`GET /api/v1/admin/roles`

**权限**

- `system_admin`

**成功返回**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "system_admin",
        "label": "系统管理员",
        "permissions": ["*"],
        "user_count": 1
      },
      {
        "id": 2,
        "name": "hotel_admin",
        "label": "酒店管理员",
        "permissions": ["hotel:read", "hotel:write", "order:read", "order:write"],
        "user_count": 3
      }
    ]
  }
}
```

#### 16.19.2 创建/更新角色

**接口**

`POST /api/v1/admin/roles/save`

**请求体**

```json
{
  "role_id": 2,
  "name": "hotel_admin",
  "label": "酒店管理员",
  "permissions": ["hotel:read", "hotel:write", "order:read", "order:write", "review:read", "review:reply"]
}
```

#### 16.19.3 权限枚举列表

**接口**

`GET /api/v1/admin/permissions`

**返回所有可分配的权限项及其分组。**

## 17. WebSocket 状态

当前仓库未提供 WebSocket 路由、消费者或实时推送实现，因此 WebSocket 不属于已交付能力。

如果后续新增实时通知，需要在代码落地后再补充：

- 连接地址
- 鉴权方式
- 事件模型
- 心跳机制

## 18. 典型接口完整示例

### 16.1 示例一：用户登录

**请求**

```http
POST /api/v1/public/auth/login
Content-Type: application/json
Accept: application/json
```

```json
{
  "username": "zhangsan",
  "password": "Password123"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": 1,
      "username": "zhangsan",
      "role": "user"
    }
  },
  "request_id": "202604041200000001",
  "timestamp": "2026-04-04 12:00:00"
}
```

### 16.2 示例二：创建订单

**请求**

```http
POST /api/v1/user/orders/create
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
```

```json
{
  "hotel_id": 1001,
  "room_type_id": 2001,
  "check_in_date": "2026-04-10",
  "check_out_date": "2026-04-12",
  "guest_name": "张三",
  "guest_mobile": "13800138000",
  "guest_count": 2,
  "coupon_id": 9001,
  "remark": "需要安静房间"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "order_id": 3001,
    "order_no": "HT202604100001",
    "status": "pending_payment",
    "payment_status": "unpaid",
    "original_amount": 798.00,
    "discount_amount": 50.00,
    "pay_amount": 748.00
  },
  "request_id": "202604041200000002",
  "timestamp": "2026-04-04 12:05:00"
}
```

### 16.3 示例三：后台更新价格库存

**请求**

```http
POST /api/v1/admin/inventory/update
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
```

```json
{
  "room_type_id": 2001,
  "date": "2026-04-10",
  "price": 399.00,
  "stock": 8,
  "status": "available"
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "room_type_id": 2001,
    "date": "2026-04-10",
    "price": 399.00,
    "stock": 8,
    "status": "available"
  },
  "request_id": "202604041200000003",
  "timestamp": "2026-04-04 12:08:00"
}
```

### 16.4 示例四：AI 评价回复建议

**请求**

```http
POST /api/v1/admin/ai/reply-suggestion
Content-Type: application/json
Accept: application/json
Authorization: Bearer <access_token>
```

```json
{
  "review_id": 5001
}
```

**响应**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "scene": "reply_suggestion",
    "suggested_reply": "感谢您的反馈，我们已经安排团队进一步优化房间隔音体验，期待您再次入住。"
  },
  "request_id": "202604041200000004",
  "timestamp": "2026-04-04 12:10:00"
}
```

## 19. 模块接口清单速查

### 19.1 系统、公共与认证

- `GET /api/v1/` — API 根路由
- `GET /api/v1/system/init-check` — 检查系统是否已初始化
- `POST /api/v1/system/init-setup` — 首次初始化：创建管理员
- `POST /api/v1/common/upload`
- `GET /api/v1/common/image-thumb` — 图片缩略图
- `GET /api/v1/common/cities`
- `GET /api/v1/common/dicts`
- `POST /api/v1/public/auth/register`
- `POST /api/v1/public/auth/login`
- `POST /api/v1/public/auth/admin-login`
- `POST /api/v1/public/auth/refresh`
- `GET /api/v1/public/home`
- `GET /api/v1/public/hotels`
- `GET /api/v1/public/hotels/search-suggest`
- `GET /api/v1/public/hotels/detail`
- `GET /api/v1/public/hotels/reviews`
- `GET /api/v1/public/room-types/calendar`
- `GET /api/v1/public/order/share/{share_token}` — 查看共享订单 \[规划中\]

### 19.2 用户端

- `POST /api/v1/user/auth/logout`
- `GET /api/v1/user/auth/me`
- `GET /api/v1/user/profile`
- `POST /api/v1/user/profile/update`
- `POST /api/v1/user/profile/avatar`
- `POST /api/v1/user/profile/change-password`
- `GET /api/v1/user/favorites`
- `POST /api/v1/user/favorites/add`
- `POST /api/v1/user/favorites/remove`
- `GET /api/v1/user/orders`
- `GET /api/v1/user/orders/detail`
- `POST /api/v1/user/orders/create`
- `POST /api/v1/user/orders/update`
- `POST /api/v1/user/orders/pay`
- `POST /api/v1/user/orders/cancel`
- `POST /api/v1/user/orders/refund` — 申请退款 \[规划中\]
- `POST /api/v1/user/orders/share` — 订单分享 \[规划中\]
- `POST /api/v1/user/reviews/create`
- `GET /api/v1/user/reviews`
- `GET /api/v1/user/points/logs`
- `GET /api/v1/user/coupons`
- `GET /api/v1/user/coupons/available`
- `POST /api/v1/user/coupons/claim`
- `GET /api/v1/user/invoices`
- `POST /api/v1/user/invoices/create`
- `POST /api/v1/user/invoices/apply`
- `GET /api/v1/user/notices`
- `GET /api/v1/user/notices/unread-count`
- `POST /api/v1/user/notices`（标记已读/未读）
- `DELETE /api/v1/user/notices`（删除通知）
- `GET /api/v1/user/orders/guest-history`
- `GET /api/v1/user/orders/available-coupons`
- `POST /api/v1/user/ai/chat`
- `POST /api/v1/user/ai/chat/stream` — AI 客服流式（SSE）
- `GET /api/v1/user/ai/sessions` — AI 会话列表 \[规划中\]
- `GET /api/v1/user/ai/sessions/{id}/messages` — 会话消息 \[规划中\]
- `POST /api/v1/user/ai/sessions/delete` — 删除会话 \[规划中\]
- `GET /api/v1/user/ai/recommendations` — AI 智能推荐 \[规划中\]
- `POST /api/v1/user/ai/hotel-compare` — AI 酒店对比 \[规划中\]
- `GET /api/v1/user/browsing-history` — 浏览历史 \[规划中\]
- `POST /api/v1/user/browsing-history/add` — 记录浏览 \[规划中\]
- `POST /api/v1/user/browsing-history/clear` — 清空浏览历史 \[规划中\]

### 19.3 管理端

- `GET /api/v1/admin/dashboard/overview`
- `GET /api/v1/admin/dashboard/charts`
- `GET /api/v1/admin/hotels`
- `POST /api/v1/admin/hotels/create`
- `POST /api/v1/admin/hotels/update`
- `POST /api/v1/admin/hotels/delete`
- `POST /api/v1/admin/hotels/batch-status` — 酒店批量上下架 \[规划中\]
- `GET /api/v1/admin/room-types`
- `POST /api/v1/admin/room-types/create`
- `POST /api/v1/admin/room-types/update`
- `POST /api/v1/admin/room-types/delete`
- `GET /api/v1/admin/rooms` — 房间列表 \[规划中\]
- `POST /api/v1/admin/rooms/create` — 新增房间 \[规划中\]
- `POST /api/v1/admin/rooms/update` — 更新房间 \[规划中\]
- `POST /api/v1/admin/rooms/delete` — 删除房间 \[规划中\]
- `GET /api/v1/admin/rooms/status-board` — 房态总览看板 \[规划中\]
- `GET /api/v1/admin/inventory/calendar`
- `POST /api/v1/admin/inventory/update`
- `POST /api/v1/admin/inventory/batch-update` — 库存批量设置 \[规划中\]
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/detail`
- `GET /api/v1/admin/orders/{order_id}/timeline` — 订单操作时间线 \[规划中\]
- `POST /api/v1/admin/orders/change-status`
- `POST /api/v1/admin/orders/check-in`
- `POST /api/v1/admin/orders/check-out`
- `POST /api/v1/admin/orders/extend-stay` — 续住 \[规划中\]
- `POST /api/v1/admin/orders/change-room` — 换房 \[规划中\]
- `POST /api/v1/admin/orders/batch` — 订单批量操作 \[规划中\]
- `GET /api/v1/admin/check-in-records` — 入住记录 \[规划中\]
- `GET /api/v1/admin/check-out-records` — 退房记录 \[规划中\]
- `GET /api/v1/admin/refunds` — 退款单列表 \[规划中\]
- `POST /api/v1/admin/refunds/process` — 退款审批 \[规划中\]
- `POST /api/v1/admin/deposits/create` — 收取押金 \[规划中\]
- `POST /api/v1/admin/deposits/release` — 退还押金 \[规划中\]
- `POST /api/v1/admin/deposits/deduct` — 扣除押金 \[规划中\]
- `GET /api/v1/admin/deposits` — 押金记录 \[规划中\]
- `GET /api/v1/admin/bills` — 账单列表 \[规划中\]
- `POST /api/v1/admin/bills/generate` — 生成退房账单 \[规划中\]
- `GET /api/v1/admin/reviews`
- `POST /api/v1/admin/reviews/reply`
- `POST /api/v1/admin/reviews/delete` \[系统管理员\]
- `POST /api/v1/admin/reviews/batch-reply` — 评价批量 AI 回复 \[规划中\]
- `GET /api/v1/admin/reports/tasks`
- `POST /api/v1/admin/reports/tasks/create`
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users/change-status`
- `GET /api/v1/admin/customers/{user_id}` — 客户档案详情 \[规划中\]
- `GET /api/v1/admin/customers/{user_id}/orders` — 客户历史订单 \[规划中\]
- `GET /api/v1/admin/customers/{user_id}/reviews` — 客户评价记录 \[规划中\]
- `GET /api/v1/admin/customers/{user_id}/ai-portrait` — 客户 AI 画像 \[规划中\]
- `POST /api/v1/admin/customers/{user_id}/ai-portrait/refresh` — 刷新客户 AI 画像 \[规划中\]
- `GET /api/v1/admin/employees`
- `POST /api/v1/admin/employees/create`
- `GET /api/v1/admin/settings`
- `POST /api/v1/admin/settings/update`
- `GET /api/v1/admin/notices` — 管理端通知列表 \[规划中\]
- `GET /api/v1/admin/notices/unread-count` — 管理端未读通知数 \[规划中\]
- `POST /api/v1/admin/notices/read` — 管理端通知标记已读 \[规划中\]
- `GET /api/v1/admin/activities` — 活动列表 \[规划中\]
- `POST /api/v1/admin/activities/create` — 创建活动 \[规划中\]
- `POST /api/v1/admin/activities/update` — 更新活动 \[规划中\]
- `POST /api/v1/admin/activities/delete` — 删除活动 \[规划中\]
- `POST /api/v1/admin/exports/create` — 创建导出任务 \[规划中\]
- `GET /api/v1/admin/exports` — 导出任务列表 \[规划中\]
- `GET /api/v1/admin/exports/{task_id}/download` — 下载导出文件 \[规划中\]
- `GET /api/v1/admin/audit-logs` — 审计日志 \[规划中\]
- `GET /api/v1/admin/roles` — 角色列表 \[规划中\]
- `POST /api/v1/admin/roles/save` — 创建/更新角色 \[规划中\]
- `GET /api/v1/admin/permissions` — 权限枚举列表 \[规划中\]

### 19.4 管理端 AI

- `POST /api/v1/admin/ai/report-summary`
- `POST /api/v1/admin/ai/review-summary`
- `POST /api/v1/admin/ai/reply-suggestion`
- `GET /api/v1/admin/ai/settings`
- `POST /api/v1/admin/ai/settings/update`
- `POST /api/v1/admin/ai/provider/add` — 新增/编辑 AI 供应商
- `POST /api/v1/admin/ai/provider/switch` — 切换活跃供应商
- `POST /api/v1/admin/ai/provider/delete` — 删除供应商
- `POST /api/v1/admin/ai/pricing-suggestion` — AI 智能定价建议 \[规划中\]
- `POST /api/v1/admin/ai/business-report` — AI 经营分析深度报告 \[规划中\]
- `POST /api/v1/admin/ai/business-report/stream` — AI 经营分析报告流式 \[规划中\]
- `POST /api/v1/admin/ai/review-sentiment` — AI 评价情感分析 \[规划中\]
- `POST /api/v1/admin/ai/review-sentiment/batch` — AI 评价情感批量分析 \[规划中\]
- `GET /api/v1/admin/ai/review-sentiment/overview` — AI 评价情感统计概览 \[规划中\]
- `POST /api/v1/admin/ai/marketing-copy` — AI 营销文案生成 \[规划中\]
- `POST /api/v1/admin/ai/content-generate` — AI 酒店/房型内容生成 \[规划中\]
- `GET /api/v1/admin/ai/anomaly-report` — AI 异常检测报告 \[规划中\]
- `GET /api/v1/admin/ai/order-anomaly-summary` — AI 订单异常摘要 \[规划中\]
- `GET /api/v1/admin/ai/call-logs` — AI 调用日志列表 \[规划中\]
- `GET /api/v1/admin/ai/usage-stats` — AI 用量统计概览 \[规划中\]
- `GET /api/v1/admin/ai/quota` — AI 配额查询 \[规划中\]
- `POST /api/v1/admin/ai/quota/update` — AI 配额更新 \[规划中\]

### 19.5 已有管理端（其他）

- `GET /api/v1/admin/members/overview` — 会员等级概览
- `GET /api/v1/admin/coupons` — 优惠券模板列表
- `POST /api/v1/admin/coupons/create` — 创建优惠券模板
- `POST /api/v1/admin/coupons/update` — 更新优惠券模板状态
- `POST /api/v1/admin/system/reset` — 系统重置（仅 system_admin）

## 20. 与论文和文档体系的关系

- 本文档已覆盖论文批注中提到的“典型接口请求/响应示例”要求
- 本文档是接口层主文档，字段、枚举、请求方式变更时优先维护这里
- 若接口新增 AI 能力，应同步更新 `docs/ai-integration.md`
- 若接口范围超出论文主线，应同步更新 [docs/thesis-alignment.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\thesis-alignment.md)

## 21. 文档维护要求

- 新增接口时同步更新本文件
- 新增字段时同步更新参数表与示例
- 新增枚举时同步更新枚举表
- 新增 WebSocket 能力时，必须先在代码中落地后再补充本文档
- 新增 AI 接口时同步更新 `docs/ai-integration.md`
- 若接口范围与论文主线有关，同步更新 [docs/thesis-alignment.md](D:\Nakamoto\Documents\Codes\Python\HoteLink\docs\thesis-alignment.md)
- 规划中接口实现后，应去除 `[规划中]` 标注并补充完整请求/响应示例
