/**
 * Date utility functions for report filtering and formatting
 */

/**
 * Format date to YYYY-MM-DD
 * @param {Date} d - Date object
 * @returns {string} Formatted date string
 */
export const formatDateYMD = (d) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};

/**
 * Get current month's start and end dates
 * @returns {Object} Object with start and end date strings
 */
export const getCurrentMonthRange = () => {
  const now = new Date();
  const first = new Date(now.getFullYear(), now.getMonth(), 1);
  const last = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  return { start: formatDateYMD(first), end: formatDateYMD(last) };
};

/**
 * Check if date string is in current month
 * @param {string} ymd - Date string in YYYY-MM-DD format
 * @returns {boolean} True if date is in current month
 */
export const isSameMonthAsNow = (ymd) => {
  if (!ymd) return false;
  const [y, m] = ymd.split("-").map(Number);
  const now = new Date();
  return y === now.getFullYear() && m === now.getMonth() + 1;
};

/**
 * Convert display date format to API format
 * @param {string} displayDate - Date in "YYYY.MM.DD" format
 * @returns {string} Date in "YYYY-MM-DD" format
 */
export const displayToAPIDate = (displayDate) => {
  return displayDate.replace(/\./g, "-");
};
