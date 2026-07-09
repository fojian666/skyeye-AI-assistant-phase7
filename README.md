# 金陵阡陌（SkyEye）— 低空遥感智能巡检平台

## 项目概述

金陵阡陌（SkyEye）是一个基于低空遥感和无人机技术的智能巡检平台，集成了 **GIS 地图（2D/3D）**、**全景图像分析**、**AI 目标检测**、**航线规划**、**图斑变化检测**、**资源管理** 等核心功能。  
平台通过 **DeepSeek 大模型** 提供 AI 智能助手，支持自然语言驱动地图导航、区域圈定、页面跳转等操作。

---

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | Vue 2 + Element UI | SPA 应用 |
| 前端构建 | Vue CLI + Webpack | — |
| 2D 地图 | Leaflet | 开源轻量 GIS |
| 3D 地图 | Cesium | 三维地球引擎 |
| 全景图 | Pannellum | 浏览器全景渲染 |
| 动画库 | GSAP | 高性能 JS 动画 |
| 图表 | ECharts | 数据可视化 |
| 后端框架 | Django | Python Web 框架 |
| 大模型 | DeepSeek (LangChain + LangGraph) | AI 对话与工具调用 |
| 地理编码 | 高德地图 API | 地名 → 坐标 / 行政区边界 |
| 实时通信 | MQTT + WebSocket | 无人机遥测数据 |
| 数据库 | PostgreSQL | 从 config.ini 读取连接信息 |

---

## 项目结构

```
skyeye/
├── README.md                     # 本文档
├── .gitignore                    # 忽略 config.ini / *.sql / node_modules 等
├── skyeye/                       # Python/Django 后端
│   ├── apps/
│   │   ├── system/               # 系统管理（用户/菜单/角色）+ AI Chat API
│   │   │   ├── views.py          # ★ chat_completions / geocode / district
│   │   │   ├── urls.py           # API 路由
│   │   │   ├── models.py
│   │   │   └── serialirzers.py
│   │   ├── drone_track/          # 无人机轨迹（MQTT + WebSocket）
│   │   ├── experience/           # 体验模块
│   │   └── interpretation/       # AI 解译分析
│   ├── utils_tools/
│   │   └── district_cache.py     # ★ 行政区划边界缓存（内存 + JSON）
│   ├── district_cache.json       # 江苏省 13 市 95 区县多边形缓存
│   └── config.ini                # API Key 配置（gitignore）
│
├── skyeye-ui/                    # Vue 前端
│   ├── src/
│   │   ├── components/
│   │   │   └── chat/
│   │   │       └── ChatModel.vue # ★ AI 助手悬浮窗组件
│   │   ├── views/
│   │   │   ├── dataManagement/oneMap/       # 一张图（2D/3D）
│   │   │   ├── routePlanning/              # 航线规划
│   │   │   ├── panoramicDetection/         # 全景检测
│   │   │   ├── intelligentMonitoring/      # 智能监测
│   │   │   ├── pattern-verifiy/            # 图斑核实
│   │   │   └── ...                         # 其他 20+ 模块
│   │   ├── router/index.js    # 路由配置
│   │   ├── store/             # Vuex 状态管理
│   │   ├── layout/            # 布局（Header/侧栏/主题切换）
│   │   ├── api/               # 接口封装
│   │   └── utils/             # 工具函数
│   └── public/
│       ├── static/Cesium/     # Cesium 3D 引擎
│       └── theme/             # 亮色/暗色主题 CSS
```

---

## AI 智能助手

### 入口

右下角悬浮 **胶囊形按钮**（🤖 AI 助手），点击弹性弹出毛玻璃聊天面板。

### 核心链路

```
用户输入 → DeepSeek 大模型 → Tool Call → 后端执行 → 前端响应事件
```

### 工具列表

| 工具名 | 功能 | 调用条件 |
|------|------|------|
| `navigate_page` | 跳转系统页面 | 用户要求跳转 |
| `map_action` | 地图定位 + 区域边界绘制 | 用户提及任何地点/区域 |
| `query_data` | 查询系统数据 | 用户询问数据 |

### 路由映射（17 条）

| 页面 | 实际路径 |
|------|------|
| 项目管理 | `/task-mgmt/verify-clue` |
| 一张图 | `/data-management/one-map` |
| 影像管理 | `/data-management/table` |
| 全景规划 | `/route-planning/panoramicpoint-planning` |
| 算法规划 | `/route-planning/algorithm-planning` |
| 人工选点 | `/route-planning/manual-planning` |
| 地图总览 | `/panoramic-detection/map-view` |
| 范围管理 | `/panoramic-detection/grid-management` |
| 批次管理 | `/panoramic-detection/task-management` |
| 全景检测 | `/panoramic-detection/main-detection` |
| 不检测区域 | `/panoramic-detection/frame-area` |
| 全景变化 | `/panoramic-detection/panorama-change-detection` |
| 场景管理 | `/panoramic-detection/scene` |
| 线索总览 | `/panoramic-detection/clue-view` |
| 临时批次 | `/panoramic-detection/main-detection-temp` |
| 报告管理 | `/panoramic-detection/report` |
| 任务管理 | `/pattern-verifiy/task_management` |

### 地图导航

- 后端调高德 `geocode` API → 地名 → 经纬度 + 完整地址名
- 前端 `navigate-map` 事件 → 2D Map `flyTo()` / 3D Map `camera.flyTo()`
- 平滑飞行动画

### 区域圈定（子区域彩色边界）

- 后端调高德 `config/district` API → 地名 → polygon 边界坐标
- **子区域圈定**：输入"南京市"自动获取鼓楼区、秦淮区等 11 个区的独立边界，各分配不同颜色
- 前端 `draw-region` 事件：
  - 3D（Cesium）：主区域白色半透明底，子区域各色填充 + 描边
  - 2D（Leaflet）：子区域 hover 显示名称 tooltip
- 同步执行 `navigate-map`，定位到区域中心
- 再次触发自动清除上一轮的图层

### 行政区划缓存

- 预加载 **江苏省 13 市 95 区县**的多边形边界，存入 `district_cache.json`
- 模块级内存缓存：首次加载后常驻内存，后续查询零磁盘 IO、零 API 调用
- 支持管理命令 `python manage.py preload_districts` 刷新缓存

### 追问建议

每段 AI 回复正文后附 3 个用户可能追问的问题，以 `|||` 分隔。

### 面板组件特性

| 特性 | 说明 |
|------|------|
| 毛玻璃 | `backdrop-filter: blur(24px)` 半透明面板 |
| GSAP 动画 | 打开弹性弹出 `back.out(1.7)` |
| 拖拽 | fab / 面板头部均可拖拽，边界碰撞检测 |
| 自由缩放 | 右下角拖拽把手，宽 320~700px，高 400~85vh |
| 右侧吸附 | 点 `→` 吸附为全高右边栏，`←` 恢复浮动 |
| 侧栏大圆 | 靠近面板边缘浮现大圆，hover 展开小圆（`←` 吸附 / `✕` 关闭） |
| 角色名称 | 每条消息上方显示用户名和模型名 |
| 主题适配 | 亮色/暗色自动适配，`html[data-theme]` 选择器 |
| 关闭 | 即时消失，无残留黑条 |

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

编辑 `skyeye/config.ini`：

```ini
[deepseek]
api_key = your_deepseek_key
api_url = https://api.deepseek.com/v1
model = deepseek-chat

[amap]
api_key = your_amap_key
```

> `config.ini` 已加入 `.gitignore`，不会提交到仓库。

---

## 许可证

内部使用项目
