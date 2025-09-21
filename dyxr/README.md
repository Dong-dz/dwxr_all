···
dyxr/
├── config.py                 # 配置管理
├── database.py               # 数据库连接管理
├── main.py                  # FastAPI主应用文件
├── requirements.txt          # 项目依赖
├── models/
│   ├── user.py              # 用户模型
│   └── biaodian.py          # 标点信息模型
├── schemas/
│   ├── user.py              # 用户数据模式
│   └── biaodian.py          # 标点信息数据模式
├── routes/
│   ├── user.py              # 用户路由
│   └── biaodian.py          # 标点信息路由
└── services/
    ├── mysql_demo.py        # MySQL操作示例
    ├── redis_demo.py        # Redis操作示例
    └── mongo_demo.py        # MongoDB操作示例
···

Models
直接映射数据库表结构
通过 ORM（如 SQLAlchemy）实现数据库操作
定义数据库表的字段、类型、约束等

Schemas
定义 API 接口的数据结构
进行请求数据验证和响应数据序列化
提供 API 文档生成所需的信息
