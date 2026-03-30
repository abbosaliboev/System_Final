// File: components/ViolationRanking.jsx
import React, { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import axios from "axios";

const ViolationRanking = () => {
  const { t } = useTranslation();
  const [ranking, setRanking] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchViolationStats = async () => {
      try {
        const response = await axios.get("http://127.0.0.1:8000/api/reports/worker-violations/");
        setRanking(response.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchViolationStats();
  }, []);

  if (loading) {
    return (
      <div className="card violation-ranking-card">
        <div className="card-body text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card violation-ranking-card">
        <div className="card-body text-danger">
          {t("error_loading_data")}: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="card violation-ranking-card">
      <div className="card-body">
        <h5 className="card-title">{t("rank_title")}</h5>
        <div className="detect-list">
          {ranking.length > 0 ? (
            ranking.map((worker, index) => (
              <div key={worker.workerId} className="detect-row d-flex justify-content-between mb-2">
                <span>{t("rank_worker_id", { id: worker.workerId })}</span>
                <span className="fw-bold">{worker.violation_count}</span>
              </div>
            ))
          ) : (
            <div className="text-muted">{t("no_violations_found")}</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ViolationRanking;
