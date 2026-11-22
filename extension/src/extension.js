/**
 * DevFlow VS Code Extension entrypoint.
 *
 * Thin shell: reads config, boots the Python backend, mounts the webview,
 * registers commands. All business logic lives in Python.
 */

const vscode = require('vscode');

const { Config } = require('./config');
const BackendManager = require('./backend_manager');
const SidebarProvider = require('./sidebar_provider');
const Commands = require('./commands');

class DevFlowExtension {
  constructor(context) {
    this._context = context;
    this._config = new Config();
    this._backend = new BackendManager({
      pythonPath: this._config.pythonPath,
      host: this._config.backendHost,
      port: this._config.backendPort,
      extensionPath: context.extensionPath,
      logLevel: this._config.logLevel,
      startupTimeoutMs: this._config.startupTimeoutMs,
    });
    this._provider = new SidebarProvider(
      context.extensionUri,
      this._backend.baseUrl,
    );
    this._commands = new Commands({
      backend: this._backend,
      provider: this._provider,
    });
  }

  async activate() {
    await this._backend.start();

    this._context.subscriptions.push(
      vscode.window.registerWebviewViewProvider('devflow.mainView', this._provider, {
        webviewOptions: { retainContextWhenHidden: true },
      }),
      ...this._commands.register(),
      this._makeStatusBar(),
    );
  }

  deactivate() { this._backend.stop(); }

  _makeStatusBar() {
    const item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    item.text = '$(rocket) DevFlow';
    item.tooltip = 'Open DevFlow';
    item.command = 'devflow.open';
    item.show();
    return item;
  }
}

let instance = null;

async function activate(context) {
  instance = new DevFlowExtension(context);
  await instance.activate();
}

function deactivate() {
  if (instance) instance.deactivate();
  instance = null;
}

module.exports = { activate, deactivate, DevFlowExtension };
