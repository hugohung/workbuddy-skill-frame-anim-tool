---
name: jd-frame-anim-tool
description: |
  将 PNG 序列帧合成为 APNG/GIF 动图，或将动图拆解为序列帧，
  支持 APNG/GIF 压缩功能。触发词：序列帧、帧动画、apng、gif、拆图、压缩动画。
agent_created: true
author: honghaoxiang
version: 2.6.0
disable: false
---

# 序列帧动图工具集

支持序列帧合成、动图拆解、压缩三大功能，输出格式支持 APNG、GIF。

## 功能总览

| 功能 | 说明 |
|---|---|
| 🎬 合成 | PNG 序列帧 → APNG / GIF |
| 🔪 拆解 | APNG / GIF → PNG 序列帧 |
| 📦 压缩 | APNG / GIF 压缩（颜色量化 + 减色） |

---

## 功能一：序列帧合成动图

### 触发条件

- "把序列帧合成动图"
- "生成 APNG / GIF"
- 上传包含 PNG 的 zip 压缩包

### 使用流程

#### 第 1 步：接收并分析压缩包

解压后向用户报告：总帧数、帧尺寸、文件名排序结果。

#### 第 2 步：设定参数

**必须依次询问（用 AskUserQuestion 提供点击选项）：**

1. **输出格式**（二选一）：
   - `APNG` — 无损透明，推荐
   - `GIF` — 兼容性好，不支持透明

2. **帧率 FPS**（默认 15，推荐 10–30）

3. **是否循环**（默认无限循环）

4. **压缩质量**（1–100%，默认 100%）

#### 第 3 步：执行合成

```bash
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compose.py \
  <input.zip> <output> \
  --format <apng|gif> \
  --fps <fps> --loops <loops> --quality <quality>
```

**Python 环境**：
```bash
/Users/honghaoxiang/.workbuddy/binaries/python/envs/png2apng3/bin/python3 \
  ~/.workbuddy/skills/frame-anim-tool/scripts/compose.py ...
```

> **GIF 合成说明**：GIF 合成使用 Node.js（`gif-encoder-2` + `jimp`），
> compose.py 会自动生成 Node.js 脚本并调用 Node 执行。
> Node 路径：`/Users/honghaoxiang/.workbuddy/binaries/node/versions/22.22.2/bin/node`

#### 第 4 步：预览和下载

**单文件输出（APNG/GIF）→ 在 Chrome 中打开预览页面**

```bash
# 停掉旧服务
lsof -ti:8767 2>/dev/null | xargs kill -9 2>/dev/null; sleep 1

# 启动预览服务器
nohup /usr/bin/python3 \
  ~/.workbuddy/skills/frame-anim-tool/scripts/apng_preview.py \
  <output> --port 8767 > /tmp/apng_preview.log 2>&1 &
sleep 2

# 在 Chrome 中打开
open -a "Google Chrome" "http://localhost:8767"
```

> ⚠️ 注意：不要用 `preview_url`，直接用 `open -a "Google Chrome"` 命令

预览页面功能：
- 中文界面 + 棋盘格背景
- 显示原始动图（非 GIF 转换）
- 参数信息展示
- 下载按钮

#### 第 5 步：返回结果

- 将输出文件作为附件返回给用户
- 提示预览页面已在 Chrome 中打开

---

## 功能二：动图拆解为序列帧

### 触发条件

- "帮我把这个动图拆成序列帧"
- "APNG/GIF 转 PNG 序列帧"
- 上传 APNG / GIF 文件

### 使用流程

#### 第 1 步：接收文件

支持格式：`.apng`、`.gif`、`.png`（APNG 格式）

> **注意**：`.png` 扩展名的文件也可能是 APNG，脚本会自动检测 `acTL` chunk 来判断。

#### 第 2 步：执行拆解

**⚠️ 必须使用系统 Python（托管 Python 有代码签名问题）：**
```bash
# 1. 在工作空间创建临时输出目录
mkdir -p <workspace>/decompose_output

# 2. 用系统 Python 执行拆解（输出到工作空间）
/usr/bin/python3 \
  ~/.workbuddy/skills/frame-anim-tool/scripts/decompose.py \
  <input> <workspace>/decompose_output

# 3. 复制到桌面（Bash 可绕过沙盒，会请求用户授权）
cp -r <workspace>/decompose_output ~/Desktop/<文件名>_frames
```

文件夹命名规则：`<原文件名>_frames`（例如 `test_animation.png` → `test_animation_frames`）

#### 第 3 步：输出结果

- **不在浏览器中预览**（多文件不适合预览）
- 向用户报告：总帧数、尺寸、桌面文件夹路径
- 提醒用户去桌面对应文件夹查看文件

---

## 功能三：动图压缩

### 触发条件

- "压缩这个 APNG/GIF"
- "帮我把动图文件压缩一下"

### 使用流程

#### 第 1 步：接收文件

支持格式：`.apng`、`.gif`

#### 第 2 步：分析文件并推荐压缩方案

**先检测 GIF 当前色数（APNG 跳过此步）：**
```bash
/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules/gifsicle/vendor/gifsicle \
  -I <input.gif> 2>&1 | grep -i "color\|global\|local"
```

**推荐策略（用 AskUserQuestion 提供点击选项）：**

| 文件类型 | 推荐方案 | 压缩效果 |
|---------|---------|---------|
| GIF | ✅ 推荐**减色**（128色/64色/32色） | 17-40% |
| APNG | ✅ 推荐**颜色量化**（128色/64色） | 38-40% |
| APNG | ⚠️ zlib 压缩（效果有限） | 3-10% |

**提问（一次问完）：**
1. **GIF 减色**（默认推荐 128 色）：
   - `不减色`
   - `128 色（推荐，画质几乎无影响）`
   - `64 色（画质轻微下降）`
   - `32 色（画质明显下降）`
2. **APNG 颜色量化**（参考 Tinify 原理）：
   - `不量化`
   - `128 色（推荐，压缩 38%）`
   - `64 色（压缩 40%，画质轻微下降）`

#### 第 3 步：执行压缩

**GIF 压缩（用 compress.py，只支持减色）：**
```bash
# 减色压缩（推荐）
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.gif> <output.gif> --colors 128

# 只检测信息，不压缩
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.gif> --info
```

> **原理说明**：
> - 减色：调用 `gifsicle --colors`（直接操作 GIF 二进制结构，无乱码）
> - 不支持减帧（已移除）

**APNG 压缩（用 compress.py）：**
```bash
# 颜色量化（推荐，参考 Tinify 原理）
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.apng> <output.apng> --colors 128

# zlib 压缩（效果有限，仅 3-10%）
python3 ~/.workbuddy/skills/frame-anim-tool/scripts/compress.py \
  <input.apng> <output.apng> --quality 1
```

> **APNG 压缩说明**：
> - 颜色量化：将 24 位 APNG 转换为 8 位索引色（使用 Pillow FASTOCTREE 方法）
> - 压缩效果显著（128 色 → 38%，64 色 → 40%）
> - zlib 压缩：降低压缩质量，效果有限（3-10%）

#### 第 4 步：对比报告

向用户展示：
- 原文件大小 vs 压缩后大小
- 压缩比例
- 画质对比提示

#### 第 5 步：预览和下载

单文件输出 → Chrome 预览（同功能一第4步）

---

## 脚本位置

```
~/.workbuddy/skills/frame-anim-tool/scripts/
├── png2apng.py        # APNG 合成核心（pypng 纯 Python）
├── compose.py         # 合成入口：序列帧 → APNG/GIF
├── decompose.py       # 拆解：APNG/GIF → 序列帧
├── compress.py        # 压缩：APNG/GIF 压缩（支持颜色量化）
├── quantize_apng.py  # APNG 颜色量化（系统 Python + Pillow）
└── apng_preview.py    # 预览服务器（中文界面+下载按钮）
```

---

## 环境依赖

- **Python 3.13**（pypng）：`/Users/honghaoxiang/.workbuddy/binaries/python/envs/png2apng3/bin/python3`
  - 用于：APNG 合成（compose.py）、APNG 拆解（decompose.py）
  - ⚠️ 注意：托管 Python 环境有代码签名问题，GIF 拆解需用系统 Python
- **系统 Python**（Pillow）：`/usr/bin/python3`
  - 用于：GIF 拆解（decompose.py）、APNG 颜色量化（quantize_apng.py）
- **Node.js 22**（gif-encoder-2 + jimp）：`/Users/honghaoxiang/.workbuddy/binaries/node/versions/22.22.2/bin/node`
  - 用于：GIF 合成（compose.py 自动调用 Node.js）
- **Node 模块路径**：`/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules`
  - gifsicle：GIF 压缩（compress.py）
- **系统 Python**（预览服务器）：`/usr/bin/python3`
  - 用于：apng_preview.py（预览服务器）

---

## 版本历史

### v2.5.0 (2026-06-12)
- ✨ 新增 APNG 颜色量化功能（参考 Tinify 原理）
- ✨ 新增 `quantize_apng.py` 脚本（系统 Python + Pillow FASTOCTREE）
- 🔧 更新 `compress.py`：新增 `--colors` 参数（APNG/GIF 通用）
- 🔧 更新压缩推荐策略：APNG 优先推荐颜色量化（38-40% 压缩比）
- 🔧 更新 SKILL.md：补充颜色量化使用说明

### v2.4.0 (2026-06-12)
- 🔧 移除 GIF 减帧功能（不稳定，已放弃）
- 🔧 简化 compress.py：只保留减色功能
- 🔧 更新 SKILL.md：移除所有减帧相关描述

### v2.3.0 (2026-06-12)
- ✨ GIF 减帧压缩功能实现（调用 gifsicle -e 拆帧 + 合并）
- 🔧 更新 compress.py：GIF 减色用 gifsicle，减帧调用 gif_frameskip.js
- 🔧 更新压缩推荐逻辑：优先减色，≤64色同步推荐减帧
- ✨ 新增 gif_frameskip.js 脚本

### v2.2.0 (2026-06-12)
- 🔧 更新压缩推荐策略：优先推荐减色，GIF ≤64色时同步推荐减帧
- 🔧 GIF 压缩改为直接调用 gifsicle（操作二进制结构，无乱码）
- ✨ compress.py 新增 `--info` 参数（检测 GIF 当前色数）

### v2.1.0 (2026-06-12)
- 🔧 移除 Lottie JSON 相关功能（合成/拆解均不再支持）
- 🔧 重命名 Skill：`png2apng` → `frame-anim-tool`
- 🔧 更新触发词：移除 `lottie`

### v2.0.0 (2026-06-12)
- ✨ 新增 GIF 导出（Node.js gif-encoder-2 + jimp）
- ✨ 新增动画拆解功能（APNG/GIF → 序列帧）
- ✨ 新增 APNG/GIF 压缩功能
- 🔧 重构为模块化脚本（compose/decompose/compress）
- 🔧 用户决策改用 AskUserQuestion 点击选项
- 🔧 预览方式改为 Chrome 浏览器直接打开
- 🔧 拆图输出到桌面文件夹，不预览

### v1.0.0 (2026-06-11)
- 初始版本：PNG 序列帧 → APNG
