export default function StatusPill({ level = 0 }) {
  const map = {
    0: ['NORMAL', 'safe'],
    1: ['TIDE ALERT', 'watch'],
    2: ['YELLOW LEVEL', 'advisory'],
    3: ['ORANGE LEVEL', 'warning'],
    4: ['RED LEVEL', 'evacuate'],
  };
  const [label, tone] = map[level] || map[0];
  return <span className={`pill ${tone}`}>{label}</span>;
}
