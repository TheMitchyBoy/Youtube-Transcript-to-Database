import type { Stats } from "../types";

interface Props {
  stats: Stats | null;
  loading: boolean;
}

export function StatsBar({ stats, loading }: Props) {
  const items = [
    { label: "Transcripts", value: stats?.transcripts ?? 0 },
    { label: "Videos", value: stats?.videos ?? 0 },
    { label: "Channels", value: stats?.channels ?? 0 },
    { label: "Sync jobs", value: stats?.sync_jobs ?? 0 },
  ];

  return (
    <section className="stats-bar">
      {items.map((item) => (
        <div className="stat-card" key={item.label}>
          <div className="stat-value">{loading ? "—" : item.value}</div>
          <div className="stat-label">{item.label}</div>
        </div>
      ))}
    </section>
  );
}
