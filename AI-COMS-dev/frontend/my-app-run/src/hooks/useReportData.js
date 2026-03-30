import { useState, useEffect } from "react";

/**
 * Custom hook for managing report data and operations
 * @returns {Object} Report data, loading state, and CRUD operations
 */
export const useReportData = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sending, setSending] = useState(false);

  // Format API timestamp to "YYYY.MM.DD HH:mm"
  const formatDate = (isoStr) => {
    const d = new Date(isoStr);
    const pad = (n) => n.toString().padStart(2, "0");
    return `${d.getFullYear()}.${pad(d.getMonth() + 1)}.${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  // Fetch reports from API
  useEffect(() => {
    const fetchReports = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch("http://127.0.0.1:8000/api/reports/");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const apiData = await response.json();
        
        // Map API data to table format
        const mapped = apiData.map((item) => ({
          id: item.workerId || item.id,
          name: item.worker || "Unknown Worker",
          date: formatDate(item.timestamp),
          event: item.event || item.alert_type || "Unknown Event",
          status: "ALERT",
          reportId: item.id,
          department: item.department,
          supervisor: item.supervisor,
          cameraId: item.camera_id,
          frameImage: item.frame_image,
          email: item.worker_email,
        }));
        setData(mapped);
      } catch (err) {
        setError("Failed to load reports. Please try again.");
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    fetchReports();
  }, []);

  // Update report statuses after sending alerts
  const updateStatuses = (reportIds) => {
    const updated = data.map((item) =>
      reportIds.includes(item.reportId) ? { ...item, status: "ALERTED" } : item
    );
    setData(updated);
  };

  // Send alert emails
  const sendAlerts = async (selectedRows, onSuccess, onError) => {
    setSending(true);
    try {
      const selectedReports = data.filter((item) => selectedRows.includes(item.reportId));
      const reportsWithEmails = selectedReports.filter((item) => item.email);

      if (reportsWithEmails.length === 0) {
        onError("no_emails_found");
        setSending(false);
        return;
      }

      const payload = reportsWithEmails.map((item) => ({
        workerId: item.id,
        name: item.name,
        email: item.email,
        event: item.event,
        date: item.date,
        reportId: item.reportId,
      }));

      const response = await fetch("http://127.0.0.1:8000/api/reports/alert/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reports: payload }),
      });

      if (response.ok) {
        updateStatuses(selectedRows);
        onSuccess("alert_emails_sent");
      } else {
        onError("alert_failed");
      }
    } catch (err) {
      console.error(err);
      onError("alert_error");
    } finally {
      setSending(false);
    }
  };

  // Download PDF report
  const downloadPDF = async (startDate, endDate, onError) => {
    const start = new Date(startDate).toISOString();
    const end = new Date(new Date(endDate).setHours(23, 59, 59)).toISOString();

    try {
      const response = await fetch("http://127.0.0.1:8000/api/reports/download-pdf/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          start_date: start,
          end_date: end,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to download PDF");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", "report_summary.pdf");
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      onError("download_failed");
      console.error(err);
    }
  };

  return {
    data,
    loading,
    error,
    sending,
    sendAlerts,
    downloadPDF,
  };
};
