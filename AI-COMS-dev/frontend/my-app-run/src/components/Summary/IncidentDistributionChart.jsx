// IncidentDistributionChart.jsx
import React, { useMemo } from "react";
import { Pie } from "react-chartjs-2";
import { useTranslation } from "react-i18next";

const IncidentDistributionChart = ({ incidentDistributionData, loading = false }) => {
  const { t } = useTranslation();

  // Check dark mode
  const isDarkMode = document.body.classList.contains("dark-mode");
  const textColor = isDarkMode ? "#f1f1f1" : "#333";

  console.log("📊 IncidentDistributionChart received data:", incidentDistributionData);

  // Default empty data structure if no data provided
  const chartData = incidentDistributionData || { 
    labels: [], 
    datasets: [{ data: [] }] 
  };

  // Calculate total incidents from the data
  const totalIncidents = useMemo(() => {
    if (!chartData?.datasets?.[0]?.data) return 0;
    return chartData.datasets[0].data.reduce((sum, val) => sum + val, 0);
  }, [chartData]);

  // Check if there's any data to display
  const hasData = useMemo(() => {
    return chartData?.datasets?.[0]?.data?.some(val => val > 0) || false;
  }, [chartData]);

  // Chart options with dynamic dark mode colors
  const chartOptions = useMemo(() => ({
    maintainAspectRatio: false,
    responsive: true,
    plugins: {
      legend: {
        position: "bottom",
        labels: { 
          font: { size: 12 }, 
          color: textColor,
          padding: 10
        },
      },
      tooltip: {
        callbacks: {
          label: function (context) {
            const value = context.parsed;
            const dataArr = context.dataset.data;
            const total = dataArr.reduce((a, b) => a + b, 0);
            const percent = total > 0 ? ((value / total) * 100).toFixed(1) : "0.0";
            return `${context.label}: ${value} (${percent}%)`;
          },
        },
      },
    },
  }), [textColor]);

  console.log("Total incidents:", totalIncidents, "Has data:", hasData);

  return (
    <div className="card distribution-card">
      <div className="card-body">
        <h5 className="card-title">{t("incident_distribution_title") || "Incident Distribution"}</h5>

        {loading ? (
          <div style={{ padding: "40px", textAlign: "center" }}>
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
          </div>
        ) : hasData ? (
          <>
            {/* Pie Chart */}
            <div className="chart-container" style={{ position: "relative", height: "250px" }}>
              <Pie
                data={chartData}
                options={chartOptions}
              />
            </div>

            {/* Total count below the chart */}
            <div className="text-center mt-3 mb-2">
              <span style={{ fontWeight: "bold", fontSize: "16px", color: textColor }}>
                {t("total_incidents") || "Total Incidents"}: {totalIncidents}
              </span>
            </div>
          </>
        ) : (
          <div style={{ padding: "40px", textAlign: "center" }}>
            <p className="text-muted">{t("no_data") || "No data available"}</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default IncidentDistributionChart;