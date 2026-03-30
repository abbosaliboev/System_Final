import { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";

const INITIAL_PER_CAMERA = 5;  // Initial load: 5 records per camera
const PAGE_SIZE = 20;          // Pagination: 20 records per page
const PAGE_CHUNK = 10;         // UI chunk for infinite scroll display

export const useTimelineData = () => {
  const [allAlerts, setAllAlerts] = useState([]);
  const [fetched, setFetched] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [selectedCam, setSelectedCam] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const initialLoadDone = useRef(false);

  // Initial load - get 5 records per camera
  const fetchInitialAlerts = useCallback(async (cancelTokenSource) => {
    setLoading(true);
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/alerts/?per_camera=${INITIAL_PER_CAMERA}`, {
        cancelToken: cancelTokenSource?.token,
      });
      
      const data = res.data?.results || (Array.isArray(res.data) ? res.data : []);
      const normalized = data.map((item) => ({ ...item, reported: item.reported || false }));
      
      setAllAlerts(normalized);
      setTotalCount(res.data?.count || normalized.length);
      setFetched(true);
      initialLoadDone.current = true;

      // Set first camera as selected
      const cams = [...new Set(normalized.map((a) => a.camera_id))];
      if (cams.length && selectedCam == null) {
        setSelectedCam(cams.sort((a, b) => a - b)[0]);
      }
      
      // Check if there might be more data
      setHasMore(res.data?.per_camera_mode ? true : !!res.data?.next);
      
    } catch (e) {
      if (!axios.isCancel(e)) console.error("Failed to fetch alerts:", e);
      setFetched(true);
    } finally {
      setLoading(false);
    }
  }, [selectedCam]);

  // Load more alerts with pagination
  const loadMoreAlerts = useCallback(async () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    try {
      const nextPage = currentPage + 1;
      const res = await axios.get(
        `http://127.0.0.1:8000/api/alerts/?page=${nextPage}&page_size=${PAGE_SIZE}`
      );
      
      const data = res.data?.results || (Array.isArray(res.data) ? res.data : []);
      const normalized = data.map((item) => ({ ...item, reported: item.reported || false }));
      
      // Merge with existing alerts, avoiding duplicates
      setAllAlerts((prev) => {
        const existingIds = new Set(prev.map(a => a.id));
        const newAlerts = normalized.filter(a => !existingIds.has(a.id));
        return [...prev, ...newAlerts];
      });
      
      setCurrentPage(nextPage);
      setHasMore(!!res.data?.next);
      setTotalCount(res.data?.count || totalCount);
      
    } catch (e) {
      console.error("Failed to load more alerts:", e);
    } finally {
      setLoadingMore(false);
    }
  }, [currentPage, hasMore, loadingMore, totalCount]);

  // Initial fetch
  useEffect(() => {
    const source = axios.CancelToken.source();
    fetchInitialAlerts(source);
    return () => source.cancel("component unmount");
  }, [fetchInitialAlerts]);

  // App refresh listener
  useEffect(() => {
    const onAppRefresh = (e) => {
      const targetPath = e?.detail?.path;
      if (targetPath && targetPath !== window.location.pathname) return;
      
      // Reset and refetch
      setCurrentPage(1);
      setHasMore(true);
      initialLoadDone.current = false;
      
      const source = axios.CancelToken.source();
      fetchInitialAlerts(source);
    };
    window.addEventListener("app:refresh", onAppRefresh);
    return () => window.removeEventListener("app:refresh", onAppRefresh);
  }, [fetchInitialAlerts]);

  const updateAlert = useCallback((alertId, updates) => {
    setAllAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, ...updates } : a))
    );
  }, []);

  const deleteAlert = useCallback(async (alertId) => {
    await axios.delete(`http://127.0.0.1:8000/api/alerts/${alertId}/`);
    setAllAlerts((prev) => prev.filter((a) => a.id !== alertId));
    setTotalCount((prev) => Math.max(0, prev - 1));
  }, []);

  return {
    allAlerts,
    fetched,
    loading,
    loadingMore,
    selectedCam,
    setSelectedCam,
    updateAlert,
    deleteAlert,
    loadMoreAlerts,
    hasMore,
    totalCount,
    PAGE_CHUNK,
  };
};
