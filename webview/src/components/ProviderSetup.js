import React, { useState, useEffect } from 'react';

function ProviderSetup({ onFetch, loading, backendUrl }) {
  const [provider, setProvider] = useState('jira');
  const [ticketId, setTicketId] = useState('');
  const [aiProvider, setAiProvider] = useState('ollama');
  const [validation, setValidation] = useState(null);

  const [jiraUrl, setJiraUrl] = useState('');
  const [jiraEmail, setJiraEmail] = useState('');
  const [jiraToken, setJiraToken] = useState('');
  const [azureOrgUrl, setAzureOrgUrl] = useState('');
  const [azureProject, setAzureProject] = useState('');
  const [azurePat, setAzurePat] = useState('');
  const [githubToken, setGithubToken] = useState('');
  const [githubOwner, setGithubOwner] = useState('');
  const [githubRepo, setGithubRepo] = useState('');
  const [openaiKey, setOpenaiKey] = useState('');
  const [openaiModel, setOpenaiModel] = useState('gpt-4o');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [anthropicModel, setAnthropicModel] = useState('claude-3-5-sonnet-20241022');
  const [geminiKey, setGeminiKey] = useState('');
  const [geminiModel, setGeminiModel] = useState('gemini-2.5-flash');
  const [ollamaModel, setOllamaModel] = useState('llama3.1');
  const [ollamaOnline, setOllamaOnline] = useState(false);
  const [ollamaModels, setOllamaModels] = useState([]);
  const [ollamaLoading, setOllamaLoading] = useState(false);

  // Load saved credentials & preferences from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem('devflow_config');
      if (saved) {
        const c = JSON.parse(saved);
        if (c.provider) setProvider(c.provider);
        if (c.aiProvider) setAiProvider(c.aiProvider);
        if (c.jiraUrl) setJiraUrl(c.jiraUrl);
        if (c.jiraEmail) setJiraEmail(c.jiraEmail);
        if (c.jiraToken) setJiraToken(c.jiraToken);
        if (c.azureOrgUrl) setAzureOrgUrl(c.azureOrgUrl);
        if (c.azureProject) setAzureProject(c.azureProject);
        if (c.azurePat) setAzurePat(c.azurePat);
        if (c.githubToken) setGithubToken(c.githubToken);
        if (c.githubOwner) setGithubOwner(c.githubOwner);
        if (c.githubRepo) setGithubRepo(c.githubRepo);
        if (c.openaiKey) setOpenaiKey(c.openaiKey);
        if (c.openaiModel) setOpenaiModel(c.openaiModel);
        if (c.anthropicKey) setAnthropicKey(c.anthropicKey);
        if (c.anthropicModel) setAnthropicModel(c.anthropicModel);
        if (c.geminiKey) setGeminiKey(c.geminiKey);
        if (c.geminiModel) setGeminiModel(c.geminiModel);
        if (c.ollamaModel) setOllamaModel(c.ollamaModel);
      }
    } catch {}
  }, []);

  // Persist configuration to localStorage whenever it changes
  useEffect(() => {
    try {
      const toSave = {
        provider, aiProvider,
        jiraUrl, jiraEmail, jiraToken,
        azureOrgUrl, azureProject, azurePat,
        githubToken, githubOwner, githubRepo,
        openaiKey, openaiModel,
        anthropicKey, anthropicModel,
        geminiKey, geminiModel,
        ollamaModel,
      };
      localStorage.setItem('devflow_config', JSON.stringify(toSave));
    } catch {}
  }, [
    provider, aiProvider,
    jiraUrl, jiraEmail, jiraToken,
    azureOrgUrl, azureProject, azurePat,
    githubToken, githubOwner, githubRepo,
    openaiKey, openaiModel,
    anthropicKey, anthropicModel,
    geminiKey, geminiModel,
    ollamaModel,
  ]);

  // Check Ollama status on 11434 and fetch local models
  const checkOllama = async () => {
    setOllamaLoading(true);
    const url = backendUrl || 'http://127.0.0.1:9120';
    try {
      const resp = await fetch(`${url}/ollama/models`);
      if (resp.ok) {
        const data = await resp.json();
        setOllamaOnline(!!data.online);
        if (data.models && data.models.length > 0) {
          setOllamaModels(data.models);
          // If current model is default or empty, select the first detected local model
          if (!ollamaModel || ollamaModel === 'llama3.1') {
            setOllamaModel(data.models[0]);
          }
        } else {
          setOllamaModels([]);
        }
      } else {
        setOllamaOnline(false);
      }
    } catch {
      setOllamaOnline(false);
    } finally {
      setOllamaLoading(false);
    }
  };

  useEffect(() => {
    checkOllama();
  }, [backendUrl]);

  const getProviderConfig = () => {
    const base = { provider };
    if (provider === 'jira') return { ...base, jira_url: jiraUrl, jira_email: jiraEmail, jira_token: jiraToken };
    if (provider === 'azure') return { ...base, azure_org_url: azureOrgUrl, azure_project: azureProject, azure_pat: azurePat };
    if (provider === 'github') return { ...base, github_token: githubToken, github_owner: githubOwner, github_repo: githubRepo };
    return base;
  };

  const getAIConfig = () => {
    const base = { ai_provider: aiProvider };
    if (aiProvider === 'gemini') return { ...base, gemini_api_key: geminiKey, gemini_model: geminiModel.trim() || 'gemini-2.5-flash' };
    if (aiProvider === 'openai') return { ...base, openai_api_key: openaiKey, openai_model: openaiModel.trim() || 'gpt-4o' };
    if (aiProvider === 'anthropic') return { ...base, anthropic_api_key: anthropicKey, anthropic_model: anthropicModel.trim() || 'claude-3-5-sonnet-20241022' };
    if (aiProvider === 'ollama') return { ...base, ollama_model: ollamaModel.trim() || 'llama3.1' };
    return base;
  };

  const handleValidate = async () => {
    setValidation('checking');
    try {
      const resp = await fetch(`${backendUrl}/provider/validate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(getProviderConfig()),
      });
      const data = await resp.json();
      setValidation(data.valid ? 'valid' : 'invalid');
    } catch {
      setValidation('invalid');
    }
  };

  const handleFetch = () => {
    if (!ticketId.trim()) return;
    onFetch(ticketId.trim(), getProviderConfig(), getAIConfig());
  };

  return (
    <div className="df-setup">
      <p className="df-section-title">Ticket Source</p>
      <div className="df-provider-selector">
        {[
          { key: 'jira', label: 'Jira' },
          { key: 'azure', label: 'Azure\nDevOps' },
          { key: 'github', label: 'GitHub' },
        ].map(p => (
          <button key={p.key}
            className={`df-provider-btn ${provider === p.key ? 'active' : ''}`}
            onClick={() => { setProvider(p.key); setValidation(null); }}
            style={{ whiteSpace: 'pre-line' }}
          >{p.label}</button>
        ))}
      </div>

      <div className="df-field-group">
        {provider === 'jira' && <>
          <input className="df-input" placeholder="Jira URL" value={jiraUrl} onChange={e => setJiraUrl(e.target.value)} />
          <input className="df-input" placeholder="Email" value={jiraEmail} onChange={e => setJiraEmail(e.target.value)} />
          <input className="df-input" type="password" placeholder="API Token" value={jiraToken} onChange={e => setJiraToken(e.target.value)} />
        </>}
        {provider === 'azure' && <>
          <input className="df-input" placeholder="Organization URL" value={azureOrgUrl} onChange={e => setAzureOrgUrl(e.target.value)} />
          <input className="df-input" placeholder="Project Name" value={azureProject} onChange={e => setAzureProject(e.target.value)} />
          <input className="df-input" type="password" placeholder="Personal Access Token" value={azurePat} onChange={e => setAzurePat(e.target.value)} />
        </>}
        {provider === 'github' && <>
          <input className="df-input" type="password" placeholder="GitHub Token" value={githubToken} onChange={e => setGithubToken(e.target.value)} />
          <input className="df-input" placeholder="Owner" value={githubOwner} onChange={e => setGithubOwner(e.target.value)} />
          <input className="df-input" placeholder="Repository" value={githubRepo} onChange={e => setGithubRepo(e.target.value)} />
        </>}
      </div>

      {validation && (
        <div className={`df-connection-status ${validation}`}>
          {validation === 'checking' && <><span className="df-spinner" /> Verifying...</>}
          {validation === 'valid' && '✓ Connected'}
          {validation === 'invalid' && '✗ Failed — check credentials'}
        </div>
      )}

      <button className="df-btn df-btn-secondary df-btn-sm" onClick={handleValidate} style={{ width: '100%', marginBottom: 4 }}>
        Test Connection
      </button>

      <div className="df-divider" />

      <p className="df-section-title">AI Engine</p>
      <div className="df-provider-selector">
        {[
          { key: 'ollama', title: 'Ollama', subtitle: ollamaModel || '(Local)' },
          { key: 'gemini', title: 'Gemini', subtitle: geminiModel || '2.5 Flash' },
          { key: 'openai', title: 'OpenAI', subtitle: openaiModel || 'GPT-4o' },
          { key: 'anthropic', title: 'Claude', subtitle: anthropicModel || 'Sonnet' },
        ].map(p => (
          <button key={p.key}
            className={`df-provider-btn ${aiProvider === p.key ? 'active' : ''}`}
            onClick={() => {
              setAiProvider(p.key);
              if (p.key === 'ollama') checkOllama();
            }}
          >
            <div className="df-provider-btn-title">{p.title}</div>
            <div className="df-provider-btn-sub" title={p.subtitle}>{p.subtitle}</div>
          </button>
        ))}
      </div>

      <div className="df-field-group">
        {aiProvider === 'gemini' && <>
          <input
            className="df-input"
            type="password"
            placeholder="Google Gemini API Key"
            value={geminiKey}
            onChange={e => setGeminiKey(e.target.value)}
          />
          <input
            className="df-input"
            placeholder="Model (e.g. gemini-2.5-flash, gemini-2.5-pro)"
            value={geminiModel}
            onChange={e => setGeminiModel(e.target.value)}
          />
          <p className="df-hint">Enter any Gemini model name. It is passed directly to the engine.</p>
        </>}

        {aiProvider === 'openai' && <>
          <input className="df-input" type="password" placeholder="OpenAI API Key" value={openaiKey} onChange={e => setOpenaiKey(e.target.value)} />
          <input className="df-input" placeholder="Model (default: gpt-4o)" value={openaiModel} onChange={e => setOpenaiModel(e.target.value)} />
          <p className="df-hint">Supports gpt-4o, gpt-4o-mini, o1, or any custom OpenAI model</p>
        </>}

        {aiProvider === 'anthropic' && <>
          <input className="df-input" type="password" placeholder="Anthropic API Key" value={anthropicKey} onChange={e => setAnthropicKey(e.target.value)} />
          <input className="df-input" placeholder="Model (default: claude-3-5-sonnet-20241022)" value={anthropicModel} onChange={e => setAnthropicModel(e.target.value)} />
          <p className="df-hint">Supports claude-3-5-sonnet-20241022, claude-3-5-haiku-20241022, etc.</p>
        </>}

        {aiProvider === 'ollama' && <>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 2 }}>
            <span style={{ fontSize: 11, display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{
                display: 'inline-block',
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: ollamaOnline ? 'var(--df-success, #3dd68c)' : 'var(--df-error, #f06c6c)',
                boxShadow: ollamaOnline ? '0 0 6px rgba(61, 214, 140, 0.6)' : 'none',
              }} />
              <strong style={{ color: ollamaOnline ? 'var(--df-success, #3dd68c)' : 'var(--df-text-muted, #8b8d94)' }}>
                {ollamaLoading ? 'Checking...' : ollamaOnline ? 'Ollama Online (11434)' : 'Ollama Offline'}
              </strong>
            </span>
            <button
              className="df-btn df-btn-secondary"
              style={{ padding: '2px 8px', fontSize: 10 }}
              onClick={checkOllama}
              type="button"
              title="Refresh local models"
            >
              {ollamaLoading ? '...' : '⟳ Refresh'}
            </button>
          </div>

          {ollamaOnline && ollamaModels.length > 0 ? (
            <>
              <select
                className="df-input"
                value={ollamaModels.includes(ollamaModel) ? ollamaModel : '__custom__'}
                onChange={e => {
                  if (e.target.value !== '__custom__') {
                    setOllamaModel(e.target.value);
                  }
                }}
                style={{ cursor: 'pointer', marginBottom: (!ollamaModels.includes(ollamaModel) || ollamaModel === '') ? 6 : 0 }}
              >
                {ollamaModels.map(m => (
                  <option key={m} value={m}>{m}</option>
                ))}
                <option value="__custom__">Custom model name...</option>
              </select>
              {(!ollamaModels.includes(ollamaModel) || ollamaModel === '') && (
                <input
                  className="df-input"
                  placeholder="Enter model name (e.g. mistral, codellama)"
                  value={ollamaModel}
                  onChange={e => setOllamaModel(e.target.value)}
                />
              )}
            </>
          ) : (
            <input
              className="df-input"
              placeholder="Model (e.g. llama3.1)"
              value={ollamaModel}
              onChange={e => setOllamaModel(e.target.value)}
            />
          )}

          <p className="df-hint">
            {ollamaOnline
              ? (ollamaModels.length > 0
                  ? `Detected ${ollamaModels.length} local model${ollamaModels.length > 1 ? 's' : ''}`
                  : 'Ollama is online. Pull a model with: ollama pull llama3.1')
              : 'Ollama is not running on localhost:11434. Start Ollama to detect models.'}
          </p>
        </>}
      </div>

      <div className="df-divider" />

      <p className="df-section-title">Generate Runbook</p>
      <div className="df-fetch-row">
        <input
          className="df-input"
          placeholder={provider === 'jira' ? 'e.g. PROJ-123' : provider === 'azure' ? 'e.g. 456' : 'e.g. 78'}
          value={ticketId}
          onChange={e => setTicketId(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleFetch()}
        />
        <button className="df-btn df-btn-primary" onClick={handleFetch} disabled={loading || !ticketId.trim()}>
          {loading ? <span className="df-spinner" /> : 'Go'}
        </button>
      </div>
    </div>
  );
}

export default ProviderSetup;
