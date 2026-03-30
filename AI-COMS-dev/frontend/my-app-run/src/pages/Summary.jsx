import React, { useMemo, useCallback } from "react";
import SafetyScoreCard from "../components/Summary/SafetyScoreCard";
import TrendAnalysisChart from "../components/Summary/TrendAnalysisChart";
import IncidentDistributionChart from "../components/Summary/IncidentDistributionChart";
import HeatmapOverview from "../components/Summary/HeatmapOverview";
import ViolationRanking from "../components/Summary/ViolationRanking";
import SummaryHeader from "../components/Summary/SummaryHeader";
import { useDateRange } from "../hooks/useDateRange";
import { useSummaryData } from "../hooks/useSummaryData";
import { useTranslation } from "react-i18next";
import "../assets/components/_summary.scss";

const Summary = () => {
  const { t } = useTranslation();

  // Date range management
  const {
    rangeType,
    startDate,
    endDate,
    handleRangeChange,
    handleCustomDateChange,
  } = useDateRange();

  // Data fetching
  const {
    loading,
    safetyScore,
    safetyStats,
    incidentTrendData,
    incidentDistributionData,
    heatmapData,
    violationRanking,
  } = useSummaryData(startDate, endDate, t);

  // Heatmap color function
  const getHeatmapColor = useCallback((v) => {
    if (v > 40) return "#003087";
    if (v > 30) return "#005eb8";
    if (v > 20) return "#4a90e2";
    return "#d3e4fa";
  }, []);

  // Memoized chart data
  const memoizedSafetyScore = useMemo(() => safetyScore, [safetyScore]);
  const memoizedSafetyStats = useMemo(() => safetyStats, [safetyStats]);
  const memoizedTrendData = useMemo(
    () => incidentTrendData,
    [incidentTrendData]
  );
  const memoizedDistData = useMemo(
    () => incidentDistributionData,
    [incidentDistributionData]
  );
  const memoizedHeatmapData = useMemo(() => heatmapData, [heatmapData]);
  const memoizedViolationData = useMemo(
    () => violationRanking,
    [violationRanking]
  );

  return (
    <div className="summary-page">
      <SummaryHeader
        rangeType={rangeType}
        startDate={startDate}
        loading={loading}
        onRangeChange={handleRangeChange}
        onCustomDateChange={handleCustomDateChange}
      />

      <div className="row g-4">
        <div className="col-12 col-lg-4">
          <SafetyScoreCard
            safetyScore={memoizedSafetyScore}
            safetyStats={memoizedSafetyStats}
            loading={loading}
          />
        </div>

        <div className="col-12 col-lg-8">
          <div className="row g-4">
            <div className="col-12 col-md-8">
              <TrendAnalysisChart
                incidentTrendData={memoizedTrendData}
                loading={loading}
              />
            </div>

            <div className="col-12 col-md-4">
              <IncidentDistributionChart
                incidentDistributionData={memoizedDistData}
                loading={loading}
              />
            </div>

            <div className="col-12 col-md-8">
              <HeatmapOverview
                heatmapData={memoizedHeatmapData}
                getHeatmapColor={getHeatmapColor}
                loading={loading}
              />
            </div>

            <div className="col-12 col-md-4">
              <ViolationRanking violationRanking={memoizedViolationData} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Summary;
