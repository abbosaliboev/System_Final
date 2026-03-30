import React, { useEffect } from "react";
import "../assets/components/_toast.scss";
import { useTranslation } from "react-i18next";

const Toast = ({ message, show, onClose, type = "success" }) => {
  const { t } = useTranslation();

  useEffect(() => {
    if (show) {
      const timer = setTimeout(() => {
        onClose();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  return (
    <div className={`toast-container ${type} ${show ? "show" : "hide"}`}>
      <div className="toast-body d-flex align-items-center justify-content-between">
        <span>{t(message)}</span>
        <button type="button" className="toast-close-btn" onClick={onClose}>
          &times;
        </button>
      </div>
    </div>
  );
};

export default Toast;
