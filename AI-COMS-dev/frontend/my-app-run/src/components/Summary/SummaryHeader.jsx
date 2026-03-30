import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Filter header component for Summary page
 */
const SummaryHeader = ({
  rangeType,
  startDate,
  loading,
  onRangeChange,
  onCustomDateChange,
}) => {
  const { t } = useTranslation();

  return (
    <div className="summary-header d-flex align-items-center gap-3 flex-wrap mb-4">
      <div className="dropdown">
        <button
          className="btn btn-outline-primary dropdown-toggle"
          type="button"
          data-bs-toggle="dropdown"
          aria-expanded="false"
        >
          {rangeType === "this"
            ? t("this_week") || "This Week"
            : rangeType === "last"
            ? t("last_week") || "Last Week"
            : t("custom_range") || "Custom Range"}
        </button>
        <ul className="dropdown-menu">
          <li>
            <button
              className={`dropdown-item ${rangeType === "this" ? "active" : ""}`}
              onClick={() => onRangeChange("this")}
            >
              {t("this_week") || "This Week"}
            </button>
          </li>
          <li>
            <button
              className={`dropdown-item ${rangeType === "last" ? "active" : ""}`}
              onClick={() => onRangeChange("last")}
            >
              {t("last_week") || "Last Week"}
            </button>
          </li>
          <li>
            <button
              className={`dropdown-item ${
                rangeType === "custom" ? "active" : ""
              }`}
              onClick={() => onRangeChange("custom")}
            >
              {t("custom_range") || "Custom Range"}
            </button>
          </li>
        </ul>
      </div>

      {rangeType === "custom" && (
        <div className="d-flex align-items-center gap-2">
          <input
            type="date"
            className="form-control"
            style={{ maxWidth: 180 }}
            value={startDate}
            onChange={onCustomDateChange}
          />
          <small className="text-muted">
            {t("one_week_range") || "1 week range"}
          </small>
        </div>
      )}

      {loading && (
        <div
          className="spinner-border spinner-border-sm text-primary ms-2"
          role="status"
        >
          <span className="visually-hidden">Loading...</span>
        </div>
      )}
    </div>
  );
};

export default SummaryHeader;
