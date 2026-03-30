// frontend/my-app/src/components/CardGrid.jsx
import React, { useEffect, useState, useContext, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import "../assets/components/_cardGrid.scss";
import { fetchLiveDetections } from "../api/liveDetections";
import { videoStreams } from "../api/videoStreamURLs";
import recLogo from "../assets/icons/rec.png";
import { CameraContext } from "../context/CameraContext";
import DangerZoneOverlay from "./DangerZone/DangerZoneOverlay"; 

const CardGrid = () => {
  const navigate = useNavigate();
  const [liveResults, setLiveResults] = useState({});
  const { cameraData } = useContext(CameraContext);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const doFetch = async () => {
      const data = await fetchLiveDetections();
      if (!mounted) return;
      setLiveResults(data);
      if (loading) setLoading(false);
    };

    doFetch();
    const interval = setInterval(doFetch, 1000);

    // listen for global refresh events to do a light fetch and show spinner
    const onAppRefresh = (e) => {
      const targetPath = e?.detail?.path;
      if (targetPath && targetPath !== window.location.pathname) return;
      setLoading(true);
      doFetch();
    };
    window.addEventListener("app:refresh", onAppRefresh);

    return () => {
      mounted = false;
      clearInterval(interval);
      window.removeEventListener("app:refresh", onAppRefresh);
    };
  }, []);

  // Determine active cameras based on live results returned by backend
  const activeCards = useMemo(() => {
    const keys = new Set(Object.keys(liveResults || {}));
    const list = cameraData.filter((c) => keys.has(c.camId));
    // If backend returned nothing yet, fall back to showing all
    return list.length ? list : cameraData;
  }, [liveResults, cameraData]);

  // Decide column class based on number of active streams
  const colClass = useMemo(() => {
    const count = activeCards.length;
    if (count <= 1) return "col-12"; // 1 stream -> full width
    if (count === 2) return "col-12 col-md-6"; // 2 streams -> two equal columns
    // 3+ streams -> keep current style (3 columns on lg+)
    return "col-12 col-sm-6 col-lg-4 col-xl-4";
  }, [activeCards.length]);

  const getStatus = (detections) => {
    if (!detections) return "Unknown";

    const hasFire = detections.some((d) => d.label.toLowerCase() === "fire");
    const hasNoHelmet = detections.some((d) => d.label.toLowerCase() === "head");

    if (hasFire) return "Danger";
    if (hasNoHelmet) return "Warning";
    return "Safe";
  };

  return (
    <div className="container-fluid card-grid-wrapper py-3">
      <div className={`row g-4 px-4 ${activeCards.length >= 2 && activeCards.length <= 6 ? 'center-vertical' : ''}`}>
        {loading && (
          <div className="w-100 text-center" style={{ padding: "20px 0" }}>
            <div className="spinner-border spinner-border-sm text-primary" role="status" style={{ width: "1.5rem", height: "1.5rem" }}>
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        )}
        {activeCards.map((card) => {
          const result = liveResults[card.camId] || {};
          const detections = result?.detections || [];

          // Prefer backend-provided daily counts (today_no_helmet / today_fall)
          const noHelmetCount = typeof result.today_no_helmet === "number"
            ? result.today_no_helmet
            : detections.filter((d) => d.label.toLowerCase() === "head").length;

          const fallCount = typeof result.today_fall === "number"
            ? result.today_fall
            : detections.filter((d) => d.label.toLowerCase() === "fall").length;

          // ✅ Use backend-provided real-time status if available; fallback to computed
          const status = result.status 
            ? result.status
            : (fallCount > 0 ? "Danger" : getStatus(detections));

          const time = result && result.timestamp ? new Date(result.timestamp * 1000).toLocaleTimeString() : "Loading...";

          return (
            <div key={card.id} className={`${colClass} px-4 mx-auto ${activeCards.length === 1 ? 'single-camera' : ''}`}>
              <div
                className="card card-camera shadow-sm overflow-hidden"
                onClick={() => navigate(`/camera/${card.id}`)}
                style={{ cursor: "pointer", position: "relative" }}
              >
                <div className="card-header d-flex justify-content-between align-items-center bg-light">
                  <div className="d-flex align-items-center gap-4">
                    <span className="fw-bold">{card.cam}</span>

                  </div>

                  <div className="d-flex align-items-center gap-2 fw-bold">
                    {(status === "Danger" || status === "Warning") && (
                      <div className="record me-1">
                        <img src={recLogo} alt="record" />
                      </div>
                    )}
                    {/* Always-show indicators: orange = today no_helmet, red = today fall */}
                    <div className="dot orange"></div>
                    <span>{noHelmetCount}</span>
                    <div className="dot red"></div>
                    <span>{fallCount}</span>
                  </div>
                </div>

                <div className={`status-bar text-white text-center ${status.toLowerCase()}`}>
                  {status}
                </div>

                <div style={{ position: "relative" }}>
                  <img
                    src={videoStreams[card.camId]}
                    alt={` No Live for ${card.cam}`}
                    className="img-fluid"
                    style={{ width: "100%", objectFit: "cover" }}
                  />
                  <DangerZoneOverlay camId={card.id} width={600} height={340} />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CardGrid;
