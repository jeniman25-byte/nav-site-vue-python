# Nav Site Vue + Python

一个从零搭建的导航网站项目：

- `frontend`: Vue 3 + Vite
- `backend`: FastAPI + SQLite + SQLAlchemy
- 鉴权：账号密码 + JWT access token
- 未登录可查看公共导航，登录后可查看更多私有导航

## 默认管理员账号

仅用于本地初始化演示，生产环境务必修改：

- Username: `admin`
- Password: `ChangeMe123!`

## 目录结构

```text
.
├── backend
│   ├── app
│   ├── .env.example
│   └── requirements.txt
├── frontend
│   ├── src
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## 本地启动

### 1. 启动后端

```bash
cd backend
cp .env.example .env
/home/cap/.pyenv/shims/python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端默认地址：`http://127.0.0.1:8000`

可选：手动执行一次初始化脚本（通常不需要，因为服务启动时会自动建表和播种）：

```bash
cd backend
source .venv/bin/activate
/home/cap/.pyenv/shims/python -m app.seed
```

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://127.0.0.1:5173`

## 核心接口

- `POST /api/auth/login`：登录，返回 access token
- `GET /api/nav/public`：公共导航
- `GET /api/nav/private`：私有导航，需要 Bearer token
- `GET /api/auth/me`：当前登录用户信息

## 环境变量

`backend/.env.example` 中至少包含：

- `SECRET_KEY`
- `TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `DEFAULT_ADMIN_USERNAME`
- `DEFAULT_ADMIN_PASSWORD`

## 说明

- 密码使用 `passlib` 哈希存储，不会明文落库。
- SQLite 数据库文件默认为 `backend/nav_site.db`。
- 首次启动会自动建表并播种默认管理员与示例导航数据。
