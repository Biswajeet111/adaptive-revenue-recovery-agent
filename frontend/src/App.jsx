import { useState, useEffect, useCallback } from "react";
import { Sparkles, AlertCircle, RefreshCw, Loader2 } from "lucide-react";
import { fetchJson, getApiBaseUrl } from "./api";

import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { OverviewPage } from "./components/OverviewPage";
import { CasesPage } from "./components/CasesPage";
import { ActivityPage } from "./components/ActivityPage";
import { CaseDrawer } from "./components/CaseDrawer";

import "./App.css";

export default function App() {
  const [page, setPage] = useState("overview");
  const [metrics, setMetrics] = useState(null);
  const [cases, setCases] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [communications, setCommunications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedCase, setSelectedCase] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [metricsData, casesData, webhooksData, communicationsData] =
        await Promise.all([
          fetchJson("/api/v1/dashboard/overview"),
          fetchJson("/api/v1/dashboard/cases?limit=50"),
          fetchJson("/api/v1/dashboard/webhooks?limit=50"),
          fetchJson("/api/v1/dashboard/communications?limit=50"),
        ]);

      setMetrics(metricsData);
      setCases(Array.isArray(casesData) ? casesData : []);
      setWebhooks(Array.isArray(webhooksData) ? webhooksData : []);
      setCommunications(
        Array.isArray(communicationsData) ? communicationsData : []
      );
      setLastUpdated(new Date().toISOString());
    } catch (err) {
      console.error("Dashboard fetch error:", err);
      const baseUrl = getApiBaseUrl();
      setError(
        `Unable to connect to ReviveAI backend at ${baseUrl}. Ensure backend API is operational.`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    const run = async () => {
      if (!ignore) {
        await loadDashboard();
      }
    };

    run();

    return () => {
      ignore = true;
    };
  }, [loadDashboard]);

  const renderContent = () => {
    if (loading && !metrics) {
      return (
        <div className="loading-screen">
          <div className="loading-orb">
            <Sparkles size={24} />
          </div>
          <h2>Loading ReviveAI</h2>
          <p>Connecting to ReviveAI revenue recovery engine...</p>
          <Loader2 size={20} className="spin" />
        </div>
      );
    }

    if (error && !metrics) {
      return (
        <div className="error-screen">
          <div className="error-icon">
            <AlertCircle size={28} />
          </div>
          <h2>Backend Connection Failure</h2>
          <p>{error}</p>
          <button className="refresh-button primary-btn" onClick={loadDashboard}>
            <RefreshCw size={16} />
            <span>Retry Connection</span>
          </button>
        </div>
      );
    }

    return (
      <>
        {error && (
          <div className="inline-error-banner">
            <AlertCircle size={16} />
            <span>{error}</span>
          </div>
        )}

        {page === "overview" && (
          <OverviewPage
            metrics={metrics}
            cases={cases}
            webhooks={webhooks}
            communications={communications}
            onSelectCase={setSelectedCase}
            onViewCases={() => setPage("cases")}
          />
        )}

        {page === "cases" && (
          <CasesPage cases={cases} onSelectCase={setSelectedCase} />
        )}

        {page === "activity" && (
          <ActivityPage webhooks={webhooks} communications={communications} />
        )}
      </>
    );
  };

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        mobileOpen={mobileOpen}
        setMobileOpen={setMobileOpen}
      />

      <div className="app-main">
        <Topbar
          page={page}
          onRefresh={loadDashboard}
          loading={loading}
          setMobileOpen={setMobileOpen}
          lastUpdated={lastUpdated}
        />

        {renderContent()}
      </div>

      <CaseDrawer
        key={selectedCase?.id}
        caseItem={selectedCase}
        onClose={() => setSelectedCase(null)}
        onOpenCase={(item) => {
          setSelectedCase(item);
          setPage("cases");
        }}
      />
    </div>
  );
}