# Django Channels 通知系统

这是一个基于Django和Django Channels实现的实时通知系统，支持运营组向财务组发送通知并获取确认状态。

## 项目功能

- 基于WebSocket的实时通知推送
- 组间通知（运营组→财务组）
- 通知确认机制
- 通知历史记录查询
- 完整的RESTful API

## 项目结构

```
channel_notify/
├── channel_notify/            # 项目配置目录
│   ├── __init__.py
│   ├── asgi.py                # ASGI配置（支持WebSocket）
│   ├── settings.py            # Django设置
│   ├── urls.py                # 项目URL配置
│   └── wsgi.py                # WSGI配置
├── channel_notify/notifications/  # 通知应用
│   ├── __init__.py
│   ├── admin.py               # 后台管理配置
│   ├── apps.py                # 应用配置
│   ├── consumers.py           # WebSocket消费者
│   ├── migrations/            # 数据库迁移
│   ├── models.py              # 数据模型
│   ├── routing.py             # WebSocket路由
│   ├── templates/             # 模板文件
│   ├── tests.py               # 测试代码
│   ├── urls.py                # API路由
│   └── views.py               # API视图
├── db.sqlite3                 # SQLite数据库文件
├── manage.py                  # Django管理脚本
└── venv/                      # Python虚拟环境
```

## 技术栈

- Python 3.11+
- Django 5.0+
- Django Channels 4.0+
- SQLite3（开发环境）
- WebSocket（实时通信）

## 安装与配置

### 1. 克隆项目

```bash
git clone <repository_url>
cd channel_notify
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

如果没有requirements.txt文件，请手动安装：

```bash
pip install django channels
```

### 4. 数据库配置

项目默认使用SQLite数据库，配置在`settings.py`中：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 5. 运行数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate
```

### 6. 创建超级用户（可选）

```bash
python manage.py createsuperuser
```

## 运行项目

### 启动Django开发服务器

```bash
python manage.py runserver
```

服务器默认运行在 `http://127.0.0.1:8000/`

## API文档

### 1. 创建通知

**URL**: `/api/notifications/`
**Method**: `POST`
**认证**: 需要登录
**权限**: 需要属于发送组（运营组）

**请求体**:
```json
{
    "content": "测试通知内容",
    "receiver_group": "finance"
}
```

**响应**:
```json
{
    "id": 1,
    "content": "测试通知内容",
    "sender": "username",
    "sender_group": "hr",
    "receiver_group": "finance",
    "status": "pending",
    "created_at": "2024-01-01T12:00:00Z"
}
```

### 2. 获取通知列表

**URL**: `/api/notifications/`
**Method**: `GET`
**认证**: 需要登录
**权限**: 只能获取自己组的通知

**查询参数**:
- `status`: 筛选状态（pending/confirmed）
- `sender_group`: 筛选发送组

**响应**:
```json
[
    {
        "id": 1,
        "content": "测试通知内容",
        "sender": "username",
        "sender_group": "hr",
        "receiver_group": "finance",
        "status": "pending",
        "created_at": "2024-01-01T12:00:00Z"
    }
]
```

### 3. 确认通知

**URL**: `/api/notifications/<id>/confirm/`
**Method**: `POST`
**认证**: 需要登录
**权限**: 只能确认自己组收到的通知

**响应**:
```json
{
    "id": 1,
    "content": "测试通知内容",
    "sender": "username",
    "sender_group": "hr",
    "receiver_group": "finance",
    "status": "confirmed",
    "confirmed_by": "current_user",
    "confirmed_at": "2024-01-01T13:00:00Z",
    "created_at": "2024-01-01T12:00:00Z"
}
```

## WebSocket使用

### 连接WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/finance/');

ws.onopen = function() {
    console.log('WebSocket连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onclose = function() {
    console.log('WebSocket连接已关闭');
};
```

### 发送通知

```javascript
ws.send(JSON.stringify({
    'type': 'send_notification',
    'content': '测试WebSocket通知',
    'receiver_group': 'finance'
}));
```

### 确认通知

```javascript
ws.send(JSON.stringify({
    'type': 'confirm_notification',
    'notification_id': 1
}));
```

## 测试

运行测试：

```bash
python manage.py test channel_notify.notifications
```

## 注意事项

1. WebSocket连接需要用户认证，请确保在连接前完成登录
2. 用户只能访问和操作自己所在组的通知
3. 财务组用户可以确认收到的通知
4. 运营组用户可以发送通知给财务组

## 扩展建议

1. 添加通知已读状态
2. 实现通知推送历史记录
3. 添加通知优先级
4. 集成消息提醒（如浏览器通知）
5. 实现批量操作功能