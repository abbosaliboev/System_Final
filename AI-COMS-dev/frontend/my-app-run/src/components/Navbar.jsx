import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FaRedo, FaGlobe, FaCog, FaBars } from "react-icons/fa";
import "../assets/components/_navbar.scss";
import { useTranslation } from "react-i18next";

const Navbar = ({ onToggleSidebar, onRefreshMain, activePage }) => {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  const [isLangDropdownOpen, setIsLangDropdownOpen] = useState(false);

  const handleLanguageChange = (lang) => {
    i18n.changeLanguage(lang);
    setIsLangDropdownOpen(false); // Close dropdown after selection
  };

  const toggleDropdown = () => {
    setIsLangDropdownOpen(!isLangDropdownOpen);
  };

  const handleSettingsClick = () => {
    navigate("/settings");
  };

  const handleReload = () => {
    // Dispatch a page-scoped refresh event (includes current path) so only the
    // active page performs a light-weight refresh. This avoids refreshing other
    // mounted pages/components.
    try {
      const payload = { path: window.location.pathname };
      window.dispatchEvent(new CustomEvent("app:refresh", { detail: payload }));
    } catch (e) {
      // fallback: call provided handler for compatibility
      if (onRefreshMain) onRefreshMain();
    }
  };

  return (
    <nav className="navbar px-4">
      {/* Menu button - visible only on small screens */}
      <button
        className="btn d-xxl-none me-3 menu-toggle"
        onClick={onToggleSidebar}
      >
        <FaBars />
      </button>

      <span className="navbar-title">{t(activePage)}</span>
      <h1 className="navbar-logo mx-auto">{t('title')}</h1>

      <div className="navbar-icons d-flex gap-3">
  <FaRedo className="icon" onClick={handleReload} />
        <div className="language-dropdown">
          <FaGlobe className="icon" onClick={toggleDropdown} />
          {isLangDropdownOpen && (
            <div className="dropdown-menu">
              <button
                className="dropdown-item"
                onClick={() => handleLanguageChange("en")}
              >
                English
              </button>
              <button
                className="dropdown-item"
                onClick={() => handleLanguageChange("kr")}
              >
                Korean
              </button>
            </div>
          )}
        </div>
        <FaCog className="icon" onClick={handleSettingsClick} />
      </div>
    </nav>
  );
};

export default Navbar;