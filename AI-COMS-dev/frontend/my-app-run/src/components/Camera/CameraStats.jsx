import React from "react";
import { useTranslation } from "react-i18next";
import icons from "../../assets/constants/icons";
import ViolationRanking from "../Summary/ViolationRanking";

/**
 * Camera statistics and detections panel
 * Shows alert counts for the last 7 days only (for performance)
 */
const CameraStats = ({ alertsCount, alertCounts }) => {
  const { t } = useTranslation();

  const statsData = [
    { label: "No Helmet", icon: icons.helmet, count: alertCounts.noHelmet },
    { label: "Danger Zone", icon: icons.zone, count: alertCounts.dangerZone },
    { label: "Fire", icon: icons.fire, count: alertCounts.fire },
    { label: "Fall", icon: icons.fall, count: alertCounts.fall },
  ];

  return (
    <div className="stats-section d-flex flex-column gap-4">
      <div className="alert-box d-flex align-items-center justify-content-center">
        <i className="bi bi-exclamation-triangle-fill me-2"></i>
        <span>
          {alertsCount} {t("totalAlerts")} <small className="text-muted">(7 days)</small>
        </span>
      </div>

      <div className="summary-card p-4 rounded text-white">
        <div className="row text-center">
          {statsData.map(({ label, icon, count }) => (
            <div className="col-6 mb-3" key={label}>
              <div className="label">{label}</div>
              <div className="count-box d-flex align-items-center justify-content-center gap-3">
                <div className="count">{count}</div>
                <div className="summary-icon">
                  <img src={icon} alt={label} width={24} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <ViolationRanking />
    </div>
  );
};

export default CameraStats;
