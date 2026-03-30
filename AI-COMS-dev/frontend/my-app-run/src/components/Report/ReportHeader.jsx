import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Header component with date range picker and action buttons
 */
const ReportHeader = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  selectedCount,
  onSendAlerts,
  onDownloadPDF,
  sending,
  hasData,
}) => {
  const { t } = useTranslation();

  return (
    <div className="summary-header">
      <div className="date-picker">
        <input
          type="date"
          className="form-control"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          aria-label={t("start_date")}
        />
        <input
          type="date"
          className="form-control"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          min={startDate}
          aria-label={t("end_date")}
        />
      </div>
      <div className="button-group">
        <button
          className="btn"
          disabled={selectedCount === 0 || sending}
          onClick={onSendAlerts}
        >
          <i className="bi bi-bell-fill"></i> {selectedCount}{" "}
          {t(selectedCount === 1 ? "alert" : "alerts")}
        </button>
        <button
          className="btn"
          disabled={!hasData}
          onClick={onDownloadPDF}
        >
          <i className="bi bi-download"></i> {t("download")}
        </button>
      </div>
    </div>
  );
};

export default ReportHeader;
