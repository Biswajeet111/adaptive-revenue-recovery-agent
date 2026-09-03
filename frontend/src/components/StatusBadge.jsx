import { statusTone, humanize } from "../api";

export function StatusBadge({ status, label }) {
  const tone = statusTone(status);
  const displayText = label || humanize(status);

  return (
    <span className={`status-badge status-${tone}`}>
      <span className="status-dot" />
      {displayText}
    </span>
  );
}
