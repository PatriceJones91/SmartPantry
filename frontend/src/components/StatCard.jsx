export default function StatCard({ label, value, note }) { return <div className="card statCard"><p>{label}</p><h2>{value}</h2>{note && <span>{note}</span>}</div>; }
