import { useState, useEffect, useCallback } from "react";

/**
 * Custom hook for fetching summary dashboard data
 */
export const useSummaryData = (startDate, endDate, t) => {
  const [loading, setLoading] = useState(true);
  const [safetyScore, setSafetyScore] = useState(1);
  const [safetyStats, setSafetyStats] = useState([]);
  const [incidentTrendData, setIncidentTrendData] = useState({});
  const [incidentDistributionData, setIncidentDistributionData] = useState({});
  const [heatmapData, setHeatmapData] = useState([]);
  const [violationRanking, setViolationRanking] = useState([]);

  const fetchAll = useCallback(
    async (signal) => {
      setLoading(true);
      try {
        const qs = `start=${startDate}&end=${endDate}`;
        const baseUrl = "http://127.0.0.1:8000/api";

        const fetchWithTimeout = (url, timeout = 5000) => {
          return Promise.race([
            fetch(url, { signal }),
            new Promise((_, reject) =>
              setTimeout(() => reject(new Error("Timeout")), timeout)
            ),
          ]);
        };

        const [safetyRes, trendRes, distRes, heatRes, violRes] =
          await Promise.allSettled([
            fetchWithTimeout(`${baseUrl}/alerts/safety-score?${qs}`),
            fetchWithTimeout(`${baseUrl}/alerts/trend?${qs}`),
            fetchWithTimeout(`${baseUrl}/alerts/distribution?${qs}`),
            fetchWithTimeout(`${baseUrl}/alerts/heatmap?${qs}`),
            fetchWithTimeout(`${baseUrl}/reports/worker-violations?${qs}`),
          ]);

        // Process safety score
        if (safetyRes.status === "fulfilled" && safetyRes.value.ok) {
          const data = await safetyRes.value.json();
          setSafetyScore((data.safety_score || 0) / 100);
          setSafetyStats(
            (data.breakdown || []).map((x) => ({
              label: x.label,
              value: 100 - x.percent,
              color:
                {
                  "Danger Zone": "#28a745",
                  "No Helmet": "#dc3545",
                  Fire: "#fd7e14",
                  Fall: "#6f42c1",
                }[x.label] || "#6c757d",
            }))
          );
        }

        // Process trend data
        if (trendRes.status === "fulfilled" && trendRes.value.ok) {
          const td = await trendRes.value.json();
          setIncidentTrendData({
            labels: td.labels || [],
            datasets: [
              {
                label: t("danger_zone") || "Danger Zone",
                data: td.danger_zone || [],
                borderColor: "#28a745",
                backgroundColor: "#28a745",
                tension: 0.3,
                pointRadius: 3,
              },
              {
                label: t("no_helmet") || "No Helmet",
                data: td.no_helmet || [],
                borderColor: "#dc3545",
                backgroundColor: "#dc3545",
                tension: 0.3,
                pointRadius: 3,
              },
              {
                label: t("fire") || "Fire",
                data: td.fire || [],
                borderColor: "#fd7e14",
                backgroundColor: "#fd7e14",
                tension: 0.3,
                pointRadius: 3,
              },
              {
                label: t("fall") || "Fall",
                data: td.fall || [],
                borderColor: "#6f42c1",
                backgroundColor: "#6f42c1",
                tension: 0.3,
                pointRadius: 3,
              },
            ],
          });
        }

        // Process distribution data
        if (distRes.status === "fulfilled" && distRes.value.ok) {
          const dd = await distRes.value.json();
          const cfg = {
            danger_zone: {
              label: t("danger_zone") || "Danger Zone",
              color: "#28a745",
            },
            no_helmet: {
              label: t("no_helmet") || "No Helmet",
              color: "#dc3545",
            },
            fire: { label: t("fire") || "Fire", color: "#fd7e14" },
            fall: { label: t("fall") || "Fall", color: "#6f42c1" },
          };
          setIncidentDistributionData({
            labels: dd.map((x) => cfg[x.alert_type]?.label || x.alert_type),
            datasets: [
              {
                data: dd.map((x) => x.count),
                backgroundColor: dd.map(
                  (x) => cfg[x.alert_type]?.color || "#6c757d"
                ),
                borderWidth: 1,
              },
            ],
          });
        }

        // Process heatmap data
        if (heatRes.status === "fulfilled" && heatRes.value.ok) {
          const hd = await heatRes.value.json();
          if (hd?.weekdays && hd?.matrix) {
            const short = {
              Monday: "Mon",
              Tuesday: "Tue",
              Wednesday: "Wed",
              Thursday: "Thu",
              Friday: "Fri",
              Saturday: "Sat",
              Sunday: "Sun",
            };
            const formatted = hd.weekdays.map((day, i) => [
              short[day] || day,
              ...(hd.matrix[i] || Array(24).fill(0)),
            ]);
            setHeatmapData(formatted);
          }
        }

        // Process violation ranking
        if (violRes.status === "fulfilled" && violRes.value.ok) {
          const vdata = await violRes.value.json();
          setViolationRanking(vdata || []);
        }
      } catch (e) {
        if (e.name !== "AbortError") {
          console.error("💥 Fetch error:", e);
        }
      } finally {
        setLoading(false);
      }
    },
    [startDate, endDate, t]
  );

  // Initial fetch on mount
  useEffect(() => {
    const controller = new AbortController();
    fetchAll(controller.signal);
    return () => controller.abort();
  }, [fetchAll]);

  // Listen for app refresh events
  useEffect(() => {
    const onAppRefresh = (e) => {
      const targetPath = e?.detail?.path;
      if (targetPath && targetPath !== window.location.pathname) return;

      const controller = new AbortController();
      fetchAll(controller.signal).catch((err) => {
        if (err.name !== "AbortError") console.error(err);
      });
    };

    window.addEventListener("app:refresh", onAppRefresh);
    return () => window.removeEventListener("app:refresh", onAppRefresh);
  }, [fetchAll]);

  return {
    loading,
    safetyScore,
    safetyStats,
    incidentTrendData,
    incidentDistributionData,
    heatmapData,
    violationRanking,
  };
};
