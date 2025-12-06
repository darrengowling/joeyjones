import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import "./styles/brand.css";
import "./styles/responsive.css";
import App from "@/App";
import * as Sentry from "@sentry/react";
import ErrorBoundary from "./components/ErrorBoundary";

// Initialize Sentry for error tracking (Production Hardening Day 6)
const SENTRY_DSN = process.env.REACT_APP_SENTRY_DSN;
const SENTRY_ENVIRONMENT = process.env.REACT_APP_SENTRY_ENVIRONMENT || 'pilot';
const SENTRY_TRACES_SAMPLE_RATE = parseFloat(process.env.REACT_APP_SENTRY_TRACES_SAMPLE_RATE || '0.1');

if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: SENTRY_ENVIRONMENT,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],
    // Performance Monitoring
    tracesSampleRate: SENTRY_TRACES_SAMPLE_RATE,
    // Session Replay
    replaysSessionSampleRate: 0.1, // 10% of sessions
    replaysOnErrorSampleRate: 1.0, // 100% of errors
    // Additional options
    beforeSend(event, hint) {
      // Filter out expected errors or add custom logic
      return event;
    },
  });
  console.log(`✅ Sentry error tracking initialized (env: ${SENTRY_ENVIRONMENT})`);
} else {
  console.log("⚠️ Sentry DSN not configured - error tracking disabled");
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
