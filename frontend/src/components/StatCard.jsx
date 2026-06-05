import { Card } from "./ui";

export default function StatCard({ label, value, sub, icon, accent = "text-blue-600" }) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <p className={`mt-2 text-2xl font-bold ${accent}`}>{value}</p>
      {sub && <p className="mt-1 text-xs text-slate-400">{sub}</p>}
    </Card>
  );
}
