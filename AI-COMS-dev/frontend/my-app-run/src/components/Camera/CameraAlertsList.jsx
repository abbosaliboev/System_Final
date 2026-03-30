import React from "react";
import { useTranslation } from "react-i18next";
import { formatAlertTime, getAlertIconSrc } from "../../utils/cameraUtils";
import icons from "../../assets/constants/icons";

/**
 * Camera alerts list component with infinite scroll
 */
const CameraAlertsList = ({
  visibleAlerts,
  filter,
  onFilterChange,
  loading,
  sentinelRef,
  hasMore,
}) => {
  const { t } = useTranslation();

  return (
    <div className="alerts-card">
      <div className="alert-filter mb-2">
        <select
          className="form-select px-2"
          value={filter}
          onChange={(e) => onFilterChange(e.target.value)}
        >
          <option value="most_recent">{t("filterRecent")}</option>
          <option value="oldest">{t("filterOldest")}</option>
        </select>
      </div>

      <div className="alert-list">
        {visibleAlerts.length > 0 ? (
          <>
            {visibleAlerts.map((alert, i) => (
              <div
                key={alert.id || i}
                className="alert-item d-flex justify-content-between align-items-center p-2 mb-2 rounded"
              >
                <span>{formatAlertTime(alert.timestamp)}</span>
                <img
                  src={getAlertIconSrc(alert.alert_type, icons)}
                  alt={alert.alert_type || "Unknown"}
                  width={24}
                  height={24}
                  onError={() =>
                    console.error("Failed to load icon:", alert.alert_type)
                  }
                />
              </div>
            ))}

            {hasMore && (
              <div ref={sentinelRef} className="text-center py-2">
                <div
                  className="spinner-border spinner-border-sm text-primary"
                  role="status"
                >
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center text-muted p-2">
            {loading ? (
              <div>
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              t("noAlerts")
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CameraAlertsList;
