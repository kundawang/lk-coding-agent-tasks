#!/usr/bin/env node

import { rmSync } from 'node:fs'
import { execFileSync, spawnSync } from 'node:child_process'

rmSync('apidoc', { recursive: true, force: true })

const head = execFileSync('git', ['show-ref', '--hash', 'HEAD'], { encoding: 'utf8' }).slice(0, 6)

const link_format = `https://github.com/{package.repository}/blob/${head}/{file}#L{line}`

const result = spawnSync(process.execPath, [
  'node_modules/.bin/ndoc',
  '--alias',
  'mjs:js',
  '--link-format',
  link_format
], { stdio: 'inherit' })

if (result.error) throw result.error

process.exitCode = result.status
