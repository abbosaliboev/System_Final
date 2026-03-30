// === DangerZoneCanvas.js ===
import React, { useEffect, useRef, useState } from "react";
import { Stage, Layer, Line } from "react-konva";
import { useTranslation } from "react-i18next";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000/api/danger-zones";

const DangerZoneCanvas = ({ camId, containerId }) => {
  const { t } = useTranslation();
  const [polygons, setPolygons] = useState([]);
  const [currentPoints, setCurrentPoints] = useState([]);
  const [dimensions, setDimensions] = useState({ width: 700, height: 480 });
  const [drawingMode, setDrawingMode] = useState(false);
  const [showControls, setShowControls] = useState(false);
  const stageRef = useRef();

  useEffect(() => {
    const updateSize = () => {
      const container = document.getElementById(containerId);
      if (container) {
        const { width, height } = container.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };
    updateSize();
    window.addEventListener("resize", updateSize);
    return () => window.removeEventListener("resize", updateSize);
  }, [containerId]);

  useEffect(() => {
    axios.get(`${API_BASE}/?camera_id=${camId}`).then((res) => {
      const formatted = res.data.map((zone) => zone.points);
      setPolygons(formatted);
    });
  }, [camId]);

  const handleClick = (e) => {
    if (!drawingMode) return;
    const stage = stageRef.current.getStage();
    const pointer = stage.getPointerPosition();
    setCurrentPoints((prev) => [...prev, pointer.x, pointer.y]);
  };

  const savePolygon = async () => {
    if (currentPoints.length < 6) return alert(t("At least 3 points required"));

    const reshapedPoints = [];
    for (let i = 0; i < currentPoints.length; i += 2) {
      reshapedPoints.push([
        currentPoints[i] / dimensions.width,
        currentPoints[i + 1] / dimensions.height,
      ]);
    }

    await axios.post(`${API_BASE}/`, {
      camera_id: camId,
      points: reshapedPoints,
      zone_name: "Zone"
    });

    setPolygons([...polygons, reshapedPoints]);
    setCurrentPoints([]);
    setDrawingMode(false);
  };

  const deleteAll = async () => {
    await axios.delete(`${API_BASE}/delete_all/${camId}/`);
    setPolygons([]);
    setCurrentPoints([]);
    setDrawingMode(false);
  };

  return (
    <div style={{ position: "relative", width: dimensions.width, height: dimensions.height + 60 }}>
      <Stage
        width={dimensions.width}
        height={dimensions.height}
        ref={stageRef}
        onClick={handleClick}
        style={{ position: "absolute", top: 0, left: 0, zIndex: 10 }}
      >
        <Layer>
          {polygons.map((points, i) => (
            <Line
              key={i}
              points={points.flat().map((val, idx) =>
                idx % 2 === 0 ? val * dimensions.width : val * dimensions.height
              )}
              closed
              stroke="red"
              fill="rgba(255, 0, 0, 0.4)"
              strokeWidth={2}
            />
          ))}
          {currentPoints.length >= 2 && (
            <Line
              points={currentPoints}
              stroke="red"
              strokeWidth={2}
              fill="rgba(255, 0, 0, 0.4)"
              closed
              dash={[10, 5]}
            />
          )}
        </Layer>
      </Stage>

      {/* Buttons below */}
      {!showControls && (
        <div style={{ width: "100%", display: "flex", justifyContent: "center", position: "absolute", top: dimensions.height, left: 0 }}>
          <button className="btn btn-dark w-100 mt-3" onClick={() => setShowControls(true)}>
            {t("Draw Danger Zone")}
          </button>
        </div>
      )}

      {showControls && (
        <div className="mt-3 d-flex gap-2 justify-content-end flex-wrap" style={{ position: "absolute", top: dimensions.height, left: 0, width: "100%" }}>
          <button
            className={`btn ${drawingMode ? "btn-outline-dark" : "btn-primary"}`}
            onClick={() => {
              if (drawingMode) setCurrentPoints([]);
              setDrawingMode(!drawingMode);
            }}
          >
            {drawingMode ? t("Cancel Drawing") : t("Add Polygon")}
          </button>

          {drawingMode && (
            <button className="btn btn-success" onClick={savePolygon} disabled={!currentPoints.length}>
              {t("Save")}
            </button>
          )}

          {!drawingMode && (
            <>
              <button className="btn btn-danger" onClick={deleteAll}>{t("Delete All")}</button>
              <button className="btn btn-secondary" onClick={() => { setShowControls(false); setDrawingMode(false); setCurrentPoints([]); }}>
                {t("Close Controls")}
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default DangerZoneCanvas;