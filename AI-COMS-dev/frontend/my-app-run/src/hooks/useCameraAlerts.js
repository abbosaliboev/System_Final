import { useState, useEffect, useRef, useMemo } from "react";
import axios from "axios";

const PAGE_CHUNK = 20;

/**
 * Custom hook for managing camera alerts data
 */
export const useCameraAlerts = (camera) => {
  const [alerts, setAlerts] = useState([]);
  const [filter, setFilter] = useState("most_recent");
  const [loading, setLoading] = useState(true);
  const [visibleCount, setVisibleCount] = useState(PAGE_CHUNK);
  const sentinelRef = useRef(null);

  // Fetch alerts from API
  useEffect(() => {
    let intervalId;
    const sourceRef = { current: null };

    const fetchAlerts = (cancelSource) => {
      if (!camera) return;
      setLoading(true);
      const source = cancelSource || axios.CancelToken.source();
      sourceRef.current = source;
      
      // Fetch only last 7 days alerts for performance
      axios
        .get(`http://127.0.0.1:8000/api/alerts/?camera_id=${camera.id}&days=7`, {
          cancelToken: source.token,
        })
        .then((res) => {
          // Handle paginated response
          const data = Array.isArray(res.data) ? res.data : (res.data?.results || []);
          setAlerts(data);
          setVisibleCount((prev) =>
            Math.min(Math.max(prev, PAGE_CHUNK), data.length || PAGE_CHUNK)
          );
        })
        .catch((err) => {
          if (!axios.isCancel(err)) {
            console.error("Failed to fetch alerts:", err);
            setAlerts([]);
            setVisibleCount(PAGE_CHUNK);
          }
        })
        .finally(() => setLoading(false));
    };

    // Initial load + periodic refresh
    fetchAlerts();
    intervalId = setInterval(() => fetchAlerts(), 10000);

    // Listen for global refresh events
    const onAppRefresh = (e) => {
      const targetPath = e?.detail?.path;
      if (targetPath && targetPath !== window.location.pathname) return;
      const src = axios.CancelToken.source();
      fetchAlerts(src);
    };
    window.addEventListener("app:refresh", onAppRefresh);

    return () => {
      clearInterval(intervalId);
      window.removeEventListener("app:refresh", onAppRefresh);
      if (sourceRef.current) sourceRef.current.cancel("component unmount");
    };
  }, [camera]);

  // Reset visible count on filter change
  useEffect(() => {
    setVisibleCount(PAGE_CHUNK);
  }, [filter]);

  // Sort alerts based on filter
  const sortedAlerts = useMemo(() => {
    return [...alerts]
      .filter((a) => a.timestamp && a.alert_type)
      .sort((a, b) => {
        const dateA = new Date(a.timestamp);
        const dateB = new Date(b.timestamp);
        return filter === "most_recent" ? dateB - dateA : dateA - dateB;
      });
  }, [alerts, filter]);

  // Visible alerts slice
  const visibleAlerts = useMemo(
    () => sortedAlerts.slice(0, Math.min(visibleCount, sortedAlerts.length)),
    [sortedAlerts, visibleCount]
  );

  // Count alert types
  const alertCounts = useMemo(() => {
    return alerts.reduce(
      (acc, alert) => {
        const type = alert.alert_type?.toLowerCase() || "unknown";
        switch (type) {
          case "no_helmet":
            acc.noHelmet += 1;
            break;
          case "danger_zone":
            acc.dangerZone += 1;
            break;
          case "fire":
            acc.fire += 1;
            break;
          case "fall":
            acc.fall += 1;
            break;
          default:
            acc.unknown += 1;
        }
        return acc;
      },
      { noHelmet: 0, dangerZone: 0, fire: 0, fall: 0, unknown: 0 }
    );
  }, [alerts]);

  // Infinite scroll observer
  useEffect(() => {
    if (!sentinelRef.current) return;

    const obs = new IntersectionObserver(
      (entries) => {
        const first = entries[0];
        if (first.isIntersecting) {
          setVisibleCount((prev) => {
            const total = sortedAlerts.length;
            if (prev >= total) return prev;
            return Math.min(prev + PAGE_CHUNK, total);
          });
        }
      },
      { root: null, rootMargin: "300px", threshold: 0.01 }
    );

    obs.observe(sentinelRef.current);
    return () => obs.disconnect();
  }, [sortedAlerts.length]);

  return {
    alerts,
    filter,
    setFilter,
    loading,
    visibleAlerts,
    alertCounts,
    sentinelRef,
    hasMore: visibleCount < sortedAlerts.length,
  };
};
