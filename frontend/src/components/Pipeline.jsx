import { Fragment } from "react";
import { CreditCard, Sparkles, Zap, CheckCircle2, AlertCircle, ChevronRight } from "lucide-react";

export function Pipeline({ recovery }) {
  const total = recovery?.total_cases || 0;
  const open = recovery?.open_cases || 0;
  const recovered = recovery?.recovered_cases || 0;
  const manual = recovery?.manual_review_cases || 0;

  const stages = [
    {
      label: "Failed Payments",
      value: total,
      icon: CreditCard,
      description: "Payment failures ingested",
    },
    {
      label: "AI Classified",
      value: total,
      icon: Sparkles,
      description: "Decline reason categorized",
    },
    {
      label: "Recovery Actions",
      value: open,
      icon: Zap,
      description: "Automated retry / dunning queue",
    },
    {
      label: "Revenue Recovered",
      value: recovered,
      icon: CheckCircle2,
      description: "Funds successfully captured",
    },
  ];

  return (
    <div className="panel pipeline-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">AUTOMATION PIPELINE</span>
          <h3>Recovery lifecycle stream</h3>
        </div>

        {manual > 0 && (
          <span className="manual-alert">
            <AlertCircle size={14} />
            {manual} manual review
          </span>
        )}
      </div>

      <div className="pipeline">
        {stages.map((stage, index) => {
          const Icon = stage.icon;

          return (
            <Fragment key={stage.label}>
              <div className="pipeline-stage">
                <div className="pipeline-icon">
                  <Icon size={18} />
                </div>
                <div className="pipeline-info">
                  <div className="pipeline-value">{stage.value}</div>
                  <div className="pipeline-label">{stage.label}</div>
                  <div className="pipeline-description">{stage.description}</div>
                </div>
              </div>

              {index < stages.length - 1 && (
                <div className="pipeline-arrow">
                  <ChevronRight size={18} />
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
