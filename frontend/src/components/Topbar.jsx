import { Menu, RefreshCw, Bell } from "lucide-react";
import { formatRelativeDate } from "../api";

export function Topbar({
  page,
  onRefresh,
  loading,
  setMobileOpen,
  lastUpdated,
}) {
  const titles = {
    overview: [
      "Revenue Overview",
      "Monitor autonomous recovery performance & risk",
    ],
    cases: [
      "Recovery Cases",
      "Investigate and track payment failure resolutions",
    ],
    activity: [
      "System Activity",
      "Live stream of Razorpay webhooks and notifications",
    ],
  };

  const [title, subtitle] = titles[page] || titles.overview;

  return (
    <header className="topbar">
      <div className="topbar-left">
        <button
          className="mobile-menu"
          onClick={() => setMobileOpen(true)}
          aria-label="Open navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="topbar-title-group">
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
      </div>

      <div className="topbar-actions">
        <span className="last-updated">
          <span className="live-indicator" />
          {lastUpdated
            ? `Updated ${formatRelativeDate(lastUpdated)}`
            : "Live data feed"}
        </span>

        <button className="icon-button" aria-label="Notifications">
          <Bell size={18} />
        </button>

        <button
          className="refresh-button"
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={15} className={loading ? "spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>
    </header>
  );
}
