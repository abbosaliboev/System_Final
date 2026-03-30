import React from "react";
import { useTranslation } from "react-i18next";
import { formatTime, formatAlertType } from "../../utils/alertFormatters";
import sampleImage from "../../assets/images/test.png";
import "./_recordCard.scss";

/**
 * RecordCard - Individual record/alert card component
 */
const RecordCard = ({ record, onRecordClick, onDeleteClick }) => {
  const { t } = useTranslation();

  const handleRootClick = () => {
    if (typeof onRecordClick === "function") {
      onRecordClick(record);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleRootClick();
    }
  };

  return (
    <div
      className="record-card p-3 mb-3 rounded shadow-sm position-relative"
      role="button"
      tabIndex={0}
      onClick={handleRootClick}
      onKeyPress={handleKey}
    >
      {/* Delete button */}
      <button
        className="delete-btn btn btn-outline-secondary"
        onClick={(e) => {
          e.stopPropagation();
          onDeleteClick(record.id);
        }}
        aria-label="Delete record"
      >
        <i className="bi bi-trash3-fill" />
      </button>

      {/* Inner layout */}
      <div className="d-flex align-items-center card-in">
        {/* Image */}
        <img
          src={record.frame_image || sampleImage}
          alt="Alert frame"
          className="record-image me-3"
          onError={(e) => {
            e.target.onerror = null;
            e.target.src = sampleImage;
          }}
        />

        {/* Text content */}
        <div className="flex-grow-1">
          <p className="mb-1">
            <strong>{t("time")}:</strong> {formatTime(record.timestamp)}
          </p>
          <p className="mb-0">
            <strong>{t("situation")}:</strong> {formatAlertType(record.alert_type)}
          </p>
        </div>
      </div>

      {/* Status badge */}
      <div className="record-status position-absolute">
        <span className={`badge ${record.reported ? "bg-success" : "bg-primary"}`}>
          {record.reported ? t("reported") : t("new")}
        </span>
      </div>
    </div>
  );
};

export default RecordCard;
