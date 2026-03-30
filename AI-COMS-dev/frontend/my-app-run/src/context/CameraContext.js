import React, { createContext, useState } from "react";

export const CameraContext = createContext();

export const CameraProvider = ({ children }) => {
  const [cameraData, setCameraData] = useState([
    { id: 1, cam: "CAM 1", camId: "cam1" },
    { id: 2, cam: "CAM 2", camId: "cam2" },
    { id: 3, cam: "CAM 3", camId: "cam3" },
    { id: 4, cam: "CAM 4", camId: "cam4" },
    { id: 5, cam: "CAM 5", camId: "cam5" },
    { id: 6, cam: "CAM 6", camId: "cam6" },

  ]);

  const updateCameraName = (id, newName) => {
    setCameraData((prevData) =>
      prevData.map((camera) =>
        camera.id === id ? { ...camera, cam: newName } : camera
      )
    );
  };

  return (
    <CameraContext.Provider value={{ cameraData, updateCameraName }}>
      {children}
    </CameraContext.Provider>
  );
};