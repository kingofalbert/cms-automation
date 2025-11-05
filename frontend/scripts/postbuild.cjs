#!/usr/bin/env node

/**
 * Post-build helper that mirrors dist/index.html to dist/app.html.
 * Keeps compatibility with legacy deployments pointing at app.html.
 */

const fs = require('fs');
const path = require('path');

const distDir = path.resolve(__dirname, '..', 'dist');
const source = path.join(distDir, 'index.html');
const target = path.join(distDir, 'app.html');

function ensureDistExists() {
  if (!fs.existsSync(distDir)) {
    console.error('[postbuild] dist/ directory not found. Did the build step succeed?');
    process.exit(1);
  }
}

function ensureSourceExists() {
  if (!fs.existsSync(source)) {
    console.error('[postbuild] dist/index.html not found. Unable to create app.html alias.');
    process.exit(1);
  }
}

function copyHtml() {
  fs.copyFileSync(source, target);
  console.log('[postbuild] Created dist/app.html to mirror dist/index.html');
}

ensureDistExists();
ensureSourceExists();
copyHtml();
