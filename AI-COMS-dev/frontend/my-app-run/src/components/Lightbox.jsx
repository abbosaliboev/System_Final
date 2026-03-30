import React, { useEffect, useState } from "react";
import "../assets/components/_lightbox.scss";

const Lightbox = ({ src, alt, onClose }) => {
  const [[x, y], setXY] = useState([0, 0]);
  const [showMagnifier, setShowMagnifier] = useState(false);
  const zoom = 2.5;
  const width = 800;
  const height = 500;

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="lightbox-overlay" onClick={onClose}>
      <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
        <button className="lightbox-close" onClick={onClose}>
          &times;
        </button>
        <div
          className="magnifier-container"
          style={{ position: "relative", width, height }}
          onMouseEnter={() => setShowMagnifier(true)}
          onMouseLeave={() => setShowMagnifier(false)}
          onMouseMove={(e) => {
            const { top, left } = e.currentTarget.getBoundingClientRect();
            const x = e.pageX - left - window.scrollX;
            const y = e.pageY - top - window.scrollY;
            setXY([x, y]);
          }}
        >
          <img
            src={src}
            alt={alt}
            style={{ width, height, display: "block" }}
          />
          {showMagnifier && (
            <div
              className="magnifier-lens"
              style={{
                left: `${x - 75}px`,
                top: `${y - 75}px`,
                backgroundImage: `url('${src}')`,
                backgroundPosition: `-${x * zoom - 75}px -${y * zoom - 75}px`,
                backgroundSize: `${width * zoom}px ${height * zoom}px`,
              }}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Lightbox;