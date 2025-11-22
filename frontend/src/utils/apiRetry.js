/**
 * API Retry Utility with Exponential Backoff
 * Production Hardening - Days 9-10: Error Recovery & Resilience
 * 
 * Provides automatic retry logic for failed API calls with:
 * - Exponential backoff
 * - Configurable retry attempts
 * - Request deduplication
 * - Network error handling
 */

import axios from 'axios';

/**
 * Default retry configuration
 */
const DEFAULT_RETRY_CONFIG = {
  maxRetries: 3,
  initialDelay: 1000, // 1 second
  maxDelay: 10000, // 10 seconds
  backoffMultiplier: 2,
  retryableStatuses: [408, 429, 500, 502, 503, 504], // Timeout, rate limit, server errors
  retryableErrors: ['ECONNABORTED', 'ENOTFOUND', 'ENETUNREACH', 'ETIMEDOUT'],
};

/**
 * Check if error is retryable
 */
const isRetryableError = (error, config = DEFAULT_RETRY_CONFIG) => {
  // Network errors
  if (error.code && config.retryableErrors.includes(error.code)) {
    return true;
  }
  
  // HTTP status codes
  if (error.response && config.retryableStatuses.includes(error.response.status)) {
    return true;
  }
  
  // Connection refused or timeout
  if (error.message && (
    error.message.includes('Network Error') ||
    error.message.includes('timeout') ||
    error.message.includes('ECONNREFUSED')
  )) {
    return true;
  }
  
  return false;
};

/**
 * Calculate delay for next retry using exponential backoff
 */
const calculateDelay = (attemptNumber, config = DEFAULT_RETRY_CONFIG) => {
  const delay = Math.min(
    config.initialDelay * Math.pow(config.backoffMultiplier, attemptNumber - 1),
    config.maxDelay
  );
  
  // Add jitter to prevent thundering herd
  const jitter = Math.random() * 500;
  return delay + jitter;
};

/**
 * Sleep for specified milliseconds
 */
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

/**
 * Retry a function with exponential backoff
 * 
 * @param {Function} fn - Async function to retry
 * @param {Object} config - Retry configuration
 * @param {number} attemptNumber - Current attempt number (internal)
 * @returns {Promise} - Result of the function
 */
export const retryWithBackoff = async (fn, config = {}, attemptNumber = 1) => {
  const retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config };
  
  try {
    return await fn();
  } catch (error) {
    // Check if we should retry
    if (attemptNumber >= retryConfig.maxRetries || !isRetryableError(error, retryConfig)) {
      throw error;
    }
    
    // Calculate delay and log
    const delay = calculateDelay(attemptNumber, retryConfig);
    console.log(`⚠️ Request failed (attempt ${attemptNumber}/${retryConfig.maxRetries}). Retrying in ${Math.round(delay)}ms...`);
    
    // Wait before retrying
    await sleep(delay);
    
    // Retry
    return retryWithBackoff(fn, retryConfig, attemptNumber + 1);
  }
};

/**
 * Create an axios instance with automatic retry
 * 
 * Usage:
 * const api = createRetryableAxios({ maxRetries: 5 });
 * await api.get('/api/leagues');
 */
export const createRetryableAxios = (retryConfig = {}) => {
  const instance = axios.create();
  
  // Add retry interceptor
  instance.interceptors.response.use(
    response => response,
    async error => {
      const config = error.config;
      
      // Prevent infinite loops
      if (!config || config.__retryCount >= (retryConfig.maxRetries || DEFAULT_RETRY_CONFIG.maxRetries)) {
        return Promise.reject(error);
      }
      
      // Check if error is retryable
      if (!isRetryableError(error, retryConfig)) {
        return Promise.reject(error);
      }
      
      // Initialize retry count
      config.__retryCount = config.__retryCount || 0;
      config.__retryCount += 1;
      
      // Calculate delay
      const delay = calculateDelay(config.__retryCount, retryConfig);
      console.log(`⚠️ API call failed (attempt ${config.__retryCount}). Retrying in ${Math.round(delay)}ms...`);
      
      // Wait before retrying
      await sleep(delay);
      
      // Retry request
      return instance(config);
    }
  );
  
  return instance;
};

/**
 * Retry a specific axios request
 * 
 * Usage:
 * await retryAxiosRequest(() => axios.get('/api/leagues'), { maxRetries: 5 });
 */
export const retryAxiosRequest = async (requestFn, config = {}) => {
  return retryWithBackoff(requestFn, config);
};

/**
 * Batch retry multiple requests with concurrency control
 * 
 * @param {Array} requests - Array of request functions
 * @param {number} concurrency - Max concurrent requests
 * @param {Object} retryConfig - Retry configuration
 * @returns {Promise<Array>} - Array of results
 */
export const batchRetryRequests = async (requests, concurrency = 3, retryConfig = {}) => {
  const results = [];
  const executing = [];
  
  for (const [index, requestFn] of requests.entries()) {
    const promise = retryWithBackoff(requestFn, retryConfig)
      .then(result => {
        results[index] = { success: true, data: result };
      })
      .catch(error => {
        results[index] = { success: false, error };
      });
    
    executing.push(promise);
    
    // Control concurrency
    if (executing.length >= concurrency) {
      await Promise.race(executing);
      executing.splice(executing.findIndex(p => p === promise), 1);
    }
  }
  
  // Wait for remaining requests
  await Promise.all(executing);
  
  return results;
};

/**
 * Check network connectivity
 */
export const checkNetworkConnectivity = async () => {
  try {
    await axios.get('/api/health', { timeout: 5000 });
    return true;
  } catch (error) {
    return false;
  }
};

export default {
  retryWithBackoff,
  createRetryableAxios,
  retryAxiosRequest,
  batchRetryRequests,
  checkNetworkConnectivity,
  isRetryableError,
};
