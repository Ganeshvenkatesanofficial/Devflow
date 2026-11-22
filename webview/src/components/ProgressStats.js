import React, { useState, useEffect } from 'react';

function ProgressStats({ backendUrl }) {
  const [records, setRecords] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${backendUrl}/records`)
      .then(r => r.json())
      .then(data => { setRecords(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [backendUrl]);

  if (loading) {
    return (
      <div className="df-stats">
        <div className="df-stats-header"><h2>My Stats</h2></div>
        <div className="df-stats-empty"><span className="df-spinner" /></div>
      </div>
    );
  }

  const totalDone = records?.total_tickets_done || 0;
  const totalTimeSec = records?.total_time_spent || 0;
  const totalMins = Math.round(totalTimeSec / 60);
  const avgMins = totalDone > 0 ? Math.round(totalMins / totalDone) : 0;
  const streak = records?.streak || { current: 0, best: 0 };

  // Calculate "this week" — count tickets completed in the last 7 days
  const now = Date.now();
  const weekAgo = now - 7 * 24 * 60 * 60 * 1000;
  const thisWeek = (records?.completed_tickets || []).filter(t => {
    const d = new Date(t.date).getTime();
    return d >= weekAgo;
  }).length;

  const formatTime = (mins) => {
    if (mins < 60) return `${mins}m`;
    const h = Math.floor(mins / 60);
    const m = mins % 60;
    return m > 0 ? `${h}h ${m}m` : `${h}h`;
  };

  return (
    <div className="df-stats">
      <div className="df-stats-header">
        <h2>My Stats</h2>
      </div>

      {/* 4 stat cards */}
      <div className="df-stats-grid">
        <div className="df-stat-card">
          <div className="df-stat-icon done">{'✅'}</div>
          <span className="df-stat-value">{totalDone}</span>
          <span className="df-stat-label">Total Done</span>
        </div>
        <div className="df-stat-card">
          <div className="df-stat-icon week">{'📅'}</div>
          <span className="df-stat-value">{thisWeek}</span>
          <span className="df-stat-label">This Week</span>
        </div>
        <div className="df-stat-card">
          <div className="df-stat-icon time">{'⏱'}</div>
          <span className="df-stat-value">{totalMins > 0 ? formatTime(totalMins) : '—'}</span>
          <span className="df-stat-label">Total Time</span>
        </div>
        <div className="df-stat-card">
          <div className="df-stat-icon avg">{'⚡'}</div>
          <span className="df-stat-value">{avgMins > 0 ? `${avgMins}m` : '—'}</span>
          <span className="df-stat-label">Avg / Ticket</span>
        </div>
      </div>

      {/* Streak */}
      <div className="df-record-card">
        <h4>{'🔥'} Streak</h4>
        <div className="df-streak-row">
          <div>
            <span className="df-streak-num">{streak.current}</span>
            <span className="df-streak-label">Current</span>
          </div>
          <div>
            <span className="df-streak-num">{streak.best}</span>
            <span className="df-streak-label">Best</span>
          </div>
        </div>
      </div>

      {/* Fastest ticket */}
      {records?.fastest_ticket && (
        <div className="df-record-card">
          <h4>{'🏆'} Personal Best</h4>
          <div className="df-history-item">
            <span className="df-history-id">#{records.fastest_ticket.id}</span>
            <span className="df-history-title">{records.fastest_ticket.title}</span>
            <span className="df-history-time">{Math.round(records.fastest_ticket.time_spent / 60)}m</span>
          </div>
        </div>
      )}

      {/* Recent history */}
      {records?.completed_tickets?.length > 0 ? (
        <div className="df-record-card">
          <h4>{'📋'} Recent</h4>
          {records.completed_tickets.slice(0, 8).map((t, i) => (
            <div key={i} className="df-history-item">
              <span className="df-history-id">#{t.id}</span>
              <span className="df-history-title">{t.title}</span>
              <span className="df-history-time">{Math.round(t.time_spent / 60)}m</span>
            </div>
          ))}
        </div>
      ) : (
        <div className="df-stats-empty">
          <p>Complete your first ticket to see stats here!</p>
        </div>
      )}
    </div>
  );
}

export default ProgressStats;
