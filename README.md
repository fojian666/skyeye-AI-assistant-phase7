# 金陵阡陌（SkyEye）— 低空遥感智能巡检平台

## 项目概述

金陵阡陌（SkyEye）是一个基于低空遥感与无人机技术的智能巡检平台，集成了 **GIS 地图（2D/3D）**、**全景图像分析**、**AI 目标检测**、**航线规划**、**图斑变化检测** 等核心功能。平台通过 **DeepSeek 大模型** 提供 AI 智能助手，支持自然语言驱动地图定位、区域圈定、页面跳转和数据查询。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 2 + Element UI | SPA 应用 |
| 2D 地图 | Leaflet | 开源轻量 GIS |
| 3D 地图 | Cesium | 三维地球引擎 |
| 全景图 | Pannellum | 浏览器全景渲染 |
| 动画库 | GSAP | 弹窗/拖拽动画 |
| 图表 | ECharts | 数据可视化 |
| 后端框架 | Django | Python Web 框架 |
| 大模型 | DeepSeek (LangChain + LangGraph) | AI 对话与工具调用 |
| 流式输出 | SSE (Server-Sent Events) | real-time 阶段反馈 |
| 地理编码 | 高德地图 API | 地名 → 坐标 / 行政区边界 |
| 实时通信 | MQTT + WebSocket | 无人机遥测数据 |
| 数据库 | PostgreSQL | config.ini 配置连接 |

---

## 项目结构

```
skyeye/
├── README.md
├── .gitignore
├── skyeye/                       # Django 后端
│   ├── apps/
│   │   ├── system/               # 系统管理 + AI Chat API
│   │   │   ├── views.py          # ★ chat_completions（SSE 流式）+ geocode + district
│   │   │   ├── urls.py           # API 路由
│   │   │   ├── models.py
│   │   │   └── serialirzers.py
│   │   ├── drone_track/          # 无人机轨迹（MQTT + WebSocket）
│   │   ├── experience/           # 体验模块
│   │   └── interpretation/       # AI 解译分析
│   ├── utils_tools/
│   │   └── district_cache.py     # 行政区划边界缓存（内存 + JSON）
│   ├── district_cache.json       # 江苏省 13 市 95 区县多边形缓存
│   └── config.ini                # API Key 配置（gitignore）
│
└── skyeye-ui/                    # Vue 前端
    ├── src/
    │   ├── components/chat/
    │   │   └── ChatModel.vue     # ★ AI 助手悬浮窗（SSE 流式 + 停止/重试/复制）
    │   ├── views/
    │   │   ├── dataManagement/oneMap/       # 一张图（2D/3D）
    │   │   ├── routePlanning/              # 航线规划
    │   │   ├── panoramicDetection/         # 全景检测
    │   │   ├── intelligentMonitoring/      # 智能监测
    │   │   └── pattern-verifiy/            # 图斑核实
    │   ├── router/index.js
    │   ├── store/                 # Vuex
    │   ├── layout/                # 布局（Header / 侧栏 / 主题切换）
    │   ├── api/                   # 接口封装
    │   └── utils/                 # 工具函数
    └── public/
        ├── config/config.js      # ★ 运行时配置（baseUrl / 全景图 / 地图服务等）
        ├── static/Cesium/        # Cesium 3D 引擎
        └── theme/                # 亮色/暗色主题 CSS
```

---

## AI 智能助手

### 入口

右下角悬浮胶囊按钮（🤖 AI 助手），点击弹性弹出毛玻璃聊天面板。

### 核心链路

```
用户输入 → DeepSeek 大模型 → Tool Call → 后端 SSE 流式返回 → 前端逐阶段展示
```

流式阶段：`🔍 理解问题 → 🗺️ 地理编码 → 📊 查询数据 → 🔎 查找任务 → ✍️ 生成回答`

### 工具列表

| 工具 | 功能 | 触发条件 |
|------|------|------|
| `navigate_page` | 跳转系统页面 | 用户要求打开/前往/进入某个页面 |
| `map_action` | 地图定位 + 区域边界绘制 | 用户提及任何地点/区域/行政区 |
| `query_data` | 查询系统数据（数量/状态/统计） | 用户询问数据量、统计、状态 |
| `lookup_task` | 按任务编号查询并跳转 | 用户提供 batch_id 格式编号 |

### 面板交互

| 特性 | 说明 |
|------|------|
| 流式输出 | SSE 实时显示处理阶段，打字机逐字渲染 Markdown |
| 停止生成 | 红色胶囊按钮，支持中止请求和打字输出 |
| 重试 | 出错/中断后一键重发最后一条消息 |
| 复制回答 | hover 显示复制按钮，点击后"已复制"提示 |
| 保留会话 | 关闭窗口不丢失历史，手动清空通过删除按钮 |
| 拖拽 | FAB / 面板头部均可拖拽，边界碰撞检测 |
| 缩放 | 右下角拖拽把手，宽 320~700px，高 400~85vh |
| 吸附 | 点 → 吸附为全高右栏，← 恢复浮动 |
| 毛玻璃 | `backdrop-filter: blur(24px)` 半透明面板 |
| GSAP 动画 | 打开 `back.out(1.7)` 弹性弹出 |
| 主题适配 | 亮色/暗色自动适配 |

### 地图导航

- 后端调高德 `geocode` API → 地名 → 经纬度 + 完整地址
- 前端 `navigate-map` 事件 → 地图 `flyTo()` 平滑飞行动画
- 自动缩放适配区域边界，确保完整显示

### 区域圈定

- 后端调高德 `config/district` API → polygon 边界坐标
- 输入"南京市"自动获取 11 个区的独立边界，各分配不同颜色
- 前端 `draw-region` 事件：主区域半透明底，子区域彩色填充 + 描边
- 再次触发自动清除上一轮图层

### 行政区划缓存

- 预加载江苏省 13 市 95 区县的多边形边界 → `district_cache.json`
- 模块级内存缓存，首次加载后常驻，后续零磁盘 IO、零 API 调用
- 管理命令：`python manage.py preload_districts`

---

## 运行说明

### 前端

```bash
cd skyeye-ui
npm install
npm run serve        # 开发模式，默认 http://localhost:8088
```

### 后端

```bash
cd skyeye
pip install -r requirements.txt
python manage.py runserver 0.0.0.0:8000
```

### 配置

编辑 `skyeye/config.ini`（已 gitignore）：

```ini
[deepseek]
api_key = your_deepseek_key
api_url = https://api.deepseek.com/v1
model = deepseek-chat

[amap]
api_key = your_amap_key
```

### 运行时配置（前端）

部署时修改 `skyeye-ui/public/config/config.js` 中的 `baseUrl` 等字段即可切换 API 地址，无需重新构建。

---

## 未提交内容（.gitignore 排除清单）

| 类别 | 文件/目录 | 说明 |
|------|----------|------|
| 密钥 | `skyeye/config.ini` | DeepSeek / 高德 API Key / 数据库连接 |
| 依赖 | `node_modules/` | npm 包（`npm install` 安装） |
| 构建产物 | `dist/` `build/` | 前端打包输出 |
| Python 缓存 | `__pycache__/` `*.pyc` `*.pyo` `*.egg-info/` | 字节码 / 包元数据 |
| 测试文件 | `test*.py` `*_test.py` `tests/` `*.spec.js` `*.test.js` `*.spec.ts` `*.test.ts` `__tests__/` | 单元测试 |
| SQL | `*.sql` | 数据库脚本 |
| 影像/视频 | `*.tif` `*.mp4` | 影像视频文件 |
| 模型权重 | `*.bin` `*.pth` `*.th` | 二进制模型文件 |
| 多媒体 | `*.swf` `*.air` `*.ipa` `*.apk` | Flash / 移动应用包 |
| 运行时产物 | `skyeye/static/shp/` `skyeye/static/route_jobs/` `skyeye/static/route_plan/` `skyeye/static/layers/` | 地理数据 / 航线缓存 / 图层 |
| 日志 | `*.log` `logs/` `dev-server.log` | 运行日志 |
| IDE | `.idea/` `.vscode/` `*.suo` `*.sln` | 编辑器个人配置 |
| 系统 | `.DS_Store` `Thumbs.db` | OS 生成文件 |

---

## 许可证

内部使用项目
