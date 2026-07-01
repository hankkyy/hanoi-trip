# 🇻🇳 河内 · 下龙湾 4日行程

> 深圳 ↔ 河内 · 7/23 – 7/26 2026 · 子豪 & 小轰轰

## 在线访问

**https://hanoi-vercel.vercel.app**

## 功能

- 📅 **4日行程** — 从 CloudBase NoSQL 数据库实时加载，支持多端同步更新
- 🗺️ **交互地图** — Leaflet 地图，40+ 标注点（景点/酒店/餐厅/下龙湾），点击标签查看详情
- 🌤️ **实时天气** — Open-Meteo API，含 5 日预报 + 逐小时详情
- ⏰ **倒计时 & 当前状态** — 行程中的实时进度条，高亮当前活动和所在天
- 🎨 **Hero 背景轮播** — 4 张河内照片自动交替淡入淡出
- 💰 **预算 & 记账** — 多币种花费追踪（VND/USD/RMB），人均/总共分摊，实时汇率换算，预算 vs 实际对比
- ✅ **出发清单** — 多人实时同步勾选
- 📱 **移动端适配** — 响应式设计，480px/360px 断点

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | 纯 HTML/CSS/JS，无框架 |
| 后端 API | CloudBase HTTP 云函数 (Node.js 18) |
| 数据库 | CloudBase NoSQL (文档型) |
| 地图 | Leaflet + OpenStreetMap |
| 天气 | Open-Meteo (免费，无需 API Key) |
| 托管 | Vercel (前端) + CloudBase (后端) |

## 项目结构

```
hanoi-vercel/
├── index.html          # 主页面（单文件应用）
├── assets/
│   └── photos/         # 图片素材（酒店/餐厅/景点/hero 背景）
├── cloudfunctions/     # 本地云函数副本
│   └── expenses/       # 花费记账 API（待部署）
└── .vercel/            # Vercel 配置
```

云函数源码位于 `~/Desktop/cloudfunctions/api/`，主入口 `index.js` 处理以下路由：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/itinerary` | GET | 获取全部行程 |
| `/api/checklist` | GET | 获取清单 |
| `/api/checklist/:id` | POST | 更新清单项 |
| `/api/expenses` | GET | 获取花费记录 |
| `/api/expenses` | POST | 批量保存花费 |

## 汇率（2026 年 7 月）

| 货币 | 换算 |
|------|------|
| 1 USD | ≈ 6.80 RMB |
| 1 RMB | ≈ 3,880 VND |

数据来源：央行中间价及 Vietcombank 牌价，每日波动约 ±2%。

## 部署

### 前端 (Vercel)

```bash
cd hanoi-vercel
vercel --prod
```

### 后端 (CloudBase)

云函数更新后需手动部署：

```bash
# 通过 CloudBase MCP 或 CLI 部署
tcb fn deploy api
```

## 开发

直接编辑 `index.html`，所有 CSS/JS 内联在单文件中。行程数据通过 CloudBase 控制台或 MCP 工具更新 NoSQL 集合 `itinerary`。

---

*Powered by CloudBase 腾讯云开发 & Vercel*
