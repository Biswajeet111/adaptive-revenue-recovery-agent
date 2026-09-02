import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Activity,
  AlertCircle,
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  CheckCircle2,
  ChevronRight,
  Clock3,
  CreditCard,
  Database,
  ExternalLink,
  LayoutDashboard,
  Loader2,
  Mail,
  Menu,
  RefreshCw,
  Search,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Webhook,
  X,
  Zap,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import "./App.css";


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";


async function fetchJson(path) {
  const response = await fetch(
    `${API_BASE_URL}${path}`
  );

  if (!response.ok) {
    throw new Error(
      `Request failed: ${response.status}`
    );
  }

  return response.json();
}


function formatCurrency(value) {
  const number = Number(value || 0);

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(number);
}


function formatDate(value) {
  if (!value) return "—";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}


function formatRelativeDate(value) {
  if (!value) return "Unknown time";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "Unknown time";
  }

  const diff =
    Date.now() - date.getTime();

  const minutes = Math.floor(
    diff / (1000 * 60)
  );

  if (minutes < 1) return "Just now";

  if (minutes < 60) {
    return `${minutes}m ago`;
  }

  const hours = Math.floor(
    minutes / 60
  );

  if (hours < 24) {
    return `${hours}h ago`;
  }

  const days = Math.floor(
    hours / 24
  );

  return `${days}d ago`;
}


function humanize(value) {
  if (!value) return "Unknown";

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}


function statusTone(status) {
  const normalized =
    String(status || "").toLowerCase();

  if (
    [
      "recovered",
      "successful",
      "executed",
      "processed",
      "captured",
      "paid",
      "delivered",
    ].includes(normalized)
  ) {
    return "success";
  }

  if (
    [
      "failed",
      "cancelled",
      "expired",
      "manual_review",
    ].includes(normalized)
  ) {
    return "danger";
  }

  if (
    [
      "executing",
      "pending",
      "open",
      "partially_paid",
    ].includes(normalized)
  ) {
    return "warning";
  }

  return "neutral";
}


function StatusBadge({ status }) {
  const tone = statusTone(status);

  return (
    <span
      className={`status-badge status-${tone}`}
    >
      <span className="status-dot" />
      {humanize(status)}
    </span>
  );
}


function MetricCard({
  label,
  value,
  detail,
  icon: Icon,
  trend,
  trendDirection = "up",
}) {
  return (
    <div className="metric-card">
      <div className="metric-card-top">
        <div className="metric-icon">
          <Icon size={18} />
        </div>

        {trend !== undefined && (
          <span
            className={`metric-trend ${trendDirection === "down"
              ? "trend-down"
              : ""
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
      </div>

      <div className="metric-label">
        {label}
      </div>

      <div className="metric-value">
        {value}
      </div>

      {detail && (
        <div className="metric-detail">
          {detail}
        </div>
      )}
    </div>
  );
}


function Sidebar({
  page,
  setPage,
  mobileOpen,
  setMobileOpen,
}) {
  const navigation = [
    {
      id: "overview",
      label: "Overview",
      icon: LayoutDashboard,
    },
    {
      id: "cases",
      label: "Recovery Cases",
      icon: Target,
    },
    {
      id: "activity",
      label: "Activity",
      icon: Activity,
    },
  ];

  return (
    <>
      {mobileOpen && (
        <div
          className="sidebar-overlay"
          onClick={() =>
            setMobileOpen(false)
          }
        />
      )}

      <aside
        className={`sidebar ${mobileOpen
          ? "sidebar-mobile-open"
          : ""
          }`}
      >
        <div className="sidebar-brand">
          <div className="brand-mark">
            <Sparkles size={19} />
          </div>

          <div>
            <div className="brand-name">
              RecoveryAI
            </div>

            <div className="brand-caption">
              Revenue intelligence
            </div>
          </div>

          <button
            className="mobile-close"
            onClick={() =>
              setMobileOpen(false)
            }
          >
            <X size={18} />
          </button>
        </div>

        <div className="sidebar-section-label">
          WORKSPACE
        </div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon;

            return (
              <button
                key={item.id}
                className={`sidebar-link ${page === item.id
                  ? "sidebar-link-active"
                  : ""
                  }`}
                onClick={() => {
                  setPage(item.id);
                  setMobileOpen(false);
                }}
              >
                <Icon size={18} />

                <span>
                  {item.label}
                </span>

                {item.id === "cases" && (
                  <span className="sidebar-count">
                    Live
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-section-label sidebar-section-spaced">
          SYSTEM
        </div>

        <div className="sidebar-system">
          <div className="system-item">
            <span className="system-icon">
              <Database size={15} />
            </span>

            <div>
              <strong>PostgreSQL</strong>
              <small>Connected</small>
            </div>

            <span className="system-online" />
          </div>

          <div className="system-item">
            <span className="system-icon">
              <Webhook size={15} />
            </span>

            <div>
              <strong>Razorpay</strong>
              <small>Webhook active</small>
            </div>

            <span className="system-online" />
          </div>

          <div className="system-item">
            <span className="system-icon">
              <Mail size={15} />
            </span>

            <div>
              <strong>SMTP</strong>
              <small>Delivery ready</small>
            </div>

            <span className="system-online" />
          </div>
        </div>

        <div className="sidebar-bottom">
          <div className="agent-status">
            <div className="agent-status-icon">
              <Zap size={16} />
            </div>

            <div>
              <strong>
                Recovery Agent
              </strong>

              <span>
                Autonomous worker active
              </span>
            </div>

            <span className="pulse-dot" />
          </div>

          <div className="sidebar-version">
            RecoveryAI v0.1.0
          </div>
        </div>
      </aside>
    </>
  );
}


function Topbar({
  page,
  onRefresh,
  loading,
  setMobileOpen,
  lastUpdated,
}) {
  const titles = {
    overview: [
      "Revenue Overview",
      "Monitor recovery performance",
    ],
    cases: [
      "Recovery Cases",
      "Investigate and track failed payments",
    ],
    activity: [
      "System Activity",
      "Live recovery and payment events",
    ],
  };

  const [title, subtitle] =
    titles[page] || titles.overview;

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="mobile-menu"
          onClick={() =>
            setMobileOpen(true)
          }
        >
          <Menu size={20} />
        </button>

        <div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <div className="topbar-actions">
        <span className="last-updated">
          <span className="live-indicator" />

          {lastUpdated
            ? `Updated ${formatRelativeDate(
              lastUpdated
            )}`
            : "Live data"}
        </span>

        <button className="icon-button">
          <Bell size={18} />
        </button>

        <button
          className="refresh-button"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw
            size={16}
            className={
              loading
                ? "spin"
                : ""
            }
          />

          Refresh
        </button>
      </div>
    </header>
  );
}


function HeroSection({
  recovery,
  onViewCases,
}) {
  const recovered =
    Number(
      recovery?.recovered_revenue || 0
    );

  const atRisk =
    Number(
      recovery?.revenue_at_risk || 0
    );

  const rate =
    Number(
      recovery?.recovery_rate_percent || 0
    );

  return (
    <section className="hero">
      <div className="hero-glow hero-glow-one" />
      <div className="hero-glow hero-glow-two" />

      <div className="hero-content">
        <div className="hero-eyebrow">
          <span className="hero-eyebrow-dot" />
          AUTONOMOUS RECOVERY ENGINE
        </div>

        <h2>
          Recover revenue
          <br />
          <span>before it is lost.</span>
        </h2>

        <p className="hero-description">
          AI analyzes payment failures,
          selects the safest recovery
          strategy, executes actions, and
          learns from the outcome.
        </p>

        <button
          className="hero-button"
          onClick={onViewCases}
        >
          Explore recovery cases
          <ChevronRight size={17} />
        </button>
      </div>

      <div className="hero-visual">
        <div className="recovery-orbit">
          <div className="orbit-ring orbit-ring-one" />
          <div className="orbit-ring orbit-ring-two" />
          <div className="orbit-ring orbit-ring-three" />

          <div className="orbit-center">
            <Sparkles size={22} />
            <strong>AI</strong>
            <span>Recovery</span>
          </div>

          <div className="orbit-node node-risk">
            <AlertCircle size={15} />
            <span>At risk</span>
          </div>

          <div className="orbit-node node-action">
            <Zap size={15} />
            <span>Action</span>
          </div>

          <div className="orbit-node node-recovered">
            <CheckCircle2 size={15} />
            <span>Recovered</span>
          </div>
        </div>
      </div>

      <div className="hero-footer">
        <div>
          <span>Revenue at risk</span>
          <strong>
            {formatCurrency(atRisk)}
          </strong>
        </div>

        <div className="hero-divider" />

        <div>
          <span>Recovered</span>
          <strong>
            {formatCurrency(recovered)}
          </strong>
        </div>

        <div className="hero-divider" />

        <div>
          <span>Recovery rate</span>
          <strong>{rate}%</strong>
        </div>
      </div>
    </section>
  );
}


function PerformanceChart({
  cases,
}) {
  const chartData = useMemo(() => {
    if (!cases.length) {
      return [
        {
          name: "No data",
          atRisk: 0,
          recovered: 0,
        },
      ];
    }

    const sorted = [...cases]
      .sort(
        (a, b) =>
          new Date(a.created_at) -
          new Date(b.created_at)
      )
      .slice(-8);

    return sorted.map(
      (item, index) => ({
        name: `Case ${index + 1}`,
        atRisk: Number(
          item.revenue_at_risk || 0
        ),
        recovered: Number(
          item.recovered_amount || 0
        ),
      })
    );
  }, [cases]);

  return (
    <div className="panel chart-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            RECOVERY PERFORMANCE
          </span>

          <h3>Revenue recovery</h3>
        </div>

        <div className="chart-legend">
          <span>
            <i className="legend-risk" />
            At risk
          </span>

          <span>
            <i className="legend-recovered" />
            Recovered
          </span>
        </div>
      </div>

      <div className="chart-wrapper">
        <ResponsiveContainer
          width="100%"
          height="100%"
        >
          <AreaChart
            data={chartData}
            margin={{
              top: 10,
              right: 8,
              left: -20,
              bottom: 0,
            }}
          >
            <defs>
              <linearGradient
                id="riskGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopOpacity={0.2}
                />

                <stop
                  offset="100%"
                  stopOpacity={0}
                />
              </linearGradient>

              <linearGradient
                id="recoveredGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop
                  offset="0%"
                  stopOpacity={0.2}
                />

                <stop
                  offset="100%"
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>

            <CartesianGrid
              vertical={false}
              strokeDasharray="4 4"
              opacity={0.5}
            />

            <XAxis
              dataKey="name"
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11 }}
            />

            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fontSize: 11 }}
              tickFormatter={(value) =>
                `₹${value}`
              }
            />

            <Tooltip
              formatter={(value) =>
                formatCurrency(value)
              }
              contentStyle={{
                borderRadius: 12,
                border: "1px solid #e5e7eb",
                boxShadow:
                  "0 10px 30px rgba(15,23,42,.12)",
              }}
            />

            <Area
              type="monotone"
              dataKey="atRisk"
              strokeWidth={2}
              fill="url(#riskGradient)"
              fillOpacity={1}
              name="At risk"
            />

            <Area
              type="monotone"
              dataKey="recovered"
              strokeWidth={2.5}
              fill="url(#recoveredGradient)"
              fillOpacity={1}
              name="Recovered"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


function Pipeline({
  recovery,
}) {
  const total =
    recovery?.total_cases || 0;

  const open =
    recovery?.open_cases || 0;

  const recovered =
    recovery?.recovered_cases || 0;

  const manual =
    recovery?.manual_review_cases || 0;

  const stages = [
    {
      label: "Failed payments",
      value: recovery?.total_cases || 0,
      icon: CreditCard,
      description:
        "Payment failures detected",
    },
    {
      label: "AI classified",
      value: total,
      icon: Sparkles,
      description:
        "Failure reason analyzed",
    },
    {
      label: "Recovery actions",
      value: open,
      icon: Zap,
      description:
        "Actions awaiting execution",
    },
    {
      label: "Recovered",
      value: recovered,
      icon: CheckCircle2,
      description:
        "Revenue successfully recovered",
    },
  ];

  return (
    <div className="panel pipeline-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            RECOVERY PIPELINE
          </span>

          <h3>
            From failure to recovery
          </h3>
        </div>

        {manual > 0 && (
          <span className="manual-alert">
            <AlertCircle size={14} />
            {manual} manual review
          </span>
        )}
      </div>

      <div className="pipeline">
        {stages.map(
          (stage, index) => {
            const Icon = stage.icon;

            return (
              <div
                className="pipeline-stage-wrap"
                key={stage.label}
              >
                <div className="pipeline-stage">
                  <div className="pipeline-icon">
                    <Icon size={18} />
                  </div>

                  <div className="pipeline-value">
                    {stage.value}
                  </div>

                  <div className="pipeline-label">
                    {stage.label}
                  </div>

                  <div className="pipeline-description">
                    {stage.description}
                  </div>
                </div>

                {index <
                  stages.length - 1 && (
                    <div className="pipeline-arrow">
                      <ChevronRight size={17} />
                    </div>
                  )}
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}


function RecoveryTable({
  cases,
  onSelect,
  onViewAll,
}) {
  const recentCases =
    cases.slice(0, 6);

  return (
    <div className="panel table-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            RECOVERY QUEUE
          </span>

          <h3>Recent cases</h3>
        </div>

        <button
          className="text-button"
          onClick={onViewAll}
        >
          View all
          <ArrowUpRight size={15} />
        </button>
      </div>

      {recentCases.length === 0 ? (
        <div className="empty-state">
          <Target size={28} />

          <strong>
            No recovery cases
          </strong>

          <span>
            Recovery cases will appear
            here when payment failures
            are detected.
          </span>
        </div>
      ) : (
        <div className="table-scroll">
          <table className="recovery-table">
            <thead>
              <tr>
                <th>CASE</th>
                <th>CLASSIFICATION</th>
                <th>RISK</th>
                <th>REVENUE AT RISK</th>
                <th>STATUS</th>
                <th />
              </tr>
            </thead>

            <tbody>
              {recentCases.map(
                (item) => (
                  <tr
                    key={item.id}
                    onClick={() =>
                      onSelect(item)
                    }
                  >
                    <td>
                      <div className="case-cell">
                        <span className="case-number">
                          #{item.id}
                        </span>

                        <div>
                          <strong>
                            Transaction #
                            {
                              item.transaction_id
                            }
                          </strong>

                          <small>
                            {formatRelativeDate(
                              item.created_at
                            )}
                          </small>
                        </div>
                      </div>
                    </td>

                    <td>
                      <span className="classification">
                        {humanize(
                          item.classification
                        )}
                      </span>
                    </td>

                    <td>
                      <div className="risk-cell">
                        <span
                          className={`risk-number ${Number(
                            item.risk_score
                          ) >= 70
                            ? "risk-high"
                            : Number(
                              item.risk_score
                            ) >= 40
                              ? "risk-medium"
                              : "risk-low"
                            }`}
                        >
                          {item.risk_score ??
                            0}
                        </span>

                        <div className="risk-bar">
                          <span
                            style={{
                              width: `${Math.min(
                                100,
                                Number(
                                  item.risk_score ||
                                  0
                                )
                              )}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>

                    <td>
                      <strong className="money-value">
                        {formatCurrency(
                          item.revenue_at_risk
                        )}
                      </strong>
                    </td>

                    <td>
                      <StatusBadge
                        status={
                          item.status
                        }
                      />
                    </td>

                    <td>
                      <button
                        className="row-arrow"
                        onClick={(event) => {
                          event.stopPropagation();

                          onSelect(item);
                        }}
                      >
                        <ChevronRight
                          size={17}
                        />
                      </button>
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


function ActivityFeed({
  webhooks,
  communications,
}) {
  const activities = useMemo(() => {
    const webhookItems =
      webhooks.map((item) => ({
        id: `webhook-${item.id}`,
        type: "webhook",
        icon: Webhook,
        title:
          humanize(item.event_type),
        description: item.processed
          ? "Razorpay event processed"
          : "Razorpay event awaiting processing",
        status: item.processed
          ? "processed"
          : "pending",
        timestamp:
          item.processed_at ||
          item.created_at ||
          item.received_at,
      }));

    const communicationItems =
      communications.map((item) => ({
        id: `communication-${item.id}`,
        type: "communication",
        icon: Mail,
        title:
          humanize(
            item.template_name
          ),
        description: `${humanize(item.channel)
          } communication`,
        status: item.status,
        timestamp:
          item.sent_at ||
          item.created_at,
      }));

    return [
      ...webhookItems,
      ...communicationItems,
    ]
      .sort(
        (a, b) =>
          new Date(b.timestamp || 0) -
          new Date(a.timestamp || 0)
      )
      .slice(0, 8);
  }, [
    webhooks,
    communications,
  ]);

  return (
    <div className="panel activity-panel">
      <div className="panel-header">
        <div>
          <span className="panel-kicker">
            LIVE ACTIVITY
          </span>

          <h3>System events</h3>
        </div>

        <div className="activity-live">
          <span />
          Live
        </div>
      </div>

      {activities.length === 0 ? (
        <div className="empty-state compact">
          <Activity size={25} />

          <span>
            No recent activity.
          </span>
        </div>
      ) : (
        <div className="activity-list">
          {activities.map(
            (activity) => {
              const Icon =
                activity.icon;

              return (
                <div
                  className="activity-item"
                  key={activity.id}
                >
                  <div
                    className={`activity-icon activity-${activity.type}`}
                  >
                    <Icon size={15} />
                  </div>

                  <div className="activity-content">
                    <strong>
                      {activity.title}
                    </strong>

                    <span>
                      {activity.description}
                    </span>
                  </div>

                  <div className="activity-meta">
                    <StatusBadge
                      status={
                        activity.status
                      }
                    />

                    <small>
                      {formatRelativeDate(
                        activity.timestamp
                      )}
                    </small>
                  </div>
                </div>
              );
            }
          )}
        </div>
      )}
    </div>
  );
}


function CaseDrawer({
  caseItem,
  onClose,
  onOpenCase,
}) {
  const [details, setDetails] =
    useState(null);

  const [loading, setLoading] =
    useState(false);

  useEffect(() => {
    let active = true;

    if (!caseItem?.id) {
      return undefined;
    }

    const task = queueMicrotask(() => {
      if (!active) {
        return;
      }

      setLoading(true);

      fetchJson(
        `/api/v1/dashboard/cases/${caseItem.id}`
      )
        .then((data) => {
          if (active) {
            setDetails(data);
          }
        })
        .catch((error) => {
          console.error(error);
        })
        .finally(() => {
          if (active) {
            setLoading(false);
          }
        });
    });

    return () => {
      active = false;
      void task;
    };
  }, [caseItem]);

  if (!caseItem) {
    return null;
  }

  const data =
    details || caseItem;

  const actions =
    Array.isArray(data.actions)
      ? data.actions
      : [];

  const communications =
    Array.isArray(
      data.communications
    )
      ? data.communications
      : [];

  return (
    <>
      <div
        className="drawer-backdrop"
        onClick={onClose}
      />

      <aside className="case-drawer">
        <div className="drawer-header">
          <div>
            <span className="drawer-kicker">
              RECOVERY CASE
            </span>

            <h2>
              Case #{caseItem.id}
            </h2>
          </div>

          <button
            className="icon-button"
            onClick={onClose}
          >
            <X size={19} />
          </button>
        </div>

        <div className="drawer-body">
          {loading && (
            <div className="drawer-loading">
              <Loader2
                size={17}
                className="spin"
              />

              Loading case intelligence…
            </div>
          )}

          <div className="drawer-status-card">
            <div>
              <span>Current status</span>

              <StatusBadge
                status={data.status}
              />
            </div>

            <div>
              <span>Revenue at risk</span>

              <strong>
                {formatCurrency(
                  data.revenue_at_risk
                )}
              </strong>
            </div>

            <div>
              <span>Recovered</span>

              <strong className="recovered-text">
                {formatCurrency(
                  data.recovered_amount
                )}
              </strong>
            </div>
          </div>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Sparkles size={16} />
              AI assessment
            </div>

            <div className="intelligence-grid">
              <div>
                <span>Classification</span>

                <strong>
                  {humanize(
                    data.classification
                  )}
                </strong>
              </div>

              <div>
                <span>Recoverability</span>

                <strong>
                  {humanize(
                    data.recoverability
                  )}
                </strong>
              </div>

              <div>
                <span>Risk score</span>

                <strong>
                  {data.risk_score ??
                    0}
                  /100
                </strong>
              </div>

              <div>
                <span>
                  Recommended action
                </span>

                <strong>
                  {humanize(
                    data.recommended_action
                  )}
                </strong>
              </div>
            </div>
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Zap size={16} />
              Recovery actions
            </div>

            {actions.length === 0 ? (
              <div className="drawer-empty">
                No recovery actions
                recorded.
              </div>
            ) : (
              <div className="drawer-actions">
                {actions.map(
                  (action) => (
                    <div
                      className="drawer-action"
                      key={action.id}
                    >
                      <div className="action-icon">
                        {action.channel ===
                          "email" ? (
                          <Mail size={15} />
                        ) : (
                          <Zap size={15} />
                        )}
                      </div>

                      <div className="action-main">
                        <strong>
                          {humanize(
                            action.action_type
                          )}
                        </strong>

                        <span>
                          {humanize(
                            action.channel
                          )}
                          {" · "}
                          {action.attempt_count ||
                            0}{" "}
                          attempt(s)
                        </span>
                      </div>

                      <StatusBadge
                        status={
                          action.status
                        }
                      />
                    </div>
                  )
                )}
              </div>
            )}
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Mail size={16} />
              Customer communication
            </div>

            {communications.length ===
              0 ? (
              <div className="drawer-empty">
                No communications
                recorded.
              </div>
            ) : (
              <div className="drawer-actions">
                {communications.map(
                  (communication) => (
                    <div
                      className="drawer-action"
                      key={
                        communication.id
                      }
                    >
                      <div className="action-icon">
                        <Mail size={15} />
                      </div>

                      <div className="action-main">
                        <strong>
                          {humanize(
                            communication.template_name
                          )}
                        </strong>

                        <span>
                          {humanize(
                            communication.channel
                          )}
                        </span>
                      </div>

                      <StatusBadge
                        status={
                          communication.status
                        }
                      />
                    </div>
                  )
                )}
              </div>
            )}
          </section>

          <section className="drawer-section">
            <div className="drawer-section-title">
              <Clock3 size={16} />
              Recovery timeline
            </div>

            <div className="timeline">
              <div className="timeline-item">
                <span className="timeline-dot" />

                <div>
                  <strong>
                    Recovery case created
                  </strong>

                  <small>
                    {formatDate(
                      data.created_at
                    )}
                  </small>
                </div>
              </div>

              {data.updated_at && (
                <div className="timeline-item">
                  <span className="timeline-dot" />

                  <div>
                    <strong>
                      Case state updated
                    </strong>

                    <small>
                      {formatDate(
                        data.updated_at
                      )}
                    </small>
                  </div>
                </div>
              )}

              {data.recovered_at && (
                <div className="timeline-item timeline-success">
                  <span className="timeline-dot" />

                  <div>
                    <strong>
                      Revenue recovered
                    </strong>

                    <small>
                      {formatDate(
                        data.recovered_at
                      )}
                    </small>
                  </div>
                </div>
              )}
            </div>
          </section>

          <button
            className="drawer-detail-button"
            onClick={() =>
              onOpenCase(caseItem)
            }
          >
            Open full case
            <ExternalLink size={15} />
          </button>
        </div>
      </aside>
    </>
  );
}


function OverviewPage({
  metrics,
  cases,
  webhooks,
  communications,
  onSelectCase,
  onViewCases,
}) {
  const recovery =
    metrics?.recovery || {};

  const transactions =
    metrics?.transactions || {};

  const actions =
    metrics?.recovery_actions || {};

  const recoveryRate =
    Number(
      recovery.recovery_rate_percent || 0
    );

  return (
    <main className="page-content">
      <HeroSection
        recovery={recovery}
        onViewCases={onViewCases}
      />

      <section className="metrics-grid">
        <MetricCard
          label="Revenue at risk"
          value={formatCurrency(
            recovery.revenue_at_risk
          )}
          detail={`${recovery.total_cases || 0} recovery cases`}
          icon={AlertCircle}
          trend="Exposure"
        />

        <MetricCard
          label="Revenue recovered"
          value={formatCurrency(
            recovery.recovered_revenue
          )}
          detail={`${recovery.recovered_cases || 0} successful recoveries`}
          icon={TrendingUp}
          trend={`${recoveryRate}%`}
        />

        <MetricCard
          label="Failed payments"
          value={
            transactions.failed || 0
          }
          detail={`of ${transactions.total || 0
            } total transactions`}
          icon={CreditCard}
          trend="Detected"
        />

        <MetricCard
          label="Actions executed"
          value={
            actions.executed || 0
          }
          detail={`${actions.successful || 0} successful`}
          icon={Zap}
          trend={
            actions.failed
              ? `${actions.failed} failed`
              : "Healthy"
          }
          trendDirection={
            actions.failed
              ? "down"
              : "up"
          }
        />
      </section>

      <section className="dashboard-grid dashboard-grid-main">
        <PerformanceChart
          cases={cases}
        />

        <div className="panel health-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">
                SYSTEM HEALTH
              </span>

              <h3>
                Recovery engine
              </h3>
            </div>

            <div className="health-check">
              <CheckCircle2 size={15} />
              Healthy
            </div>
          </div>

          <div className="health-score">
            <div className="health-ring">
              <div>
                <strong>99</strong>
                <span>%</span>
              </div>
            </div>

            <div>
              <strong>
                Autonomous operations
              </strong>

              <p>
                The recovery worker is
                processing failed payments
                and executing eligible
                actions.
              </p>
            </div>
          </div>

          <div className="health-stats">
            <div>
              <span>Pending actions</span>

              <strong>
                {actions.pending || 0}
              </strong>
            </div>

            <div>
              <span>Executing</span>

              <strong>
                {actions.executing || 0}
              </strong>
            </div>

            <div>
              <span>Failed</span>

              <strong>
                {actions.failed || 0}
              </strong>
            </div>
          </div>
        </div>
      </section>

      <Pipeline
        recovery={recovery}
      />

      <section className="dashboard-grid dashboard-grid-bottom">
        <RecoveryTable
          cases={cases}
          onSelect={onSelectCase}
          onViewAll={onViewCases}
        />

        <ActivityFeed
          webhooks={webhooks}
          communications={
            communications
          }
        />
      </section>
    </main>
  );
}


function CasesPage({
  cases,
  onSelectCase,
}) {
  const [search, setSearch] =
    useState("");

  const [filter, setFilter] =
    useState("all");

  const filteredCases =
    useMemo(() => {
      return cases.filter((item) => {
        const matchesSearch =
          !search ||
          String(item.id)
            .includes(search) ||
          String(
            item.transaction_id
          ).includes(search) ||
          String(
            item.classification || ""
          )
            .toLowerCase()
            .includes(
              search.toLowerCase()
            );

        const matchesFilter =
          filter === "all" ||
          String(
            item.status
          ).toLowerCase() ===
          filter;

        return (
          matchesSearch &&
          matchesFilter
        );
      });
    }, [
      cases,
      search,
      filter,
    ]);

  return (
    <main className="page-content">
      <div className="page-heading">
        <div>
          <span className="page-kicker">
            RECOVERY INTELLIGENCE
          </span>

          <h2>
            Recovery cases
          </h2>

          <p>
            Every failed payment becomes
            an actionable recovery case.
          </p>
        </div>

        <div className="case-summary">
          <strong>
            {cases.length}
          </strong>

          <span>
            total cases
          </span>
        </div>
      </div>

      <div className="case-toolbar">
        <div className="search-box">
          <Search size={17} />

          <input
            value={search}
            onChange={(event) =>
              setSearch(
                event.target.value
              )
            }
            placeholder="Search cases, transactions or classifications..."
          />
        </div>

        <div className="filter-group">
          {[
            ["all", "All"],
            ["open", "Open"],
            ["recovered", "Recovered"],
            ["manual_review", "Manual"],
          ].map(
            ([value, label]) => (
              <button
                key={value}
                className={
                  filter === value
                    ? "filter-active"
                    : ""
                }
                onClick={() =>
                  setFilter(value)
                }
              >
                {label}
              </button>
            )
          )}
        </div>
      </div>

      <div className="panel cases-full-panel">
        {filteredCases.length ===
          0 ? (
          <div className="empty-state">
            <Search size={28} />

            <strong>
              No matching cases
            </strong>

            <span>
              Try changing your search
              or filter.
            </span>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="recovery-table cases-table">
              <thead>
                <tr>
                  <th>CASE</th>
                  <th>CLASSIFICATION</th>
                  <th>RECOVERABILITY</th>
                  <th>RISK</th>
                  <th>RECOMMENDATION</th>
                  <th>AT RISK</th>
                  <th>STATUS</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {filteredCases.map(
                  (item) => (
                    <tr
                      key={item.id}
                      onClick={() =>
                        onSelectCase(
                          item
                        )
                      }
                    >
                      <td>
                        <div className="case-cell">
                          <span className="case-number">
                            #{item.id}
                          </span>

                          <div>
                            <strong>
                              Transaction #
                              {
                                item.transaction_id
                              }
                            </strong>

                            <small>
                              {formatDate(
                                item.created_at
                              )}
                            </small>
                          </div>
                        </div>
                      </td>

                      <td>
                        {humanize(
                          item.classification
                        )}
                      </td>

                      <td>
                        <span className="recoverability">
                          {humanize(
                            item.recoverability
                          )}
                        </span>
                      </td>

                      <td>
                        <strong
                          className={`risk-number ${Number(
                            item.risk_score
                          ) >= 70
                            ? "risk-high"
                            : Number(
                              item.risk_score
                            ) >= 40
                              ? "risk-medium"
                              : "risk-low"
                            }`}
                        >
                          {item.risk_score ??
                            0}
                        </strong>
                      </td>

                      <td>
                        <span className="recommendation">
                          <Zap size={13} />

                          {humanize(
                            item.recommended_action
                          )}
                        </span>
                      </td>

                      <td>
                        <strong>
                          {formatCurrency(
                            item.revenue_at_risk
                          )}
                        </strong>
                      </td>

                      <td>
                        <StatusBadge
                          status={
                            item.status
                          }
                        />
                      </td>

                      <td>
                        <button
                          className="row-arrow"
                          onClick={(
                            event
                          ) => {
                            event.stopPropagation();

                            onSelectCase(
                              item
                            );
                          }}
                        >
                          <ChevronRight
                            size={17}
                          />
                        </button>
                      </td>
                    </tr>
                  )
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  );
}


function ActivityPage({
  webhooks,
  communications,
}) {
  const events = useMemo(() => {
    const webhookEvents =
      webhooks.map((item) => ({
        id: `w-${item.id}`,
        icon: Webhook,
        type: "Webhook",
        title:
          humanize(item.event_type),
        description: item.processed
          ? "Webhook received and processed successfully."
          : "Webhook received and awaiting processing.",
        status: item.processed
          ? "processed"
          : "pending",
        timestamp:
          item.processed_at ||
          item.created_at ||
          item.received_at,
      }));

    const communicationEvents =
      communications.map((item) => ({
        id: `c-${item.id}`,
        icon: Mail,
        type: "Communication",
        title:
          humanize(
            item.template_name
          ),
        description: `${humanize(
          item.channel
        )} communication · ${humanize(
          item.provider || "provider"
        )}`,
        status: item.status,
        timestamp:
          item.sent_at ||
          item.created_at,
      }));

    return [
      ...webhookEvents,
      ...communicationEvents,
    ].sort(
      (a, b) =>
        new Date(b.timestamp || 0) -
        new Date(a.timestamp || 0)
    );
  }, [
    webhooks,
    communications,
  ]);

  return (
    <main className="page-content">
      <div className="page-heading">
        <div>
          <span className="page-kicker">
            EVENT STREAM
          </span>

          <h2>
            System activity
          </h2>

          <p>
            Observe payment, webhook and
            communication events flowing
            through the platform.
          </p>
        </div>

        <div className="activity-count">
          <Activity size={16} />
          {events.length} events
        </div>
      </div>

      <div className="activity-layout">
        <div className="panel event-stream-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">
                EVENT STREAM
              </span>

              <h3>
                Recent events
              </h3>
            </div>

            <div className="activity-live">
              <span />
              Live
            </div>
          </div>

          {events.length === 0 ? (
            <div className="empty-state">
              <Activity size={28} />

              <strong>
                No events yet
              </strong>

              <span>
                Incoming system activity
                will appear here.
              </span>
            </div>
          ) : (
            <div className="event-stream">
              {events.map(
                (event) => {
                  const Icon =
                    event.icon;

                  return (
                    <div
                      className="event-row"
                      key={event.id}
                    >
                      <div className="event-icon">
                        <Icon size={16} />
                      </div>

                      <div className="event-body">
                        <div className="event-title-row">
                          <strong>
                            {event.title}
                          </strong>

                          <StatusBadge
                            status={
                              event.status
                            }
                          />
                        </div>

                        <p>
                          {event.description}
                        </p>

                        <small>
                          {formatDate(
                            event.timestamp
                          )}
                        </small>
                      </div>

                      <span className="event-type">
                        {event.type}
                      </span>
                    </div>
                  );
                }
              )}
            </div>
          )}
        </div>

        <div className="panel activity-summary-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">
                OPERATIONS
              </span>

              <h3>
                Event summary
              </h3>
            </div>
          </div>

          <div className="event-summary">
            <div className="summary-card">
              <div className="summary-icon">
                <Webhook size={17} />
              </div>

              <div>
                <span>
                  Webhooks
                </span>

                <strong>
                  {webhooks.length}
                </strong>
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-icon">
                <Mail size={17} />
              </div>

              <div>
                <span>
                  Communications
                </span>

                <strong>
                  {communications.length}
                </strong>
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-icon">
                <ShieldCheck size={17} />
              </div>

              <div>
                <span>
                  Processed webhooks
                </span>

                <strong>
                  {
                    webhooks.filter(
                      (item) =>
                        item.processed
                    ).length
                  }
                </strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}


function App() {
  const [page, setPage] =
    useState("overview");

  const [metrics, setMetrics] =
    useState(null);

  const [cases, setCases] =
    useState([]);

  const [webhooks, setWebhooks] =
    useState([]);

  const [
    communications,
    setCommunications,
  ] = useState([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const [
    selectedCase,
    setSelectedCase,
  ] = useState(null);

  const [
    mobileOpen,
    setMobileOpen,
  ] = useState(false);

  const [
    lastUpdated,
    setLastUpdated,
  ] = useState(null);

  const loadDashboard =
    useCallback(async () => {
      setLoading(true);
      setError("");

      try {
        const [
          metricsData,
          casesData,
          webhooksData,
          communicationsData,
        ] = await Promise.all([
          fetchJson(
            "/api/v1/dashboard/overview"
          ),
          fetchJson(
            "/api/v1/dashboard/cases?limit=50"
          ),
          fetchJson(
            "/api/v1/dashboard/webhooks?limit=50"
          ),
          fetchJson(
            "/api/v1/dashboard/communications?limit=50"
          ),
        ]);

        setMetrics(metricsData);

        setCases(
          Array.isArray(casesData)
            ? casesData
            : []
        );

        setWebhooks(
          Array.isArray(
            webhooksData
          )
            ? webhooksData
            : []
        );

        setCommunications(
          Array.isArray(
            communicationsData
          )
            ? communicationsData
            : []
        );

        setLastUpdated(
          new Date().toISOString()
        );
      } catch (requestError) {
        console.error(
          requestError
        );

        setError(
          "Unable to connect to the recovery backend. Make sure FastAPI is running."
        );
      } finally {
        setLoading(false);
      }
    }, []);

  useEffect(() => {
    const task = queueMicrotask(() => {
      loadDashboard();
    });

    return () => {
      void task;
    };
  }, [loadDashboard]);

  const pageContent =
    loading && !metrics ? (
      <div className="loading-screen">
        <div className="loading-orb">
          <Sparkles size={22} />
        </div>

        <h2>
          Loading RecoveryAI
        </h2>

        <p>
          Connecting to the recovery engine…
        </p>

        <Loader2
          size={18}
          className="spin"
        />
      </div>
    ) : error && !metrics ? (
      <div className="error-screen">
        <div className="error-icon">
          <AlertCircle size={24} />
        </div>

        <h2>
          Backend unavailable
        </h2>

        <p>{error}</p>

        <button
          className="refresh-button"
          onClick={loadDashboard}
        >
          <RefreshCw size={16} />
          Retry connection
        </button>
      </div>
    ) : (
      <>
        {error && (
          <div className="inline-error">
            <AlertCircle size={15} />
            {error}
          </div>
        )}

        {page === "overview" && (
          <OverviewPage
            metrics={metrics}
            cases={cases}
            webhooks={webhooks}
            communications={
              communications
            }
            onSelectCase={
              setSelectedCase
            }
            onViewCases={() =>
              setPage("cases")
            }
          />
        )}

        {page === "cases" && (
          <CasesPage
            cases={cases}
            onSelectCase={
              setSelectedCase
            }
          />
        )}

        {page === "activity" && (
          <ActivityPage
            webhooks={webhooks}
            communications={
              communications
            }
          />
        )}
      </>
    );

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        mobileOpen={mobileOpen}
        setMobileOpen={
          setMobileOpen
        }
      />

      <div className="app-main">
        <Topbar
          page={page}
          onRefresh={loadDashboard}
          loading={loading}
          setMobileOpen={
            setMobileOpen
          }
          lastUpdated={lastUpdated}
        />

        {pageContent}
      </div>

      <CaseDrawer
        caseItem={selectedCase}
        onClose={() =>
          setSelectedCase(null)
        }
        onOpenCase={(item) => {
          setSelectedCase(item);
          setPage("cases");
        }}
      />
    </div>
  );
}


export default App;