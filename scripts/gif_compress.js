#!/usr/bin/env node
/**
 * gif_compress.js - GIF 压缩（调用 gifsicle）
 * 
 * 用法:
 *   node gif_compress.js <input.gif> <output.gif> [--colors N] [--fps N]
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const GIFSICLE = '/Users/honghaoxiang/.workbuddy/binaries/node/workspace/node_modules/gifsicle/vendor/gifsicle';

function getFrameCount(gifPath) {
    try {
        const output = execSync(`"${GIFSICLE}" -I "${gifPath}"`, { encoding: 'utf8' });
        const match = output.match(/\* .+? (\d+) images?/);
        return match ? parseInt(match[1]) : null;
    } catch (e) {
        return null;
    }
}

function compressGif(input, output, options = {}) {
    const { colors, fps } = options;
    
    // 获取原始帧数
    const totalFrames = getFrameCount(input);
    console.log(`  原始帧数: ${totalFrames || '未知'}`);
    
    // 构建 gifsicle 命令
    let cmd = `"${GIFSICLE}"`;
    
    // 帧选择（跳帧）
    if (fps && totalFrames) {
        // 计算需要保留的帧
        // 假设原始是 30fps，要降到 10fps，则每3帧取1帧
        // 需要先检测原始帧率，这里简化为均匀采样
        const inputGif = `"${input}"`;
        
        // 用 --delay 调整帧率（不改变帧数，但改变播放速度）
        // 如果要真正减少帧数，需要用帧选择语法
        // 这里先用 --delay 实现，后续优化
        console.log(`  ⚠️  帧率调整需用帧选择，当前仅调整 delay`);
    }
    
    cmd += ` --optimize=3`;
    
    if (colors) {
        cmd += ` --colors ${colors}`;
        console.log(`  色数: ${colors}`);
    }
    
    if (fps) {
        const delay = Math.round(100 / fps);
        cmd += ` --delay ${delay}`;
        console.log(`  帧率: ${fps} FPS (delay=${delay})`);
    }
    
    cmd += ` -o "${output}" "${input}"`;
    
    console.log(`  执行: ${cmd.substring(0, 80)}...`);
    
    try {
        execSync(cmd, { stdio: 'inherit' });
        
        const origSize = fs.statSync(input).size;
        const newSize = fs.statSync(output).size;
        const ratio = (1 - newSize / origSize) * 100;
        
        console.log(`  ✅ 压缩完成`);
        console.log(`  原大小: ${(origSize/1024).toFixed(1)} KB`);
        console.log(`  新大小: ${(newSize/1024).toFixed(1)} KB`);
        if (Math.abs(ratio) > 0.5) {
            console.log(`  压缩比: ${ratio.toFixed(1)}%`);
        }
    } catch (e) {
        console.error(`  ❌ 压缩失败: ${e.message}`);
        process.exit(1);
    }
}

// 命令行参数解析
const args = process.argv.slice(2);
if (args.length < 2) {
    console.error('用法: node gif_compress.js <input.gif> <output.gif> [--colors N] [--fps N]');
    process.exit(1);
}

const input = args[0];
const output = args[1];
const colors = args.includes('--colors') ? parseInt(args[args.indexOf('--colors') + 1]) : null;
const fps = args.includes('--fps') ? parseInt(args[args.indexOf('--fps') + 1]) : null;

console.log(`🗜️  压缩 GIF: ${path.basename(input)}`);
compressGif(input, output, { colors, fps });
