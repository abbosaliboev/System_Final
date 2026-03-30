import React, { useState, useEffect } from "react";
import "../assets/components/_report.scss";
import { useTranslation } from "react-i18next";
import Toast from "../components/Toast";
import MoreInfoModal from "../components/MoreInfoModal";
import ReportHeader from "../components/Report/ReportHeader";
import ReportTable from "../components/Report/ReportTable";
import { useReportData } from "../hooks/useReportData";
import {
  getCurrentMonthRange,
  isSameMonthAsNow,
  displayToAPIDate,
} from "../utils/dateUtils";

const ReportPage = () => {
  const { t } = useTranslation();

  // Date range state
  const initialRange = getCurrentMonthRange();
  const [startDate, setStartDate] = useState(initialRange.start);
  const [endDate, setEndDate] = useState(initialRange.end);

  // Reset to current month on mount if dates are from previous month
  useEffect(() => {
    if (!isSameMonthAsNow(startDate) || !isSameMonthAsNow(endDate)) {
      const r = getCurrentMonthRange();
      setStartDate(r.start);
      setEndDate(r.end);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Search and selection state
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRows, setSelectedRows] = useState([]);

  // Toast and modal state
  const [toastMessage, setToastMessage] = useState("");
  const [showToast, setShowToast] = useState(false);
  const [toastType, setToastType] = useState("success");
  const [modalData, setModalData] = useState(null);
  const [showModal, setShowModal] = useState(false);

  // Data from custom hook
  const { data, loading, error, sending, sendAlerts, downloadPDF } = useReportData();

  // Filter data by search query and date range
  const filteredData = data.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.event.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.id.toString().includes(searchQuery);

    const itemDateStr = item.date.split(" ")[0]; // "YYYY.MM.DD"
    const itemDate = displayToAPIDate(itemDateStr); // -> "YYYY-MM-DD"
    const matchesDate = itemDate >= startDate && itemDate <= endDate;

    return matchesSearch && matchesDate;
  });

  // Selection handlers
  const toggleSelect = (id) => {
    setSelectedRows((prev) =>
      prev.includes(id) ? prev.filter((rowId) => rowId !== id) : [...prev, id]
    );
  };

  const handleSelectAll = () => {
    if (selectedRows.length === filteredData.length) {
      setSelectedRows([]);
    } else {
      setSelectedRows(filteredData.map((item) => item.reportId));
    }
  };

  // Modal handler
  const handleMoreInfo = (item) => {
    setModalData(item);
    setShowModal(true);
  };

  // Toast helper
  const triggerToast = (messageKey, type = "success") => {
    setToastMessage(messageKey);
    setToastType(type);
    setShowToast(true);
  };

  // Action handlers
  const handleSendAlerts = () => {
    sendAlerts(
      selectedRows,
      (msg) => triggerToast(msg, "success"),
      (msg) => triggerToast(msg, "error")
    );
  };

  const handleDownloadPDF = () => {
    downloadPDF(startDate, endDate, (msg) => triggerToast(msg, "error"));
  };

  return (
    <div className="search-results-page">
      <ReportHeader
        startDate={startDate}
        endDate={endDate}
        onStartDateChange={setStartDate}
        onEndDateChange={setEndDate}
        selectedCount={selectedRows.length}
        onSendAlerts={handleSendAlerts}
        onDownloadPDF={handleDownloadPDF}
        sending={sending}
        hasData={filteredData.length > 0}
      />

      {/* Search bar */}
      <div className="search-section">
        <h5 className="fw-bold">
          {t("search_results")}
          {!loading && (
            <span>
              {" "}
              ({filteredData.length}{" "}
              {t(filteredData.length === 1 ? "result" : "results")})
            </span>
          )}
        </h5>
        <input
          type="text"
          placeholder={t("search_placeholder") || "Search by name, event, or ID..."}
          className="form-control search-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label={t("search_input")}
        />
      </div>

      {/* Error message */}
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <ReportTable
        loading={loading}
        error={error}
        filteredData={filteredData}
        selectedRows={selectedRows}
        onToggleSelect={toggleSelect}
        onSelectAll={handleSelectAll}
        onMoreInfo={handleMoreInfo}
      />

      {/* Summary footer */}
      {!loading && filteredData.length > 0 && (
        <div className="mt-3 text-muted">
          <small>
            {t("showing")} {filteredData.length} {t("of")} {data.length}{" "}
            {t("total_reports")}
            {selectedRows.length > 0 && ` • ${selectedRows.length} ${t("selected")}`}
          </small>
        </div>
      )}

      <Toast
        message={toastMessage}
        show={showToast}
        onClose={() => setShowToast(false)}
        type={toastType}
      />

      <MoreInfoModal
        show={showModal}
        onHide={() => setShowModal(false)}
        data={modalData}
      />
    </div>
  );
};

export default ReportPage;
