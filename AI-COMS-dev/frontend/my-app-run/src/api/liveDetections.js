import axios from "axios";

const API_URL = "http://127.0.0.1:8000/api/live/";

export const fetchLiveDetections = async () => {
  try {
    const res = await axios.get(API_URL);
    return res.data;
  } catch (err) {
    console.error("Failed to fetch live detections:", err);
    return {};
  }
};
