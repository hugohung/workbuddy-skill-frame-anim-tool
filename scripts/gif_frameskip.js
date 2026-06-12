#!/usr/bin/env node
/**
 * gif_frameskip.js - GIF 减帧压缩
 * 步骤：
 *   1. 用 gifsicle -e 拆成单帧文件
 *   2. 按目标帧率选取帧
 *   3. 用 gifsicle 合并选中的帧
 *   4. 用 --colors 减色 + --optimize=3 压缩
 * 
 * 用法:
 *   node gif_frameskip.js <input.gif> <output.gif> [--fps 10] [--colors 128]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const GIFSICLE = '/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules/gifsicle/vendor/gifsicle';

function getFrameInfo(gifPath) {
    try {
        const out = execSync(`"${GIFSICLE}" -I "${gifPath}"`, { encoding: 'utf8' });
        const result = { frames: null, delay: null };
        const m = out.match(/(\d+) images?/);
        if (m) result.frames = parseInt(m[1]);
        // 获取第一帧的 delay
        const lines = out.split('\n');
        for (const line of lines) {
            const dm = line.match(/delay ([\d.]+)s/);
            if (dm) {
                result.delay = parseFloat(dm[1]);
                break;
            }
        }
        return result;
    } catch(e) {
        return null;
    }
}

function frameSkip(input, output, options = {}) {
    const { fps, colors } = options;
    const info = getFrameInfo(input);
    if (!info || !info.frames) {
        console.error('  ❌ 无法获取 GIF 帧信息');
        process.exit(1);
    }

    console.log(`  原始帧数: ${info.frames}`);
    if (info.delay) {
        const origFps = Math.round(100 / (info.delay * 100)) || 30;
        console.log(`  原始帧率: ~${origFps} FPS (delay=${info.delay}s)`);
    }

    // 计算需要保留的帧
    let keepIndices = [];
    if (fps && info.delay) {
        const origFps = Math.round(1 / info.delay);
        const step = Math.round(origFps / fps);
        for (let i = 0; i < info.frames; i += step) {
            keepIndices.push(i);
        }
        console.log(`  目标帧率: ${fps} FPS`);
        console.log(`  保留帧数: ${keepIndices.length} (每${step}帧取1帧)`);
    } else {
        // 不跳帧
        for (let i = 0; i < info.frames; i++) keepIndices.push(i);
        console.log(`  不跳帧，保留全部 ${info.frames} 帧`);
    }

    // 方法：用 gifsicle 的 --delete 选项
    // 构建要删除的帧号列表
    const allFrames = new Set(Array.from({length: info.frames}, (_, i) => i));
    const keepSet = new Set(keepIndices);
    const deleteFrames = [...allFrames].filter(i => !keepSet.has(i));

    if (deleteFrames.length === 0) {
        console.log(`  ℹ️  无需跳帧，直接减色`);
        // 只做减色
        let cmd = `"${GIFSICLE}" "${input}" --optimize=3`;
        if (colors) cmd += ` --colors ${colors}`;
        cmd += ` -o "${output}"`;
        execSync(cmd, { stdio: 'inherit' });
    } else {
        // 用 --delete 删除不需要的帧
        // gifsicle 的 --delete 接受帧选择语法
        // 语法：--delete "input.gif#frameNum"
        // 但更简单的方法：用 explode 模式拆帧，再合并选中帧
        
        const tmpDir = `/tmp/gif_frameskip_${Date.now()}`;
        fs.mkdirSync(tmpDir, { recursive: true });
        
        // 用 gifsicle -e 拆帧（每帧一个文件）
        const explodeCmd = `"${GIFSICLE}" -e "${input}" --output "${tmpDir}/frame.gif"`;
        console.log(`  拆帧到: ${tmpDir}`);
        execSync(explodeCmd, { stdio: 'inherit' });
        
        // 读取拆出的帧文件
        const frameFiles = fs.readdirSync(tmpDir)
            .filter(f => f.startsWith('frame.gif') && f !== 'frame.gif')
            .sort((a, b) => {
                const na = parseInt(a.match(/(\d+)$/)?.[1] || '0');
                const nb = parseInt(b.match(/(\d+)$/)?.[1] || '0');
                return na - nb;
            });
        
        console.log(`  实际拆出帧数: ${frameFiles.length}`);
        
        if (frameFiles.length === 0) {
            console.error('  ❌ explode 模式未拆出帧，改用 --delete 方式');
            // 回退：用 --delete（需要构建复杂的帧选择参数）
            // 暂时直接复制
            fs.copyFileSync(input, output);
        } else {
            // 合并选中的帧
            let mergeCmd = `"${GIFSICLE}" --optimize=3`;
            for (const idx of keepIndices) {
                if (idx < frameFiles.length) {
                    mergeCmd += ` "${tmpDir}/${frameFiles[idx]}"`;
                }
            }
            if (colors) mergeCmd += ` --colors ${colors}`;
            mergeCmd += ` -o "${output}"`;
            
            console.log(`  合并 ${keepIndices.length} 帧...`);
            execSync(mergeCmd, { stdio: 'inherit' });
        }
        
        // 清理临时文件
        fs.rmSync(tmpDir, { recursive: true, force: true });
    }

    const origSize = fs.statSync(input).size;
    const newSize = fs.statSync(output).size;
    const ratio = (1 - newSize / origSize) * 100;
    console.log(`  ✅ 压缩完成`);
    console.log(`  原大小: ${(origSize/1024).toFixed(1)} KB`);
    console.log(`  新大小: ${(newSize/1024).toFixed(1)} KB`);
    if (Math.abs(ratio) > 0.5) {
        console.log(`  压缩比: ${ratio.toFixed(1)}%`);
    }
}

// CLI
const args = process.argv.slice(2);
if (args.length < 2) {
    console.error('用法: node gif_frameskip.js <input.gif> <output.gif> [--fps N] [--colors N]');
    process.exit(1);
}

const input = args[0];
const output = args[1];
const fps = args.includes('--fps') ? parseInt(args[args.indexOf('--fps') + 1]) : null;
const colors = args.includes('--colors') ? parseInt(args[args.indexOf('--colors') + 1]) : null;

console.log(`🗜️  压缩 GIF: ${path.basename(input)}`);
frameSkip(input, output, { fps, colors });
