import React, { useRef, useEffect, useState, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { formatTime, getAlertIcon } from "../../utils/alertFormatters";

const AlertsList = ({ 
  alerts, 
  filter, 
  onFilterChange, 
  loading, 
  fetched, 
  pageChunk,
  loadMoreAlerts,
  hasMore,
  loadingMore 
}) => {
  const { t } = useTranslation();
  const [visibleCount, setVisibleCount] = useState(pageChunk);
  const sentinelRef = useRef(null);
  const listRef = useRef(null);

  const sortedAlerts = useMemo(() => {
    const arr = [...alerts];
    arr.sort((a, b) =>
      filter === "most_recent"
        ? new Date(b.timestamp) - new Date(a.timestamp)
        : new Date(a.timestamp) - new Date(b.timestamp)
    );
    return arr;
  }, [alerts, filter]);

  const visibleAlerts = useMemo(
    () => sortedAlerts.slice(0, Math.min(visibleCount, sortedAlerts.length)),
    [sortedAlerts, visibleCount]
  );

  // Infinite scroll for UI display
  useEffect(() => {
    if (!sentinelRef.current) return;
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          // First, show more from current data
          if (visibleCount < sortedAlerts.length) {
            setVisibleCount((prev) => Math.min(prev + pageChunk, sortedAlerts.length));
          } 
          // If all current data shown and more available, load from backend
          else if (hasMore && !loadingMore && loadMoreAlerts) {
            loadMoreAlerts();
          }
        }
      },
      { root: null, rootMargin: "100px", threshold: 0.01 }
    );
    obs.observe(sentinelRef.current);
    return () => obs.disconnect();
  }, [sortedAlerts.length, pageChunk, visibleCount, hasMore, loadingMore, loadMoreAlerts]);

  useEffect(() => {
    setVisibleCount(pageChunk);
  }, [filter, pageChunk]);

  return (
    <div className="col-12 col-lg-3 px-2 alerts-panel">
      <h2 className="mb-4 fw-bold">{t("alertsTitle")}</h2>
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

        <div className="alert-list" ref={listRef}>
          {loading && !fetched ? (
            <div className="timeline-inner-loading text-center py-4">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <div className="mt-2">{t("loading") || "Loading alerts..."}</div>
            </div>
          ) : (
            <>
              {visibleAlerts.map((alert, i) => (
                <div
                  key={`${alert.id ?? "a"}-${i}`}
                  className="alert-item d-flex justify-content-between align-items-center p-2 mb-2 rounded"
                >
                  <span>
                    <strong>{`Cam ${alert.camera_id}`}</strong>{" "}
                    {formatTime(alert.timestamp)}
                  </span>
                  <img
                    src={getAlertIcon(alert.alert_type)}
                    alt={alert.alert_type}
                    width={24}
                    height={24}
                  />
                </div>
              ))}

              {/* Sentinel for infinite scroll */}
              {(visibleCount < sortedAlerts.length || hasMore) && (
                <div ref={sentinelRef} className="text-center py-2">
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

              {sortedAlerts.length === 0 && !loading && (
                <div className="text-center py-2 small text-muted">
                  {t("noAlerts") || "No alerts"}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AlertsList;
