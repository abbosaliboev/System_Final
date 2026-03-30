import React from "react";
import { Modal, Button } from "react-bootstrap";
import { useTranslation } from "react-i18next";
import "../assets/components/_deleteConfirmModal.scss";

const DeleteConfirmModal = ({ show, onClose, onConfirm }) => {
  const { t } = useTranslation();

  return (
    <Modal show={show} onHide={onClose} centered backdrop="static" className="delete-confirm-modal">
    <Modal.Header>
        <Modal.Title>{t("deleteModal.title")}</Modal.Title>
    </Modal.Header>
    <Modal.Body>
        <p className="fs-5">{t("deleteModal.message")}</p>
        <p className="text-muted">{t("deleteModal.warning")}</p>
    </Modal.Body>
    <Modal.Footer>
        <Button variant="secondary" onClick={onClose}>
        {t("deleteModal.cancel")}
        </Button>
        <Button variant="danger" onClick={onConfirm}>
        {t("deleteModal.confirm")}
        </Button>
    </Modal.Footer>
    </Modal>

  );
};

export default DeleteConfirmModal;
