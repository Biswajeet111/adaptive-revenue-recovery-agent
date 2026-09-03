import { useState, useMemo } from "react";
import { Search, ChevronRight, Zap } from "lucide-react";
import { formatCurrency, formatDate, humanize } from "../api";
import { StatusBadge } from "./StatusBadge";

export function CasesPage({ cases, onSelectCase }) {
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");

  const filteredCases = useMemo(() => {
    return cases.filter((item) => {
      const query = search.toLowerCase();
      const matchesSearch =
        !search ||
        String(item.id).includes(query) ||
        String(item.transaction_id).includes(query) ||
        String(item.classification || "").toLowerCase().includes(query) ||
        String(item.recommended_action || "").toLowerCase().includes(query);

      const matchesFilter =
        filter === "all" ||
        String(item.status || "").toLowerCase() === filter;

      return matchesSearch && matchesFilter;
    });
  }, [cases, search, filter]);

  return (
    <main className="page-content">
      <div className="page-heading">
        <div>
          <span className="page-kicker">RECOVERY INTELLIGENCE</span>
          <h2>Recovery cases</h2>
          <p>Analyze and inspect failed transaction recovery lifecycle state.</p>
        </div>

        <div className="heading-stat">
          <strong>{cases.length}</strong>
          <span>Total Cases</span>
        </div>
      </div>

      <div className="case-toolbar">
        <div className="search-box">
          <Search size={17} />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search cases, transactions or classifications..."
          />
        </div>

        <div className="filter-group">
          {[
            ["all", "All"],
            ["open", "Open"],
            ["recovered", "Recovered"],
            ["manual_review", "Manual"],
          ].map(([val, label]) => (
            <button
              key={val}
              className={`filter-btn ${filter === val ? "filter-active" : ""}`}
              onClick={() => setFilter(val)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="panel cases-full-panel">
        {filteredCases.length === 0 ? (
          <div className="empty-state">
            <Search size={28} />
            <strong>No matching cases found</strong>
            <span>Try adjusting your search terms or filter selection.</span>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="recovery-table cases-table">
              <thead>
                <tr>
                  <th>CASE</th>
                  <th>CLASSIFICATION</th>
                  <th>RECOVERABILITY</th>
                  <th>RISK SCORE</th>
                  <th>RECOMMENDED ACTION</th>
                  <th>REVENUE AT RISK</th>
                  <th>STATUS</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filteredCases.map((item) => {
                  const score = Number(item.risk_score || 0);

                  return (
                    <tr key={item.id} onClick={() => onSelectCase(item)}>
                      <td>
                        <div className="case-cell">
                          <span className="case-number">#{item.id}</span>
                          <div>
                            <strong>Tx #{item.transaction_id}</strong>
                            <small>{formatDate(item.created_at)}</small>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="classification-pill">
                          {humanize(item.classification)}
                        </span>
                      </td>
                      <td>
                        <span className={`recoverability-${item.recoverability}`}>
                          {humanize(item.recoverability)}
                        </span>
                      </td>
                      <td>
                        <strong
                          className={`risk-number ${
                            score >= 70
                              ? "risk-high"
                              : score >= 40
                              ? "risk-medium"
                              : "risk-low"
                          }`}
                        >
                          {score}
                        </strong>
                      </td>
                      <td>
                        <span className="recommendation">
                          <Zap size={13} />
                          <span>{humanize(item.recommended_action)}</span>
                        </span>
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
                            onSelectCase(item);
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
    </main>
  );
}
