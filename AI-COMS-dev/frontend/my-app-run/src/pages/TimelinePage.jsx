import React, { useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import Toast from "../components/Toast";
import DeleteConfirmModal from "../components/DeleteConfirmModal";
import ReportModal from "../components/ReportModal";
import AlertsList from "../components/Timeline/AlertsList";
import ArchivePanel from "../components/Timeline/ArchivePanel";
import { useTimelineData } from "../hooks/useTimelineData";
import "../assets/components/_timeline.scss";

const TimelinePage = () => {
  const { t } = useTranslation();

  const {
    allAlerts,
    fetched,
    loading,
    loadingMore,
    selectedCam,
    setSelectedCam,
    updateAlert,
    deleteAlert,
    loadMoreAlerts,
    hasMore,
    PAGE_CHUNK,
  } = useTimelineData();

  const [filter, setFilter] = useState("most_recent");
  const [showModal, setShowModal] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");
  const [toastType, setToastType] = useState("success");
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [alertToDelete, setAlertToDelete] = useState(null);

  const sortedAlerts = useMemo(() => {
    const arr = [...allAlerts];
    arr.sort((a, b) =>
      filter === "most_recent"
        ? new Date(b.timestamp) - new Date(a.timestamp)
        : new Date(a.timestamp) - new Date(b.timestamp)
    );
    return arr;
  }, [allAlerts, filter]);

  const handleRecordClick = (record) => {
    console.log("TimelinePage: handleRecordClick called with:", record);
    setSelectedRecord(record);
    setShowModal(true);
    console.log("TimelinePage: showModal set to true");
  };

  const triggerToast = (messageKey, type = "success") => {
    setToastMessage(messageKey);
    setToastType(type);
    setShowToast(true);
  };

  const handleReportSubmit = (reportData) => {
    updateAlert(reportData.alert_id, { reported: true });
    triggerToast("reportSuccess", "success");
    setShowModal(false);
  };

  const handleDeleteClick = (id) => {
    setAlertToDelete(id);
    setShowConfirmModal(true);
  };

  const confirmDelete = async () => {
    if (!alertToDelete) return;
    try {
      await deleteAlert(alertToDelete);
      triggerToast("deleteSuccess", "success");
    } catch (error) {
      console.error("Delete error:", error);
      triggerToast("deleteFail", "error");
    } finally {
      setShowConfirmModal(false);
      setAlertToDelete(null);
    }
  };

  // Show full-page spinner while initial data is loading
  if (loading && !fetched) {
    return (
      <div className="container-fluid timeline-page p-4 d-flex justify-content-center align-items-center" style={{ minHeight: "80vh" }}>
        <div className="text-center">
          <div className="spinner-border text-primary" role="status" style={{ width: "3rem", height: "3rem" }}>
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3 text-muted">{t("loading") || "Loading timeline..."}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container-fluid timeline-page p-4">
      {/* Refresh overlay — shown when re-fetching after initial load */}
      {loading && fetched && (
        <div className="page-loading-overlay">
          <div className="spinner-border text-primary" role="status" style={{ width: "3rem", height: "3rem" }}>
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      )}
      <div className="row">
        <AlertsList
          alerts={sortedAlerts}
          filter={filter}
          onFilterChange={setFilter}
          loading={loading}
          fetched={fetched}
          pageChunk={PAGE_CHUNK}
          loadMoreAlerts={loadMoreAlerts}
          hasMore={hasMore}
          loadingMore={loadingMore}
        />

        <ArchivePanel
          alerts={sortedAlerts}
          selectedCam={selectedCam}
          onSelectCam={setSelectedCam}
          onRecordClick={handleRecordClick}
          onDeleteClick={handleDeleteClick}
          fetched={fetched}
          loading={loading}
          pageChunk={PAGE_CHUNK}
          loadMoreAlerts={loadMoreAlerts}
          hasMore={hasMore}
          loadingMore={loadingMore}
        />
      </div>

      {showModal && selectedRecord && (
        <ReportModal
          record={selectedRecord}
          onClose={() => setShowModal(false)}
          onSubmit={handleReportSubmit}
        />
      )}

      <Toast
        message={toastMessage}
        show={showToast}
        onClose={() => setShowToast(false)}
        type={toastType}
      />

      <DeleteConfirmModal
        show={showConfirmModal}
        onClose={() => setShowConfirmModal(false)}
        onConfirm={confirmDelete}
      />
    </div>
  );
};

export default TimelinePage;
