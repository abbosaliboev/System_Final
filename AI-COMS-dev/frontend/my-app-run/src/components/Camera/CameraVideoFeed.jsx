import React from "react";
import DangerZoneCanvas from "../DangerZone/DangerZoneCanvas";
import { useTranslation } from "react-i18next";

/**
 * Camera video feed component with fullscreen support
 */
const CameraVideoFeed = ({ camera, streamUrl }) => {
  const { t } = useTranslation();

  const handleFullscreen = () => {
    const videoElement = document.getElementById(`video-cam${camera.camId}`);
    if (videoElement.requestFullscreen) {
      videoElement.requestFullscreen();
    } else if (videoElement.webkitRequestFullscreen) {
      videoElement.webkitRequestFullscreen();
    } else if (videoElement.msRequestFullscreen) {
      videoElement.msRequestFullscreen();
    }
  };

  return (
    <>
      <div className="buttons d-flex justify-content-between align-items-center mb-4">
        <div className="photo-video-toggle d-flex gap-2">
          <button className="btn">
            <i className="bi bi-camera"></i>
          </button>
          <button className="btn">
            <i className="bi bi-camera-video-fill"></i>
          </button>
        </div>
      </div>

      <div
        className="video-section p-4"
        style={{ position: "relative", width: "100%" }}
      >
        {streamUrl ? (
          <div className="video-wrapper" style={{ position: "relative" }}>
            <img
              id={`video-cam${camera.camId}`}
              src={streamUrl}
              alt={`Live stream for Camera ${camera.id}`}
              style={{
                width: "100%",
                height: "auto",
                display: "block",
              }}
            />
            <div style={{ position: "absolute", top: 0, left: 0 }}>
              <DangerZoneCanvas
                camId={camera.id}
                containerId={`video-cam${camera.camId}`}
              />
            </div>

            <button
              onClick={handleFullscreen}
              className="btn btn-sm fullscreen-btn"
              style={{
                position: "absolute",
                bottom: "10px",
                right: "10px",
                zIndex: 20,
                padding: "6px 12px",
                fontSize: "14px",
                borderRadius: "6px",
              }}
            >
              ⛶
            </button>
          </div>
        ) : (
          <div className="text-center text-danger">
            {t("camera.noStream", { id: camera.id })}
          </div>
        )}
      </div>
    </>
  );
};

export default CameraVideoFeed;
