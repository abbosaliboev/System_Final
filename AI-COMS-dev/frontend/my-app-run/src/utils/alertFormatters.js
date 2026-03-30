import icons from "../assets/constants/icons";

/**
 * Format timestamp to readable string
 */
export const formatTime = (str) =>
  new Date(str).toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });

/**
 * Get icon for alert type
 */
export const getAlertIcon = (type) => {
  const iconMap = {
    no_helmet: icons.helmet,
    helmet: icons.helmet,
    vest: icons.vest,
    novest: icons.vest,
    zone: icons.zone,
    danger_zone: icons.zone,
    fire: icons.fire,
    fall: icons.fall,
  };
  return iconMap[type?.toLowerCase()] || icons.zone;
};

/**
 * Format alert type for display
 */
export const formatAlertType = (type) => {
  const typeMap = {
    no_helmet: "NO HELMET",
    helmet: "HELMET",
    vest: "VEST",
    novest: "NO VEST",
    zone: "ZONE",
    danger_zone: "DANGER ZONE",
    fire: "FIRE",
    fall: "FALL",
  };
  return typeMap[type] || (type ? String(type).toUpperCase() : "");
};
