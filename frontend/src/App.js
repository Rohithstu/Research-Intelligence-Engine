import React, { useState, useEffect, useRef, useMemo } from 'react';
import './App.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/^http/, 'ws');

// ─── SVG Components ───

const ChartSVG = () => (
  <svg viewBox="0 0 400 150" className="trend-graph">
    <path d="M0,130 Q50,110 80,120 T150,90 T220,100 T280,60 T350,70 T400,30" fill="none" stroke="var(--accent-purple)" strokeWidth="4" />
    <circle cx="80" cy="120" r="5" fill="#fff" />
    <circle cx="280" cy="60" r="5" fill="#fff" />
    <path d="M0,150 L0,130 Q50,110 80,120 T150,90 T220,100 T280,60 T350,70 T400,30 L400,150 Z" fill="url(#glossGrad)" opacity="0.1" />
    <defs>
      <linearGradient id="glossGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="var(--accent-purple)" />
        <stop offset="100%" stopColor="transparent" />
      </linearGradient>
    </defs>
  </svg>
);

// ─── Main Application ───

const INITIAL_STEPS = [
  { state: 'refining', label: 'Refining' },
  { state: 'fetching', label: 'Aggregation' },
  { state: 'embedding', label: 'Encoding' },
  { state: 'searching', label: 'Discovery' },
  { state: 'ranking', label: 'Intelligence' },
  { state: 'analyzing', label: 'Synthesis' },
];

export default function App() {
  const [view, setView] = useState('Home');
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [currentStep, setCurrentStep] = useState(null);
  const [steps, setSteps] = useState(INITIAL_STEPS);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [library, setLibrary] = useState([]);
  const [isDarkMode, setIsDarkMode] = useState(true);
  
  const [filters, setFilters] = useState({
    accessType: 'All',
    yearFrom: 2010,
    yearTo: 2024,
    minCitations: 0,
    sourceType: 'All Sources',
    hasCode: false,
    isSurvey: false,
    isPeerReviewed: false,
    isTrending: false
  });

  const ws = useRef(null);

  useEffect(() => {
    document.body.className = isDarkMode ? 'dark-theme' : 'light-theme';
  }, [isDarkMode]);

  useEffect(() => {
    fetchLibrary();
    connectWS();
    return () => ws.current?.close();
  }, []);

  const connectWS = () => {
    ws.current = new WebSocket(`${WS_BASE}/ws/progress`);
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setCurrentStep(data.state);
      setSteps(prev => prev.map(s => {
        if (s.state === data.state) return { ...s, complete: false };
        const stepIdx = INITIAL_STEPS.findIndex(is => is.state === s.state);
        const currIdx = INITIAL_STEPS.findIndex(is => is.state === data.state);
        if (stepIdx < currIdx) return { ...s, complete: true };
        return s;
      }));
    };
    ws.current.onclose = () => setTimeout(connectWS, 2000);
  };

  const fetchLibrary = async () => {
    try {
      const res = await fetch(`${API_BASE}/library`);
      if (res.ok) {
        const data = await res.json();
        setLibrary(data);
      }
    } catch (err) { console.error("Library fetch failed:", err); }
  };

  const handleSave = async (paper) => {
    try {
      await fetch(`${API_BASE}/library`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(paper),
      });
      fetchLibrary();
    } catch (err) { console.error(err); }
  };

  const handleRemove = async (paperId) => {
    try {
      await fetch(`${API_BASE}/library/${paperId}`, { method: 'DELETE' });
      fetchLibrary();
    } catch (err) { console.error(err); }
  };

  const handleSearch = async () => {
    if (!query.trim()) return;
    setView('Search');
    setLoading(true);
    setResult(null);
    setSteps(INITIAL_STEPS);

    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, max_results: 60 }),
      });
      const data = await response.json();
      setResult(data);
    } catch (err) { console.error(err); } finally { setLoading(false); }
  };

  const filteredPapers = useMemo(() => {
    if (!result) return [];
    return result.papers.filter(p => {
      if (filters.accessType !== 'All' && p.access_type.toLowerCase() !== filters.accessType.toLowerCase().replace(' ', '')) return false;
      if (p.year && (p.year < filters.yearFrom || p.year > filters.yearTo)) return false;
      if (p.citation_count < filters.minCitations) return false;
      if (filters.sourceType !== 'All Sources' && p.source.toLowerCase().replace('_', ' ') !== filters.sourceType.toLowerCase()) return false;
      return true;
    });
  }, [result, filters]);

  const isSaved = (id) => library.some(p => p.id === id);

  const PaperCard = ({ paper, onSave, onRemove, saved }) => (
    <div className="paper-card-new">
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'start'}}>
        <h3 className="card-title" style={{maxWidth:'80%'}}>{paper.title}</h3>
        <span className={`access-badge ${paper.access_type}`}>{paper.access_type.toUpperCase()}</span>
      </div>
      <div className="card-authors" style={{ fontSize: '0.9rem', margin: '10px 0', opacity: 0.7 }}>{paper.authors.slice(0,3).join(', ')}</div>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, opacity: 0.5, marginBottom: 20 }}>{paper.year} • {paper.publisher || 'Research Venue'}</div>
      <p style={{ fontSize: '0.9rem', lineHeight: 1.6, marginBottom: 25, opacity: 0.8 }}>{paper.abstract}</p>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 12 }}>
          <button 
            onClick={() => saved ? onRemove(paper.id) : onSave(paper)}
            style={{ 
              background: saved ? 'var(--accent-purple)' : 'transparent', 
              border: '1px solid var(--accent-purple)',
              color: saved ? '#fff' : 'var(--accent-purple)',
              padding: '6px 16px', borderRadius: 10, fontSize: '0.7rem', fontWeight: 700, cursor: 'pointer'
            }}
          >
            {saved ? '✓ SAVED' : '+ SAVE'}
          </button>
        </div>
        <a href={paper.url} target="_blank" rel="noopener noreferrer" className="view-btn" style={{ background: 'var(--accent-purple)', color: '#fff', padding: '12px 28px', borderRadius: 14, textDecoration: 'none', fontWeight: 800, fontSize: '0.8rem' }}>
          VIEW PAPER
        </a>
      </div>
    </div>
  );

  return (
    <div className="app-shell">
      {/* Navbar */}
      <nav className="navbar">
        <div className="logo-area" onClick={() => setView('Home')}>
          <div className="graphite-3d">
            <div className="side top"></div>
            <div className="side front"></div>
            <div className="side right"></div>
          </div>
          <span style={{ fontSize: '1rem', marginLeft: '15px' }}>RESEARCH <span style={{ opacity: 0.5 }}>INTELLIGENCE SYSTEM</span></span>
        </div>
        <div className="search-bar-container">
          <input 
            className="main-search-input"
            placeholder="Explore global research matrix..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button className="theme-toggle-btn" onClick={() => setIsDarkMode(!isDarkMode)}>
          <div className="toggle-track">
            <div className={`toggle-thumb ${isDarkMode ? 'dark' : 'light'}`}>
              {isDarkMode ? '🌙' : '☀️'}
            </div>
          </div>
          <span className="toggle-label">{isDarkMode ? 'DARK' : 'LIGHT'}</span>
        </button>
      </nav>

      {/* Sidebar Left */}
      <aside className="sidebar-left">
        <div className="nav-group">
          <div className={`nav-item ${view === 'Home' ? 'active' : ''}`} onClick={() => setView('Home')}>🏠 Home</div>
          <div className={`nav-item ${view === 'Search' ? 'active' : ''}`} onClick={() => setView('Search')}>🔍 Neural Search</div>
          <div className={`nav-item ${view === 'Trends' ? 'active' : ''}`} onClick={() => setView('Trends')}>📈 Trends Matrix</div>
          <div className={`nav-item ${view === 'Library' ? 'active' : ''}`} onClick={() => setView('Library')}>🔖 My Library ({library.length})</div>
        </div>

        <div className="filter-panel">
          <div className="filter-header">Matrix Filters</div>
          <div className="filter-control-group">
            <div className="filter-label">Access <span>🛡️</span></div>
            <div className="pill-grid">
              {['All', 'Open Access', 'Preprint', 'Closed'].map(t => (
                <div key={t} className={`pill-btn ${filters.accessType === t ? 'active' : ''}`} onClick={() => setFilters({...filters, accessType: t})}>{t}</div>
              ))}
            </div>
          </div>
          <div className="filter-control-group">
            <div className="filter-label">Year Range <span>📅</span> <span>{filters.yearFrom}-{filters.yearTo}</span></div>
            <div className="dual-range-container">
              <div className="range-track"></div>
              <input type="range" min="2000" max="2024" value={filters.yearFrom} onChange={e => setFilters({...filters, yearFrom: Math.min(parseInt(e.target.value), filters.yearTo - 1)})} />
              <input type="range" min="2000" max="2024" value={filters.yearTo} onChange={e => setFilters({...filters, yearTo: Math.max(parseInt(e.target.value), filters.yearFrom + 1)})} />
            </div>
          </div>
          <div className="filter-control-group">
            <div className="filter-label">Min Citations <span>❝</span> <span>{filters.minCitations}</span></div>
            <input type="range" min="0" max="1000" step="50" value={filters.minCitations} onChange={e => setFilters({...filters, minCitations: parseInt(e.target.value)})} />
          </div>
          <div className="filter-control-group">
            <div className="filter-label">Primary Source <span>🌐</span></div>
            <select className="glossy-select" value={filters.sourceType} onChange={e => setFilters({...filters, sourceType: e.target.value})}>
              <option>All Sources</option>
              <option>arXiv</option>
              <option>Semantic Scholar</option>
              <option>OpenAlex</option>
              <option>Crossref</option>
            </select>
          </div>
          <div className="advanced-toggle" onClick={() => setShowAdvanced(!showAdvanced)}>
            ADVANCED DISCOVERY <span>{showAdvanced ? '▲' : '▼'}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {view === 'Home' && (
          <div className="page-container" style={{ textAlign: 'center', padding: '100px 0' }}>
            <h1 style={{ fontSize: '4.5rem', fontWeight: 900, letterSpacing: '-2.5px' }}>RESEARCH <span style={{ color: 'var(--accent-purple)' }}>INTELLIGENCE</span></h1>
            <p style={{ color: 'var(--text-dim)', fontSize: '1.2rem', marginTop: 20 }}>Discover insights. Bypass paywalls. Analyze global trends.</p>
          </div>
        )}
        
        {view === 'Search' && (
          <div className="page-container">
            {loading && (
              <div className="section-card">
                <div className="filter-header" style={{ marginBottom: 20 }}>Neural Processing</div>
                <div style={{ display: 'flex', gap: 25 }}>
                  {steps.map(s => (
                    <div key={s.state} style={{ display: 'flex', alignItems: 'center', gap: 10, opacity: s.state === currentStep ? 1 : 0.4 }}>
                      <div className={`step-dot-mini ${s.state === currentStep ? 'pulse' : ''}`} style={{ width: 8, height: 8 }} />
                      <span style={{ fontSize: '0.7rem', fontWeight: 700 }}>{s.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result && (
              <>
                <div className="section-card">
                  <div className="filter-header" style={{ marginBottom: 20 }}>Intelligence Synthesis</div>
                  <p style={{ fontSize: '1rem', lineHeight: 1.7 }}>{result.analysis.summary}</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
                  {filteredPapers.map(paper => (
                    <PaperCard key={paper.id} paper={paper} onSave={handleSave} onRemove={handleRemove} saved={isSaved(paper.id)} />
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {view === 'Library' && (
          <div className="page-container">
            <div className="results-header" style={{marginBottom:30}}>
              <h2>My Knowledge Library <span>({library.length} Papers)</span></h2>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {library.length > 0 ? library.map(paper => (
                <PaperCard key={paper.id} paper={paper} onSave={handleSave} onRemove={handleRemove} saved={true} />
              )) : (
                <div style={{textAlign:'center', padding:100, opacity:0.4}}>Your library is empty. Save papers from search results.</div>
              )}
            </div>
          </div>
        )}

        {view === 'Trends' && (
          <div className="page-container">
            <div className="section-card">
              <div className="filter-header" style={{ marginBottom: 25 }}>Research Trajectory</div>
              <ChartSVG />
            </div>
          </div>
        )}
      </main>

      {/* Right Sidebar */}
      <aside className="sidebar-right">
        <div className="section-card">
          <div className="filter-header" style={{ marginBottom: 20 }}>Key Gaps</div>
          {result?.analysis.gaps.map((g, i) => (
            <div key={i} style={{ marginBottom: 20, paddingBottom: 20, borderBottom: '1px solid var(--glass-border)' }}>
              <div style={{ color: 'var(--accent-purple)', fontWeight: 800, fontSize: '0.75rem', marginBottom: 8 }}>{g.area}</div>
              <div style={{ fontSize: '0.75rem', opacity: 0.6 }}>{g.description}</div>
            </div>
          )) || <div style={{ opacity: 0.4 }}>Awaiting data...</div>}
        </div>
      </aside>
    </div>
  );
}
