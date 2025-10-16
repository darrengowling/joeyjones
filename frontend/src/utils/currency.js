/**
 * Universal currency formatting for the entire app
 * Displays amounts in £m format for consistency
 */

/**
 * Format amount to £m format (e.g., £500m, £250m, £23.5m)
 * @param {number} amount - Amount in base currency (e.g., 500000000)
 * @returns {string} - Formatted string (e.g., "£500m")
 */
export const formatCurrency = (amount) => {
  if (!amount && amount !== 0) return '£0m';
  const millions = amount / 1000000;
  
  // If it's a whole number, don't show decimals
  if (millions % 1 === 0) {
    return `£${millions}m`;
  }
  
  // Show one decimal place for non-whole numbers
  return `£${millions.toFixed(1)}m`;
};

/**
 * Parse £m format input to base currency amount
 * @param {string} input - User input (e.g., "5m", "£5m", "5", "250")
 * @returns {number} - Amount in base currency (e.g., 5000000)
 */
export const parseCurrencyInput = (input) => {
  if (!input) return 0;
  
  // Remove £, m, M, spaces, and commas
  const cleaned = input.toString().replace(/[£,\s]/g, '').toLowerCase();
  
  // Check if it ends with 'm'
  if (cleaned.endsWith('m')) {
    const value = parseFloat(cleaned.replace('m', ''));
    return Math.round(value * 1000000);
  }
  
  // If no 'm', assume it's already in millions
  const value = parseFloat(cleaned);
  return Math.round(value * 1000000);
};

/**
 * Validate currency input
 * @param {string} input - User input
 * @returns {boolean} - True if valid
 */
export const isValidCurrencyInput = (input) => {
  if (!input) return false;
  const cleaned = input.toString().replace(/[£,\s]/g, '').toLowerCase();
  const withoutM = cleaned.replace('m', '');
  return !isNaN(parseFloat(withoutM)) && parseFloat(withoutM) > 0;
};
