#!/usr/bin/env node
'use strict';

const { spawnSync, execSync } = require('child_process');
const path = require('path');

function hasCmd(cmd) {
  try {
    execSync(`which ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

const args = process.argv.slice(2);

// 优先使用 pip 安装的 CLI 命令（避免循环调用自身）
const pipCmd = 'liuguang-card-gen';
if (process.env._LIUGUANG_FROM_NPX !== '1' && hasCmd(pipCmd)) {
  const r = spawnSync(pipCmd, args, { stdio: 'inherit', env: { ...process.env, _LIUGUANG_FROM_NPX: '1' } });
  process.exit(r.status ?? 1);
}

// 检查 python3
if (!hasCmd('python3')) {
  console.error([
    'Error: python3 not found.',
    'Please install Python 3.10+ from https://python.org',
    '',
    'Then install Python dependencies:',
    '  pip3 install anthropic requests Pillow',
  ].join('\n'));
  process.exit(1);
}

// 直接调用本包内的 generator.py
const script = path.join(__dirname, '..', 'generator.py');
const r = spawnSync('python3', [script, ...args], { stdio: 'inherit' });
if (r.error) {
  console.error('Failed to start generator.py:', r.error.message);
  process.exit(1);
}
process.exit(r.status ?? 1);
