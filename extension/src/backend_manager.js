/**
 * BackendManager — owns the Python backend process lifecycle.
 * All runtime values (host, port, python path, log level, timeout) are
 * injected; nothing is hardcoded here.
 */

const { spawn } = require('child_process');
const path = require('path');
const http = require('http');
const fs = require('fs');

class BackendManager {
  /**
   * @param {object} opts
   * @param {string} opts.pythonPath   Python interpreter (may be 'python3')
   * @param {string} opts.host         Bind host for uvicorn
   * @param {number} opts.port         Bind port for uvicorn
   * @param {string} opts.extensionPath Absolute extension install path
   * @param {string} opts.logLevel     uvicorn log level
   * @param {number} opts.startupTimeoutMs Max time to wait for /health
   * @param {object} [opts.logger]     Logger with .info/.warn/.error
   */
  constructor(opts) {
    const {
      pythonPath, host, port, extensionPath,
      logLevel, startupTimeoutMs, logger = console,
    } = opts;
    this._pythonPath = pythonPath;
    this._host = host;
    this._port = port;
    this._extensionPath = extensionPath;
    this._logLevel = logLevel;
    this._startupTimeoutMs = startupTimeoutMs;
    this._log = logger;
    this._process = null;
  }

  get baseUrl() { return `http://${this._host}:${this._port}`; }

  _resolvePython() {
    if (this._pythonPath && this._pythonPath !== 'python3') return this._pythonPath;
    const venvPython = process.platform === 'win32'
      ? path.join(this._extensionPath, '.venv', 'Scripts', 'python.exe')
      : path.join(this._extensionPath, '.venv', 'bin', 'python');
    return fs.existsSync(venvPython) ? venvPython : this._pythonPath;
  }

  async start() {
    if (this._process) return;
    const pythonBin = this._resolvePython();
    this._log.info(`[DevFlow] python=${pythonBin} backend=${this.baseUrl}`);

    this._process = spawn(pythonBin, [
      '-m', 'uvicorn', 'backend.server:app',
      '--host', this._host,
      '--port', String(this._port),
      '--log-level', this._logLevel,
    ], {
      cwd: this._extensionPath,
      env: {
        ...process.env,
        PYTHONPATH: this._extensionPath,
        DEVFLOW_STORAGE: path.join(this._extensionPath, '.devflow', 'store.json'),
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    this._process.stdout.on('data', d => this._log.info(`[DevFlow] ${d}`));
    this._process.stderr.on('data', d => this._log.error(`[DevFlow] ${d}`));
    this._process.on('exit', code => {
      this._log.info(`[DevFlow] backend exited code=${code}`);
      this._process = null;
    });

    await this._waitForReady();
  }

  stop() {
    if (!this._process) return;
    this._process.kill('SIGTERM');
    this._process = null;
  }

  async _waitForReady() {
    const deadline = Date.now() + this._startupTimeoutMs;
    const intervalMs = 250;
    while (Date.now() < deadline) {
      if (await this._healthCheck()) return true;
      await new Promise(r => setTimeout(r, intervalMs));
    }
    this._log.warn('[DevFlow] backend did not pass health check in time');
    return false;
  }

  _healthCheck() {
    return new Promise(resolve => {
      const req = http.get(`${this.baseUrl}/health`, res => {
        res.resume();
        resolve(res.statusCode === 200);
      });
      req.on('error', () => resolve(false));
      req.setTimeout(1000, () => { req.destroy(); resolve(false); });
    });
  }
}

module.exports = BackendManager;
