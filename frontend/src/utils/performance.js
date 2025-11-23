/**
 * Performance Utilities
 * Production Hardening - Day 11: Frontend Performance Optimization
 * 
 * Provides utilities for optimizing React performance:
 * - Debouncing
 * - Throttling  
 * - Memoization helpers
 */

/**
 * Debounce function calls
 * Delays execution until after wait milliseconds have elapsed since last call
 * 
 * @param {Function} func - Function to debounce
 * @param {number} wait - Milliseconds to wait
 * @param {boolean} immediate - Execute on leading edge instead of trailing
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  
  return function executedFunction(...args) {
    const context = this;
    
    const later = () => {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    
    const callNow = immediate && !timeout;
    
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    
    if (callNow) func.apply(context, args);
  };
};

/**
 * Throttle function calls
 * Ensures function is called at most once per specified time period
 * 
 * @param {Function} func - Function to throttle
 * @param {number} limit - Milliseconds between calls
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  let lastResult;
  
  return function(...args) {
    const context = this;
    
    if (!inThrottle) {
      lastResult = func.apply(context, args);
      inThrottle = true;
      
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
    
    return lastResult;
  };
};

/**
 * Create a memoized version of a function
 * Caches results based on arguments
 * 
 * @param {Function} func - Function to memoize
 * @param {Function} resolver - Optional custom resolver for cache key
 * @returns {Function} Memoized function
 */
export const memoize = (func, resolver) => {
  const cache = new Map();
  
  return function(...args) {
    const key = resolver ? resolver.apply(this, args) : JSON.stringify(args);
    
    if (cache.has(key)) {
      return cache.get(key);
    }
    
    const result = func.apply(this, args);
    cache.set(key, result);
    
    return result;
  };
};

/**
 * Debounce Socket.IO event handlers
 * Useful for high-frequency events like bidding updates
 * 
 * @param {Function} handler - Event handler function
 * @param {number} delay - Milliseconds to debounce (default: 100ms)
 * @returns {Function} Debounced handler
 */
export const debounceSocketEvent = (handler, delay = 100) => {
  return debounce(handler, delay, false);
};

/**
 * Throttle Socket.IO event handlers
 * Useful for limiting updates to UI (e.g., timer updates)
 * 
 * @param {Function} handler - Event handler function
 * @param {number} limit - Milliseconds between calls (default: 200ms)
 * @returns {Function} Throttled handler
 */
export const throttleSocketEvent = (handler, limit = 200) => {
  return throttle(handler, limit);
};

/**
 * Batch state updates
 * Collects multiple updates and applies them together
 * 
 * @param {Function} updateFn - Function that performs the update
 * @param {number} delay - Milliseconds to wait before batching (default: 50ms)
 * @returns {Function} Batched update function
 */
export const batchUpdates = (updateFn, delay = 50) => {
  let pending = [];
  let timeout;
  
  return (data) => {
    pending.push(data);
    
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      updateFn(pending);
      pending = [];
    }, delay);
  };
};

/**
 * Deep equality check for objects
 * Used in React.memo or useMemo comparisons
 * 
 * @param {any} a - First value
 * @param {any} b - Second value
 * @returns {boolean} Whether values are deeply equal
 */
export const deepEqual = (a, b) => {
  if (a === b) return true;
  
  if (a == null || b == null) return false;
  if (typeof a !== 'object' || typeof b !== 'object') return false;
  
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  
  if (keysA.length !== keysB.length) return false;
  
  for (const key of keysA) {
    if (!keysB.includes(key)) return false;
    if (!deepEqual(a[key], b[key])) return false;
  }
  
  return true;
};

/**
 * Shallow equality check for objects
 * Faster than deep equality, good for React.memo
 * 
 * @param {Object} objA - First object
 * @param {Object} objB - Second object
 * @returns {boolean} Whether objects are shallowly equal
 */
export const shallowEqual = (objA, objB) => {
  if (objA === objB) return true;
  
  if (typeof objA !== 'object' || objA === null ||
      typeof objB !== 'object' || objB === null) {
    return false;
  }
  
  const keysA = Object.keys(objA);
  const keysB = Object.keys(objB);
  
  if (keysA.length !== keysB.length) return false;
  
  for (const key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(objB, key) ||
        objA[key] !== objB[key]) {
      return false;
    }
  }
  
  return true;
};

/**
 * Request animation frame helper
 * Ensures function runs on next browser paint
 * 
 * @param {Function} callback - Function to run
 */
export const raf = (callback) => {
  if (typeof window !== 'undefined') {
    return window.requestAnimationFrame(callback);
  }
  return setTimeout(callback, 16); // ~60fps fallback
};

/**
 * Cancel animation frame helper
 * 
 * @param {number} id - Animation frame ID to cancel
 */
export const cancelRaf = (id) => {
  if (typeof window !== 'undefined') {
    return window.cancelAnimationFrame(id);
  }
  return clearTimeout(id);
};

export default {
  debounce,
  throttle,
  memoize,
  debounceSocketEvent,
  throttleSocketEvent,
  batchUpdates,
  deepEqual,
  shallowEqual,
  raf,
  cancelRaf,
};
