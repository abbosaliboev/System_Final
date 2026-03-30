import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Table component for displaying report data
 */
const ReportTable = ({
  loading,
  error,
  filteredData,
  selectedRows,
  onToggleSelect,
  onSelectAll,
  onMoreInfo,
}) => {
  const { t } = useTranslation();

  const isAllSelected = selectedRows.length === filteredData.length && filteredData.length > 0;

  return (
    <div className="table-wrapper">
      <div className="table-responsive">
        <table className="table table-bordered table-hover">
          <thead className="table-dark">
            <tr>
              <th>{t("id") || "ID"}</th>
              <th>{t("name") || "Name"}</th>
              <th>{t("date") || "Date"}</th>
              <th>{t("event") || "Event"}</th>
              <th>{t("notify") || "Notify"}</th>
              <th>
                <button
                  className="btn btn-light btn-sm"
                  onClick={onSelectAll}
                  disabled={loading || filteredData.length === 0}
                >
                  {isAllSelected
                    ? t("deselect_all") || "Deselect All"
                    : t("select_all") || "Select All"}
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="6" className="text-center py-4">
                  <div className="spinner-border spinner-border-sm me-2" role="status">
                    <span className="visually-hidden">Loading...</span>
                  </div>
                  {t("loading") || "Loading reports..."}
                </td>
              </tr>
            ) : filteredData.length > 0 ? (
              filteredData.map((item) => (
                <tr key={`${item.reportId}-${item.date}`} className="align-middle">
                  <td className="fw-bold">{item.id}</td>
                  <td>{item.name}</td>
                  <td className="text-nowrap">{item.date}</td>
                  <td>
                    <button
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => onMoreInfo(item)}
                      title="Click for more details"
                    >
                      {t(item.event.toLowerCase().replaceAll(" ", "_"))}
                    </button>
                  </td>
                  <td>
                    <span
                      className={`badge px-2 py-1 rounded-pill fw-semibold ${
                        item.status === "ALERTED"
                          ? "bg-success text-white"
                          : "bg-warning text-dark"
                      }`}
                    >
                      {t(item.status.toLowerCase())}
                    </span>
                  </td>
                  <td className="text-center">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      checked={selectedRows.includes(item.reportId)}
                      onChange={() => onToggleSelect(item.reportId)}
                    />
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="6" className="text-center py-4 text-muted">
                  {error
                    ? "Unable to load reports"
                    : t("no_results") || "No reports found for the selected criteria"}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ReportTable;
