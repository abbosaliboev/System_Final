import { useState, useEffect, useCallback } from "react";

/**
 * Date utility functions for Summary page
 */
const fmt = (d) => d.toISOString().slice(0, 10);
const parse = (s) => new Date(s);
const addDays = (d, n) => new Date(d.getTime() + n * 86400000);

const startOfWeekMon = (date = new Date()) => {
  const d = new Date(date);
  const day = d.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
};

export const thisWeekRange = () => {
  const start = startOfWeekMon();
  const end = addDays(start, 6);
  return { start: fmt(start), end: fmt(end) };
};

export const lastWeekRange = () => {
  const end = addDays(startOfWeekMon(), -1);
  const start = addDays(end, -6);
  return { start: fmt(start), end: fmt(end) };
};

/**
 * Custom hook for managing date range state
 */
export const useDateRange = () => {
  const [rangeType, setRangeType] = useState("this");
  const [startDate, setStartDate] = useState(thisWeekRange().start);
  const [endDate, setEndDate] = useState(thisWeekRange().end);

  // Update dates when range type changes
  useEffect(() => {
    if (rangeType === "this") {
      const r = thisWeekRange();
      setStartDate(r.start);
      setEndDate(r.end);
    } else if (rangeType === "last") {
      const r = lastWeekRange();
      setStartDate(r.start);
      setEndDate(r.end);
    }
  }, [rangeType]);

  const handleRangeChange = useCallback((type) => {
    setRangeType(type);
  }, []);

  const handleCustomDateChange = useCallback((e) => {
    const s = e.target.value;
    setStartDate(s);
    setEndDate(fmt(addDays(parse(s), 6)));
  }, []);

  return {
    rangeType,
    startDate,
    endDate,
    handleRangeChange,
    handleCustomDateChange,
  };
};
