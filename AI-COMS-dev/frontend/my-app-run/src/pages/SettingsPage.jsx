import React, { useState, useContext } from "react";
import { CameraContext } from "../context/CameraContext";
import { useTranslation } from "react-i18next";
import "../assets/components/_settings.scss";

const SettingsPage = ({ isDarkMode, setIsDarkMode }) => {
  const { t } = useTranslation();
  const { cameraData, updateCameraName } = useContext(CameraContext);
  const [cameraNames, setCameraNames] = useState(
    cameraData.reduce((acc, camera) => {
      acc[camera.id] = camera.cam;
      return acc;
    }, {})
  );
  const [showCameraInputs, setShowCameraInputs] = useState(false);
  const [editingCameraId, setEditingCameraId] = useState(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  const handleToggle = () => {
    setIsDarkMode(!isDarkMode);
  };

  const handleNameChange = (id, value) => {
    setCameraNames((prev) => ({ ...prev, [id]: value }));
  };

  const handleSaveName = (id) => {
    const newName = cameraNames[id].trim();
    if (newName) {
      updateCameraName(id, newName);
      setToastMessage(t("camera_name_updated", { id }));
      setShowToast(true);
      setEditingCameraId(null);
      setTimeout(() => setShowToast(false), 3000);
    }
  };

  const toggleCameraInputs = () => {
    setShowCameraInputs(!showCameraInputs);
  };

  return (
    <div className="container py-5">
      <h2 className="mb-4">{t("settings")}</h2>

      {/* Dark Mode Toggle */}
      <div className="dark-mode-toggle mb-4">
        <label className="switch">
          <input
            type="checkbox"
            id="darkModeToggle"
            checked={isDarkMode}
            onChange={handleToggle}
          />
          <span className="slider round"></span>
        </label>
        <span className="ms-2">{t("enable_dark_mode")}</span>
      </div>

      {/* Toggle Camera Input Section */}
      <button
        className={`btn ${showCameraInputs ? 'btn-secondary' : 'btn-light'} mb-3 d-flex align-items-center gap-2`}
        onClick={toggleCameraInputs}
      >
        {showCameraInputs ? t("hide_camera_name_settings") : t("show_camera_name_settings")}
        <i className={`bi ${showCameraInputs ? 'bi-chevron-up' : 'bi-chevron-down'}`}></i>
      </button>

      {/* Camera Name Settings */}
      {showCameraInputs && (
        <div className="camera-settings">
          {cameraData.map((camera) => (
            <div key={camera.id} className="camera-item d-flex justify-content-between align-items-center mb-3">
              <label htmlFor={`cameraName${camera.id}`} className="camera-label">
                (ID: {camera.id}) {camera.cam}
              </label>

              {editingCameraId === camera.id ? (
                <div className="input-group">
                  <input
                    type="text"
                    id={`cameraName${camera.id}`}
                    value={cameraNames[camera.id]}
                    onChange={(e) => handleNameChange(camera.id, e.target.value)}
                  />
                  <button className="save-btn" onClick={() => handleSaveName(camera.id)}>
                    {t("save")}
                  </button>
                </div>
              ) : (
                <button className="change-btn" onClick={() => setEditingCameraId(camera.id)}>
                  {t("change")}
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Toast */}
      <div className={`toast-container ${showToast ? "show" : "hide"}`}>
        <div className="toast-body">{toastMessage}</div>
        <button
          type="button"
          className="toast-close-btn"
          onClick={() => setShowToast(false)}
        ></button>
      </div>
    </div>
  );
};

export default SettingsPage;
