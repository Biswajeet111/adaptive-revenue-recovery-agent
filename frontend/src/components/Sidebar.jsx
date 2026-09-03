import {
  LayoutDashboard,
  Target,
  Activity,
  Database,
  Webhook,
  Mail,
  Zap,
  X,
} from "lucide-react";

export function Sidebar({ page, setPage, mobileOpen, setMobileOpen }) {
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
      badge: "Live",
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
          onClick={() => setMobileOpen(false)}
        />
      )}

      <aside className={`sidebar ${mobileOpen ? "sidebar-mobile-open" : ""}`}>
        <div className="sidebar-brand">
          <img
            src="/branding/reviveai-logo.png"
            alt="ReviveAI - Autonomous Revenue Recovery"
            className="brand-logo-desktop"
          />
          <img
            src="/branding/reviveai-icon.png"
            alt="ReviveAI Icon"
            className="brand-logo-mobile"
          />
          <button
            className="mobile-close"
            onClick={() => setMobileOpen(false)}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        <div className="sidebar-section-label">WORKSPACE</div>

        <nav className="sidebar-nav">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = page === item.id;

            return (
              <button
                key={item.id}
                className={`sidebar-link ${isActive ? "sidebar-link-active" : ""}`}
                onClick={() => {
                  setPage(item.id);
                  setMobileOpen(false);
                }}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {item.badge && <span className="sidebar-count">{item.badge}</span>}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-section-label sidebar-section-spaced">SYSTEM</div>

        <div className="sidebar-system">
          <div className="system-item">
            <span className="system-icon">
              <Database size={14} />
            </span>
            <div className="system-info">
              <strong>PostgreSQL</strong>
              <small>Connected</small>
            </div>
            <span className="system-online" />
          </div>

          <div className="system-item">
            <span className="system-icon">
              <Webhook size={14} />
            </span>
            <div className="system-info">
              <strong>Razorpay</strong>
              <small>Webhook active</small>
            </div>
            <span className="system-online" />
          </div>

          <div className="system-item">
            <span className="system-icon">
              <Mail size={14} />
            </span>
            <div className="system-info">
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
            <div className="agent-status-info">
              <strong>ReviveAI Agent</strong>
              <span>Autonomous worker active</span>
            </div>
            <span className="pulse-dot" />
          </div>

          <div className="sidebar-version">ReviveAI v0.1.0</div>
        </div>
      </aside>
    </>
  );
}
