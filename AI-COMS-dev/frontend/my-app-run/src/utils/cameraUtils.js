/**
 * Utility functions for alert formatting
 */

/**
 * Format ISO timestamp to readable string
 * @param {string} isoString - ISO 8601 timestamp
 * @returns {string} Formatted date string
 */
export const formatAlertTime = (isoString) => {
  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) throw new Error("Invalid date");
    return date.toLocaleString("en-US", {
      month: "short",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  } catch (error) {
    console.error("Invalid time:", isoString);
    return "Invalid Time";
  }
};

/**
 * Get alert icon based on type
 * @param {string} alertType - Alert type string
 * @param {Object} icons - Icons object
 * @returns {string} Icon URL
 */
export const getAlertIconSrc = (alertType, icons) => {
  const type = alertType?.toLowerCase();
  switch (type) {
    case "no_helmet":
      return icons.helmet;
    case "danger_zone":
      return icons.zone;
    case "fire":
      return icons.fire;
    case "fall":
      return icons.fall;
    default:
      return icons.default;
  }
};
