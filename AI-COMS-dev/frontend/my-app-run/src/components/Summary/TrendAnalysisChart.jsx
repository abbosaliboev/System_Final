// ==== TrendAnalysisChart.jsx (Final i18n + Dynamic Version) ====
import React, { useMemo } from "react";
import { Line } from "react-chartjs-2";
import { useTranslation } from "react-i18next";
import {
  Chart as ChartJS,
  LineElement,
  CategoryScale,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(LineElement, CategoryScale, LinearScale, PointElement, Tooltip, Legend);

const TrendAnalysisChart = ({ incidentTrendData, loading = false }) => {
  const { t } = useTranslation();

  // Check dark mode
  const isDarkMode = document.body.classList.contains("dark-mode");
  const textColor = isDarkMode ? "#f1f1f1" : "#333";
  const axisColor = isDarkMode ? "#aaaaaa" : "#555";
  const gridColor = isDarkMode ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)";

  const hasData =
    incidentTrendData &&
    incidentTrendData.labels &&
    incidentTrendData.labels.length > 0;

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    tension: 0.35,
    interaction: { mode: "index", intersect: false },
    plugins: {
      legend: {
        position: "bottom",
        labels: {
          font: { size: 13 },
          color: textColor,
          usePointStyle: true,
          pointStyle: "circle",
        },
      },
      tooltip: {
        backgroundColor: "rgba(0,0,0,0.75)",
        padding: 10,
        bodyFont: { size: 13 },
        titleFont: { weight: "bold" },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: t("trend_x_axis"),
          color: textColor,
          font: { size: 13 },
        },
        ticks: { color: axisColor },
        grid: { display: false },
      },
      y: {
        title: {
          display: true,
          text: t("trend_y_axis"),
          color: textColor,
          font: { size: 13 },
        },
        beginAtZero: true,
        ticks: { precision: 0, color: axisColor },
        grid: { color: gridColor },
      },
    },
  }), [t, textColor, axisColor, gridColor]);

  return (
    <div className="card trend-analysis-card">
      <div className="card-body">
        {/* 🔹 Title */}
        <h5 className="card-title">{t("trend_title")}</h5>
        {/* 🔹 Chart */}
        {loading ? (
          <div className="text-center py-4">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : hasData ? (
          <div className="chart-container" style={{ height: "320px" }}>
            <Line
              data={incidentTrendData}
              options={chartOptions}
            />
          </div>
        ) : (
          <p className="text-muted text-center mt-3">
            {t("no_data") || "No data available"}
          </p>
        )}

      </div>
    </div>
  );
};

export default TrendAnalysisChart;
