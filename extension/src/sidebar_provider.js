/**
 * VS Code Webview provider — renders the React UI in the sidebar
 * and passes messages between webview and backend.
 */

const vscode = require('vscode');
const path = require('path');
const fs = require('fs');

class SidebarProvider {
  constructor(extensionUri, backendUrl) {
    this._extensionUri = extensionUri;
    this._backendUrl = backendUrl;
    this._view = null;
  }

  postMessage(msg) {
    if (this._view) this._view.webview.postMessage(msg);
  }

  resolveWebviewView(webviewView) {
    this._view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [
        vscode.Uri.joinPath(this._extensionUri, 'webview', 'build'),
      ],
    };

    webviewView.webview.html = this._getHtml(webviewView.webview);

    // Send initial config to webview
    setTimeout(() => {
      const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || null;
      webviewView.webview.postMessage({
        type: 'init',
        backendUrl: this._backendUrl,
        workspacePath,
      });
    }, 500);

    // Handle messages from webview
    webviewView.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.type) {
        case 'runCommand': {
          vscode.commands.executeCommand('devflow.runCommand', msg.command);
          break;
        }

        case 'copyToClipboard': {
          vscode.env.clipboard.writeText(msg.text);
          vscode.window.showInformationMessage('Copied to clipboard!');
          break;
        }

        case 'saveFile': {
          const uri = await vscode.window.showSaveDialog({
            defaultUri: vscode.Uri.file(msg.defaultName || 'devflow-runbook.md'),
            filters: { Markdown: ['md'] },
          });
          if (uri) {
            fs.writeFileSync(uri.fsPath, msg.content);
            const action = await vscode.window.showInformationMessage(
              'Runbook exported!', 'Open File'
            );
            if (action === 'Open File') {
              const doc = await vscode.workspace.openTextDocument(uri);
              vscode.window.showTextDocument(doc);
            }
          }
          break;
        }

        case 'notify': {
          if (msg.level === 'error') {
            vscode.window.showErrorMessage(`DevFlow: ${msg.message}`);
          } else {
            vscode.window.showInformationMessage(`DevFlow: ${msg.message}`);
          }
          break;
        }
      }
    });
  }

  _getHtml(webview) {
    const buildPath = vscode.Uri.joinPath(this._extensionUri, 'webview', 'build');
    const indexPath = path.join(buildPath.fsPath, 'index.html');

    if (!fs.existsSync(indexPath)) {
      return `<html><body style="color:white;padding:20px;font-family:sans-serif;">
        <h2>DevFlow — Webview Not Built</h2>
        <p>Run: <code>cd webview && npm install && npm run build</code></p>
      </body></html>`;
    }

    const webviewUri = webview.asWebviewUri(buildPath);
    const nonce = Math.random().toString(36).slice(2);

    let html = fs.readFileSync(indexPath, 'utf8');
    html = html.replace(/(src|href)="\.\/static\//g, `$1="${webviewUri}/static/`);
    html = html.replace(/(src|href)="\/static\//g, `$1="${webviewUri}/static/`);

    const csp = [
      `default-src 'none'`,
      `style-src 'unsafe-inline' ${webview.cspSource}`,
      `script-src 'nonce-${nonce}' ${webview.cspSource}`,
      `connect-src ${this._backendUrl}`,
      `img-src ${webview.cspSource} data:`,
      `font-src ${webview.cspSource}`,
    ].join('; ');

    html = html.replace('<head>',
      `<head><meta http-equiv="Content-Security-Policy" content="${csp}">`
    );
    html = html.replace(/<script /g, `<script nonce="${nonce}" `);

    return html;
  }
}

module.exports = SidebarProvider;
