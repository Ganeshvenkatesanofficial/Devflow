import React, { useState, useEffect, useRef } from 'react';

function ImplementationStep({ step, onToggle, onRunCommand }) {
  const [timerRunning, setTimerRunning] = useState(false);
  const [elapsed, setElapsed] = useState(step.timeSpentSeconds || 0);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (timerRunning) {
      intervalRef.current = setInterval(() => setElapsed(prev => prev + 1), 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [timerRunning]);

  const formatTime = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  const cls = ['df-step', step.isCompleted ? 'completed' : '', step.isGitStep ? 'git' : ''].filter(Boolean).join(' ');

  return (
    <div className={cls}>
      <div className="df-step-row">
        <button className={`df-check ${step.isCompleted ? 'done' : ''}`} onClick={onToggle}>
          {step.isCompleted ? '✓' : ''}
        </button>
        <div className="df-step-body">
          <span className="df-step-title">{step.title}</span>
          {step.description && <span className="df-step-desc">{step.description}</span>}
        </div>
        <div className="df-step-timer">
          <span className="df-timer-display">{formatTime(elapsed)}</span>
          <button className={`df-timer-btn ${timerRunning ? 'running' : ''}`} onClick={() => setTimerRunning(!timerRunning)}>
            {timerRunning ? '⏸' : '▶'}
          </button>
        </div>
      </div>
      {step.commands && step.commands.length > 0 && (
        <div className="df-commands">
          {step.commands.map((cmd, i) => (
            <button key={i} className="df-cmd" onClick={() => onRunCommand(cmd)} title={`Run: ${cmd}`}>
              <span className="df-cmd-prefix">$</span> {cmd}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default ImplementationStep;
