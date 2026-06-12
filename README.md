# 序列帧动图工具集 (frame-anim-tool)

> WorkBuddy Skill — 将 PNG 序列帧合成为 APNG/GIF 动图，或将动图拆解为序列帧，支持 APNG/GIF 压缩功能

## 功能特性

- 🎬 **序列帧合成**：PNG 序列帧 → APNG / GIF 动图
- 🔪 **动图拆解**：APNG / GIF → PNG 序列帧
- 📦 **动图压缩**：GIF 减色压缩（128色/64色/32色）
- 🌐 **Chrome 预览**：合成/压缩后直接在 Chrome 中预览动图
- 🖱️ **可视化界面**：中文界面 + 棋盘格背景 + 下载按钮

## 支持格式

| 输入 | 输出 |
|---|---|
| PNG 序列帧（zip） | APNG / GIF |
| APNG（.apng / .png） | PNG 序列帧 |
| GIF（.gif） | PNG 序列帧 / 压缩 GIF |

## 安装方式

### WorkBuddy 用户

1. 下载 [Release zip](../../releases/latest)
2. 在 WorkBuddy 技能管理 → 上传技能，选择 zip 文件

### 从源码安装

```bash
git clone https://github.com/hugohung/workbuddy-skill-frame-anim-tool.git ~/.workbuddy/skills/frame-anim-tool
```

## 使用方式

在 WorkBuddy 对话中直接说：

- **"把序列帧合成动图"** → 上传 PNG 序列帧 zip，选择格式和帧率
- **"帮我把这个动图拆成序列帧"** → 上传 APNG/GIF，自动拆解
- **"压缩这个 GIF"** → 上传 GIF，推荐减色方案

## 技术依赖

- **Python 3.13**（pypng）：APNG 合成核心
- **Node.js 22**（gif-encoder-2 + jimp）：GIF 合成
- **gifsicle**：GIF 压缩（减色）

## 版本历史

### v2.4.0 (2026-06-12)
- 🔧 移除 GIF 减帧功能（不稳定，已放弃）
- 🔧 简化压缩逻辑：只保留减色功能

### v2.3.0 (2026-06-12)
- ✨ GIF 减帧压缩功能实现
- 🔧 更新压缩推荐逻辑

### v2.2.0 (2026-06-12)
- 🔧 GIF 压缩改为直接调用 gifsicle（无乱码）

### v2.1.0 (2026-06-12)
- 🔧 移除 Lottie JSON 相关功能
- 🔧 重命名 Skill：`png2apng` → `frame-anim-tool`

### v2.0.0 (2026-06-12)
- ✨ 新增 GIF 导出、动画拆解、压缩功能

### v1.0.0 (2026-06-11)
- 初始版本：PNG 序列帧 → APNG

## License

MIT License
