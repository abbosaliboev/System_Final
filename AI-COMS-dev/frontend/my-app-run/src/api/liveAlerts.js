import axios from "axios";

export const getAlerts = async (cameraId) =>
  axios.get(`http://127.0.0.1:8000/api/alerts/?camera_id=${cameraId}`).then((res) => res.data);
