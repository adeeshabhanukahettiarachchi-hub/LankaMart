import { FormEvent, useCallback, useEffect, useState } from "react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { get, post } from "./api";

type Summary = { total_orders: number; total_sales: number; total_profit: number; avg_order_value: number; late_rate: number; return_rate: number };
type Month = { month: string; sales: number; profit: number };
type Group = { name: string; sales: number; profit: number; late_rate: number; return_rate: number };
type Order = { order_id: string; order_date: string; category: string; region: string; quantity: number; sales_amount: number; delivery_days: number; late_delivery: number; returned: number };
type Pred = { probability: number; risk_label: string; note: string };
type Metrics = { accuracy: number; precision: number; recall: number; f1: number; roc_auc: number };

const CATS = ["Electronics", "Fashion", "Home and Kitchen", "Beauty", "Sports"];
const REGIONS = ["Western", "Central", "Southern", "Northern", "Eastern", "North Western"];
const lkr = (n: number) => "LKR " + Math.round(n).toLocaleString("en-LK");

export default function App() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [monthly, setMonthly] = useState<Month[]>([]);
  const [cats, setCats] = useState<Group[]>([]);
  const [regions, setRegions] = useState<Group[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [s, m, c, r, o] = await Promise.all([
        get<Summary>("/api/summary"), get<Month[]>("/api/monthly-sales"), get<Group[]>("/api/category-sales"),
        get<Group[]>("/api/region-sales"), get<Order[]>("/api/recent-orders?limit=8"),
      ]);
      setSummary(s); setMonthly(m); setCats(c); setRegions(r); setOrders(o);
      get<Metrics>("/api/model-metrics").then(setMetrics).catch(() => setMetrics(null));
    } catch {
      setError("Cannot reach the backend. Start it with: uvicorn app.main:app --port 8000");
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  return (
    <main>
      <header>
        <div>
          <h1>LankaMart Dashboard</h1>
          <p className="muted">Synthetic data · decision support only</p>
        </div>
        <button onClick={load} disabled={loading}>{loading ? "Refreshing…" : "Refresh data"}</button>
      </header>

      {error && <div className="alert" role="alert">{error}</div>}

      {summary && (
        <section className="kpis">
          <Kpi label="Total orders" value={summary.total_orders.toLocaleString()} />
          <Kpi label="Sales" value={lkr(summary.total_sales)} />
          <Kpi label="Profit" value={lkr(summary.total_profit)} />
          <Kpi label="Avg order value" value={lkr(summary.avg_order_value)} />
          <Kpi label="Late delivery rate" value={`${summary.late_rate}%`} />
          <Kpi label="Return rate" value={`${summary.return_rate}%`} />
        </section>
      )}

      <section className="grid">
        <Card title="Monthly sales (LKR)">
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={monthly}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="month" fontSize={11} />
              <YAxis fontSize={11} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={(v: number) => lkr(v)} />
              <Area type="monotone" dataKey="sales" stroke="#2563eb" fill="#2563eb" fillOpacity={0.25} />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Sales by category (LKR)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={cats}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="name" fontSize={11} />
              <YAxis fontSize={11} tickFormatter={(v) => `${Math.round(v / 1000)}k`} />
              <Tooltip formatter={(v: number) => lkr(v)} />
              <Bar dataKey="sales" fill="#0d9488" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <Card title="Late-delivery rate by region (%)">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={regions}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="name" fontSize={11} />
              <YAxis fontSize={11} />
              <Tooltip />
              <Bar dataKey="late_rate" fill="#e11d48" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
        <RiskForm />
      </section>

      <Card title="Region comparison">
        <div className="scroll">
          <table>
            <thead><tr><th>Region</th><th>Sales</th><th>Profit</th><th>Late %</th><th>Return %</th></tr></thead>
            <tbody>{regions.map((r) => (
              <tr key={r.name}><td>{r.name}</td><td>{lkr(r.sales)}</td><td>{lkr(r.profit)}</td><td>{r.late_rate}</td><td>{r.return_rate}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </Card>

      <Card title="Recent orders">
        <div className="scroll">
          <table>
            <thead><tr><th>ID</th><th>Date</th><th>Category</th><th>Region</th><th>Qty</th><th>Sales</th><th>Days</th><th>Late</th></tr></thead>
            <tbody>{orders.map((o) => (
              <tr key={o.order_id}><td>{o.order_id}</td><td>{o.order_date}</td><td>{o.category}</td><td>{o.region}</td>
                <td>{o.quantity}</td><td>{lkr(o.sales_amount)}</td><td>{o.delivery_days}</td><td>{o.late_delivery ? "Yes" : "No"}</td></tr>
            ))}</tbody>
          </table>
        </div>
      </Card>

      {metrics && (
        <Card title="Model metrics (synthetic test set)">
          <p className="muted">Accuracy {metrics.accuracy} · Precision {metrics.precision} · Recall {metrics.recall} · F1 {metrics.f1} · ROC-AUC {metrics.roc_auc}. Technical demonstration only; not real-world performance.</p>
        </Card>
      )}
    </main>
  );
}

function Kpi({ label, value }: { label: string; value: string }) {
  return <div className="kpi"><span className="muted">{label}</span><strong>{value}</strong></div>;
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="card"><h2>{title}</h2>{children}</div>;
}

function RiskForm() {
  const [f, setF] = useState({ category: CATS[0], region: REGIONS[0], quantity: "1", unit_price: "25000", discount_rate: "0.1", returned: "0" });
  const [res, setRes] = useState<Pred | null>(null);
  const [err, setErr] = useState("");
  const set = (k: string) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr(""); setRes(null);
    try {
      setRes(await post<Pred>("/api/predict-late-delivery", {
        category: f.category, region: f.region, quantity: Number(f.quantity),
        unit_price: Number(f.unit_price), discount_rate: Number(f.discount_rate), returned: Number(f.returned),
      }));
    } catch (x) { setErr((x as Error).message); }
  }

  return (
    <Card title="Delivery-risk estimate">
      <form onSubmit={submit} className="form">
        <label>Category<select value={f.category} onChange={set("category")}>{CATS.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label>Region<select value={f.region} onChange={set("region")}>{REGIONS.map((c) => <option key={c}>{c}</option>)}</select></label>
        <label>Quantity<input type="number" min={1} max={50} value={f.quantity} onChange={set("quantity")} /></label>
        <label>Unit price (LKR)<input type="number" min={1} value={f.unit_price} onChange={set("unit_price")} /></label>
        <label>Discount (0–0.5)<input type="number" step="0.05" value={f.discount_rate} onChange={set("discount_rate")} /></label>
        <label>Returned<select value={f.returned} onChange={set("returned")}><option value="0">No</option><option value="1">Yes</option></select></label>
        <button type="submit">Estimate risk</button>
      </form>
      {err && <div className="alert" role="alert">{err}</div>}
      {res && (
        <div className={`result ${res.risk_label.toLowerCase()}`}>
          <strong>{res.risk_label} risk · {(res.probability * 100).toFixed(1)}%</strong>
          <p className="muted">{res.note}</p>
        </div>
      )}
    </Card>
  );
}
