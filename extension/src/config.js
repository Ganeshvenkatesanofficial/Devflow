/**
 * Config — single source of truth for extension settings.
 * All values come from the user's VS Code configuration; no literals
 * are kept here except the setting key namespace.
 */

const vscode = require('vscode');

const NAMESPACE = 'devflow';

class Config {
  constructor(workspace = vscode.workspace) {
    this._workspace = workspace;
  }

  _raw() { return this._workspace.getConfiguration(NAMESPACE); }

  get pythonPath()        { return this._raw().get('pythonPath'); }
  get backendPort()       { return this._raw().get('backendPort'); }
  get backendHost()       { return this._raw().get('backendHost'); }
  get startupTimeoutMs()  { return this._raw().get('startupTimeoutMs'); }
  get logLevel()          { return this._raw().get('logLevel'); }

  toJSON() {
    return {
      pythonPath: this.pythonPath,
      backendHost: this.backendHost,
      backendPort: this.backendPort,
      startupTimeoutMs: this.startupTimeoutMs,
      logLevel: this.logLevel,
    };
  }
}

module.exports = { Config, NAMESPACE };
