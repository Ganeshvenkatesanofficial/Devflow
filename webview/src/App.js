import React, { useState, useEffect } from 'react';
import ProviderSetup from './components/ProviderSetup';
import RunbookPanel from './components/RunbookPanel';
import ProgressStats from './components/ProgressStats';
import './App.css';

const vscode = typeof acquireVsCodeApi === 'function' ? acquireVsCodeApi() : null;

function App() {
  const [activeTab, setActiveTab] = useState('connect'); // connect | runbook | stats
  const [backendUrl, setBackendUrl] = useState('http://127.0.0.1:9120');
  const [workspacePath, setWorkspacePath] = useState(null);
  const [ticket, setTicket] = useState(null);
  const [steps, setSteps] = useState([]);
  const [aiConfig, setAiConfig] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking'); // checking | online | offline

  // Listen for VS Code messages
  useEffect(() => {
    const handler = (event) => {
      const msg = event.data;
      if (msg.type === 'init') {
        if (msg.backendUrl) setBackendUrl(msg.backendUrl);
        if (msg.workspacePath) setWorkspacePath(msg.workspacePath);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  // Health check
  useEffect(() => {
    const check = async () => {
      try {
        const r = await fetch(`${backendUrl}/health`);
        setBackendStatus(r.ok ? 'online' : 'offline');
      } catch { setBackendStatus('offline'); }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  const fetchTicket = async (ticketId, providerConfig, aiConfigParam) => {
    setLoading(true);
    setError(null);
    setAiConfig(aiConfigParam);
    try {
      const resp = await fetch(`${backendUrl}/ticket/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticket_id: ticketId,
          provider_config: providerConfig,
          ai_config: aiConfigParam,
          workspace_path: workspacePath,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Failed to fetch ticket');
      }
      const data = await resp.json();
      setTicket(data.ticket);
      setSteps(data.steps);
      setActiveTab('runbook');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const saveSteps = async (updatedSteps) => {
    setSteps(updatedSteps);
    if (ticket) {
      try {
        await fetch(`${backendUrl}/ticket/save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ticket_id: ticket.id, steps: updatedSteps }),
        });
      } catch (_) {}
    }
  };

  const runCommand = (cmd) => vscode?.postMessage({ type: 'runCommand', command: cmd });
  const copyToClipboard = (text) => vscode ? vscode.postMessage({ type: 'copyToClipboard', text }) : navigator.clipboard.writeText(text);
  const saveFile = (content, name) => vscode?.postMessage({ type: 'saveFile', content, defaultName: name });

  return (
    <div className="df-app">
      {/* Bottom tab bar — always visible */}
      <nav className="df-tabbar">
        <button className={`df-tab ${activeTab === 'connect' ? 'active' : ''}`} onClick={() => setActiveTab('connect')}>
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 2a3 3 0 00-3 3v1H5a2 2 0 00-2 2v8a2 2 0 002 2h10a2 2 0 002-2V8a2 2 0 00-2-2h-2V5a3 3 0 00-3-3zm-1 3a1 1 0 112 0v1H9V5zm1 6a1.5 1.5 0 110 3 1.5 1.5 0 010-3z"/></svg>
          <span>Connect</span>
        </button>
        <button className={`df-tab ${activeTab === 'runbook' ? 'active' : ''} ${!ticket ? 'disabled' : ''}`} onClick={() => ticket && setActiveTab('runbook')}>
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z"/></svg>
          <span>Runbook</span>
          {ticket && steps.length > 0 && (
            <span className="df-tab-badge">
              {steps.filter(s => s.isCompleted && !s.isGitStep).length}/{steps.filter(s => !s.isGitStep).length}
            </span>
          )}
        </button>
        <button className={`df-tab ${activeTab === 'stats' ? 'active' : ''}`} onClick={() => setActiveTab('stats')}>
          <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zm6-4a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zm6-3a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z"/></svg>
          <span>Stats</span>
        </button>
      </nav>

      {/* Status indicator */}
      <div className="df-status-bar">
        <span className={`df-status-dot ${backendStatus}`} />
        <span className="df-status-text">
          {backendStatus === 'online' ? 'Engine ready' : backendStatus === 'checking' ? 'Connecting...' : 'Engine offline'}
        </span>
        {ticket && <span className="df-active-ticket">#{ticket.id}</span>}
      </div>

      {/* Error */}
      {error && (
        <div className="df-error">
          <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/></svg>
          <span>{error}</span>
          <button onClick={() => setError(null)}>dismiss</button>
        </div>
      )}

      {/* Content */}
      <main className="df-content">
        {activeTab === 'connect' && (
          <ProviderSetup onFetch={fetchTicket} loading={loading} backendUrl={backendUrl} />
        )}
        {activeTab === 'runbook' && ticket && (
          <RunbookPanel ticket={ticket} steps={steps} onStepsChange={saveSteps}
            onRunCommand={runCommand} onCopy={copyToClipboard} onSaveFile={saveFile} backendUrl={backendUrl} aiConfig={aiConfig} />
        )}
        {activeTab === 'runbook' && !ticket && (
          <div className="df-empty-state">
            <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" strokeWidth="1.5">
              <rect x="8" y="6" width="32" height="36" rx="3" />
              <line x1="16" y1="16" x2="32" y2="16" /><line x1="16" y1="22" x2="28" y2="22" />
              <line x1="16" y1="28" x2="24" y2="28" />
            </svg>
            <h3>No active runbook</h3>
            <p>Go to <strong>Connect</strong> tab, link your ticket provider and generate your first runbook.</p>
          </div>
        )}
        {activeTab === 'stats' && (
          <ProgressStats backendUrl={backendUrl} />
        )}
      </main>
    </div>
  );
}

export default App;
