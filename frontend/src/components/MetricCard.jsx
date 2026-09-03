import { ArrowUpRight, ArrowDownRight } from "lucide-react";

export function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  trend,
  trendDirection = "up",
  accentTone = "neutral",
}) {
  return (
    <div className={`metric-card metric-${accentTone}`}>
      <div className="metric-top">
        <span className="metric-label">{label}</span>
        {Icon && (
          <div className="metric-icon">
            <Icon size={18} />
          </div>
        )}
      </div>

      <div className="metric-value">{value}</div>

      <div className="metric-footer">
        {trend !== undefined && (
          <span
            className={`metric-trend ${
              trendDirection === "down" ? "trend-down" : "trend-up"
            }`}
          >
            {trendDirection === "down" ? (
              <ArrowDownRight size={14} />
            ) : (
              <ArrowUpRight size={14} />
            )}
            {trend}
          </span>
        )}
        {detail && <span className="metric-detail">{detail}</span>}
      </div>
    </div>
  );
}
