# 老破小车位哨兵

这是一个面向老小区固定停车位场景的监控项目，用摄像头实时判断楼下停车位是否有空位，并通过网页或手机浏览器展示当前状态。

## 新增能力

- 检测到空位时推送微信消息
- 持续记录车位快照到本地 SQLite 历史库
- 自动生成最近 30 天的周几趋势和高峰时段统计
- 为后续补充月度报告、到家前提醒、误判回放留出接口

## 当前能力

- 接入固定视角摄像头或 RTSP 监控流
- 识别预先标定的停车位是否空闲
- 实时展示空闲车位数量和每个车位状态
- 提供截图接口、趋势接口、状态接口

## 技术架构

### 后端

- Python 3.13
- FastAPI: 状态接口、统计接口和静态页面托管
- OpenCV: 读取摄像头和图像处理
- SQLite: 本地持久化快照和趋势分析
- Uvicorn: 本地开发服务器

### 前端

- 原生 HTML + CSS + JavaScript
- 轮询 `/api/status` 和 `/api/analytics`
- 实时展示通知状态、车位状态和历史趋势

## 核心流程

1. 后台线程持续读取摄像头画面
2. 系统对每个停车位区域做占用检测
3. 将快照写入 `data/parking_history.sqlite3`
4. 从“无空位”切换到“有空位”时触发微信提醒
5. 页面展示实时状态和最近 30 天趋势摘要

## 微信提醒支持

当前支持两种方式，配置任意一种即可：

- 企业微信机器人 Webhook：`wechat_webhook_url`
- Server酱：`serverchan_sendkey`

配置文件在 [config/settings.json](/Users/olaf.meng/develop/code/AIProjects/laopoxiao-spot-watch/config/settings.json)。

示例：

```json
{
  "camera_source": 0,
  "occupancy_threshold": 0.12,
  "refresh_interval_ms": 3000,
  "history_db_path": "data/parking_history.sqlite3",
  "wechat_webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key",
  "serverchan_sendkey": "",
  "notification_cooldown_seconds": 1800
}
```

## 趋势统计说明

系统会记录每次检测的空位数，当前提供：

- 最近 30 天每周趋势
- 最近 30 天更容易有空位的小时段
- 每个时间段的有空位概率

这能回答你关心的典型问题，例如：

- 周几更容易停车
- 哪个时段最紧张
- 晚上几点更容易等到空位

## 启动方式

```bash
cd /Users/olaf.meng/develop/code/AIProjects/laopoxiao-spot-watch
bash scripts/bootstrap.sh
source .venv/bin/activate
uvicorn app.main:app --reload
```

打开：

- http://127.0.0.1:8000
- `GET /api/status`
- `GET /api/analytics?days=30`

## 下一步建议

- 增加车位标注工具，直接在截图上点选多边形
- 引入 YOLO 做夜间和树影场景优化
- 做“回家前 15 分钟空位提醒”
- 增加周报和月报导出
- 对微信提醒加入截图和直达页面链接
