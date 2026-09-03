import { Target, ChevronRight, ArrowUpRight } from "lucide-react";
import { formatCurrency, formatRelativeDate, humanize } from "../api";
import { StatusBadge } from "./StatusBadge";

export function RecoveryTable({ cases, onSelect, onViewAll }) {
  const recentCases = cases.slice(0, 6);

  return (
    <div className="panel table-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">RECOVERY QUEUE</span>
          <h3>Recent active cases</h3>
        </div>

        {onViewAll && (
          <button className="text-button" onClick={onViewAll}>
            <span>View all cases</span>
            <ArrowUpRight size={15} />
          </button>
        )}
      </div>

      {recentCases.length === 0 ? (
        <div className="empty-state">
          <Target size={28} />
          <strong>No recovery cases</strong>
          <span>Recovery cases will populate here when payment failures occur.</span>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="recovery-table">
            <thead>
              <tr>
                <th>CASE</th>
                <th>CLASSIFICATION</th>
                <th>RISK SCORE</th>
                <th>REVENUE AT RISK</th>
                <th>STATUS</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {recentCases.map((item) => {
                const score = Number(item.risk_score || 0);

                return (
                  <tr key={item.id} onClick={() => onSelect(item)}>
                    <td>
                      <div className="case-cell">
                        <span className="case-number">#{item.id}</span>
                        <div>
                          <strong>Tx #{item.transaction_id}</strong>
                          <small>{formatRelativeDate(item.created_at)}</small>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="classification-pill">
                        {humanize(item.classification)}
                      </span>
                    </td>
                    <td>
                      <div className="risk-cell">
                        <span
                          className={`risk-number ${
                            score >= 70
                              ? "risk-high"
                              : score >= 40
                              ? "risk-medium"
                              : "risk-low"
                          }`}
                        >
                          {score}
                        </span>
                        <div className="risk-bar">
                          <span style={{ width: `${Math.min(100, score)}%` }} />
                        </div>
                      </div>
                    </td>
                    <td>
                      <strong className="money-value">
                        {formatCurrency(item.revenue_at_risk)}
                      </strong>
                    </td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>
                      <button
                        className="row-arrow"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(item);
                        }}
                        aria-label="View case details"
                      >
                        <ChevronRight size={17} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
