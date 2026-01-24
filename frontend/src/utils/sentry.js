/**
 * Sentry Error Tracking Utilities
 * Production Hardening - Day 6
 */

import * as Sentry from "@sentry/react";

/**
 * Manually capture an exception
 * @param {Error} error - The error object
 * @param {Object} context - Additional context
 */
export const captureException = (error, context = {}) => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.captureException(error, {
      extra: context,
    });
  } else {
    console.error("Error captured (Sentry disabled):", error, context);
  }
};

/**
 * Capture a custom message
 * @param {string} message - The message to capture
 * @param {string} level - Severity level (error, warning, info, debug)
 * @param {Object} context - Additional context
 */
export const captureMessage = (message, level = "info", context = {}) => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.captureMessage(message, {
      level,
      extra: context,
    });
  } else {
    console.log(`Message captured (Sentry disabled) [${level}]:`, message, context);
  }
};

/**
 * Set user context for error tracking
 * @param {Object} user - User object with id, email, name
 */
export const setUser = (user) => {
  if (process.env.REACT_APP_SENTRY_DSN && user) {
    Sentry.setUser({
      id: user.id,
      email: user.email,
      username: user.name,
    });
  }
};

/**
 * Clear user context (on logout)
 */
export const clearUser = () => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.setUser(null);
  }
};

/**
 * Add breadcrumb for tracking user actions
 * @param {string} message - Breadcrumb message
 * @param {Object} data - Additional data
 * @param {string} category - Category (navigation, ui, auth, etc.)
 */
export const addBreadcrumb = (message, data = {}, category = "user-action") => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.addBreadcrumb({
      message,
      category,
      data,
      level: "info",
    });
  }
};

/**
 * Wrap async functions to capture errors
 * @param {Function} fn - Async function to wrap
 * @param {string} context - Context description
 */
export const captureAsync = (fn, context = "async operation") => {
  return async (...args) => {
    try {
      return await fn(...args);
    } catch (error) {
      captureException(error, { context, args });
      throw error;
    }
  };
};

/**
 * Error Boundary Component
 * Catches React errors and reports to Sentry
 */
export const ErrorBoundary = Sentry.ErrorBoundary;

/**
 * Performance monitoring for specific operations
 * @param {string} name - Operation name
 * @param {Function} fn - Function to measure
 */
export const measurePerformance = async (name, fn) => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    const start = performance.now();
    try {
      const result = await fn();
      const duration = performance.now() - start;
      Sentry.addBreadcrumb({
        message: `${name} completed`,
        category: "performance",
        data: { duration: `${duration.toFixed(2)}ms` },
        level: "info",
      });
      return result;
    } catch (error) {
      throw error;
    }
  } else {
    return await fn();
  }
};

/**
 * Set custom tags for filtering in Sentry
 * @param {Object} tags - Key-value pairs of tags
 */
export const setTags = (tags) => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.setTags(tags);
  }
};

/**
 * Set custom context
 * @param {string} name - Context name
 * @param {Object} context - Context data
 */
export const setContext = (name, context) => {
  if (process.env.REACT_APP_SENTRY_DSN) {
    Sentry.setContext(name, context);
  }
};

export default {
  captureException,
  captureMessage,
  setUser,
  clearUser,
  addBreadcrumb,
  captureAsync,
  ErrorBoundary,
  measurePerformance,
  setTags,
  setContext,
};
