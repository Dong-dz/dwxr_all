# 抖音小程序功能迁移部署指南

## 概述

本文档描述了如何将dyxr项目的抖音小程序功能迁移到dwxr_backend中，并进行部署配置。

## 功能迁移内容

### 1. 数据模型扩展
- **DouyinUser**: 抖音用户信息管理
- **BiaodianItem**: 标点（钓点）信息管理  
- **DouyinLoginLog**: 登录日志记录

### 2. 核心服务
- **DouyinLoginService**: 抖音小程序登录认证
- **DouyinCRUD**: 数据库操作服务
- **认证中间件**: JWT + Redis 会话管理

### 3. API接口
- `/api/v1/douyin/login` - 抖音小程序登录
- `/api/v1/douyin/profile` - 用户资料管理
- `/api/v1/douyin/logout` - 用户登出
- `/api/v1/biaodian/*` - 标点信息管理

## 部署配置

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# 抖音小程序配置
DOUYIN_APP_ID=your_actual_douyin_app_id
DOUYIN_APP_SECRET=your_actual_douyin_app_secret
DOUYIN_AUTH_URL=https://developer.toutiao.com/api/apps/v2/jscode2session

# JWT配置
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password

# 会话配置
SESSION_EXPIRE_SECONDS=7200
USER_ACTIVE_EXPIRE_SECONDS=1800

# 安全配置
LOGIN_RATE_LIMIT=10
RATE_LIMIT_WINDOW=3600
```

### 2. 数据库迁移

运行数据库迁移来创建新的表结构：

```bash
# 进入后端目录
cd dwxr_backend

# 运行迁移
alembic upgrade head
```

迁移将创建以下表：
- `douyin_users` - 抖音用户表
- `biaodian_items` - 标点信息表
- `douyin_login_logs` - 登录日志表

### 3. Redis 服务

确保Redis服务正在运行：

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server

# CentOS/RHEL
sudo yum install redis
sudo systemctl start redis

# Docker方式
docker run -d --name redis -p 6379:6379 redis:latest
```

### 4. 依赖安装

安装新增的Python依赖：

```bash
pip install redis httpx
```

### 5. 抖音小程序配置

在抖音开发者平台配置：

1. 登录[抖音开放平台](https://developer.open-douyin.com/)
2. 创建小程序应用
3. 获取 `App ID` 和 `App Secret`
4. 配置服务器域名
5. 更新 `.env` 文件中的配置

## 测试验证

### 1. 运行集成测试

```bash
cd dwxr_backend
python integration_test.py
```

### 2. API测试

使用以下curl命令测试API：

```bash
# 测试登录接口
curl -X POST http://localhost:8000/api/v1/douyin/login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_code_from_miniapp"}'

# 测试获取公开标点
curl -X GET http://localhost:8000/api/v1/biaodian/public

# 测试健康检查
curl -X GET http://localhost:8000/health
```

### 3. 前端集成

小程序前端调用示例：

```javascript
// 小程序登录
tt.login({
  success(res) {
    if (res.code) {
      // 发送code到后端
      tt.request({
        url: 'https://your-domain.com/api/v1/douyin/login',
        method: 'POST',
        data: {
          code: res.code
        },
        success(response) {
          // 保存token
          tt.setStorageSync('token', response.data.token);
        }
      });
    }
  }
});

// 创建标点
function createBiaodian(data) {
  const token = tt.getStorageSync('token');
  tt.request({
    url: 'https://your-domain.com/api/v1/biaodian',
    method: 'POST',
    header: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    data: data,
    success(res) {
      console.log('标点创建成功', res.data);
    }
  });
}
```

## 性能优化

### 1. Redis优化

```bash
# Redis配置优化 (redis.conf)
maxmemory 256mb
maxmemory-policy allkeys-lru
timeout 300
tcp-keepalive 60
```

### 2. 数据库索引

已创建的索引：
- `ix_douyin_users_openid` - 用户openid索引
- `ix_douyin_users_unionid` - 用户unionid索引  
- `ix_biaodian_items_openid` - 标点openid索引
- `ix_douyin_login_logs_openid` - 登录日志openid索引

### 3. API限流

已实现基于IP的登录频率限制：
- 每小时最多10次登录尝试
- 超过限制返回429状态码

## 监控和日志

### 1. 日志配置

在 `logging.conf` 中添加：

```ini
[logger_douyin]
level=INFO
handlers=douyin_handler
qualname=app.services.douyin_login_service

[handler_douyin_handler]
class=FileHandler
level=INFO
formatter=generic
args=('logs/douyin.log',)
```

### 2. 监控指标

建议监控以下指标：
- 登录成功率
- API响应时间
- Redis连接状态
- 数据库查询性能
- 标点创建/查询频率

## 安全考虑

### 1. 数据脱敏

所有返回给客户端的敏感数据已进行脱敏处理：
- openid前6位保留，其余用*替代
- unionid前6位保留，其余用*替代

### 2. 权限控制

实现了三级权限：
- `user` - 普通用户
- `admin` - 管理员  
- `superuser` - 超级管理员

### 3. 会话安全

- JWT令牌2小时过期
- Redis会话2小时过期
- 支持主动登出清除会话

## 故障排除

### 1. 常见问题

**Redis连接失败**
```bash
# 检查Redis状态
redis-cli ping

# 检查配置
redis-cli config get "*"
```

**数据库连接问题**
```bash
# 检查数据库连接
python -c "from app.core.db import engine; print(engine.execute('SELECT 1').scalar())"
```

**抖音API调用失败**
- 检查App ID和App Secret配置
- 验证网络连接
- 查看抖音开发者平台限制

### 2. 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看抖音相关日志
tail -f logs/douyin.log

# 查看错误日志
grep ERROR logs/*.log
```

## 后续优化建议

1. **性能监控**: 集成APM工具（如Sentry、New Relic）
2. **缓存策略**: 为频繁查询的标点数据添加缓存
3. **地理搜索**: 集成PostGIS支持更精确的地理位置搜索
4. **图片存储**: 为标点添加图片上传功能
5. **推送通知**: 集成消息推送服务
6. **数据备份**: 建立定期数据备份机制

## 联系支持

如遇到问题，请：
1. 查看日志文件获取详细错误信息
2. 运行集成测试确定问题范围
3. 检查配置文件是否正确
4. 联系开发团队获取支持