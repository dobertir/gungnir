// charts.jsx — Simple SVG charts (no external lib — clean, editorial)

const Bar = ({ data, labelKey, valueKey, formatValue = (v)=>v, height = 180, barColor = 'var(--accent)', rowLabelWidth = 160, showValues = true, selected, onSelect }) => {
  const max = Math.max(...data.map(d => d[valueKey]));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, height }}>
      {data.map((d, i) => {
        const isSel = selected === d[labelKey];
        return (
          <div key={i}
            onClick={() => onSelect && onSelect(d[labelKey])}
            style={{
              display: 'grid',
              gridTemplateColumns: `${rowLabelWidth}px 1fr 60px`,
              alignItems: 'center',
              gap: 12,
              cursor: onSelect ? 'pointer' : 'default',
              padding: '2px 0',
              opacity: selected && !isSel ? 0.45 : 1,
              transition: 'opacity 120ms',
            }}
          >
            <div style={{ fontSize: 12, color: 'var(--ink-700)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d[labelKey]}</div>
            <div style={{ position: 'relative', height: 18, background: 'var(--ink-100)', borderRadius: 1 }}>
              <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: `${(d[valueKey]/max)*100}%`, background: isSel ? 'var(--highlight)' : barColor, borderRadius: 1 }} />
            </div>
            {showValues && <div className="num mono" style={{ fontSize: 12, color: 'var(--ink-500)', textAlign: 'right' }}>{formatValue(d[valueKey])}</div>}
          </div>
        );
      })}
    </div>
  );
};

// Time series line chart — for yearly trends
const LineChart = ({ data, xKey = 'y', yKey = 'n', height = 180, width = 600, formatX = (x)=>x, formatY = (y)=>y }) => {
  const maxY = Math.max(...data.map(d => d[yKey]));
  const padL = 36, padR = 12, padT = 12, padB = 28;
  const W = width, H = height;
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  const x = (i) => padL + (i / (data.length - 1)) * plotW;
  const y = (v) => padT + plotH - (v / maxY) * plotH;
  const pathD = data.map((d, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(d[yKey])}`).join(' ');
  const areaD = `${pathD} L${x(data.length-1)},${padT+plotH} L${x(0)},${padT+plotH} Z`;
  const yTicks = 4;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} style={{ width: '100%', height }}>
      {/* Y axis ticks */}
      {Array.from({ length: yTicks+1 }).map((_, i) => {
        const v = (maxY / yTicks) * (yTicks - i);
        const yy = padT + (plotH / yTicks) * i;
        return (
          <g key={i}>
            <line x1={padL} x2={W-padR} y1={yy} y2={yy} stroke="var(--ink-100)" />
            <text x={padL-6} y={yy+3} textAnchor="end" fontSize="10" fill="var(--ink-400)" fontFamily="var(--font-mono)">{formatY(Math.round(v))}</text>
          </g>
        );
      })}
      {/* Area */}
      <path d={areaD} fill="var(--accent)" opacity="0.08" />
      {/* Line */}
      <path d={pathD} fill="none" stroke="var(--accent)" strokeWidth="1.5" />
      {/* Dots */}
      {data.map((d, i) => (
        <circle key={i} cx={x(i)} cy={y(d[yKey])} r={2.5} fill="var(--accent)" />
      ))}
      {/* X ticks (every other) */}
      {data.map((d, i) => {
        if (i % 2 !== 0 && i !== data.length - 1) return null;
        return (
          <text key={i} x={x(i)} y={H-8} textAnchor="middle" fontSize="10" fill="var(--ink-400)" fontFamily="var(--font-mono)">{formatX(d[xKey])}</text>
        );
      })}
    </svg>
  );
};

// Donut for region breakdown
const Donut = ({ data, labelKey, valueKey, size = 160, colors = ['var(--data-1)','var(--data-2)','var(--data-3)','var(--data-4)','var(--data-5)','var(--data-6)','var(--data-7)','var(--data-8)'] }) => {
  const total = data.reduce((a,b)=>a+b[valueKey],0);
  const r = size/2 - 6;
  const cx = size/2, cy = size/2;
  let acc = 0;
  const segs = data.map((d, i) => {
    const start = acc / total * Math.PI * 2;
    acc += d[valueKey];
    const end = acc / total * Math.PI * 2;
    const large = end - start > Math.PI ? 1 : 0;
    const x1 = cx + r * Math.sin(start), y1 = cy - r * Math.cos(start);
    const x2 = cx + r * Math.sin(end), y2 = cy - r * Math.cos(end);
    return <path key={i} d={`M${cx},${cy} L${x1},${y1} A${r},${r} 0 ${large} 1 ${x2},${y2} Z`} fill={colors[i % colors.length]} />;
  });
  return (
    <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {segs}
        <circle cx={cx} cy={cy} r={r-28} fill="var(--card)" />
        <text x={cx} y={cy-2} textAnchor="middle" fontSize="11" fontFamily="var(--font-mono)" fill="var(--ink-400)" style={{ textTransform: 'uppercase', letterSpacing: '0.1em' }}>Total</text>
        <text x={cx} y={cy+14} textAnchor="middle" fontSize="16" fontFamily="var(--font-serif)" fill="var(--ink-900)" style={{ fontVariantNumeric: 'tabular-nums' }}>{total.toLocaleString('es-CL')}</text>
      </svg>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 4 }}>
        {data.slice(0,6).map((d, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '10px 1fr auto auto', gap: 8, alignItems: 'center', fontSize: 12 }}>
            <span style={{ width: 8, height: 8, background: colors[i % colors.length], borderRadius: 1 }} />
            <span style={{ color: 'var(--ink-700)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d[labelKey]}</span>
            <span className="num mono" style={{ color: 'var(--ink-400)', fontSize: 11 }}>{d[valueKey]}</span>
            <span className="num mono" style={{ color: 'var(--ink-400)', fontSize: 11, minWidth: 36, textAlign: 'right' }}>{((d[valueKey]/total)*100).toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
};

// KPI block — big number with serif
const KPI = ({ label, value, sub, trend }) => (
  <div style={{ padding: 'var(--s-5)' }}>
    <div className="upper" style={{ marginBottom: 6 }}>{label}</div>
    <div style={{ fontFamily: 'var(--font-serif)', fontSize: 36, fontWeight: 500, color: 'var(--ink-900)', fontVariantNumeric: 'tabular-nums', letterSpacing: '-0.02em', lineHeight: 1 }}>{value}</div>
    {sub && <div style={{ marginTop: 6, fontSize: 12, color: 'var(--ink-500)' }}>{sub}</div>}
    {trend && (
      <div style={{ marginTop: 8, display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, fontFamily: 'var(--font-mono)', color: trend.dir === 'up' ? 'var(--pos)' : 'var(--neg)' }}>
        <span>{trend.dir === 'up' ? '▲' : '▼'}</span><span>{trend.value}</span><span style={{ color: 'var(--ink-400)' }}>{trend.label}</span>
      </div>
    )}
  </div>
);

Object.assign(window, { Bar, LineChart, Donut, KPI });
