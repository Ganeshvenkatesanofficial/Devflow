import React, { useState } from 'react';
import ImplementationStep from './ImplementationStep';

function RunbookPanel({ ticket, steps, onStepsChange, onRunCommand, onCopy, onSaveFile, backendUrl, aiConfig }) {
  const [prText, setPrText] = useState('');
  const [prLoading, setPrLoading] = useState(false);

  const userSteps = steps.filter(s => !s.isGitStep);
  const completedCount = userSteps.filter(s => s.isCompleted).length;
  const progress = userSteps.length > 0 ? Math.round((completedCount / userSteps.length) * 100) : 0;

  const toggleStep = (stepId) => {
    onStepsChange(steps.map(s => s.id === stepId ? { ...s, isCompleted: !s.isCompleted } : s));
  };

  const handleExportMarkdown = async () => {
    try {
      const resp = await fetch(`${backendUrl}/export/markdown`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticket_id: ticket.id, steps }),
      });
      const data = await resp.json();
      onSaveFile(data.markdown, `DevFlow-${ticket.id}.md`);
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  const handleGeneratePR = async () => {
    setPrLoading(true);
    try {
      // Determine effective AI config dynamically from props or saved preferences
      let effectiveAI = aiConfig;
      if (!effectiveAI) {
        try {
          const saved = localStorage.getItem('devflow_config');
          if (saved) {
            const c = JSON.parse(saved);
            const p = c.aiProvider || 'ollama';
            const base = { ai_provider: p };
            if (p === 'gemini') effectiveAI = { ...base, gemini_api_key: c.geminiKey, gemini_model: c.geminiModel || 'gemini-2.5-flash' };
            else if (p === 'openai') effectiveAI = { ...base, openai_api_key: c.openaiKey, openai_model: c.openaiModel || 'gpt-4o' };
            else if (p === 'anthropic') effectiveAI = { ...base, anthropic_api_key: c.anthropicKey, anthropic_model: c.anthropicModel || 'claude-3-5-sonnet-20241022' };
            else if (p === 'ollama') effectiveAI = { ...base, ollama_model: c.ollamaModel || 'llama3.1' };
          }
        } catch (_) {}
      }
      if (!effectiveAI) {
        effectiveAI = { ai_provider: 'ollama', ollama_model: 'llama3.1' };
      }

      const resp = await fetch(`${backendUrl}/export/pr`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticket_id: ticket.id, ticket_title: ticket.title,
          ticket_type: ticket.type || 'Task', steps,
          ai_config: effectiveAI,
        }),
      });
      const data = await resp.json();
      setPrText(data.description);
    } catch (e) {
      console.error('PR generation failed:', e);
    } finally {
      setPrLoading(false);
    }
  };

  return (
    <div className="df-runbook">
      {/* Ticket card */}
      <div className="df-ticket-card">
        <div className="df-ticket-meta">
          <span className="df-ticket-type">{ticket.type}</span>
          <span className="df-ticket-id">#{ticket.id}</span>
          <span className="df-ticket-status">{ticket.status}</span>
        </div>
        <h2 className="df-ticket-title">{ticket.title}</h2>
      </div>

      {/* Progress */}
      <div className="df-progress-section">
        <div className="df-progress-track">
          <div className="df-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="df-progress-label">
          <span>{completedCount} of {userSteps.length} steps</span>
          <span className="df-progress-pct">{progress}%</span>
        </div>
      </div>

      {/* Steps */}
      <p className="df-section-title">Implementation Steps</p>
      <div className="df-steps">
        {steps.map(step => (
          <ImplementationStep key={step.id} step={step}
            onToggle={() => toggleStep(step.id)} onRunCommand={onRunCommand} />
        ))}
      </div>

      {/* Actions */}
      <div className="df-actions">
        <button className="df-btn df-btn-secondary df-btn-sm" onClick={handleExportMarkdown}>
          Export .md
        </button>
        <button className="df-btn df-btn-secondary df-btn-sm" onClick={handleGeneratePR} disabled={prLoading}>
          {prLoading ? <><span className="df-spinner" /> Generating...</> : 'Generate PR'}
        </button>
      </div>

      {/* PR output */}
      {prText && (
        <div className="df-pr-output">
          <div className="df-pr-header">
            <h3>PR Description</h3>
            <button className="df-btn df-btn-ghost df-btn-sm" onClick={() => onCopy(prText)}>Copy</button>
          </div>
          <pre className="df-pr-body">{prText}</pre>
        </div>
      )}
    </div>
  );
}

export default RunbookPanel;
