// File: components/MoreInfoModal.jsx
import React from "react";
import { Modal, Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";

const MoreInfoModal = ({ show, onHide, data }) => {
  const { t } = useTranslation();

  if (!data) return null;

  return (
    <Modal show={show} onHide={onHide} centered>
      <Modal.Header closeButton>
        <Modal.Title>{t("report_details")}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <p><strong>{t("name")}:</strong> {data.name}</p>
        <p><strong>{t("department")}:</strong> {data.department || t("unknown")}</p>
        <p><strong>{t("supervisor")}:</strong> {data.supervisor || t("unknown")}</p>
        <p><strong>{t("camera")}:</strong> {data.cameraId}</p>
        <p><strong>{t("event")}:</strong> {data.event}</p>
        <p><strong>{t("date")}:</strong> {data.date}</p>
      </Modal.Body>
      <Modal.Footer>
        <Button variant="secondary" onClick={onHide}>
          {t("close")}
        </Button>
      </Modal.Footer>
    </Modal>
  );
};

export default MoreInfoModal;
