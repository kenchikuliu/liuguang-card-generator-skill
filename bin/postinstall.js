#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');
const path = require('path');

console.log('liuguang-card-generator: Installing Python dependencies...');
const req = path.join(__dirname, '..', 'requirements.txt');
const r = spawnSync('pip3', ['install', '-r', req, '--quiet'], { stdio: 'inherit' });
if (r.status !== 0) {
  console.warn('Warning: pip3 install failed. Please run manually:');
  console.warn('  pip3 install anthropic requests Pillow');
}
