import React, { useContext } from "react";
import { useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { CameraContext } from "../context/CameraContext";
import { videoStreams } from "../api/videoStreamURLs";
import { useCameraAlerts } from "../hooks/useCameraAlerts";
import CameraAlertsList from "../components/Camera/CameraAlertsList";
import CameraVideoFeed from "../components/Camera/CameraVideoFeed";
import CameraStats from "../components/Camera/CameraStats";
import "../assets/components/_camera.scss";

const Camera = () => {
  const { id } = useParams();
  const { t } = useTranslation();
  const { cameraData } = useContext(CameraContext);

  // Find the current camera by ID
  const camera = cameraData.find((cam) => cam.id === parseInt(id));
  const streamUrl = camera ? videoStreams[camera.camId] : null;

  // Fetch and manage alerts
  const {
    alerts,
    filter,
    setFilter,
    loading,
    visibleAlerts,
    alertCounts,
    sentinelRef,
    hasMore,
  } = useCameraAlerts(camera);

  return (
    <div className="container-fluid camera-page">
      <div className="row g-4">
        {/* Alerts Panel */}
        <div className="col-12 col-lg-3 px-3">
          <h2 className="mb-4 fw-bold">{t("alertsTitle")}</h2>
          <CameraAlertsList
            visibleAlerts={visibleAlerts}
            filter={filter}
            onFilterChange={setFilter}
            loading={loading}
            sentinelRef={sentinelRef}
            hasMore={hasMore}
          />
        </div>

        {/* Video Feed Section */}
        <div className="col-12 col-lg-6 px-3">
          <CameraVideoFeed camera={camera} streamUrl={streamUrl} />
        </div>

        {/* Stats & Detections Section */}
        <div className="col-12 col-lg-3 px-3">
          <CameraStats alertsCount={alerts.length} alertCounts={alertCounts} />
        </div>
      </div>
    </div>
  );
};

export default Camera;
