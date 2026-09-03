import { ChevronRight, AlertCircle, Zap, CheckCircle2 } from "lucide-react";
import { formatCurrency } from "../api";

export function HeroSection({ recovery, onViewCases }) {
  const recovered = Number(recovery?.recovered_revenue || 0);
  const atRisk = Number(recovery?.revenue_at_risk || 0);
  const rate = Number(recovery?.recovery_rate_percent || 0);

  return (
    <section className="hero">
      <div className="hero-glow hero-glow-one" />
      <div className="hero-glow hero-glow-two" />

      <div className="hero-content">
        <div className="hero-eyebrow">
          <span className="hero-eyebrow-dot" />
          AUTONOMOUS REVENUE RECOVERY AGENT
        </div>

        <h2>
          ReviveAI
          <br />
          <span>Intelligent Revenue Protection</span>
        </h2>

        <p className="hero-description">
          ReviveAI continuously inspects payment decline codes, assigns risk scores,
          executes optimal recovery actions, and prevents subscriber churn.
        </p>

        <button className="hero-button" onClick={onViewCases}>
          <span>Explore recovery cases</span>
          <ChevronRight size={17} />
        </button>
      </div>

      <div className="hero-visual">
        <div className="recovery-orbit">
          <div className="orbit-ring orbit-ring-one" />
          <div className="orbit-ring orbit-ring-two" />

          <div className="orbit-center">
            <img
              src="/branding/reviveai-icon.png"
              alt="ReviveAI"
              className="orbit-icon-img"
            />
            <strong>ReviveAI Core</strong>
          </div>

          <div className="orbit-node node-risk">
            <AlertCircle size={14} />
            <span>Risk Analysis</span>
          </div>

          <div className="orbit-node node-action">
            <Zap size={14} />
            <span>Auto Action</span>
          </div>

          <div className="orbit-node node-recovered">
            <CheckCircle2 size={14} />
            <span>Captured</span>
          </div>
        </div>
      </div>

      <div className="hero-footer">
        <div className="hero-stat-item">
          <span>Revenue at risk</span>
          <strong>{formatCurrency(atRisk)}</strong>
        </div>

        <div className="hero-divider" />

        <div className="hero-stat-item">
          <span>Recovered revenue</span>
          <strong>{formatCurrency(recovered)}</strong>
        </div>

        <div className="hero-divider" />

        <div className="hero-stat-item">
          <span>Recovery rate</span>
          <strong>{rate}%</strong>
        </div>
      </div>
    </section>
  );
}
