import { useMemo } from "react";
import { Activity, Webhook, Mail } from "lucide-react";
import { formatRelativeDate, humanize } from "../api";
import { StatusBadge } from "./StatusBadge";

export function ActivityFeed({ webhooks = [], communications = [] }) {
  const activities = useMemo(() => {
    const webhookItems = webhooks.map((item) => ({
      id: `webhook-${item.id}`,
      type: "webhook",
      icon: Webhook,
      title: humanize(item.event_type),
      description: item.processed
        ? `Event ${item.event_id || ""} processed`
        : `Event ${item.event_id || ""} pending`,
      status: item.processed ? "processed" : "pending",
      timestamp: item.processed_at || item.received_at || item.created_at,
    }));

    const communicationItems = communications.map((item) => ({
      id: `comm-${item.id}`,
      type: "communication",
      icon: Mail,
      title: humanize(item.template_name || item.channel || "Message"),
      description: `${humanize(item.channel || "email")} communication`,
      status: item.status || "sent",
      timestamp: item.sent_at || item.created_at,
    }));

    return [...webhookItems, ...communicationItems]
      .sort((a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0))
      .slice(0, 8);
  }, [webhooks, communications]);

  return (
    <div className="panel activity-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">LIVE ACTIVITY</span>
          <h3>Real-time events</h3>
        </div>

        <div className="activity-live">
          <span className="live-pulse" />
          <span>Stream</span>
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="empty-state compact">
          <Activity size={24} />
          <span>No recent events logged.</span>
        </div>
      ) : (
        <div className="activity-list">
          {activities.map((act) => {
            const Icon = act.icon;

            return (
              <div className="activity-item" key={act.id}>
                <div className={`activity-icon activity-${act.type}`}>
                  <Icon size={15} />
                </div>
                <div className="activity-content">
                  <strong>{act.title}</strong>
                  <span>{act.description}</span>
                </div>
                <div className="activity-meta">
                  <StatusBadge status={act.status} />
                  <time>{formatRelativeDate(act.timestamp)}</time>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
