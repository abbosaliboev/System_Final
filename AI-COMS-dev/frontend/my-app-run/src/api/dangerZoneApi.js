import axios from 'axios';

const BASE = 'http://127.0.0.1:8000/api/danger-zones/';

export const getZones = async (cameraId) =>
  axios.get(BASE + `?camera_id=${cameraId}`).then(res => res.data);

export const createZone = async (zone) =>
  axios.post(BASE, zone).then(res => res.data);

export const deleteZone = async (id) =>
  axios.delete(`${BASE}${id}/`).then(res => res.data);
