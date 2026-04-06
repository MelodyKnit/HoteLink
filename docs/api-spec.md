# HoteLink API 接口设计文档

## 1. 文档目标

本文件用于统一 HoteLink 酒店预订与管理平台的接口设计规则，服务于以下场景：

- 前后端联调
- 后端接口开发
- 数据库与业务建模
- 测试用例编写
- WebSocket 实时消息设计
- 毕业论文中的接口设计说明

本接口文档遵循以下原则：

- 以论文主线功能为核心
- 采用统一的请求头、参数格式、返回格式
- 优先使用 `GET`、`POST`、`WS`
- 描述尽量通俗易懂，方便前端、后端、测试共同理解
- 枚举值统一管理，避免前后端口径不一致
- 当前先做接口设计，不要求所有接口都已完成开发

## 2. 接口总览

### 2.1 请求方式

本项目主要使用三种方式：

- `GET`：查询、获取详情、获取列表、获取统计
- `POST`：新增、修改、删除、状态流转、登录、提交表单、动作型操作
- `WS`：实时通知、后台提醒、订单状态变化、系统消息

说明：

- 为保持论文和工程文档表述一致，更新和删除行为优先使用动作型 `POST`
- 当前不强制使用 `PUT`、`PATCH`、`DELETE`

### 2.2 接口分组

- 公共接口：`/api/v1/public/`
- 通用基础接口：`/api/v1/common/`
- 用户端接口：`/api/v1/user/`
- 管理端接口：`/api/v1/admin/`
- WebSocket：`/ws/`

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

### 9.1 上传文件

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

### 9.2 城市列表

**接口**

`GET /api/v1/common/cities`

**说明**

- 用于前端酒店筛选、地址表单、管理端酒店编辑

### 9.3 字典数据

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

### 12.9 用户订单详情

`GET /api/v1/user/orders/detail`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `order_id` | int | 是 | 订单 ID |

### 12.10 创建订单

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

### 12.20 我的消息通知

`GET /api/v1/user/notices`

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
| `page` | int | 否 | 页码 |
| `page_size` | int | 否 | 每页数量 |

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

### 13.20 报表任务列表

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

## 15. WebSocket 设计

### 15.1 连接地址

- 用户端：`WS /ws/user/notifications`
- 管理端：`WS /ws/admin/notifications`

### 15.2 连接认证

建议使用以下任一方式：

```http
Authorization: Bearer <access_token>
```

或：

```text
/ws/admin/notifications?token=<access_token>
```

### 15.3 WS 统一消息结构

```json
{
  "event": "order_status_changed",
  "data": {},
  "timestamp": "2026-04-04 12:00:00"
}
```

字段说明：

| 字段 | 类型 | 说明 |
|---|---|---|
| `event` | string | 事件名称 |
| `data` | object | 事件数据 |
| `timestamp` | string | 推送时间 |

### 15.4 用户端 WS 事件

| 事件 | 含义 |
|---|---|
| `order_status_changed` | 订单状态变化 |
| `payment_status_changed` | 支付状态变化 |
| `coupon_received` | 收到优惠券 |
| `system_notice` | 系统通知 |

**消息示例**

```json
{
  "event": "order_status_changed",
  "data": {
    "order_id": 3001,
    "old_status": "pending_payment",
    "new_status": "paid"
  },
  "timestamp": "2026-04-04 12:00:00"
}
```

### 15.5 管理端 WS 事件

| 事件 | 含义 |
|---|---|
| `new_order` | 新订单提醒 |
| `room_status_changed` | 房态变化 |
| `report_task_finished` | 报表任务完成 |
| `review_created` | 新评价提醒 |
| `system_notice` | 系统通知 |

### 15.6 心跳消息

客户端可每隔 30 秒发送一次：

```json
{
  "event": "ping"
}
```

服务端返回：

```json
{
  "event": "pong",
  "timestamp": "2026-04-04 12:00:00"
}
```

## 16. 典型接口完整示例

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

## 17. 模块接口清单速查

### 17.1 公共与认证

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
- `POST /api/v1/common/upload`
- `GET /api/v1/common/cities`
- `GET /api/v1/common/dicts`

### 17.2 用户端

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
- `POST /api/v1/user/reviews/create`
- `GET /api/v1/user/points/logs`
- `GET /api/v1/user/coupons`
- `GET /api/v1/user/invoices`
- `POST /api/v1/user/invoices/create`
- `POST /api/v1/user/invoices/apply`
- `GET /api/v1/user/notices`
- `POST /api/v1/user/ai/chat`

### 17.3 管理端

- `GET /api/v1/admin/dashboard/overview`
- `GET /api/v1/admin/dashboard/charts`
- `GET /api/v1/admin/hotels`
- `POST /api/v1/admin/hotels/create`
- `POST /api/v1/admin/hotels/update`
- `POST /api/v1/admin/hotels/delete`
- `GET /api/v1/admin/room-types`
- `POST /api/v1/admin/room-types/create`
- `POST /api/v1/admin/room-types/update`
- `POST /api/v1/admin/room-types/delete`
- `GET /api/v1/admin/inventory/calendar`
- `POST /api/v1/admin/inventory/update`
- `GET /api/v1/admin/orders`
- `GET /api/v1/admin/orders/detail`
- `POST /api/v1/admin/orders/change-status`
- `POST /api/v1/admin/orders/check-in`
- `POST /api/v1/admin/orders/check-out`
- `GET /api/v1/admin/reviews`
- `POST /api/v1/admin/reviews/reply`
- `GET /api/v1/admin/reports/tasks`
- `POST /api/v1/admin/reports/tasks/create`
- `GET /api/v1/admin/users`
- `POST /api/v1/admin/users/change-status`
- `GET /api/v1/admin/employees`
- `POST /api/v1/admin/employees/create`
- `GET /api/v1/admin/settings`
- `POST /api/v1/admin/settings/update`
- `POST /api/v1/admin/ai/report-summary`
- `POST /api/v1/admin/ai/review-summary`
- `POST /api/v1/admin/ai/reply-suggestion`
- `GET /api/v1/admin/ai/settings`
- `POST /api/v1/admin/ai/settings/update`

## 18. 与论文和文档体系的关系

- 本文档已覆盖论文批注中提到的“典型接口请求/响应示例”要求
- 本文档是接口层主文档，字段、枚举、请求方式变更时优先维护这里
- 若接口新增 AI 能力，应同步更新 `docs/ai-integration.md`
- 若接口范围超出论文主线，应同步更新 `docs/thesis-alignment.md`

## 19. 文档维护要求

- 新增接口时同步更新本文件
- 新增字段时同步更新参数表与示例
- 新增枚举时同步更新枚举表
- 新增 WS 事件时同步更新 WS 章节
- 新增 AI 接口时同步更新 `docs/ai-integration.md`
- 若接口范围与论文主线有关，同步更新 `docs/thesis-alignment.md`
