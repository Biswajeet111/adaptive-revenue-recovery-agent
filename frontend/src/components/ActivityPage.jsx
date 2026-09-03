import { useMemo } from "react";
import { Activity, Webhook, Mail, ShieldCheck } from "lucide-react";
import { formatDate, humanize } from "../api";
import { StatusBadge } from "./StatusBadge";

export function ActivityPage({ webhooks = [], communications = [] }) {
  const events = useMemo(() => {
    const webhookEvents = webhooks.map((item) => ({
      id: `w-${item.id}`,
      icon: Webhook,
      type: "Webhook",
      title: humanize(item.event_type),
      description: item.processed
        ? `Razorpay webhook event (${item.event_id || ""}) processed.`
        : `Razorpay webhook event (${item.event_id || ""}) received, pending execution.`,
      status: item.processed ? "processed" : "pending",
      timestamp: item.processed_at || item.received_at || item.created_at,
    }));

    const communicationEvents = communications.map((item) => ({
      id: `c-${item.id}`,
      icon: Mail,
      type: "Communication",
      title: humanize(item.template_name || item.channel || "Message"),
      description: `${humanize(item.channel || "email")} communication dispatched via ${humanize(
        item.provider || "SMTP"
      )}.`,
      status: item.status || "sent",
      timestamp: item.sent_at || item.created_at,
    }));

    return [...webhookEvents, ...communicationEvents].sort(
      (a, b) => new Date(b.timestamp || 0) - new Date(a.timestamp || 0)
    );
  }, [webhooks, communications]);

  const processedWebhooks = webhooks.filter((w) => w.processed).length;

  return (
    <main className="page-content">
      <div className="page-heading">
        <div>
          <span className="page-kicker">EVENT STREAM</span>
          <h2>System activity feed</h2>
          <p>Real-time audit log of webhooks and automated messaging.</p>
        </div>

        <div className="heading-stat">
          <strong>{events.length}</strong>
          <span>Total Events</span>
        </div>
      </div>

      <div className="activity-layout">
        <div className="panel event-stream-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">EVENT STREAM</span>
              <h3>Recent events log</h3>
            </div>
            <div className="activity-live">
              <span className="live-pulse" />
              <span>Live Feed</span>
            </div>
          </div>

          {events.length === 0 ? (
            <div className="empty-state">
              <Activity size={28} />
              <strong>No system activity events recorded</strong>
              <span>Incoming Razorpay webhooks and communications will show up here.</span>
            </div>
          ) : (
            <div className="event-stream">
              {events.map((event) => {
                const Icon = event.icon;

                return (
                  <div className="event-row" key={event.id}>
                    <div className="event-icon">
                      <Icon size={16} />
                    </div>

                    <div className="event-body">
                      <div className="event-title-row">
                        <strong>{event.title}</strong>
                        <StatusBadge status={event.status} />
                      </div>
                      <p>{event.description}</p>
                      <small>{formatDate(event.timestamp)}</small>
                    </div>

                    <span className="event-type-badge">{event.type}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="panel activity-summary-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">OPERATIONS</span>
              <h3>Event summary</h3>
            </div>
          </div>

          <div className="event-summary-cards">
            <div className="summary-card">
              <div className="summary-icon">
                <Webhook size={18} />
              </div>
              <div className="summary-info">
                <span>Webhooks Received</span>
                <strong>{webhooks.length}</strong>
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-icon">
                <Mail size={18} />
              </div>
              <div className="summary-info">
                <span>Communications Sent</span>
                <strong>{communications.length}</strong>
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-icon">
                <ShieldCheck size={18} />
              </div>
              <div className="summary-info">
                <span>Processed Webhooks</span>
                <strong>{processedWebhooks}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
