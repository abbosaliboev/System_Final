// src/layout/MainLayout.jsx
import React, { useState } from "react";
import { Navigate, Routes, Route, useLocation } from "react-router-dom";
import Sidebar from "../components/Sidebar";
import Navbar from "../components/Navbar";

// Pages
import Home from "../pages/Home";
import SettingsPage from "../pages/SettingsPage";
import Camera from "../pages/Camera";
import Summary from "../pages/Summary";
import TimelinePage from "../pages/TimelinePage";
import ReportPage from "../pages/ReportPage";
import InfoPage from "../pages/InfoPage";

const MainLayout = ({ isAuthenticated, isDarkMode, setIsDarkMode }) => {
  const location = useLocation();
  const isLoginPage = location.pathname === "/login";

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activePage, setActivePage] = useState("Home");

  if (!isAuthenticated && !isLoginPage) {
    return <Navigate to="/login" />;
  }

  return (
    <div className={`layout-wrapper ${isDarkMode ? "dark-mode" : ""}`}>
      {/* Sidebar */}
      {!isLoginPage && (
        <>
          <div className={`sidebar-wrapper ${sidebarOpen ? "open" : ""}`}>
            <Sidebar toggleSidebar={setSidebarOpen} setActivePage={setActivePage} />
          </div>
          {sidebarOpen && <div className="overlay" onClick={() => setSidebarOpen(false)} />}
        </>
      )}

      {/* Main content */}
      <div className="main-area">
        {!isLoginPage && (
          <Navbar
            onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
            activePage={activePage}
          />
        )}
        <div className="content-scrollable">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/settings" element={<SettingsPage isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />} />
            <Route path="/camera/:id" element={<Camera />} />
            <Route path="/summary" element={<Summary />} />
            <Route path="/timeline" element={<TimelinePage />} />
            <Route path="/report" element={<ReportPage />} />
            <Route path="/info" element={<InfoPage />} />
          </Routes>
        </div>
      </div>
    </div>
  );
};

export default MainLayout;