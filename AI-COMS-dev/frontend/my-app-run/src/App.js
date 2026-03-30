import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { CameraProvider } from "./context/CameraContext";
import "./assets/styles.scss";

import MainLayout from "./layout/MainLayout";
import Login from "./pages/Login";
import Home from "./pages/Home";
import SettingsPage from "./pages/SettingsPage";
import Camera from "./pages/Camera";
import Summary from "./pages/Summary";
import TimelinePage from "./pages/TimelinePage";
import ReportPage from "./pages/ReportPage";
import InfoPage from "./pages/InfoPage";
// App.js yoki Summary.jsx (1 marta bajarilishi kifoya)
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  BarElement,
  ArcElement,          
  CategoryScale,        
  LinearScale,          
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  LineElement,
  PointElement,
  BarElement,
  ArcElement,           
  CategoryScale,      
  LinearScale,
  Tooltip,
  Legend
);

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(true); // demo: true
  
  // Load dark mode from localStorage (persists across reloads)
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const saved = localStorage.getItem("darkMode");
    return saved === "true";
  });

  // Dark mode effect - save to localStorage and apply to body
  useEffect(() => {
    document.body.classList.toggle("dark-mode", isDarkMode);
    localStorage.setItem("darkMode", isDarkMode);
  }, [isDarkMode]);

  return (
    <Router>
      <CameraProvider>
        <Routes>
          <Route path="/login" element={<Login setIsAuthenticated={setIsAuthenticated} />} />
          <Route
            path="/"
            element={<MainLayout isAuthenticated={isAuthenticated} isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />}
          >
            <Route index element={<Home />} />
            <Route path="settings" element={<SettingsPage isDarkMode={isDarkMode} setIsDarkMode={setIsDarkMode} />} />
            <Route path="camera/:id" element={<Camera />} />
            <Route path="summary" element={<Summary />} />
            <Route path="timeline" element={<TimelinePage />} />
            <Route path="report" element={<ReportPage />} />
            <Route path="info" element={<InfoPage />} />
          </Route>
        </Routes>
      </CameraProvider>
    </Router>
  );
}

export default App;