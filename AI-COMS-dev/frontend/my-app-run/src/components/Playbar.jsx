// src/components/Playbar.jsx
import React from "react";
import "../assets/components/_videoPlayer.scss";
import { useTranslation } from "react-i18next";

const Playbar = ({ currentTime, duration, onSeek, onTogglePlay, isPlaying }) => {
  const formatTime = (time) => {
      const { t } = useTranslation();
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60).toString().padStart(2, '0');
    return `${minutes}:${seconds}`;
  };

  return (
    <div className="playbar-wrapper">
      <div className="playbar mt-3 d-flex align-items-center justify-content-between">
        <span>{formatTime(currentTime)}</span>
        <input
          type="range"
          className="form-range mx-2 flex-grow-1"
          min={0}
          max={duration}
          value={currentTime}
          onChange={(e) => onSeek(Number(e.target.value))}
        />
        <span>-{formatTime(duration - currentTime)}</span>
      </div>
      <div className="play-controls mt-2 d-flex justify-content-center gap-3">
        <button className="btn btn-light">⏮️</button>
        <button className="btn btn-dark" onClick={onTogglePlay}>
          {isPlaying ? "⏸️" : "▶️"}
        </button>
        <button className="btn btn-light">⏭️</button>
      </div>
    </div>
  );
};

export default Playbar;
