// shell.jsx — Sidebar, topbar, command palette

const Icon = ({ name, size = 14 }) => {
  const paths = {
    search: <path d="M6.5 11a4.5 4.5 0 1 0 0-9 4.5 4.5 0 0 0 0 9Zm3.5-1 3 3" />,
    chat: <path d="M2 3h10v7H5l-3 2V3Z" />,
    dash: <><rect x="2" y="2" width="5" height="5" /><rect x="9" y="2" width="5" height="5" /><rect x="2" y="9" width="5" height="5" /><rect x="9" y="9" width="5" height="5" /></>,
    building: <><path d="M3 14V3h10v11" /><path d="M6 6h1M9 6h1M6 9h1M9 9h1M6 12h1M9 12h1" /></>,
    users: <><circle cx="5.5" cy="5" r="2.5" /><circle cx="11" cy="6" r="2" /><path d="M1.5 13c.5-2 2-3 4-3s3.5 1 4 3M9 13c.3-1.3 1.3-2.2 2.5-2.5" /></>,
    folder: <path d="M2 4.5A1.5 1.5 0 0 1 3.5 3H6l1.5 1.5h5A1.5 1.5 0 0 1 14 6v6.5A1.5 1.5 0 0 1 12.5 14h-9A1.5 1.5 0 0 1 2 12.5v-8Z" />,
    star: <path d="M8 2l1.8 3.6 4 .6-2.9 2.8.7 4L8 11.1l-3.6 1.9.7-4L2.2 6.2l4-.6L8 2Z" />,
    settings: <><circle cx="8" cy="8" r="2.5" /><path d="M8 1v2M8 13v2M15 8h-2M3 8H1M12.9 3.1l-1.4 1.4M4.5 11.5l-1.4 1.4M12.9 12.9l-1.4-1.4M4.5 4.5 3.1 3.1" /></>,
    plus: <path d="M8 3v10M3 8h10" />,
    arrow: <path d="M3 8h10M9 4l4 4-4 4" />,
    external: <><path d="M6 3H3v10h10v-3" /><path d="M9 3h4v4M8 8l5-5" /></>,
    db: <><ellipse cx="8" cy="4" rx="5" ry="1.8" /><path d="M3 4v4c0 1 2.2 1.8 5 1.8s5-.8 5-1.8V4" /><path d="M3 8v4c0 1 2.2 1.8 5 1.8s5-.8 5-1.8V8" /></>,
    download: <path d="M8 2v8M4 7l4 4 4-4M3 13h10" />,
    filter: <path d="M2 3h12l-4.5 5.5V13l-3-1.5V8.5L2 3Z" />,
    pin: <path d="M10 2 14 6l-2 1-1 4-3-3-3.5 3.5L4 11l3.5-3.5-3-3L9 3l1-1Z" />,
    close: <path d="M3 3l10 10M13 3 3 13" />,
    check: <path d="M3 8l3 3 7-7" />,
    sparkle: <path d="M8 2v4M8 10v4M2 8h4M10 8h4M4 4l2 2M10 10l2 2M4 12l2-2M10 6l2-2" />,
    clock: <><circle cx="8" cy="8" r="6" /><path d="M8 5v3l2 1.5" /></>,
    chevron: <path d="M5 3l4 5-4 5" />,
    caret: <path d="M4 6l4 4 4-4" />,
    copy: <><rect x="4" y="4" width="9" height="9" rx="1" /><path d="M3 11V3a1 1 0 0 1 1-1h8" /></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" className="icon">
      {paths[name]}
    </svg>
  );
};

const GungnirLogo = ({ size = 28 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-label="Gungnir">
    {/* Outer ring */}
    <circle cx="16" cy="16" r="15" fill="#FBFAF7" stroke="var(--accent)" strokeWidth="1.25" />
    {/* Spearhead — elongated kite/leaf */}
    <path d="M16 5.5 L19.1 13 L16 18.2 L12.9 13 Z" fill="var(--accent)" />
    {/* Midrib highlight */}
    <path d="M16 6.8 L16 17.5" stroke="#FBFAF7" strokeWidth="0.7" strokeLinecap="round" opacity="0.55" />
    {/* Crossguard — violet accent */}
    <rect x="11.2" y="18.6" width="9.6" height="1.5" rx="0.4" fill="var(--highlight)" />
    {/* Shaft */}
    <rect x="15.3" y="20.4" width="1.4" height="5.6" rx="0.4" fill="var(--ink-700)" />
    {/* Foot cap */}
    <rect x="14.4" y="25.8" width="3.2" height="1.1" rx="0.35" fill="var(--ink-900)" />
  </svg>
);

const Sidebar = ({ active, onNav, counts = {} }) => {
  const item = (id, label, icon, count) => (
    <div className={`nav-item ${active === id ? 'active' : ''}`} onClick={() => onNav(id)} key={id}>
      <Icon name={icon} />
      <span>{label}</span>
      {count != null && <span className="count">{count}</span>}
    </div>
  );
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-row">
          <GungnirLogo size={28} />
          <div className="wordmark">Gungnir<em>·</em></div>
        </div>
        <div className="tagline">Public Funding Analytics</div>
      </div>

      <div className="nav-section">
        <div className="nav-label">Workspace</div>
        {item('consultas', 'Consultas', 'chat', counts.consultas)}
        {item('dashboard', 'Dashboard', 'dash')}
        {item('empresas', 'Empresas', 'building', counts.empresas)}
        {item('leads', 'Leads', 'users', counts.leads)}
      </div>

      <div className="nav-section">
        <div className="nav-label">Saved</div>
        {item('pinned', 'Pinned queries', 'pin', counts.pinned)}
        {item('reports', 'Reports', 'folder')}
      </div>

      <div className="nav-section">
        <div className="nav-label">Data</div>
        {item('sync', 'Sync & sources', 'db')}
        {item('settings', 'Settings', 'settings')}
      </div>

      <div className="sidebar-footer">
        <div className="avatar">M</div>
        <div className="who">
          <div className="name">María Torres</div>
          <div className="role">Admin · Consultora</div>
        </div>
      </div>
    </aside>
  );
};

const Topbar = ({ crumbs = [], onCmdK, right }) => (
  <div className="topbar">
    <div className="crumbs">
      {crumbs.map((c, i) => (
        <React.Fragment key={i}>
          {i > 0 && <span className="sep">/</span>}
          <span className={i === crumbs.length - 1 ? 'current' : ''}>{c}</span>
        </React.Fragment>
      ))}
    </div>
    <div className="spacer" />
    <div className="cmdk" onClick={onCmdK}>
      <Icon name="search" size={13} />
      <span>Buscar empresa, consulta, proyecto…</span>
      <kbd>⌘K</kbd>
    </div>
    {right}
  </div>
);

const SectionHeader = ({ title, meta, right }) => (
  <div className="section-h">
    <h1>{title}</h1>
    {meta && <div className="meta">{meta}</div>}
    <div className="spacer" />
    {right}
  </div>
);

const Card = ({ title, subtitle, right, children, flush }) => (
  <div className="card">
    {(title || right) && (
      <div className="card-h">
        <div>
          {title && <h3>{title}</h3>}
          {subtitle && <div className="sub" style={{ marginTop: 2 }}>{subtitle}</div>}
        </div>
        {right}
      </div>
    )}
    <div className={`card-b ${flush ? 'flush' : ''}`}>{children}</div>
  </div>
);

const Chip = ({ variant = 'neutral', children }) => (
  <span className={`chip chip-${variant}`}>{children}</span>
);

const Status = ({ value }) => {
  const key = value.toLowerCase().replace(/\s+/g, '-').replace('contactado','contactado').split('-')[0];
  const map = {
    'nuevo': 'nuevo', 'no': 'nuevo', 'contactado': 'contactado', 'en': 'seguimiento', 'propuesta': 'propuesta', 'cerrado': 'cerrado',
  };
  return <span className={`status s-${map[key] || 'nuevo'}`}>{value}</span>;
};

// ── Formatting helpers ─────────────────────────────────────────────
const fmtCLP = (n) => {
  if (n == null) return '—';
  if (n >= 1e9) return `$${(n/1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n/1e6).toFixed(0)}M`;
  if (n >= 1e3) return `$${(n/1e3).toFixed(0)}K`;
  return `$${n}`;
};
const fmtCLPFull = (n) => n == null ? '—' : '$' + Math.round(n).toLocaleString('es-CL');
const fmtN = (n) => n == null ? '—' : n.toLocaleString('es-CL');

Object.assign(window, {
  Icon, Sidebar, Topbar, SectionHeader, Card, Chip, Status,
  fmtCLP, fmtCLPFull, fmtN,
});
