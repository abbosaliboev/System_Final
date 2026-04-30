// Sidebar.js
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  FaHome,
  FaChartPie,
  FaClock,
  FaArchive,
  FaFileAlt,
  FaInfoCircle,
  FaUser,
} from "react-icons/fa";
import aiLogo from "../assets/icons/ai-logo.png";
import "../assets/components/_sidebar.scss";

const Sidebar = ({ toggleSidebar, setActivePage }) => {
  const [activeItem, setActiveItem] = useState("home");
  const { t } = useTranslation();
  const navigate = useNavigate();

  const menuItems = [
    { key: "home", labelKey: "home", icon: <FaHome />, path: "/" },
    { key: "summary", labelKey: "summary", icon: <FaChartPie />, path: "/summary" },
    { key: "timeline", labelKey: "timeline", icon: <FaClock />, path: "/timeline" },
    { key: "report", labelKey: "report", icon: <FaFileAlt />, path: "/report" },
    { key: "info", labelKey: "info", icon: <FaInfoCircle />, path: "/info" },
  ];

  const handleMenuClick = (item) => {
    setActiveItem(item.key);
    setActivePage(t(item.labelKey));
    toggleSidebar(false);
    navigate(item.path);
  };

  return (
    <div className="bg-dark text-white py-3 vh-100 sidebar">
      <div className="text-center mb-3">
        <img src={aiLogo} alt="logo" width="50" className="rounded" />
      </div>

      <ul className="nav flex-column text-center">
        {menuItems.map((item) => (
          <li
            key={item.key}
            className={`nav-item py-3 ${activeItem === item.key ? "bg-secondary" : ""}`}
            style={{ cursor: "pointer" }}
            onClick={() => handleMenuClick(item)}
          >
            <div className="d-flex flex-column align-items-center">
              {item.icon}
              <span className="mt-1">{t(item.labelKey)}</span>
            </div>
          </li>
        ))}
      </ul>

      <div className="mt-auto text-center pt-4 mb-3">
        <a href="/login" className="text-white">
          <FaUser size={28} />
        </a>
      </div>
    </div>
  );
};

export default Sidebar;
