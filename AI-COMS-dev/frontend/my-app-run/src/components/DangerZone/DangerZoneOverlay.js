// === DangerZoneOverlay.js ===
import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { Stage, Layer, Line } from "react-konva";

const DangerZoneOverlay = ({ camId }) => {
  const [polygons, setPolygons] = useState([]);
  const [dimensions, setDimensions] = useState({ width: 600, height: 340 });
  const containerRef = useRef();

  useEffect(() => {
    const resize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  useEffect(() => {
    axios
      .get(`http://127.0.0.1:8000/api/danger-zones/?camera_id=${camId}`)
      .then((res) => {
        const zones = res.data.map((zone) => zone.points);
        setPolygons(zones);
      });
  }, [camId]);

  return (
    <div ref={containerRef} style={{ position: "absolute", top: 0, left: 0, width: "100%", height: "100%" }}>
      <Stage width={dimensions.width} height={dimensions.height}>
        <Layer>
          {polygons.map((points, idx) => (
            <Line
              key={idx}
              points={points.flat().map((val, i) =>
                i % 2 === 0 ? val * dimensions.width : val * dimensions.height
              )}
              closed
              stroke="red"
              strokeWidth={2}
              fill="rgba(255, 0, 0, 0.4)"
            />
          ))}
        </Layer>
      </Stage>
    </div>
  );
};

export default DangerZoneOverlay;