/**
 * Commands — all VS Code command handlers, in one place.
 * No hardcoded URLs; everything routes through BackendManager.baseUrl.
 */

const vscode = require('vscode');

class Commands {
  constructor({ backend, provider }) {
    this._backend = backend;
    this._provider = provider;
  }

  register() {
    return [
      vscode.commands.registerCommand('devflow.open', () => this._open()),
      vscode.commands.registerCommand('devflow.clearStorage', () => this._clear()),
      vscode.commands.registerCommand('devflow.runCommand', (cmd) => this._runInTerminal(cmd)),
    ];
  }

  _open() {
    return vscode.commands.executeCommand('workbench.view.extension.devflow-sidebar');
  }

  async _clear() {
    try {
      await fetch(`${this._backend.baseUrl}/clear`, { method: 'POST' });
      vscode.window.showInformationMessage('DevFlow: all data cleared.');
      this._provider.postMessage({ type: 'init', config: null, records: null });
    } catch (e) {
      vscode.window.showErrorMessage(`DevFlow: failed to clear data — ${e.message || e}`);
    }
  }

  _runInTerminal(command) {
    if (!command) return;
    const name = 'DevFlow';
    let terminal = vscode.window.terminals.find(t => t.name === name);
    if (!terminal) terminal = vscode.window.createTerminal(name);
    terminal.show(true);
    terminal.sendText(command);
  }
}

module.exports = Commands;
