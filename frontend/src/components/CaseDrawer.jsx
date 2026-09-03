import { useEffect, useState } from "react";
import {
  X,
  Loader2,
  Sparkles,
  Zap,
  Mail,
  Clock3,
  ExternalLink,
  ShieldAlert,
} from "lucide-react";
import { fetchJson, formatCurrency, formatDate, humanize } from "../api";
import { StatusBadge } from "./StatusBadge";

export function CaseDrawer({ caseItem, onClose, onOpenCase }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;

    if (!caseItem?.id) {
      return;
    }

    const loadDetails = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await fetchJson(`/api/v1/dashboard/cases/${caseItem.id}`);
        if (active) {
          setDetails(data);
        }
      } catch (err) {
        if (active) {
          console.error("Failed to load case details", err);
          setError(err.message || "Failed to load case details");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadDetails();

    return () => {
      active = false;
    };
  }, [caseItem?.id]);

  if (!caseItem) return null;

  // The endpoint returns { case: {...}, actions: [...], communications: [...] }
  const caseObj = details?.case || details || caseItem;
  const actions = Array.isArray(details?.actions) ? details.actions : [];
  const communications = Array.isArray(details?.communications)
    ? details.communications
    : [];

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />

      <aside className="case-drawer">
        <div className="drawer-header">
          <div>
            <span className="drawer-kicker">RECOVERY CASE INTELLIGENCE</span>
            <h2>Case #{caseItem.id}</h2>
          </div>
          <button className="icon-button drawer-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          {loading && (
            <div className="drawer-loading">
              <Loader2 size={18} className="spin" />
              <span>Fetching case intelligence...</span>
            </div>
          )}

          {error && (
            <div className="inline-error">
              <ShieldAlert size={16} />
              <span>{error}</span>
            </div>
          )}

          <div className="drawer-status-card">
            <div className="status-stat-item">
              <span>Status</span>
              <StatusBadge status={caseObj.status} />
            </div>

            <div className="status-stat-item">
              <span>Revenue at Risk</span>
              <strong>{formatCurrency(caseObj.revenue_at_risk)}</strong>
            </div>

            <div className="status-stat-item">
              <span>Recovered Amount</span>
              <strong className="recovered-text">
                {formatCurrency(caseObj.recovered_amount || 0)}
              </strong>
            </div>
          </div>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Sparkles size={16} />
              <span>AI Assessment & Risk Scoring</span>
            </div>

            <div className="intelligence-grid">
              <div className="intel-card">
                <span>Classification</span>
                <strong>{humanize(caseObj.classification)}</strong>
              </div>

              <div className="intel-card">
                <span>Recoverability</span>
                <strong className={`recoverability-${caseObj.recoverability}`}>
                  {humanize(caseObj.recoverability)}
                </strong>
              </div>

              <div className="intel-card">
                <span>Risk Score</span>
                <strong>{caseObj.risk_score ?? 0} / 100</strong>
              </div>

              <div className="intel-card">
                <span>Recommended Strategy</span>
                <strong>{humanize(caseObj.recommended_action)}</strong>
              </div>
            </div>
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Zap size={16} />
              <span>Recovery Actions History ({actions.length})</span>
            </div>

            {actions.length === 0 ? (
              <div className="drawer-empty">
                No recovery actions executed yet. Pending automated evaluation.
              </div>
            ) : (
              <div className="drawer-actions">
                {actions.map((act) => (
                  <div className="drawer-action-card" key={act.id}>
                    <div className="action-top">
                      <div className="action-type">
                        <Zap size={14} />
                        <strong>{humanize(act.action_type)}</strong>
                      </div>
                      <StatusBadge status={act.status} />
                    </div>

                    <div className="action-details">
                      <span>Channel: {humanize(act.channel)}</span>
                      <span>Attempts: {act.attempt_count || 0}</span>
                      {act.last_attempt_at && (
                        <span>Last Attempt: {formatDate(act.last_attempt_at)}</span>
                      )}
                    </div>

                    {act.result && (
                      <div className="action-result">
                        <small>Result:</small>
                        <p>{act.result}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Mail size={16} />
              <span>Customer Communications ({communications.length})</span>
            </div>

            {communications.length === 0 ? (
              <div className="drawer-empty">No communications sent for this case.</div>
            ) : (
              <div className="drawer-actions">
                {communications.map((comm) => (
                  <div className="drawer-action-card" key={comm.id}>
                    <div className="action-top">
                      <div className="action-type">
                        <Mail size={14} />
                        <strong>{humanize(comm.template_name)}</strong>
                      </div>
                      <StatusBadge status={comm.status} />
                    </div>
                    <div className="action-details">
                      <span>Channel: {humanize(comm.channel)}</span>
                      {comm.sent_at && <span>Sent: {formatDate(comm.sent_at)}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Clock3 size={16} />
              <span>Audit Timeline</span>
            </div>

            <div className="timeline">
              <div className="timeline-item">
                <span className="timeline-dot" />
                <div className="timeline-content">
                  <strong>Case Created</strong>
                  <small>{formatDate(caseObj.created_at)}</small>
                </div>
              </div>

              {caseObj.updated_at && (
                <div className="timeline-item">
                  <span className="timeline-dot" />
                  <div className="timeline-content">
                    <strong>State Updated</strong>
                    <small>{formatDate(caseObj.updated_at)}</small>
                  </div>
                </div>
              )}

              {caseObj.recovered_at && (
                <div className="timeline-item timeline-success">
                  <span className="timeline-dot done" />
                  <div className="timeline-content">
                    <strong>Revenue Recovered</strong>
                    <small>{formatDate(caseObj.recovered_at)}</small>
                  </div>
                </div>
              )}
            </div>
          </section>

          {onOpenCase && (
            <button
              className="drawer-detail-button"
              onClick={() => onOpenCase(caseItem)}
            >
              <span>View Full Case</span>
              <ExternalLink size={15} />
            </button>
          )}
        </div>
      </aside>
    </>
  );
}
