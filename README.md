# 自习座位预约系统

## 项目简介
本系统面向高等学校自习室管理场景，为学生提供座位查询、预约、签到、历史记录等功能，帮助管理员动态调整自习室资源、监控利用率并处理违约。系统支持基于角色的访问控制（RBAC），分离学生端与管理端，提升管理效率与使用体验。

---

## 技术栈
| 层级 | 技术 |
|------|------|
| 后端框架 | Python Flask 3.x |
| ORM | Flask-SQLAlchemy |
| 数据库 | SQLite（存放于 `databases/studyroom.db`） |
| 认证 | Flask-JWT-Extended（JWT Token） |
| 跨域 | Flask-CORS |
| 定时任务 | Flask-APScheduler（提醒推送、违约检测、签到码生成） |
| 前端框架 | Vue 3（Composition API + `<script setup>`） |
| 路由 | Vue Router 4 |
| 状态管理 | Pinia |
| HTTP 客户端 | Axios（拦截器封装） |
| UI 组件库 | Element Plus |
| 构建工具 | Vite 5 |

---

## 快速开始

### 1. 后端启动
```bash
cd backend
pip install -r requirements.txt
python run.py
# 服务运行在 http://127.0.0.1:5000
```

### 2. 前端启动
```bash
cd front
npm install
npm run dev
# 服务运行在 http://localhost:3000
# Vite 自动代理 /api 请求到后端 5000 端口
```

### 3. 预设管理员
| 用户名 | 密码 | 角色 |
|--------|------|------|
| `admin` | `admin123` | 超级管理员 |

首次启动后端会自动创建数据库表、预置角色权限和系统配置项。

---

## 项目结构
```
project/
├── backend/                      # Python Flask 后端
│   ├── run.py                    # 启动入口
│   ├── requirements.txt          # Python 依赖
│   └── app/
│       ├── __init__.py           # 应用工厂、蓝图注册、数据初始化
│       ├── config.py             # 配置文件
│       ├── models/               # 数据模型（10 张表）
│       ├── routes/               # 路由模块（12 个文件）
│       └── utils/                # 工具函数
│           ├── decorators.py     # 权限装饰器
│           ├── init_data.py      # 初始化数据
│           └── scheduled_tasks.py# 定时任务
├── front/                        # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js               # 入口
│       ├── App.vue
│       ├── api/                  # API 封装
│       ├── router/               # 路由 + 导航守卫
│       ├── stores/               # Pinia 状态管理
│       └── views/                # 页面组件
│           ├── Login.vue
│           ├── Register.vue
│           ├── student/          # 学生端（7 个页面）
│           └── admin/            # 管理端（8 个页面）
├── databases/
│   └── studyroom.db              # SQLite 数据库
├── README.md
└── 修改日志.md
```

---

## RBAC 权限体系

### 预置角色
| 角色 | 说明 | 可删除/修改 |
|------|------|-------------|
| 学生 | 注册时自动分配 | 否（系统预置） |
| 管理员 | 管理自习室、座位、用户、预约 | 否（系统预置） |
| 超级管理员 | 全部权限 + 角色/权限管理 | 否（系统预置） |

### 权限码列表（共 12 项）
| 权限码 | 说明 |
|--------|------|
| `reservation:view` | 查看预约记录 |
| `reservation:create` | 创建预约 |
| `reservation:cancel` | 取消预约 |
| `reservation:checkin` | 签到 |
| `reservation:manage` | 管理所有预约 |
| `room:manage` | 管理自习室 |
| `seat:manage` | 管理座位 |
| `user:manage` | 管理用户和角色分配 |
| `role:manage` | 管理角色和权限 |
| `violation:view` | 查看违约记录 |
| `system:config` | 修改系统配置 |
| `statistics:view` | 查看统计概览 |

### 权限保护规则
- **超级管理员角色**：不允许删除、修改角色名或修改其权限配置
- **超级管理员用户**：不允许删除、修改其角色分配
- **管理员用户**：不允许删除
- **系统预置角色**：不允许删除或修改名称

---

## 数据库设计
所有表名统一使用下划线复数命名，遵循第三范式。

### 1. 用户表 `users`
| 字段 | 类型 | 备注 |
|------|------|------|
| user_id | int (PK) | 主键，自增 |
| username | varchar(50) | 学号/工号，唯一，非空 |
| password_hash | varchar(255) | 加密密码，非空 |
| email | varchar(100) | 邮箱 |
| credit_score | int | 信誉分，默认100，违约扣分 |
| created_at | datetime | 注册时间 |
| is_del | int | 软删除标记 0-否，1-是 |

### 2. 角色表 `roles`
| 字段 | 类型 | 备注 |
|------|------|------|
| role_id | int (PK) | 主键，自增 |
| role_name | varchar(50) | 角色名称，唯一 |
| description | varchar(200) | 角色描述 |
| is_system | boolean | 是否系统预置角色 |

### 3. 权限表 `permissions`
| 字段 | 类型 | 备注 |
|------|------|------|
| perm_id | int (PK) | 主键，自增 |
| perm_name | varchar(50) | 权限名称 |
| perm_code | varchar(100) | 权限编码，如 `reservation:view` |
| description | varchar(200) | 权限说明 |

### 4. 角色权限关联表 `role_permissions`
| 字段 | 类型 | 备注 |
|------|------|------|
| role_id | int (FK) | 关联 roles |
| perm_id | int (FK) | 关联 permissions |
| 联合主键 (role_id, perm_id) | | |

### 5. 用户角色关联表 `user_roles`
| 字段 | 类型 | 备注 |
|------|------|------|
| user_id | int (FK) | 关联 users |
| role_id | int (FK) | 关联 roles |
| 联合主键 (user_id, role_id) | | |

### 6. 自习室表 `studyrooms`
| 字段 | 类型 | 备注 |
|------|------|------|
| room_id | int (PK) | 主键，自增 |
| room_name | varchar(100) | 自习室名称 |
| location | varchar(200) | 位置描述 |
| open_time | time | 开放时间，默认 07:00 |
| close_time | time | 关闭时间，默认 22:00 |
| is_available | boolean | 是否开放 |
| total_seats | int | 总座位数 |
| description | text | 备注 |
| is_del | int | 软删除 0-否，1-是 |

### 7. 座位表 `seats`
| 字段 | 类型 | 备注 |
|------|------|------|
| seat_id | int (PK) | 主键，自增 |
| room_id | int (FK) | 关联 studyrooms |
| seat_number | int | 座位编号（同自习室内唯一） |
| has_power | boolean | 是否有插座 |
| is_active | boolean | 是否可用 |
| is_del | int | 软删除 0-否，1-是 |

### 8. 预约记录表 `reservations`
| 字段 | 类型 | 备注 |
|------|------|------|
| res_id | int (PK) | 主键，自增 |
| user_id | int (FK) | 关联 users |
| seat_id | int (FK) | 关联 seats |
| start_time | datetime | 预约开始时间（整点） |
| end_time | datetime | 预约结束时间（整点） |
| status | varchar(20) | PENDING/ACTIVE/COMPLETED/CANCELLED/VIOLATED |
| actual_check_in | datetime | 实际签到时间 |
| created_at | datetime | 下单时间 |
| is_del | int | 软删除 0-否，1-是 |

### 9. 违约记录表 `violations`
| 字段 | 类型 | 备注 |
|------|------|------|
| violation_id | int (PK) | 主键，自增 |
| user_id | int (FK) | 关联 users |
| reservation_id | int (FK) | 关联 reservations |
| reason | varchar(100) | 违约原因 |
| penalty | int | 扣除信誉分 |
| created_at | datetime | 发生时间 |

### 10. 系统配置表 `system_configs`
| 字段 | 类型 | 备注 |
|------|------|------|
| config_id | int (PK) | 主键，自增 |
| config_key | varchar(50) | 配置键，唯一 |
| config_value | text | 配置值 |
| description | varchar(200) | 参数说明 |

### 11. 签到码表 `room_checkin_codes`
| 字段 | 类型 | 备注 |
|------|------|------|
| code_id | int (PK) | 主键，自增 |
| room_id | int (FK) | 关联 studyrooms |
| code_date | date | 日期 |
| checkin_code | varchar(10) | 6位随机码 |
| qr_code_url | varchar(255) | 二维码链接（可选） |
| created_at | datetime | 生成时间 |

---

## 后端 API 接口文档

基础路径：`/api/v1`
认证方式：除登录/注册外，需在请求头携带 `Authorization: Bearer <access_token>`
响应格式：`{"code": 200, "message": "success", "data": ...}`

### 一、认证模块（无需管理员权限）

**1. 注册**
- `POST /auth/register`
- 权限：无需登录
- Body：`{"username": "2024001", "password": "123456", "email": "xx@univ.edu.cn"}`
- 说明：自动分配"学生"角色，初始信誉分100

**2. 登录**
- `POST /auth/login`
- 权限：无需登录
- Body：`{"username": "2024001", "password": "123456"}`
- 返回：`{"access_token": "xxx", "token_type": "bearer", "user": {...}}`

**3. 获取当前用户信息**
- `GET /auth/me`
- 权限：需登录
- 返回：用户信息 + roles 对象数组 + permissions 字符串数组

**4. 修改当前用户信息**
- `PUT /auth/me`
- 权限：需登录
- Body：`{"email": "new@qq.com"}`
- 说明：任何登录用户均可修改自己的邮箱

**5. 登出**
- `POST /auth/logout`
- 权限：需登录
- 说明：服务端无状态，客户端丢弃 Token 即可

---

### 二、用户管理（需管理员权限）

**1. 用户列表**
- `GET /users`
- 权限：管理员/超级管理员
- Query：`?page=1&size=10&keyword=`

**2. 用户详情**
- `GET /users/{id}`
- 权限：管理员/超级管理员

**3. 更新用户**
- `PUT /users/{id}`
- 权限：管理员/超级管理员
- Body：`{"email": "new@qq.com", "credit_score": 90}`

**4. 删除用户（软删）**
- `DELETE /users/{id}`
- 权限：管理员/超级管理员
- 限制：不允许删除管理员或超级管理员账号

**5. 分配角色**
- `POST /users/{id}/roles`
- 权限：管理员/超级管理员
- Body：`{"role_ids": [1, 2]}`
- 限制：不允许修改超级管理员用户的角色

---

### 三、角色管理（需管理员/超级管理员权限）

**1. 角色列表**
- `GET /roles`
- 权限：管理员/超级管理员

**2. 创建角色**
- `POST /roles`
- 权限：仅超级管理员
- Body：`{"role_name": "运营", "description": "..."}`

**3. 更新角色**
- `PUT /roles/{id}`
- 权限：仅超级管理员
- 限制：系统预置角色不可修改

**4. 删除角色**
- `DELETE /roles/{id}`
- 权限：仅超级管理员
- 限制：系统预置角色不可删除

**5. 查看角色权限**
- `GET /roles/{id}/permissions`
- 权限：管理员/超级管理员

**6. 设置角色权限**
- `PUT /roles/{id}/permissions`
- 权限：仅超级管理员
- Body：`{"perm_ids": [1, 3, 5]}`
- 限制：不允许修改"超级管理员"角色的权限

---

### 四、权限列表
- `GET /permissions`
- 权限：需登录
- 返回：所有权限项（用于角色配置时选择）

---

### 五、自习室管理

**1. 自习室列表**
- `GET /studyrooms`
- 权限：需登录
- Query：`?available=true&location=教学楼&has_power=true&page=1&size=10`
- 返回：分页列表，含实时 free_seats/occupied_seats/total_seats

**2. 创建自习室**
- `POST /studyrooms`
- 权限：管理员/超级管理员
- Body：`{"room_name": "自习室A", "location": "教学楼1层", "open_time": "07:00", "close_time": "22:00", "description": "安静区域"}`

**3. 自习室详情**
- `GET /studyrooms/{id}`
- 权限：需登录
- 返回：自习室信息 + seats 座位数组（含 is_occupied 标记）

**4. 更新自习室**
- `PUT /studyrooms/{id}`
- 权限：管理员/超级管理员

**5. 删除自习室（软删）**
- `DELETE /studyrooms/{id}`
- 权限：管理员/超级管理员

**6. 可用座位概况**
- `GET /studyrooms/{id}/availability-summary`
- 权限：需登录
- 返回：`{room_id, room_name, total_seats, occupied_seats, free_seats}`

---

### 六、座位管理

**1. 座位列表**
- `GET /studyrooms/{room_id}/seats`
- 权限：需登录
- Query：`?has_power=true&is_active=true`
- 返回：座位数组，含 is_occupied 实时占用标记

**2. 新增座位**
- `POST /studyrooms/{room_id}/seats`
- 权限：管理员/超级管理员
- Body：`{"seat_number": 10, "has_power": false}`
- 限制：同自习室内座位编号必须唯一

**3. 座位详情**
- `GET /seats/{id}`
- 权限：需登录

**4. 更新座位**
- `PUT /seats/{id}`
- 权限：管理员/超级管理员
- 限制：座位编号不允许修改（前端交互层面已禁用，后端校验同室唯一性）

**5. 删除座位（软删）**
- `DELETE /seats/{id}`
- 权限：管理员/超级管理员

---

### 七、预约核心

**1. 查询空闲时段**
- `GET /seats/{seat_id}/availability`
- 权限：需登录
- Query：`?date=2026-05-09`（默认当天）
- 返回：`{"date":"...", "open_time":"07:00", "close_time":"22:00", "slots":[{"start":"07:00","end":"08:00","free":true}, {"start":"08:00","end":"09:00","free":false},...]}`
- 说明：返回全部整点时段，`free=true` 表示空闲，`free=false` 表示已占用
- 限制：日期范围从今天起 MAX_RESERVATION_DAYS 天内（默认7天）

**2. 创建预约**
- `POST /reservations`
- 权限：需登录
- Body：`{"seat_id": 5, "start_time": "2026-05-10 09:00:00", "end_time": "2026-05-10 11:00:00"}`
- 校验：整点时间、时长 ≤ MAX_RESERVATION_HOURS、日期 ≤ MAX_RESERVATION_DAYS、不超开放时间、不冲突、信誉分 > 0

**3. 我的预约**
- `GET /reservations/my`
- 权限：需登录
- Query：`?status=PENDING&page=1&size=10`

**4. 预约详情**
- `GET /reservations/{id}`
- 权限：需登录

**5. 取消预约**
- `PUT /reservations/{id}/cancel`
- 权限：需登录（本人可取消自己的；管理员/超级管理员可取消任意用户的）
- 限制：仅 PENDING 状态可取消

**6. 签到**
- `POST /reservations/{id}/checkin`
- 权限：需登录（仅本人）
- Body：`{"checkin_code": "A1B2C3"}`
- 说明：签到码需与座位所属自习室当日签到码一致，签到后状态变为 ACTIVE

---

### 八、签到码管理

**1. 获取签到码**
- `GET /studyrooms/{room_id}/checkin-code`
- 权限：需登录
- Query：`?date=2026-05-09`（默认当天）
- 说明：不存在则自动生成6位随机码

**2. 刷新签到码**
- `POST /studyrooms/{room_id}/checkin-code/refresh`
- 权限：需登录

---

### 九、管理端预约查询

**1. 全部预约记录**
- `GET /admin/reservations`
- 权限：管理员/超级管理员
- Query：`?user_id=&status=&room_id=&page=1&size=10`
- 返回：含用户名、邮箱、自习室名称等扩展信息

### 十、违约记录

**1. 违约列表**
- `GET /violations`
- 权限：需登录
  - 学生：仅查看自己的违约记录
  - 管理员/超级管理员：查看所有用户的违约记录
- Query：`?user_id=&page=1&size=10`

---

### 十一、系统配置（需管理员权限）

**1. 获取配置**
- `GET /system-configs`
- 权限：管理员/超级管理员
- 预置配置项：

| 配置键 | 默认值 | 说明 |
|--------|--------|------|
| `MAX_RESERVATION_HOURS` | 4 | 最大预约小时数 |
| `MAX_RESERVATION_DAYS` | 7 | 最大可预约天数 |
| `CHECKIN_GRACE_MINUTES` | 15 | 签到宽限分钟数 |
| `VIOLATION_PENALTY` | 10 | 违约扣分 |
| `REMINDER_BEFORE_MINUTES` | 15 | 预约前提醒分钟数 |
| `SECOND_REMINDER_MINUTES` | 10 | 再次提醒（开始后分钟数） |

**2. 更新配置**
- `PUT /system-configs/{key}`
- 权限：管理员/超级管理员
- Body：`{"config_value": 6}`
- 限制：config_value 必须为正整数

---

### 十二、统计概览（需管理员权限）
- `GET /statistics/overview`
- 权限：管理员/超级管理员
- 返回：`{today_reservations, today_violations, room_stats: [{room_id, room_name, total_seats, occupied_seats, occupancy_rate}, ...]}`

### 十三、智能问答
- `POST /ai/ask`
- 权限：需登录
- Body：`{"question": "如何签到？"}`
- 返回：`{"answer": "..."}`
- 匹配关键词：签到、预约、取消、违约、开放时间、座位、注册；未匹配返回通用帮助提示

---

### 十四、定时任务（后端自动执行）
| 任务 | 频率 | 说明 |
|------|------|------|
| 违约检测 | 每分钟 | 检查 PENDING 超时未签到的预约，自动标记 VIOLATED、扣信誉分 |
| 提醒通知 | 每分钟 | 预约前15分钟首次提醒、开始后10分钟再次提醒（当前为终端打印，可扩展邮件） |
| 签到码生成 | 每天 00:00 | 为每个自习室自动生成当日6位签到码 |

---

## 页面功能总览

### 学生端
| 页面 | 路由 | 功能 |
|------|------|------|
| 登录 | `/login` | 学号/工号 + 密码登录 |
| 注册 | `/register` | 注册账号，自动分配学生角色 |
| 首页 | `/student/home` | 自习室列表，按位置/插座搜索，实时空闲数 |
| 自习室详情 | `/student/room/:id` | 自习室信息 + 座位网格（空闲/占用/插座标记） |
| 座位详情 | `/student/seat/:id` | 空闲时间段网格，连续时段多选，发起预约 |
| 个人中心 | `/student/profile` | 信誉分、角色、修改邮箱、当前预约管理 |
| 预约历史 | `/student/history` | 分页列表、状态筛选、签到/取消操作 |
| 预约详情 | `/student/history/:id` | 完整预约信息、取消/再次预约 |

### 管理端
| 页面 | 路由 | 功能 |
|------|------|------|
| 仪表盘 | `/admin/dashboard` | 今日预约/违约统计，各教室占用率 |
| 自习室管理 | `/admin/rooms` | 增删改自习室 |
| 座位管理 | `/admin/seats` | 按自习室管理座位（编辑时编号不可改） |
| 预约记录 | `/admin/reservations` | 多条件检索所有预约，手动取消 |
| 违约记录 | `/admin/violations` | 查看全部违约记录 |
| 用户管理 | `/admin/users` | 用户列表、分配角色 |
| 角色管理 | `/admin/roles` | 创建/编辑角色、设置权限 |
| 参数调整 | `/admin/config` | 修改系统参数（最大预约时长等） |