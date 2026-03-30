import React, { useRef, useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import RecordCard from "./RecordCard";

const ArchivePanel = ({
  alerts,
  selectedCam,
  onSelectCam,
  onRecordClick,
  onDeleteClick,
  fetched,
  loading,
  pageChunk,
  loadMoreAlerts,
  hasMore,
  loadingMore,
}) => {
  const { t } = useTranslation();
  const [camVisibleCounts, setCamVisibleCounts] = useState({});
  const sentinelRef = useRef(null);

  const uniqueCams = useMemo(
    () => [...new Set(alerts.map((a) => a.camera_id))].sort((a, b) => a - b),
    [alerts]
  );

  const recordsByCam = useMemo(() => {
    const map = new Map();
    uniqueCams.forEach((cid) => map.set(cid, []));
    for (const rec of alerts) {
      if (!map.has(rec.camera_id)) map.set(rec.camera_id, []);
      map.get(rec.camera_id).push(rec);
    }
    return map;
  }, [alerts, uniqueCams]);

  const selectedRecords = useMemo(() => {
    if (selectedCam == null) return [];
    return recordsByCam.get(selectedCam) || [];
  }, [recordsByCam, selectedCam]);

  const visibleCount = camVisibleCounts[selectedCam] ?? pageChunk;
  const visibleRecords = useMemo(
    () => selectedRecords.slice(0, Math.min(visibleCount, selectedRecords.length)),
    [selectedRecords, visibleCount]
  );

  useEffect(() => {
    const initCounts = {};
    uniqueCams.forEach((id) => (initCounts[id] = pageChunk));
    setCamVisibleCounts((prev) => ({ ...initCounts, ...prev }));
  }, [uniqueCams, pageChunk]);

  useEffect(() => {
    if (!sentinelRef.current || selectedCam == null) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          const total = selectedRecords.length;
          const current = camVisibleCounts[selectedCam] ?? pageChunk;
          
          // First show more from current data
          if (current < total) {
            setCamVisibleCounts((prev) => ({
              ...prev,
              [selectedCam]: Math.min(current + pageChunk, total)
            }));
          } 
          // If all shown and more available from backend, load more
          else if (hasMore && !loadingMore && loadMoreAlerts) {
            loadMoreAlerts();
          }
        }
      },
      { root: null, rootMargin: "100px", threshold: 0.01 }
    );
    obs.observe(sentinelRef.current);
    return () => obs.disconnect();
  }, [selectedRecords.length, selectedCam, pageChunk, camVisibleCounts, hasMore, loadingMore, loadMoreAlerts]);

  const handleCameraSelect = (id) => {
    onSelectCam(id);
    setCamVisibleCounts((prev) => ({
      ...prev,
      [id]: prev[id] ?? pageChunk,
    }));
  };

  return (
    <div className="col-12 col-lg-9">
      <h2 className="fw-bold mb-4">{t("archiveTitle")}</h2>
      <div className="archive-container p-4 rounded shadow-sm">
        <div className="buttons mb-3">
          {uniqueCams.map((id) => (
            <button
              key={id}
              className={`btn ${id === selectedCam ? "btn-dark" : "btn-outline-dark"} me-2 mb-2`}
              onClick={() => handleCameraSelect(id)}
            >
              {`Cam ${id}`}
            </button>
          ))}
        </div>
        <hr />

        <div className="record-list">
          {loading && !fetched ? (
            <div className="timeline-inner-loading text-center py-4">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              {t("loading") || "Loading archive..."}
            </div>
          ) : (
            <>
              {selectedCam == null && (
                <div className="text-center py-2 small text-muted">
                  {t("loading...") || "No records"}
                </div>
              )}

              {visibleRecords.map((rec, i) => (
                <RecordCard
                  key={`${rec.id ?? "r"}-${i}`}
                  record={rec}
                  onRecordClick={onRecordClick}
                  onDeleteClick={onDeleteClick}
                />
              ))}

              {/* Sentinel for infinite scroll - show when more data available */}
              {selectedCam != null && (visibleCount < selectedRecords.length || hasMore) && (
                <div ref={sentinelRef} className="text-center py-3">
                  {loadingMore ? (
                    <>
                      <div className="spinner-border spinner-border-sm text-primary" role="status">
                        <span className="visually-hidden">Loading...</span>
                      </div>
                      <div className="small text-muted mt-1">{t("loadingMore") || "Loading more..."}</div>
                    </>
                  ) : (
                    <div className="spinner-border spinner-border-sm text-primary" role="status">
                      <span className="visually-hidden">Loading...</span>
                    </div>
                  )}
                </div>
              )}

              {selectedCam != null && selectedRecords.length === 0 && !loading && (
                <div className="text-center py-2 small text-muted">
                  {t("noRecords") || "No records"}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ArchivePanel;
