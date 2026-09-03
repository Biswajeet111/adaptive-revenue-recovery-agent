import { useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { formatCurrency } from "../api";

export function PerformanceChart({ cases }) {
  const chartData = useMemo(() => {
    if (!cases || !cases.length) {
      return [
        { name: "Initial", atRisk: 0, recovered: 0 },
        { name: "Current", atRisk: 0, recovered: 0 },
      ];
    }

    const sorted = [...cases]
      .sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));

    return sorted.map((item, index) => ({
      name: `Case #${item.id || index + 1}`,
      atRisk: Number(item.revenue_at_risk || 0),
      recovered: Number(item.recovered_amount || 0),
    }));
  }, [cases]);

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">RECOVERY METRICS</span>
          <h3>Revenue exposure by case</h3>
        </div>

        <div className="chart-legend">
          <span className="legend-item">
            <i className="legend-dot legend-risk" />
            Revenue at Risk
          </span>
          <span className="legend-item">
            <i className="legend-dot legend-recovered" />
            Recovered Amount
          </span>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height={230}>
          <AreaChart
            data={chartData}
            margin={{ top: 15, right: 15, left: -15, bottom: 0 }}
          >
            <defs>
              <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>

            <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f1f5f9" />

            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickFormatter={(v) => `₹${v}`}
            />

            <Tooltip
              formatter={(value) => formatCurrency(value)}
              contentStyle={{
                borderRadius: 10,
                border: "1px solid #e2e8f0",
                boxShadow: "0 10px 25px rgba(0,0,0,0.08)",
                fontSize: "12px",
              }}
            />

            <Area
              type="monotone"
              dataKey="atRisk"
              stroke="#ef4444"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#riskGrad)"
              name="Revenue at Risk"
            />

            <Area
              type="monotone"
              dataKey="recovered"
              stroke="#10b981"
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#recGrad)"
              name="Recovered Amount"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
