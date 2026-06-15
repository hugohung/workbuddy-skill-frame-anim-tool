# 🎬 序列帧动图工具集

> **WorkBuddy Skill** — 将 PNG 序列帧合成为 APNG/GIF 动图，或将动图拆解为序列帧，支持 APNG/GIF 压缩功能

[![Version](https://img.shields.io/github/v/release/hugohung/workbuddy-skill-frame-anim-tool?style=flat-square)](https://github.com/hugohung/workbuddy-skill-frame-anim-tool/releases)
[![License](https://img.shields.io/github/license/hugohung/workbuddy-skill-frame-anim-tool?style=flat-square)](LICENSE)
[![WorkBuddy](https://img.shields.io/badge/WorkBuddy-skill-orange.svg?style=flat-square)](https://www.codebuddy.cn)
[![Python](https://img.shields.io/badge/Python-3.13+-blue?style=flat-square)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-22+-green?style=flat-square)](https://nodejs.org/)
[![GitHub Stars](https://img.shields.io/github/stars/hugohung/workbuddy-skill-frame-anim-tool?style=flat-square)](https://github.com/hugohung/workbuddy-skill-frame-anim-tool/stargazers)

---

## 📊 核心能力

本 Skill 提供序列帧与动图之间的双向转换，以及动图压缩功能，适用于游戏开发、UI动效制作等场景。

### ✨ 功能特性

| 功能 | 说明 | 支持格式 |
|------|------|----------|
| 🎬 **合成** | PNG 序列帧 → 动图 | 输出：APNG / GIF |
| 🔪 **拆解** | 动图 → PNG 序列帧 | 输入：APNG / GIF |
| 📦 **压缩** | 动图压缩（颜色量化 + 减色） | 输入：APNG / GIF |

---

## 🎯 适用场景

- 🎮 **游戏开发** — 将游戏引擎导出的序列帧合成为动图，或将动图拆解为序列帧
- 🎨 **UI动效制作** — 制作网页/APP需要的动图素材
- 📱 **社交媒体素材** — 生成适用于各平台的动图格式
- 🗜️ **动图压缩优化** — 减小动图文件大小，提升加载速度

---

## 🚀 快速开始

### 前置要求

#### Python 环境
- **托管 Python 3.13**（pypng）：用于 APNG 合成/拆解
- **系统 Python 3**（Pillow）：用于 GIF 拆解、APNG 颜色量化

#### Node.js 环境
- **Node.js 22+**（gif-encoder-2 + jimp）：用于 GIF 合成
- **gifsicle**：用于 GIF 压缩

#### 依赖安装

```bash
# Python 依赖
pip install pypng pillow

# Node.js 依赖
npm install gif-encoder-2 jimp gifsicle

# macOS 安装 gifsicle
brew install gifsicle
```

---

## 📖 使用方式

在 WorkBuddy 对话中直接说：

### 功能一：序列帧合成动图

```
把序列帧合成动图
```

```
生成 APNG / GIF
```

**使用流程**：
1. 上传包含 PNG 的 zip 压缩包
2. 设定参数（输出格式、帧率、循环次数、压缩质量）
3. 自动执行合成
4. 在 Chrome 中打开预览页面
5. 下载输出文件

**参数说明**：
- **输出格式**：APNG（无损透明，推荐）/ GIF（兼容性好，不支持透明）
- **帧率 FPS**：默认 15，推荐 10–30
- **循环次数**：默认无限循环
- **压缩质量**：1–100%，默认 100%

---

### 功能二：动图拆解为序列帧

```
帮我把这个动图拆成序列帧
```

```
APNG/GIF 转 PNG 序列帧
```

**使用流程**：
1. 上传 APNG / GIF 文件
2. 自动执行拆解
3. 输出到桌面文件夹（命名规则：`<原文件名>_frames`）
4. 向用户报告总帧数、尺寸、文件夹路径

> ⚠️ 注意：拆图结果不直接预览，请到桌面对应文件夹查看

---

### 功能三：动图压缩

```
压缩这个 APNG/GIF
```

```
帮我把动图文件压缩一下
```

**压缩策略**：

| 文件类型 | 推荐方案 | 压缩效果 |
|---------|---------|---------|
| GIF | ✅ 推荐**减色**（128色/64色/32色） | 17-40% |
| APNG | ✅ 推荐**颜色量化**（128色/64色） | 38-40% |
| APNG | ⚠️ zlib 压缩（效果有限） | 3-10% |

**使用流程**：
1. 上传 APNG / GIF 文件
2. 自动分析文件并推荐压缩方案
3. 选择压缩参数（GIF 减色 / APNG 颜色量化）
4. 执行压缩
5. 展示对比报告（原文件大小 vs 压缩后大小、压缩比例）
6. 在 Chrome 中预览压缩后的文件

---

## 📋 支持格式

### 输入格式

| 格式 | 说明 | 注意事项 |
|------|------|---------|
| PNG 序列帧（.zip） | 按帧顺序排列的 PNG 文件压缩包 | 文件名建议按 `frame_001.png` 格式命名 |
| APNG（.apng/.png） | APNG 格式动图 | `.png` 扩展名的文件也可能是 APNG，脚本会自动检测 `acTL` chunk |
| GIF（.gif） | GIF 格式动图 | 支持所有标准 GIF 文件 |

### 输出格式

| 格式 | 说明 | 适用场景 |
|------|------|---------|
| APNG（.apng） | 无损透明动图 | 需要透明通道、高质量动图 |
| GIF（.gif） | 兼容性好的动图 | 需要广泛兼容性的场景 |

---

## 🛠️ 脚本说明

本 Skill 包含以下脚本：

```
~/.workbuddy/skills/frame-anim-tool/scripts/
├── png2apng.py        # APNG 合成核心（pypng 纯 Python）
├── compose.py         # 合成入口：序列帧 → APNG/GIF
├── decompose.py       # 拆解：APNG/GIF → 序列帧
├── compress.py        # 压缩：APNG/GIF 压缩（支持颜色量化）
├── quantize_apng.py  # APNG 颜色量化（系统 Python + Pillow）
└── apng_preview.py    # 预览服务器（中文界面+下载按钮）
```

### 核心脚本说明

#### compose.py — 合成入口
```bash
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compose.py \
  <input.zip> <output> \
  --format <apng|gif> \
  --fps <fps> --loops <loops> --quality <quality>
```

#### decompose.py — 拆解入口
```bash
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/decompose.py \
  <input> <output_dir>
```

#### compress.py — 压缩入口
```bash
# APNG 颜色量化（推荐）
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.apng> <output.apng> --colors 128

# GIF 减色压缩
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.gif> <output.gif> --colors 128

# 只检测信息，不压缩
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.gif> --info
```

---

## 📦 安装方式

### 方式一：WorkBuddy 用户

1. 下载 [最新 Release zip](https://github.com/hugohung/workbuddy-skill-frame-anim-tool/releases/latest)
2. 在 WorkBuddy **技能管理** → **上传技能**，选择 zip 文件
3. 安装依赖（见上方"前置要求"）
4. 重启 WorkBuddy 即可使用

### 方式二：从源码安装

```bash
git clone https://github.com/hugohung/workbuddy-skill-frame-anim-tool.git ~/.workbuddy/skills/frame-anim-tool
```

安装依赖后重启 WorkBuddy 即可。

---

## 🔄 版本历史

### v2.5.0 (2026-06-12)
- ✨ 新增 APNG 颜色量化功能（参考 Tinify 原理）
- ✨ 新增 `quantize_apng.py` 脚本（系统 Python + Pillow FASTOCTREE）
- 🔧 更新 `compress.py`：新增 `--colors` 参数（APNG/GIF 通用）
- 🔧 更新压缩推荐策略：APNG 优先推荐颜色量化（38-40% 压缩比）

### v2.4.0 (2026-06-12)
- 🔧 移除 GIF 减帧功能（不稳定，已放弃）
- 🔧 简化 compress.py：只保留减色功能

### v2.3.0 (2026-06-12)
- ✨ GIF 减帧压缩功能实现（调用 gifsicle -e 拆帧 + 合并）

### v2.2.0 (2026-06-12)
- 🔧 更新压缩推荐策略：优先推荐减色，GIF ≤64色时同步推荐减帧

### v2.1.0 (2026-06-12)
- 🔧 移除 Lottie JSON 相关功能（合成/拆解均不再支持）
- 🔧 重命名 Skill：`png2apng` → `frame-anim-tool`

### v2.0.0 (2026-06-12)
- ✨ 新增 GIF 导出（Node.js gif-encoder-2 + jimp）
- ✨ 新增动画拆解功能（APNG/GIF → 序列帧）
- ✨ 新增 APNG/GIF 压缩功能
- 🔧 重构为模块化脚本（compose/decompose/compress）

### v1.0.0 (2026-06-11)
- 初始版本：PNG 序列帧 → APNG

---

## ⚠️ 注意事项

1. **Python 环境选择** — APNG 合成/拆解使用托管 Python，GIF 拆解使用系统 Python（避免代码签名问题）
2. **预览方式** — 合成/压缩后在 Chrome 中打开预览，拆图结果输出到桌面文件夹
3. **文件命名** — 序列帧文件名建议按 `frame_001.png` 格式命名，确保顺序正确
4. **GIF 透明通道** — GIF 不支持透明通道，如需透明请使用 APNG 格式

---

## 🐛 常见问题

### 1. 合成 APNG 失败？
检查是否安装 pypng 依赖，且输入 zip 包内的 PNG 文件命名按帧顺序排列（如 `frame_001.png`、`frame_002.png`）

### 2. GIF 压缩后颜色失真严重？
建议优先选择 128 色压缩，32 色仅适用于色彩较少的动图

### 3. WorkBuddy 上传技能失败？
确认下载的是最新 Release 的 zip 包，未自行修改包内文件结构

### 4. 预览页面无法打开？
检查端口 8767 是否被占用，或手动执行以下命令：
```bash
lsof -ti:8767 2>/dev/null | xargs kill -9 2>/dev/null
```

---

## 🔗 相关 Skill

- [**GitHub Skill 发布管理工具**](https://github.com/hugohung/workbuddy-skill-github-skill-publisher) — 将 Skill 发布到 GitHub
- [**Skill 介绍页文案生成器**](https://github.com/hugohung/workbuddy-skill-skill-intro-writer) — 为 Skill 生成介绍页文案

---

## 📄 License

[MIT License](LICENSE)

---

## 👨‍💻 作者

**honghaoxiang**

- GitHub: [@hugohung](https://github.com/hugohung)
- WorkBuddy: [codebuddy.cn](https://www.codebuddy.cn)

---

## 🙏 致谢

- [pypng](https://github.com/drj11/pypng) — APNG 合成核心库
- [gif-encoder-2](https://github.com/TrevorS/gif-encoder-2) — GIF 合成库
- [jimp](https://github.com/jimp-dev/jimp) — Node.js 图像处理库
- [gifsicle](https://www.lcdf.org/gifsicle/) — GIF 压缩工具
- [Pillow](https://python-pillow.org/) — Python 图像处理库

---

**⭐ 如果这个 Skill 对你有帮助，欢迎 Star 和分享！**
