# SkyEye 后端

无人机智能监管平台 Django 服务，集成 DeepSeek 大模型 AI 智能助手。

## AI 助手 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `chat_completions` | POST (SSE) | 流式对话，支持工具调用 |
| `geocode` | GET | 高德地理编码 |
| `district` | GET | 行政区划边界 |

### 三种模式

| 模式 | 功能 |
|------|------|
| 聊天模式 | 自由对话，通用问答 |
| 数据查询模式 | 检索系统线索、图斑、批次等数据 |
| 智能摘要模式 | 当前页面数据分析 |

### 工具列表

| 工具 | 功能 |
|------|------|
| `navigate_page` | 跳转系统页面（18 条路由映射，含 AI 设置页） |
| `map_action` | 地图定位 + 区域边界绘制 |
| `query_data` | 查询系统数据（数量/状态/统计/列表/明细） |
| `lookup_task` | 按任务编号查询并跳转 |

### 行政区划缓存

预加载江苏省 13 市 95 区县多边形边界至 `district_cache.json`，内存缓存常驻，零磁盘 IO。
管理命令：`python manage.py preload_districts`

## 安装教程

```
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

## 配置

编辑 `config.ini`：

```ini
[deepseek]
api_key = your_deepseek_key
api_url = https://api.deepseek.com/v1
model = deepseek-chat

[amap]
api_key = your_amap_key
```

## Celery 启动

```bash
celery -A gtus.celery_config worker -l info -c 1
```
