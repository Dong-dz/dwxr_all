# 抖音小程序登录后端使用说明

## 1. 环境配置

### 1.1 依赖安装

```bash
pip install -r requirements.txt
```

### 1.2 环境变量配置

创建 `.env` 文件并配置以下变量：

```env
# 应用配置
DEBUG=False
APP_NAME=抖音小程序登录后端
APP_VERSION=1.0.0

# MySQL配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=douyin_miniapp

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 抖音小程序配置
DOUYIN_APP_ID=your_douyin_app_id
DOUYIN_APP_SECRET=your_douyin_app_secret
DOUYIN_AUTH_URL=https://developer.toutiao.com/api/apps/v2/jscode2session

# JWT配置
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# 会话配置
SESSION_EXPIRE_SECONDS=7200
USER_ACTIVE_EXPIRE_SECONDS=1800

# 安全配置
LOGIN_RATE_LIMIT=10
RATE_LIMIT_WINDOW=3600
```

## 2. 数据库初始化

### 2.1 完整初始化（推荐）

```bash
python scripts/init_database.py --init-all
```

### 2.2 分步初始化

```bash
# 创建数据库
python scripts/init_database.py --create-db

# 创建表结构
python scripts/init_database.py --create-tables

# 创建管理员用户
python scripts/init_database.py --create-admin

# 创建测试用户
python scripts/init_database.py --create-test-users

# 查看数据库信息
python scripts/init_database.py --show-info
```

### 2.3 重置数据库（危险操作）

```bash
# 删除所有表
python scripts/init_database.py --drop-tables
```

## 3. 启动服务

### 3.1 开发环境

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3.2 生产环境

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 4. API接口说明

### 4.1 抖音小程序登录

**请求：**
```http
POST /users/apps/login
Content-Type: application/json

{
  \"code\": \"小程序调用tt.login()获取的code\"
}
```

**响应：**
```json
{
  \"errCode\": 0,
  \"errMsg\": \"success\",
  \"token\": \"jwt_token_string\",
  \"openid\": \"mas***xyz\",
  \"unionid\": \"abc***def\"
}
```

### 4.2 获取用户资料

**请求：**
```http
GET /users/profile
Authorization: Bearer {token}
```

**响应：**
```json
{
  \"openid\": \"user_openid\",
  \"name\": \"用户昵称\",
  \"type\": \"normal\",
  \"quanxian\": \"user\",
  \"dengji\": \"1\",
  \"uuid\": \"user_uuid\"
}
```

### 4.3 更新用户资料

**请求：**
```http
PUT /users/profile
Authorization: Bearer {token}
Content-Type: application/json

{
  \"name\": \"新昵称\",
  \"phone\": \"手机号码\"
}
```

### 4.4 用户登出

**请求：**
```http
POST /users/logout
Authorization: Bearer {token}
```

**响应：**
```json
{
  \"errCode\": 0,
  \"errMsg\": \"success\"
}
```

### 4.5 刷新令牌

**请求：**
```http
POST /users/refresh-token
Authorization: Bearer {token}
```

**响应：**
```json
{
  \"token\": \"new_jwt_token_string\",
  \"expires_in\": 7200
}
```

## 5. 管理员接口

### 5.1 获取用户列表

```http
GET /users/?skip=0&limit=10&status=1&user_type=normal
Authorization: Bearer {admin_token}
```

### 5.2 搜索用户

```http
GET /users/search?keyword=关键词&skip=0&limit=10
Authorization: Bearer {admin_token}
```

### 5.3 删除用户

```http
DELETE /users/{openid}
Authorization: Bearer {admin_token}
```

## 6. 系统接口

### 6.1 健康检查

```http
GET /health
```

### 6.2 API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 7. 开发说明

### 7.1 项目结构

```
dyxr/
├── middleware/          # 中间件
│   ├── __init__.py
│   └── auth.py         # 认证中间件
├── models/             # 数据模型
│   ├── userModel.py    # 用户模型
│   └── ...
├── routes/             # 路由
│   ├── douyin_route.py # 抖音登录路由
│   └── ...
├── schemas/            # 数据验证
│   ├── userSche.py     # 用户schemas
│   └── ...
├── services/           # 业务服务
│   ├── douyin_login_service.py  # 抖音登录服务
│   ├── session_service.py       # 会话管理服务
│   ├── user_service.py          # 用户管理服务
│   └── ...
├── scripts/            # 脚本
│   └── init_database.py # 数据库初始化脚本
├── utils/              # 工具
│   ├── jwt_utils.py    # JWT工具
│   └── ...
├── config.py           # 配置文件
├── database.py         # 数据库连接
├── main.py             # 主应用
└── requirements.txt    # 依赖包
```

### 7.2 数据库设计

#### 用户表 (users)
- openid: 用户OpenID（主键）
- unionid: 用户UnionID
- name: 用户昵称
- type: 用户类型（normal, vip, admin）
- quanxian: 用户权限（user, admin）
- dengji: 用户等级
- uuid: UUID标识
- avatar_url: 头像URL
- phone: 手机号
- created_at: 创建时间
- updated_at: 更新时间
- last_login_at: 最后登录时间
- status: 用户状态（1-正常，0-禁用）

#### 登录日志表 (login_logs)
- id: 自增主键
- openid: 用户OpenID
- login_time: 登录时间
- ip_address: 登录IP
- user_agent: 用户代理
- login_result: 登录结果（1-成功，0-失败）
- error_message: 错误信息

### 7.3 Redis缓存设计

- `session:{token}`: 用户会话数据（Hash）
- `user:active:{openid}`: 用户活跃状态（String）
- `rate_limit:{ip}`: 请求频率限制（String）

## 8. 注意事项

1. **安全配置**：生产环境务必修改JWT密钥和数据库密码
2. **抖音配置**：需要在抖音开发者平台申请小程序并获取AppID和AppSecret
3. **数据库权限**：确保MySQL用户有创建数据库的权限
4. **Redis服务**：确保Redis服务正常运行
5. **日志监控**：生产环境建议配置日志收集和监控系统

## 9. 故障排除

### 9.1 常见问题

1. **数据库连接失败**：检查MySQL服务状态和配置信息
2. **Redis连接失败**：检查Redis服务状态和配置信息
3. **抖音API调用失败**：检查AppID、AppSecret和网络连接
4. **JWT验证失败**：检查密钥配置和令牌格式

### 9.2 日志查看

服务运行时会输出详细的日志信息，包括：
- 请求开始和完成时间
- 数据库操作日志
- 错误信息和堆栈跟踪
- 用户登录/登出记录