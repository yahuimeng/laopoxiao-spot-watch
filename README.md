# 老破小车位哨兵

这是一个面向老小区固定停车位场景的监控项目，用摄像头实时判断楼下停车位是否有空位，并通过网页或手机浏览器展示当前状态。

## 目标

- 接入一个固定视角摄像头
- 识别画面中预先标定的停车位是否空闲
- 实时展示空闲车位数量和每个车位状态
- 后续支持消息提醒和历史统计

## 为什么先做固定车位检测

你的场景是“卧室楼下固定一排停车位”，摄像头位置基本固定，所以第一版不必先做复杂的目标跟踪或车牌识别。我们只需要：

1. 手工框选每个停车位区域
2. 分析该区域是否被车辆占用
3. 持续输出状态

这样开发更快，稳定性也更高。

## 技术架构

### 后端

- Python 3.13
- FastAPI: 提供状态接口和视频流接口
- OpenCV: 读取摄像头和图像处理
- NumPy: 图像计算
- Uvicorn: 本地开发服务器

### 前端

- 原生 HTML + CSS + JavaScript
- 通过 `/api/status` 轮询获取实时状态
- 通过 `/api/frame` 查看当前画面快照

### 配置

- `config/parking_slots.json`: 停车位区域配置
- `config/settings.json`: 摄像头和判定阈值配置

## 项目结构

```text
laopoxiao-spot-watch/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── camera.py
│   ├── detector.py
│   ├── models.py
│   └── services/
│       ├── __init__.py
│       └── parking_service.py
├── config/
│   ├── parking_slots.example.json
│   └── settings.example.json
├── web/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── scripts/
│   └── bootstrap.sh
├── .vscode/
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── requirements.txt
└── README.md
```

## 核心流程

1. 摄像头持续采集画面
2. 系统读取配置好的停车位多边形区域
3. 对每个区域做占用检测
4. 生成每个车位的 `occupied/free` 状态
5. 后端对外提供 JSON 状态接口
6. 前端页面实时展示状态

## 首版检测思路

第一版用轻量规则法，便于快速验证：

- 把每个车位裁剪出来
- 转灰度并做模糊、边缘或纹理分析
- 结合亮度变化、边缘密度判断该区域是否被车辆占用
- 用多帧平滑避免闪烁误判

如果后续发现环境变化大，例如夜晚、雨天、树影干扰明显，再升级为：

- YOLO 检测车辆后判断与车位区域是否重叠
- 或者训练一个“车位空闲/占用”二分类模型

## 适合你的实施路径

### 第 1 阶段

- 确定摄像头位置
- 获取稳定画面
- 手工标注停车位区域
- 跑通本地页面，显示有无空位

### 第 2 阶段

- 优化白天/夜间识别
- 增加截图留档
- 增加 Telegram、企业微信或邮件提醒

### 第 3 阶段

- 记录空位变化历史
- 做“预计何时有车位”的统计
- 增加手机端推送

## 如何运行

### 1. 创建虚拟环境

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 复制配置文件

```bash
cp config/settings.example.json config/settings.json
cp config/parking_slots.example.json config/parking_slots.json
```

### 3. 修改摄像头地址

编辑 `config/settings.json` 中的 `camera_source`：

- 本地 USB 摄像头可填 `0`
- 网络摄像头可填 RTSP 地址，例如 `rtsp://user:password@192.168.1.20:554/stream1`

### 4. 启动服务

```bash
uvicorn app.main:app --reload
```

### 5. 打开页面

浏览器访问：

```text
http://127.0.0.1:8000
```

## 下一步怎么把它真正做起来

你后面只要把一张真实监控截图给我，我就可以继续帮你做下面两件事：

1. 帮你设计 `parking_slots.json` 的标注方式
2. 把检测逻辑从示例规则调到更适合你楼下画面的版本
