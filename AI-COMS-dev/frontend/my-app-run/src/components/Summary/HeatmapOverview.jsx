// ==== HeatmapOverview.jsx (final scroll-synced version) ====
import React, { useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";

const getColor = (v = 0) => {
  if (v <= 0) return "var(--heatmap-level-0, #eef2f7)";
  if (v < 5) return "var(--heatmap-level-1, #b3c6e6)";
  if (v < 10) return "var(--heatmap-level-2, #5a99d4)";
  if (v < 20) return "var(--heatmap-level-3, #1b4f72)";
  return "var(--heatmap-level-4, #0a2855)";
};

const HeatmapOverview = ({ heatmapData = [], loading = false }) => {
  const { t } = useTranslation();
  const hours = useMemo(() => Array.from({ length: 24 }, (_, i) => i), []);

  useEffect(() => {
    if (!window.bootstrap || !heatmapData.length) return;
    const tooltips = [...document.querySelectorAll('[data-bs-toggle="tooltip"]')].map(
      (el) => new window.bootstrap.Tooltip(el)
    );
    return () => tooltips.forEach((t) => t.dispose());
  }, [heatmapData]);

  console.log("🧊 HeatmapOverview received:", heatmapData);

  if (loading) {
    return (
      <div className="card heatmap-card">
        <div className="card-body text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!heatmapData.length)
    return (
      <div className="card heatmap-card">
        <div className="card-body">
          <h5 className="card-title">{t("heatmap_title")}</h5>
          <p className="text-muted text-center">{t("no_data") || "No data available"}</p>
        </div>
      </div>
    );

  return (
    <div className="card heatmap-card">
      <div className="card-body">
        <h5 className="card-title mb-3">{t("heatmap_title")}</h5>

        {/* 🔁 Scroll container - hidden on desktop, visible on mobile only */}
        <div
          className="heatmap-scroll-container"
          style={{
            overflowX: "hidden",  // Default: no scroll on desktop
            paddingBottom: "8px",
            borderRadius: "8px",
          }}
        >
          {/* All weekday rows */}
          <div className="heatmap-content" style={{ minWidth: "950px" }}>
            {heatmapData.map((row, i) => (
              <div
                key={i}
                className="heatmap-row"
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: 6,
                }}
              >
                <span
                  className="heatmap-day-label"
                  style={{
                    width: 55,
                    textAlign: "left",
                    fontWeight: 600,
                  }}
                >
                  {row[0]}
                </span>

                <div
                  className="heatmap-cells"
                  style={{
                    display: "flex",
                    flex: 1,
                    gap: "3px",
                  }}
                >
                  {row.slice(1).map((v, j) => (
                    <div
                      key={j}
                      className="heatmap-cell"
                      title={`${t("heatmap_detections") || "Detections"}: ${v}`}
                      data-bs-toggle="tooltip"
                      style={{
                        backgroundColor: getColor(v),
                        width: 28,
                        height: 28,
                        borderRadius: 5,
                        transition: "transform 0.1s ease",
                        flexShrink: 0,
                      }}
                      onMouseEnter={(e) => (e.target.style.transform = "scale(1.1)")}
                      onMouseLeave={(e) => (e.target.style.transform = "scale(1)")}
                    ></div>
                  ))}
                </div>
              </div>
            ))}

            {/* Hour labels (inside same scroll container ✅) */}
            <div
              className="heatmap-hours d-flex mt-2"
              style={{
                marginLeft: 55,
                paddingBottom: "5px",
                gap: "7px",
              }}
            >
              {hours.map((h) => (
                <span
                  key={h}
                  className="heatmap-hour-label"
                  style={{
                    width: 24,
                    textAlign: "center",
                    fontSize: 11,
                    flexShrink: 0,
                  }}
                >
                  {h.toString().padStart(2, "0")}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HeatmapOverview;
