#!/usr/bin/env node
/**
 * One-command development launcher.
 *
 *   npm run dev                 # backend + frontend
 *   npm run dev:backend        # backend only
 *   npm run dev:frontend       # frontend only
 *
 * First run prepares backend/.venv and frontend/node_modules automatically.
 * Ctrl+C stops both child processes (including uvicorn --reload / Vite).
 */

import { spawn, spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = dirname(dirname(fileURLToPath(import.meta.url)))
const backendDir = join(rootDir, 'backend')
const frontendDir = join(rootDir, 'frontend')
const venvDir = join(backendDir, '.venv')
const isWindows = process.platform === 'win32'
const venvPython = join(venvDir, isWindows ? 'Scripts' : 'bin', isWindows ? 'python.exe' : 'python')
const npmCommand = isWindows ? 'npm.cmd' : 'npm'

const onlyArgument = process.argv.find((argument) => argument.startsWith('--only='))
const only = onlyArgument ? onlyArgument.split('=')[1] : null

if (only && !['backend', 'frontend'].includes(only)) {
  console.error(`未知参数 --only=${only}，可选值：backend / frontend`)
  process.exit(1)
}

const startBackend = only !== 'frontend'
const startFrontend = only !== 'backend'

function fail(message) {
  console.error(`\n[setup] ${message}`)
  process.exit(1)
}

function runChecked(command, args, { cwd, shell = false, label }) {
  console.log(`[setup] ${label}...`)
  const result = spawnSync(command, args, { cwd, stdio: 'inherit', shell })
  if (result.error) {
    fail(`${label}失败：${result.error.message}`)
  }
  if (result.status !== 0) {
    fail(`${label}失败（退出码 ${result.status ?? 'unknown'}）`)
  }
}

function findSystemPython() {
  const candidates = [process.env.PYTHON, 'python', 'python3'].filter(Boolean)
  for (const candidate of candidates) {
    const result = spawnSync(candidate, ['--version'], { stdio: 'ignore' })
    if (result.status === 0) return candidate
  }
  fail('未找到 Python。请安装 Python 3.12+ 并确保 python 在 PATH 中。')
}

function ensureBackend() {
  if (!existsSync(join(backendDir, 'requirements.txt'))) {
    fail(`找不到 ${join('backend', 'requirements.txt')}`)
  }

  let python = existsSync(venvPython) ? venvPython : null

  if (!python) {
    const systemPython = findSystemPython()
    runChecked(systemPython, ['-m', 'venv', '.venv'], {
      cwd: backendDir,
      label: '创建 Python 虚拟环境',
    })
    python = venvPython
  }

  // Importing the app is the most reliable dependency probe: it exercises
  // FastAPI, SQLAlchemy, settings and the multipart upload dependency.
  const probe = spawnSync(python, ['-c', 'import app.main'], {
    cwd: backendDir,
    stdio: 'ignore',
  })
  if (probe.status !== 0) {
    runChecked(python, ['-m', 'pip', 'install', '-r', 'requirements.txt'], {
      cwd: backendDir,
      label: '安装后端依赖',
    })
  }

  return python
}

function ensureFrontend() {
  const viteInstalled = existsSync(join(frontendDir, 'node_modules', 'vite'))
  if (!viteInstalled) {
    runChecked(npmCommand, ['install'], {
      cwd: frontendDir,
      shell: isWindows,
      label: '安装前端依赖',
    })
  }
}

function ensureSeedData(python) {
  // Only seeds when job_postings is empty; never overwrites imported data.
  const result = spawnSync(python, ['-m', 'scripts.seed_if_empty'], {
    cwd: backendDir,
    stdio: 'inherit',
  })
  if (result.status !== 0) {
    console.warn('[setup] 初始数据检查失败，可稍后手动导入。')
  }
}

const children = []
let shuttingDown = false

function stopChild(child) {
  if (child.exitCode !== null || child.signalCode !== null) return

  if (isWindows) {
    // taskkill /T also terminates npm.cmd -> vite and uvicorn reload children.
    spawnSync('taskkill', ['/pid', String(child.pid), '/T', '/F'], {
      stdio: 'ignore',
    })
    return
  }

  try {
    // Children run in their own process group (detached), so signal the group.
    process.kill(-child.pid, 'SIGTERM')
  } catch {
    try {
      child.kill('SIGTERM')
    } catch {
      // Process already gone.
    }
  }
}

function shutdown(exitCode = 0) {
  if (shuttingDown) return
  shuttingDown = true

  if (children.length > 0) {
    console.log('\n正在停止前后端服务...')
    children.forEach(({ child }) => stopChild(child))
  }

  // Give children a moment to release ports before this process exits.
  setTimeout(() => process.exit(exitCode), 800)
}

function startService(name, command, args, cwd, { shell = false } = {}) {
  const child = spawn(command, args, {
    cwd,
    stdio: 'inherit',
    detached: !isWindows,
    env: process.env,
    shell,
  })

  children.push({ name, child })

  child.on('error', (error) => {
    console.error(`[${name}] 启动失败：${error.message}`)
    shutdown(1)
  })

  child.on('exit', (code, signal) => {
    if (shuttingDown) return
    console.error(
      `\n[${name}] 已退出（code=${code ?? 'null'}, signal=${signal ?? 'null'}）`,
    )
    shutdown(code === 0 ? 0 : 1)
  })

  return child
}

process.on('SIGINT', () => shutdown(0))
process.on('SIGTERM', () => shutdown(0))

async function main() {
  const python = startBackend ? ensureBackend() : null
  if (startFrontend) ensureFrontend()
  if (python) ensureSeedData(python)

  console.log('\nJobLens 开发环境')
  if (startBackend) {
    console.log('  后端 API  http://127.0.0.1:8000/docs')
    console.log('  健康检查  http://127.0.0.1:8000/api/v1/health')
  }
  if (startFrontend) {
    console.log('  前端页面  http://localhost:5173')
  }
  console.log('  按 Ctrl+C 同时停止\n')

  if (startBackend) {
    startService(
      'backend',
      python,
      [
        '-m',
        'uvicorn',
        'app.main:app',
        '--reload',
        '--host',
        '127.0.0.1',
        '--port',
        '8000',
      ],
      backendDir,
    )
  }

  if (startFrontend) {
    // npm is a .cmd shim on Windows and requires a shell to be spawned.
    startService('frontend', npmCommand, ['run', 'dev'], frontendDir, {
      shell: isWindows,
    })
  }
}

main().catch((error) => {
  console.error(error)
  shutdown(1)
})
