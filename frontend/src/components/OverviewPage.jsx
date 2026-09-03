import { AlertCircle, TrendingUp, CreditCard, Zap, CheckCircle2 } from "lucide-react";
import { formatCurrency } from "../api";
import { HeroSection } from "./HeroSection";
import { MetricCard } from "./MetricCard";
import { PerformanceChart } from "./PerformanceChart";
import { Pipeline } from "./Pipeline";
import { RecoveryTable } from "./RecoveryTable";
import { ActivityFeed } from "./ActivityFeed";

export function OverviewPage({
  metrics,
  cases,
  webhooks,
  communications,
  onSelectCase,
  onViewCases,
}) {
  const recovery = metrics?.recovery || {};
  const transactions = metrics?.transactions || {};
  const actions = metrics?.recovery_actions || {};
  const recoveryRate = Number(recovery.recovery_rate_percent || 0);

  return (
    <main className="page-content">
      <HeroSection recovery={recovery} onViewCases={onViewCases} />

      <section className="metrics-grid">
        <MetricCard
          label="Revenue at risk"
          value={formatCurrency(recovery.revenue_at_risk)}
          detail={`${recovery.total_cases || 0} total cases`}
          icon={AlertCircle}
          trend="Exposure"
          accentTone="risk"
        />

        <MetricCard
          label="Revenue recovered"
          value={formatCurrency(recovery.recovered_revenue)}
          detail={`${recovery.recovered_cases || 0} recovered`}
          icon={TrendingUp}
          trend={`${recoveryRate}%`}
          accentTone="success"
        />

        <MetricCard
          label="Failed payments"
          value={transactions.failed || 0}
          detail={`of ${transactions.total || 0} total transactions`}
          icon={CreditCard}
          trend="Detected"
          accentTone="neutral"
        />

        <MetricCard
          label="Actions executed"
          value={actions.executed || 0}
          detail={`${actions.successful || 0} successful`}
          icon={Zap}
          trend={actions.failed ? `${actions.failed} failed` : "Healthy"}
          trendDirection={actions.failed ? "down" : "up"}
          accentTone="ai"
        />
      </section>

      <section className="dashboard-grid dashboard-grid-main">
        <PerformanceChart cases={cases} />

        <div className="panel health-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">SYSTEM HEALTH</span>
              <h3>Recovery engine status</h3>
            </div>
            <div className="health-check">
              <CheckCircle2 size={15} />
              <span>Healthy</span>
            </div>
          </div>

          <div className="health-score">
            <div className="health-ring">
              <div className="health-number">
                <strong>99</strong>
                <span>%</span>
              </div>
            </div>

            <div className="health-info">
              <strong>Autonomous operations</strong>
              <p>
                The recovery worker is monitoring failed payments and executing policy actions seamlessly.
              </p>
            </div>
          </div>

          <div className="health-stats">
            <div className="health-stat">
              <span>Pending Actions</span>
              <strong>{actions.pending || 0}</strong>
            </div>

            <div className="health-stat">
              <span>Executing</span>
              <strong>{actions.executing || 0}</strong>
            </div>

            <div className="health-stat">
              <span>Failed Actions</span>
              <strong>{actions.failed || 0}</strong>
            </div>
          </div>
        </div>
      </section>

      <Pipeline recovery={recovery} />

      <section className="dashboard-grid dashboard-grid-bottom">
        <RecoveryTable
          cases={cases}
          onSelect={onSelectCase}
          onViewAll={onViewCases}
        />

        <ActivityFeed webhooks={webhooks} communications={communications} />
      </section>
    </main>
  );
}
