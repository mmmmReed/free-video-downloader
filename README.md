# FreeVideo - 万能视频下载网站

支持 YouTube、B站、TikTok、Instagram、Twitter 等 **1700+** 平台的在线视频下载工具。

## 技术栈

- **前端**: Vue 3 + TypeScript + Vite + Tailwind CSS
- **后端**: Python FastAPI + yt-dlp
- **通信**: RESTful API + SSE (Server-Sent Events) 实时进度

## 快速开始

### 前置依赖

- Node.js 20+
- Python 3.10+
- FFmpeg (用于合并音视频流)

### 后端启动

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173 即可使用。

## 项目结构

```
free-video-downloader/
├── docs/                  # 项目文档
│   ├── 需求分析.md
│   └── 技术方案.md
├── frontend/              # Vue 3 前端
│   └── src/
│       ├── components/    # UI 组件
│       ├── composables/   # 组合式函数
│       ├── api/           # API 请求
│       ├── types/         # TypeScript 类型
│       └── views/         # 页面
├── backend/               # FastAPI 后端
│   ├── main.py            # 入口
│   ├── routers/           # 路由
│   ├── services/          # 业务逻辑
│   └── downloads/         # 临时下载目录
└── README.md
```

## 免责声明

本工具仅供学习研究使用，请尊重内容创作者版权，用户需自行遵守相关平台服务条款。
