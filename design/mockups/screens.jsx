// screens.jsx — All main screens of the Gungnir · Public Funding Analytics mockup

// ─────────────────────────────────────────────────────────────────────
// CONSULTAS — threaded NL query interface
// ─────────────────────────────────────────────────────────────────────
const ConsultasScreen = ({ onOpenEmpresa }) => {
  const [activeId, setActiveId] = React.useState('c-2026-041');
  const [draft, setDraft] = React.useState('');
  const active = CONSULTA_ACTIVA;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'minmax(220px, 260px) minmax(0, 1fr)', gap: 'var(--s-4)', height: 'calc(100vh - 52px - 48px)' }}>
      {/* Consultation list */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: 'var(--s-4) var(--s-4) var(--s-3)', borderBottom: '1px solid var(--ink-200)' }}>
          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
            <Icon name="plus" size={13} />Nueva consulta
          </button>
        </div>
        <div style={{ padding: 'var(--s-3) var(--s-3) 0' }}>
          <div className="upper">Recientes</div>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--s-2)' }}>
          {CONSULTAS.map(c => (
            <div key={c.id}
              onClick={() => setActiveId(c.id)}
              style={{
                padding: 'var(--s-3)',
                borderRadius: 'var(--r-3)',
                cursor: 'pointer',
                background: activeId === c.id ? 'var(--accent-dim)' : 'transparent',
                marginBottom: 2,
                borderLeft: activeId === c.id ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
                {c.pinned && <Icon name="pin" size={11} />}
                <div style={{ flex: 1, fontSize: 13, fontWeight: 500, color: 'var(--ink-900)', lineHeight: 1.35 }}>{c.titulo}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4, fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)' }}>
                <span>{c.fecha}</span>
                <span>·</span>
                <span>{c.mensajes} turnos</span>
                <span>·</span>
                <span>{c.resultados} resultados</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active conversation */}
      <div className="card" style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div className="card-h" style={{ alignItems: 'flex-start', flexWrap: 'wrap', gap: 8 }}>
          <div style={{ flex: '1 1 240px', minWidth: 0 }}>
            <h3 style={{ overflowWrap: 'anywhere', lineHeight: 1.25 }}>{active.titulo}</h3>
            <div className="sub" style={{ marginTop: 4 }}>{active.turnos.length} turnos · actualizado hace 1 hora</div>
          </div>
          <div className="row" style={{ gap: 6, flexShrink: 0 }}>
            <button className="btn btn-ghost btn-sm"><Icon name="pin" size={12} />Pinned</button>
            <button className="btn btn-secondary btn-sm"><Icon name="download" size={12} />Exportar</button>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--s-5)' }}>
          {active.turnos.map((t, i) => t.rol === 'user' ? (
            <div key={i} style={{ marginBottom: 'var(--s-6)' }}>
              <div className="upper" style={{ marginBottom: 6 }}>Tú · {t.fecha}</div>
              <div style={{ fontFamily: 'var(--font-serif)', fontSize: 20, color: 'var(--ink-900)', lineHeight: 1.4, letterSpacing: '-0.01em' }}>
                {t.pregunta}
              </div>
            </div>
          ) : (
            <AssistantTurn key={i} t={t} onOpenEmpresa={onOpenEmpresa} />
          ))}
        </div>

        {/* Composer */}
        <div style={{ borderTop: '1px solid var(--ink-200)', padding: 'var(--s-4) var(--s-5)', background: 'var(--paper-2)' }}>
          <div style={{ background: 'var(--card)', border: '1px solid var(--ink-200)', borderRadius: 'var(--r-4)', padding: 'var(--s-3)', display: 'flex', gap: 'var(--s-2)', alignItems: 'flex-end' }}>
            <textarea
              className="inp"
              placeholder="Pregunta de seguimiento sobre esta consulta…  ⌘↵ para enviar"
              value={draft}
              onChange={e => setDraft(e.target.value)}
              style={{ border: 0, resize: 'none', padding: 6, minHeight: 24, flex: 1, background: 'transparent' }}
              rows={1}
            />
            <button className="btn btn-primary btn-sm"><Icon name="sparkle" size={12} />Consultar</button>
          </div>
          <div style={{ display: 'flex', gap: 6, marginTop: 8, flexWrap: 'wrap' }}>
            <span className="upper" style={{ alignSelf: 'center' }}>Ejemplos:</span>
            {EXAMPLES.slice(0,3).map((e, i) => (
              <button key={i} className="btn btn-secondary btn-sm" style={{ fontWeight: 400, color: 'var(--ink-500)' }}>{e}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const AssistantTurn = ({ t, onOpenEmpresa }) => {
  const [sqlOpen, setSqlOpen] = React.useState(false);
  return (
    <div style={{ marginBottom: 'var(--s-6)', borderLeft: '2px solid var(--highlight)', paddingLeft: 'var(--s-4)' }}>
      <div className="upper" style={{ marginBottom: 6 }}>
        <span style={{ color: 'var(--highlight)' }}>Gungnir</span> · {t.fecha}
      </div>

      {/* Answer */}
      <div style={{ fontSize: 14, color: 'var(--ink-700)', lineHeight: 1.6, marginBottom: 'var(--s-4)' }}
           dangerouslySetInnerHTML={{ __html: t.respuesta.replace(/\*\*(.+?)\*\*/g, '<strong style="color:var(--ink-900)">$1</strong>') }} />

      {/* SQL block (collapsible) */}
      <div style={{ marginBottom: 'var(--s-4)' }}>
        <button onClick={() => setSqlOpen(!sqlOpen)} className="btn btn-ghost btn-sm" style={{ padding: '4px 8px', fontFamily: 'var(--font-mono)', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          <Icon name="caret" size={10} /> SQL generado · {sqlOpen ? 'ocultar' : 'ver'}
        </button>
        {sqlOpen && (
          <pre style={{ marginTop: 8, background: 'var(--paper-2)', border: '1px solid var(--ink-200)', borderRadius: 'var(--r-3)', padding: 12, fontSize: 11.5, fontFamily: 'var(--font-mono)', color: 'var(--ink-700)', overflowX: 'auto', lineHeight: 1.6 }}>
            {t.sql}
          </pre>
        )}
      </div>

      {/* Result table */}
      {t.resultados && (
        <div className="card" style={{ overflow: 'hidden', marginBottom: 'var(--s-4)' }}>
          <div className="card-h" style={{ padding: '10px var(--s-4)' }}>
            <div className="upper">{t.resultados.length} filas mostradas</div>
            <div className="row" style={{ gap: 4 }}>
              <button className="btn btn-ghost btn-sm"><Icon name="filter" size={11} />Filtrar</button>
              <button className="btn btn-ghost btn-sm"><Icon name="download" size={11} />CSV</button>
              <button className="btn btn-ghost btn-sm"><Icon name="plus" size={11} />Agregar a leads</button>
            </div>
          </div>
          <table className="t">
            <thead>
              <tr>{Object.keys(t.resultados[0]).map(k => (
                <th key={k} className={typeof t.resultados[0][k] === 'number' ? 'num' : ''}>{k}</th>
              ))}</tr>
            </thead>
            <tbody>
              {t.resultados.slice(0, 7).map((r, i) => (
                <tr key={i}>
                  {Object.entries(r).map(([k, v], j) => {
                    if (k === 'razon' || k === 'empresa') {
                      return <td key={j} className="primary"><a onClick={() => onOpenEmpresa && onOpenEmpresa(v)} style={{ cursor: 'pointer' }}>{v}</a></td>;
                    }
                    if (k === 'monto' || k === 'monto_total') {
                      return <td key={j} className="num mono">{fmtCLP(v)}</td>;
                    }
                    if (k === 'estado') return <td key={j}><Status value={v} /></td>;
                    if (typeof v === 'number') return <td key={j} className="num mono">{v}</td>;
                    return <td key={j}>{v}</td>;
                  })}
                </tr>
              ))}
              {t.resultados.length > 7 && (
                <tr><td colSpan={Object.keys(t.resultados[0]).length} style={{ textAlign: 'center', color: 'var(--ink-400)', padding: 12, fontSize: 12 }}>
                  + {t.resultados.length - 7} filas más · <a>ver todas</a>
                </td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Follow-up suggestions */}
      {t.followups && (
        <div>
          <div className="upper" style={{ marginBottom: 6 }}>Continuar con</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {t.followups.map((f, i) => (
              <button key={i} className="btn btn-secondary btn-sm" style={{ fontWeight: 400 }}>
                <Icon name="sparkle" size={11} />{f}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─────────────────────────────────────────────────────────────────────
// DASHBOARD — integrated analytics with cross-filter
// ─────────────────────────────────────────────────────────────────────
const DashboardScreen = () => {
  const [filter, setFilter] = React.useState(null);
  const activeFilter = filter;

  return (
    <div>
      <SectionHeader
        title="Dashboard"
        meta="2,009 proyectos · 2009–2025 · CORFO"
        right={<div className="row">
          <button className="btn btn-secondary btn-sm"><Icon name="filter" size={12} />Filtros</button>
          <button className="btn btn-secondary btn-sm"><Icon name="download" size={12} />Exportar PDF</button>
          <button className="btn btn-primary btn-sm"><Icon name="pin" size={12} />Guardar vista</button>
        </div>}
      />

      {/* KPI strip */}
      <div className="card" style={{ marginBottom: 'var(--s-5)', padding: 0, display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <KPI label="Monto total aprobado" value="$111.7B" sub="CLP · 2009–2025" trend={{ dir: 'up', value: '+8.2%', label: 'vs 2023' }} />
        <div style={{ borderLeft: '1px solid var(--ink-200)' }}><KPI label="Proyectos" value="2,009" sub="1,689 finalizados · 320 vigentes" /></div>
        <div style={{ borderLeft: '1px solid var(--ink-200)' }}><KPI label="Empresas únicas" value="1,060" sub="Todas en pipeline de leads" /></div>
        <div style={{ borderLeft: '1px solid var(--ink-200)' }}><KPI label="Monto promedio" value="$55.6M" sub="Rango: 0 – $3.2B CLP" trend={{ dir: 'up', value: '+4.1%', label: 'YoY' }} /></div>
      </div>

      {/* Cross-filter banner */}
      {activeFilter && (
        <div style={{ background: 'var(--highlight-dim)', border: '1px solid var(--highlight)', borderRadius: 'var(--r-3)', padding: '8px 14px', display: 'flex', alignItems: 'center', gap: 10, marginBottom: 'var(--s-4)' }}>
          <Icon name="filter" size={12} />
          <span style={{ fontSize: 13 }}>Filtrado por <strong>{activeFilter}</strong></span>
          <span style={{ flex: 1 }} />
          <button className="btn btn-ghost btn-sm" onClick={() => setFilter(null)}><Icon name="close" size={11} />Limpiar</button>
        </div>
      )}

      <div className="grid-12">
        <div className="span-8">
          <Card title="Monto aprobado por año" subtitle="CLP · haz clic en un año para filtrar"
                right={<Chip variant="navy">línea principal: monto</Chip>}>
            <LineChart data={YEARS.map(y => ({ y: y.y, n: y.n * 50e6 + (y.n > 150 ? 2e9 : 0) }))}
                       xKey="y" yKey="n" height={220}
                       formatY={(v) => fmtCLP(v)} />
          </Card>
        </div>

        <div className="span-4">
          <Card title="Distribución regional" subtitle="Participación por región">
            <Donut data={REGIONS.slice(0, 6)} labelKey="name" valueKey="n" size={160} />
          </Card>
        </div>

        <div className="span-6">
          <Card title="Top sectores económicos" subtitle="Proyectos por sector · clic para filtrar">
            <Bar data={SECTORS.slice(0, 7)} labelKey="name" valueKey="n"
                 formatValue={fmtN} selected={activeFilter === 'sector' ? activeFilter : null}
                 onSelect={(v) => setFilter(`Sector: ${v}`)} />
          </Card>
        </div>

        <div className="span-6">
          <Card title="Instrumentos CORFO" subtitle="Monto total por instrumento">
            <Bar data={INSTRUMENTOS} labelKey="name" valueKey="monto"
                 formatValue={fmtCLP} barColor="var(--data-3)"
                 onSelect={(v) => setFilter(`Instrumento: ${v}`)} />
          </Card>
        </div>

        <div className="span-6">
          <Card title="Tendencias tecnológicas" subtitle="Excluye 'Sin tendencia' (80% de proyectos)">
            <Bar data={TENDENCIAS} labelKey="name" valueKey="n" formatValue={fmtN} barColor="var(--data-2)" />
          </Card>
        </div>

        <div className="span-6">
          <Card title="Composición de proyectos" subtitle="Atributos transversales">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 'var(--s-4)' }}>
              <Metric label="Proyectos vigentes" value="320" pct={15.9} color="var(--accent)" />
              <Metric label="Sostenibles" value="910" pct={45.3} color="var(--data-3)" />
              <Metric label="Economía circular" value="320" pct={15.9} color="var(--highlight)" />
              <Metric label="Ley I+D" value="348" pct={17.3} color="var(--data-5)" />
              <Metric label="Dirigidos por mujeres" value="287" pct={14.3} color="var(--data-4)" />
              <Metric label="Grandes empresas" value="412" pct={20.5} color="var(--data-6)" />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

const Metric = ({ label, value, pct, color }) => (
  <div>
    <div className="upper" style={{ marginBottom: 4 }}>{label}</div>
    <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, marginBottom: 6 }}>
      <span style={{ fontFamily: 'var(--font-serif)', fontSize: 22, color: 'var(--ink-900)', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
      <span className="mono" style={{ fontSize: 11, color: 'var(--ink-400)' }}>{pct}%</span>
    </div>
    <div style={{ height: 3, background: 'var(--ink-100)', borderRadius: 1 }}>
      <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 1 }} />
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────
// LEADS — pipeline (board + table view)
// ─────────────────────────────────────────────────────────────────────
const LeadsScreen = ({ onOpenEmpresa }) => {
  const [view, setView] = React.useState('pipeline');
  const [selected, setSelected] = React.useState(null);

  return (
    <div>
      <SectionHeader
        title="Leads"
        meta={`${LEADS.length} de 1,060 empresas · pipeline CRM`}
        right={<div className="row">
          <div style={{ display: 'flex', background: 'var(--card)', border: '1px solid var(--ink-200)', borderRadius: 'var(--r-3)', padding: 2 }}>
            {['pipeline','tabla','mapa'].map(v => (
              <button key={v} onClick={() => setView(v)}
                className={view === v ? 'btn btn-primary btn-sm' : 'btn btn-ghost btn-sm'}
                style={{ textTransform: 'capitalize' }}>{v}</button>
            ))}
          </div>
          <button className="btn btn-secondary btn-sm"><Icon name="download" size={12} />Exportar CSV</button>
          <button className="btn btn-primary btn-sm"><Icon name="plus" size={12} />Agregar lead</button>
        </div>}
      />

      {/* Stat strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--s-4)', marginBottom: 'var(--s-5)' }}>
        {[
          { l: 'Nuevos', v: 3, delta: '+2 esta semana' },
          { l: 'Contactados', v: 3, delta: '+1' },
          { l: 'En seguimiento', v: 3, delta: '—' },
          { l: 'Propuesta enviada', v: 2, delta: '+1' },
          { l: 'Monto pipeline', v: '$17.9B', delta: 'CLP total' },
        ].map((s, i) => (
          <div key={i} className="card" style={{ padding: 'var(--s-4)' }}>
            <div className="upper" style={{ marginBottom: 4 }}>{s.l}</div>
            <div style={{ fontFamily: 'var(--font-serif)', fontSize: 22, color: 'var(--ink-900)', fontVariantNumeric: 'tabular-nums' }}>{s.v}</div>
            <div style={{ fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>{s.delta}</div>
          </div>
        ))}
      </div>

      {view === 'pipeline' && <PipelineBoard onSelect={setSelected} onOpenEmpresa={onOpenEmpresa} />}
      {view === 'tabla' && <LeadsTable onSelect={setSelected} selected={selected} onOpenEmpresa={onOpenEmpresa} />}
      {view === 'mapa' && <LeadsMap />}

      {selected && <LeadDrawer lead={selected} onClose={() => setSelected(null)} onOpenEmpresa={onOpenEmpresa} />}
    </div>
  );
};

const PipelineBoard = ({ onSelect, onOpenEmpresa }) => {
  const estados = ['Nuevo', 'Contactado', 'En seguimiento', 'Propuesta enviada', 'Cerrado'];
  const byEstado = estados.map(e => ({ e, leads: LEADS.filter(l => l.estado === e) }));

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 'var(--s-4)', alignItems: 'start' }}>
      {byEstado.map(col => (
        <div key={col.e} style={{ background: 'var(--paper-2)', border: '1px solid var(--ink-200)', borderRadius: 'var(--r-4)', padding: 'var(--s-3)', minHeight: 400 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--s-3)', padding: '0 4px' }}>
            <Status value={col.e} />
            <span className="mono" style={{ fontSize: 11, color: 'var(--ink-400)' }}>{col.leads.length}</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {col.leads.map(l => (
              <div key={l.id}
                   onClick={() => onSelect(l)}
                   className="card"
                   style={{ padding: 10, cursor: 'pointer', boxShadow: 'var(--shadow-1)' }}>
                <div style={{ fontSize: 12.5, fontWeight: 500, color: 'var(--ink-900)', lineHeight: 1.3, marginBottom: 4 }}>{l.razon}</div>
                <div style={{ fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)', marginBottom: 6 }}>{l.region} · {l.tramo}</div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span className="num mono" style={{ fontSize: 12, color: 'var(--ink-700)', fontWeight: 500 }}>{fmtCLP(l.monto)}</span>
                  <span style={{ fontSize: 10, color: 'var(--ink-400)' }}>{l.proyectos} proyectos</span>
                </div>
                {l.proxima_fecha && (
                  <div style={{ marginTop: 6, fontSize: 11, color: 'var(--ink-500)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Icon name="clock" size={10} />{l.proxima} · {l.proxima_fecha.slice(5)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const LeadsTable = ({ onSelect, selected, onOpenEmpresa }) => (
  <div className="card" style={{ overflow: 'hidden' }}>
    <div style={{ padding: 'var(--s-3) var(--s-4)', borderBottom: '1px solid var(--ink-200)', display: 'flex', gap: 8, alignItems: 'center' }}>
      <input className="inp" placeholder="Buscar empresa, RUT, sector…" style={{ flex: 1, maxWidth: 360 }} />
      <select className="inp" style={{ width: 'auto' }}>
        <option>Todos los estados</option>
        <option>Nuevo</option><option>Contactado</option><option>En seguimiento</option>
      </select>
      <select className="inp" style={{ width: 'auto' }}>
        <option>Todas las regiones</option>
        {REGIONS.map(r => <option key={r.name}>{r.name}</option>)}
      </select>
      <span style={{ flex: 1 }} />
      <span className="upper">12 de 1,060</span>
    </div>
    <table className="t">
      <thead>
        <tr>
          <th>Empresa</th><th>Región</th><th>Sector</th><th>Tamaño</th>
          <th className="num">Proyectos</th><th className="num">Monto total</th>
          <th>Estado</th><th>Interés</th><th>Próxima acción</th>
        </tr>
      </thead>
      <tbody>
        {LEADS.map(l => (
          <tr key={l.id} onClick={() => onSelect(l)} style={{ cursor: 'pointer' }}>
            <td className="primary"><a onClick={(e) => { e.stopPropagation(); onOpenEmpresa(l.razon); }} style={{ cursor: 'pointer' }}>{l.razon}</a><div style={{ fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)' }}>{l.rut}</div></td>
            <td>{l.region}</td>
            <td style={{ fontSize: 12, color: 'var(--ink-500)' }}>{l.sector.replace(/ \(.+\)/, '')}</td>
            <td>{l.tramo}</td>
            <td className="num mono">{l.proyectos}</td>
            <td className="num mono primary">{fmtCLP(l.monto)}</td>
            <td><Status value={l.estado} /></td>
            <td><Chip variant={l.interes === 'alto' ? 'ochre' : 'neutral'}>{l.interes}</Chip></td>
            <td style={{ fontSize: 12, color: 'var(--ink-500)' }}>
              {l.proxima_fecha ? <><span>{l.proxima}</span><div style={{ fontSize: 11, color: 'var(--ink-400)' }}>{l.proxima_fecha}</div></> : <span className="muted">—</span>}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const LeadsMap = () => (
  <Card title="Distribución geográfica" subtitle="Leads por región de ejecución">
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--s-5)', alignItems: 'center' }}>
      <div style={{ background: 'var(--paper-2)', border: '1px dashed var(--ink-200)', borderRadius: 'var(--r-3)', padding: 40, textAlign: 'center', color: 'var(--ink-400)', height: 360, display: 'grid', placeItems: 'center' }}>
        <div>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 18, color: 'var(--ink-700)', marginBottom: 6 }}>Mapa de Chile</div>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.14em' }}>[ placeholder · choropleth region-level ]</div>
        </div>
      </div>
      <Bar data={REGIONS} labelKey="name" valueKey="n" formatValue={fmtN} rowLabelWidth={180} />
    </div>
  </Card>
);

const LeadDrawer = ({ lead, onClose, onOpenEmpresa }) => (
  <div style={{ position: 'fixed', inset: 0, background: 'rgba(18,21,26,0.3)', zIndex: 100, display: 'flex', justifyContent: 'flex-end' }} onClick={onClose}>
    <div onClick={(e) => e.stopPropagation()} style={{ width: 440, background: 'var(--card)', height: '100vh', overflowY: 'auto', boxShadow: 'var(--shadow-3)', borderLeft: '1px solid var(--ink-200)' }}>
      <div style={{ padding: 'var(--s-5) var(--s-5) var(--s-4)', borderBottom: '1px solid var(--ink-200)', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
        <div style={{ flex: 1 }}>
          <div className="upper" style={{ marginBottom: 6 }}>Lead · {lead.rut}</div>
          <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: 22, marginBottom: 6, lineHeight: 1.2 }}>{lead.razon}</h2>
          <Status value={lead.estado} />
        </div>
        <button className="btn btn-ghost btn-sm" onClick={onClose}><Icon name="close" size={14} /></button>
      </div>
      <div style={{ padding: 'var(--s-5)' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--s-4)', marginBottom: 'var(--s-5)' }}>
          <div><div className="upper" style={{ marginBottom: 4 }}>Monto total</div><div style={{ fontFamily: 'var(--font-serif)', fontSize: 20 }}>{fmtCLP(lead.monto)}</div></div>
          <div><div className="upper" style={{ marginBottom: 4 }}>Proyectos</div><div style={{ fontFamily: 'var(--font-serif)', fontSize: 20 }}>{lead.proyectos}</div></div>
          <div><div className="upper" style={{ marginBottom: 4 }}>Región</div><div style={{ fontSize: 14 }}>{lead.region}</div></div>
          <div><div className="upper" style={{ marginBottom: 4 }}>Tamaño</div><div style={{ fontSize: 14 }}>{lead.tramo}</div></div>
        </div>

        <div style={{ marginBottom: 'var(--s-5)' }}>
          <div className="upper" style={{ marginBottom: 6 }}>Tendencias tecnológicas</div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {lead.tendencias.map(t => <Chip key={t} variant="navy">{t}</Chip>)}
          </div>
        </div>

        <div className="hr" />

        <div className="upper" style={{ marginBottom: 8 }}>Estado del contacto</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div><label className="label">Estado</label>
            <select className="inp" defaultValue={lead.estado}>
              <option>Nuevo</option><option>Contactado</option><option>En seguimiento</option><option>Propuesta enviada</option><option>Cerrado</option>
            </select></div>
          <div><label className="label">Nivel de interés</label>
            <select className="inp" defaultValue={lead.interes}><option>alto</option><option>medio</option><option>bajo</option></select></div>
          <div><label className="label">Próxima acción</label>
            <input className="inp" defaultValue={lead.proxima} /></div>
          <div><label className="label">Fecha próxima acción</label>
            <input type="date" className="inp" defaultValue={lead.proxima_fecha || ''} /></div>
          <div><label className="label">Notas</label>
            <textarea className="inp" rows={3} placeholder="Notas internas sobre el contacto…" /></div>
        </div>

        <div className="hr" />

        <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => { onClose(); onOpenEmpresa(lead.razon); }}>
          Ver perfil completo <Icon name="arrow" size={12} />
        </button>
      </div>
    </div>
  </div>
);

// ─────────────────────────────────────────────────────────────────────
// EMPRESA 360 — the integration hub
// ─────────────────────────────────────────────────────────────────────
const EmpresaScreen = ({ razon, onBack }) => {
  const e = EMPRESA;
  const [tab, setTab] = React.useState('resumen');

  return (
    <div>
      {/* Back + breadcrumbs are in topbar */}

      {/* Hero header */}
      <div style={{ background: 'var(--card)', border: '1px solid var(--ink-200)', borderRadius: 'var(--r-4)', padding: 'var(--s-6)', marginBottom: 'var(--s-5)' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--s-5)' }}>
          <div style={{ flex: 1 }}>
            <div className="upper" style={{ marginBottom: 6 }}>{e.rut} · {e.region} · {e.tramo}</div>
            <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: 36, letterSpacing: '-0.02em', marginBottom: 10 }}>{e.razon}</h1>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              <Chip variant="navy">{e.sector}</Chip>
              {e.sostenible && <Chip variant="pos">Sostenible</Chip>}
              {e.economiaCircular && <Chip variant="ochre">Economía circular</Chip>}
              <Chip variant="neutral">Primer proyecto · {e.primerProyecto}</Chip>
              <Chip variant="neutral">Último · {e.ultimoProyecto}</Chip>
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
            <Status value={e.leadStatus} />
            <div className="row" style={{ gap: 6 }}>
              <button className="btn btn-secondary btn-sm"><Icon name="copy" size={12} />Copiar RUT</button>
              <button className="btn btn-secondary btn-sm"><Icon name="external" size={12} />Ver en DatáInnovación</button>
              <button className="btn btn-primary btn-sm"><Icon name="external" size={12} />Exportar a HubSpot</button>
            </div>
          </div>
        </div>

        {/* KPI row — integrated across the app */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', marginTop: 'var(--s-5)', borderTop: '1px solid var(--ink-200)', paddingTop: 'var(--s-5)' }}>
          <Summary label="Monto CORFO total" value={fmtCLP(e.totalMonto)} sub={`${e.totalProyectos} proyectos`} />
          <Summary label="Monto promedio" value={fmtCLP(e.totalMonto/e.totalProyectos)} sub="por proyecto" />
          <Summary label="Tendencias" value={e.tendencias.length} sub={e.tendencias.slice(0,2).join(' · ')} />
          <Summary label="Estado de contacto" value={e.leadStatus} sub={`Interés: ${e.interes}`} />
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 2, borderBottom: '1px solid var(--ink-200)', marginBottom: 'var(--s-5)' }}>
        {['resumen','proyectos','actividad','crm'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{
              padding: '10px 16px',
              fontSize: 13,
              color: tab === t ? 'var(--accent)' : 'var(--ink-500)',
              fontWeight: tab === t ? 500 : 400,
              borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
              marginBottom: -1,
              textTransform: 'capitalize',
            }}>{t}</button>
        ))}
      </div>

      {tab === 'resumen' && <EmpresaResumen e={e} />}
      {tab === 'proyectos' && <EmpresaProyectos e={e} />}
      {tab === 'actividad' && <EmpresaActividad e={e} />}
      {tab === 'crm' && <EmpresaCRM e={e} />}
    </div>
  );
};

const Summary = ({ label, value, sub }) => (
  <div style={{ paddingRight: 'var(--s-5)', borderRight: '1px solid var(--ink-200)' }}>
    <div className="upper" style={{ marginBottom: 4 }}>{label}</div>
    <div style={{ fontFamily: 'var(--font-serif)', fontSize: 22, color: 'var(--ink-900)' }}>{value}</div>
    <div style={{ fontSize: 12, color: 'var(--ink-500)', marginTop: 2 }}>{sub}</div>
  </div>
);

const EmpresaResumen = ({ e }) => (
  <div className="grid-12">
    <div className="span-8">
      <Card title="Financiamiento en el tiempo" subtitle="Proyectos adjudicados por año">
        <LineChart
          data={e.proyectos.map(p => ({ y: p.año, n: p.monto })).sort((a,b) => a.y - b.y)}
          xKey="y" yKey="n" height={220} formatY={fmtCLP} />
      </Card>

      <div style={{ height: 20 }} />

      <Card title="Notas del analista" subtitle="Editable · sincronizado con CRM">
        <div style={{ fontSize: 14, color: 'var(--ink-700)', lineHeight: 1.7 }}>{e.notas}</div>
        <div style={{ marginTop: 12 }}>
          <button className="btn btn-secondary btn-sm">Editar</button>
        </div>
      </Card>
    </div>

    <div className="span-4">
      <Card title="Contacto principal">
        <div style={{ marginBottom: 'var(--s-4)' }}>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 16, color: 'var(--ink-900)' }}>{e.contacto.nombre}</div>
          <div style={{ fontSize: 12, color: 'var(--ink-500)' }}>{e.contacto.cargo}</div>
        </div>
        <div style={{ fontSize: 13, color: 'var(--ink-700)', fontFamily: 'var(--font-mono)', lineHeight: 1.8 }}>
          <div>{e.contacto.email}</div>
          <div>{e.contacto.telefono}</div>
        </div>
      </Card>

      <div style={{ height: 20 }} />

      <Card title="Tendencias tecnológicas">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {e.tendencias.map(t => (
            <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="status s-contactado"></span>
              <span style={{ fontSize: 13 }}>{t}</span>
            </div>
          ))}
        </div>
      </Card>

      <div style={{ height: 20 }} />

      <Card title="Consultas relacionadas" subtitle="Dónde apareció esta empresa">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {CONSULTAS.slice(0, 3).map(c => (
            <div key={c.id} style={{ padding: 10, border: '1px solid var(--ink-100)', borderRadius: 'var(--r-3)', fontSize: 12 }}>
              <div style={{ fontWeight: 500, color: 'var(--ink-900)', marginBottom: 2 }}>{c.titulo}</div>
              <div style={{ color: 'var(--ink-400)', fontFamily: 'var(--font-mono)', fontSize: 11 }}>{c.fecha}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  </div>
);

const EmpresaProyectos = ({ e }) => (
  <Card title={`${e.totalProyectos} proyectos`} subtitle="Ordenados por año descendente"
        right={<button className="btn btn-secondary btn-sm"><Icon name="download" size={12} />Exportar</button>} flush>
    <table className="t">
      <thead>
        <tr><th>Código</th><th>Título</th><th className="num">Año</th><th className="num">Monto</th><th>Instrumento</th><th>Estado</th><th>Tendencia</th></tr>
      </thead>
      <tbody>
        {e.proyectos.map(p => (
          <tr key={p.codigo}>
            <td className="mono" style={{ fontSize: 11, color: 'var(--ink-500)' }}>{p.codigo}</td>
            <td className="primary">{p.titulo}</td>
            <td className="num mono">{p.año}</td>
            <td className="num mono primary">{fmtCLP(p.monto)}</td>
            <td style={{ fontSize: 12 }}>{p.instrumento}</td>
            <td><Chip variant={p.estado === 'VIGENTE' ? 'pos' : 'neutral'}>{p.estado}</Chip></td>
            <td style={{ fontSize: 12, color: p.tendencia === 'Sin tendencia' ? 'var(--ink-400)' : 'var(--ink-700)' }}>{p.tendencia}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </Card>
);

const EmpresaActividad = ({ e }) => (
  <Card title="Registro de actividad" subtitle="Interacciones con esta empresa">
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {e.actividad.map((a, i) => (
        <div key={i} style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: 20, padding: '14px 0', borderBottom: i < e.actividad.length - 1 ? '1px solid var(--ink-100)' : 'none' }}>
          <div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--ink-500)' }}>{a.fecha}</div>
            <Chip variant="neutral">{a.tipo}</Chip>
          </div>
          <div>
            <div style={{ fontSize: 13, color: 'var(--ink-900)', marginBottom: 2 }}>{a.nota}</div>
            <div style={{ fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)' }}>con {a.con}</div>
          </div>
        </div>
      ))}
    </div>
    <div style={{ marginTop: 'var(--s-4)' }}>
      <button className="btn btn-secondary btn-sm"><Icon name="plus" size={12} />Registrar actividad</button>
    </div>
  </Card>
);

const EmpresaCRM = ({ e }) => (
  <Card title="Objeto CRM" subtitle="Estructura canónica exportable a HubSpot · GET /api/crm/empresa/…" flush>
    <pre style={{ margin: 0, padding: 'var(--s-5)', fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--ink-700)', lineHeight: 1.7, overflowX: 'auto' }}>
{`{
  "crm_id":           "${e.razon.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')}",
  "nombre":           "${e.razon}",
  "total_adjudicado": ${e.totalMonto},
  "num_proyectos":    ${e.totalProyectos},
  "primer_proyecto":  ${e.primerProyecto},
  "ultimo_proyecto":  ${e.ultimoProyecto},
  "regiones":         ["${e.region}"],
  "sectores":         ["${e.sector}"],
  "tendencias":       ${JSON.stringify(e.tendencias)},
  "sostenible":       ${e.sostenible},
  "economia_circular":${e.economiaCircular},
  "en_leads":         true,
  "lead_status":      "${e.leadStatus}",
  "proyectos": [...${e.totalProyectos} registros]
}`}
    </pre>
    <div style={{ padding: 'var(--s-4) var(--s-5)', borderTop: '1px solid var(--ink-200)', display: 'flex', gap: 8 }}>
      <button className="btn btn-primary"><Icon name="external" size={12} />Exportar a HubSpot</button>
      <button className="btn btn-secondary"><Icon name="download" size={12} />Descargar JSON</button>
      <button className="btn btn-secondary"><Icon name="copy" size={12} />Copiar</button>
    </div>
  </Card>
);

// ─────────────────────────────────────────────────────────────────────
// COMMAND PALETTE
// ─────────────────────────────────────────────────────────────────────
const CmdPalette = ({ open, onClose, onNav, onOpenEmpresa }) => {
  if (!open) return null;
  const items = [
    { type: 'action', icon: 'chat',  label: 'Nueva consulta', kbd: 'N' },
    { type: 'action', icon: 'dash',  label: 'Ir a Dashboard' },
    { type: 'action', icon: 'users', label: 'Ir a Leads' },
    { type: 'section', label: 'Empresas' },
    { type: 'empresa', label: 'Agrícola Las Cruces SpA', sub: '76.123.456-7 · Maule' },
    { type: 'empresa', label: 'Viña Altos del Maipo S.A.', sub: '96.551.210-K · Metropolitana' },
    { type: 'empresa', label: 'Salmones Austral Ltda.', sub: '77.890.123-4 · Los Lagos' },
    { type: 'section', label: 'Consultas recientes' },
    ...CONSULTAS.slice(0, 3).map(c => ({ type: 'consulta', label: c.titulo, sub: c.fecha })),
  ];

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(18,21,26,0.3)', zIndex: 200, display: 'grid', placeItems: 'start center', paddingTop: '15vh' }}>
      <div onClick={e => e.stopPropagation()} style={{ width: 600, background: 'var(--card)', borderRadius: 'var(--r-4)', boxShadow: 'var(--shadow-3)', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: 'var(--s-4) var(--s-5)', borderBottom: '1px solid var(--ink-200)' }}>
          <Icon name="search" size={14} />
          <input autoFocus placeholder="Buscar empresas, consultas, acciones…" style={{ border: 0, outline: 0, flex: 1, fontSize: 15, background: 'transparent' }} />
          <kbd style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--ink-400)', border: '1px solid var(--ink-200)', padding: '2px 6px', borderRadius: 3 }}>ESC</kbd>
        </div>
        <div style={{ maxHeight: 400, overflowY: 'auto', padding: 'var(--s-2)' }}>
          {items.map((it, i) => it.type === 'section' ? (
            <div key={i} className="upper" style={{ padding: 'var(--s-3) var(--s-3) 4px' }}>{it.label}</div>
          ) : (
            <div key={i}
                 onClick={() => { if (it.type === 'empresa') onOpenEmpresa(it.label); onClose(); }}
                 style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 12px', borderRadius: 'var(--r-3)', cursor: 'pointer' }}
                 onMouseEnter={e => e.currentTarget.style.background = 'var(--accent-dim)'}
                 onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
              {it.icon && <Icon name={it.icon} size={13} />}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: 'var(--ink-900)' }}>{it.label}</div>
                {it.sub && <div style={{ fontSize: 11, color: 'var(--ink-400)', fontFamily: 'var(--font-mono)' }}>{it.sub}</div>}
              </div>
              {it.kbd && <kbd style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: 'var(--ink-400)' }}>⌘{it.kbd}</kbd>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { ConsultasScreen, DashboardScreen, LeadsScreen, EmpresaScreen, CmdPalette });
