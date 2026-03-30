import React, { useState, useEffect } from "react";
import sampleImage from "../assets/images/test.png";
import "../assets/components/_report-modal.scss";
import { useTranslation } from "react-i18next";
import Lightbox from "./Lightbox";


const ReportModal = ({ record, onClose, onSubmit }) => {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    worker: "",
    workerId: "",
    department: "",
    supervisor: "",
    event: "",
  });
  const [showLightbox, setShowLightbox] = useState(false);
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch workers from API
  useEffect(() => {
    const fetchWorkers = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch("http://127.0.0.1:8000/api/workers/");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setWorkers(Array.isArray(data) ? data : []);
      } catch (err) {
        console.error("Failed to fetch workers:", err);
        setError("Failed to load workers");
        setWorkers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchWorkers();
  }, []);

  // When worker is selected, autofill other fields
  const handleWorkerChange = e => {
    const selectedName = e.target.value;
    const worker = workers.find(w => w.name === selectedName);
    if (worker) {
      setForm({
        ...form,
        worker: worker.name,
        workerId: worker.workerId,
        department: worker.department,
        supervisor: worker.supervisor,
      });
    } else {
      setForm({
        ...form,
        worker: selectedName,
        workerId: "",
        department: "",
        supervisor: "",
      });
    }
  };

  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSend = async () => {
    const reportData = {
      ...form,
      timestamp: record.timestamp,
      camera_id: record.camera_id, // Fixed: use camera_id from record
      alert_type: record.alert_type,
      alert_id: record.id, // Include alert ID for reference
      frame_image: record.frame_image,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/api/reports/", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          // Add authentication headers if needed
          // "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify(reportData),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Report submitted successfully:", data);
      onSubmit(data);
      onClose();
    } catch (err) {
      console.error("Failed to save report:", err);
      alert("Failed to save report. Please try again.");
    }
  };

  const imageSrc = record && record.frame_image ? record.frame_image : sampleImage;

  return (
    <div className="modal-backdrop">
      <div className="modal-content report-modal">
        <h4 className="fw-bold mb-3">{t("report_title")}</h4>

        {/* Image View */}
        <div className="image-container mb-3" style={{ position: "relative" }}>
          <img
            src={imageSrc}
            alt="snapshot"
            className="img-fluid"
            onClick={() => setShowLightbox(true)}
            style={{ cursor: "zoom-in", borderRadius: "8px" }}
            onError={e => { e.target.onerror = null; e.target.src = sampleImage; }}
          />
          <span
            style={{
              position: "absolute",
              bottom: "10px",
              right: "10px",
              fontSize: "1.2rem",
              color: "white",
              padding: "4px 8px",
              borderRadius: "6px",
            }}
          >
            🔍
          </span>
        </div>

        {/* Form */}
        <div className="row mb-3">
          <div className="col">
            <label>{t("worker_name")}</label>
            <select
              className="form-control"
              name="worker"
              value={form.worker}
              onChange={handleWorkerChange}
              disabled={loading}
            >
              <option value="">
                {loading ? "Loading workers..." : error ? "Error loading workers" : t("select")}
              </option>
              {workers.map(w => (
                <option key={w.workerId} value={w.name}>
                  {w.name}
                </option>
              ))}
            </select>
            {error && (
              <small className="text-danger">{error}</small>
            )}
          </div>
          <div className="col">
            <label>{t("worker_id")}</label>
            <input
              type="text"
              className="form-control"
              name="workerId"
              value={form.workerId}
              readOnly
            />
          </div>
        </div>

        <div className="row mb-3">
          <div className="col">
            <label>{t("department")}</label>
            <input
              type="text"
              className="form-control"
              name="department"
              value={form.department}
              readOnly
            />
          </div>
          <div className="col">
            <label>{t("supervisor")}</label>
            <input
              type="text"
              className="form-control"
              name="supervisor"
              value={form.supervisor}
              readOnly
            />
          </div>
        </div>

        <div className="mb-3">
          <label>{t("event")}</label>
          <select
            name="event"
            className="form-control"
            value={form.event}
            onChange={handleChange}
          >
            <option value="">{t("select")}</option>
            <option value="Danger Zone">{t("danger_zone")}</option>
            <option value="No Helmet">{t("no_helmet")}</option>
            <option value="No Vest">{t("no_vest")}</option>
            <option value="Fall">{t("fall")}</option>
            <option value="Fire">{t("fire")}</option>
          </select>
        </div>

        <div className="d-flex justify-content-end gap-2">
          <button className="btn btn-light" onClick={onClose}>
            {t("cancel")}
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSend}
            disabled={!form.worker || !form.event}
          >
            {t("send")}
          </button>
        </div>
      </div>

      {/* Open Lightbox */}
      {showLightbox && (
        <Lightbox
          src={imageSrc}
          alt="snapshot"
          onClose={() => setShowLightbox(false)}
        />
      )}
    </div>
  );
};

export default ReportModal;
