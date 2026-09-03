/**
 * API Client for ReviveAI Operations Dashboard
 * Consumes read-only FastAPI endpoints.
 */

export const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL.replace(/\/$/, "");
  }

  // If running in browser locally
  if (
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1")
  ) {
    return "http://127.0.0.1:8000";
  }

  // Production fallback
  return "https://adaptive-revenue-recovery-api.onrender.com";
};

export async function fetchJson(path) {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith("/") ? path : `/${path}`}`;

  try {
    const response = await fetch(url, {
      headers: {
        Accept: "application/json",
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API fetch error [${url}]:`, error);
    throw error;
  }
}

export function formatCurrency(value) {
  const number = Number(value || 0);
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(number);
}

export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatRelativeDate(value) {
  if (!value) return "Unknown time";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown time";

  const diff = Date.now() - date.getTime();
  const minutes = Math.floor(diff / (1000 * 60));

  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function humanize(value) {
  if (value === null || value === undefined) return "Unknown";
  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function statusTone(status) {
  const normalized = String(status || "").toLowerCase();

  if (
    [
      "recovered",
      "successful",
      "executed",
      "processed",
      "captured",
      "paid",
      "delivered",
      "high",
      "healthy",
      "true",
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
      "unprocessed",
      "false",
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
      "medium",
    ].includes(normalized)
  ) {
    return "warning";
  }

  return "neutral";
}
