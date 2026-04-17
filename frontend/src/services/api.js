import axios from "axios";

const apiProtocol = window.location.protocol;
const apiHost = window.location.hostname;

const api = axios.create({
  baseURL: `${apiProtocol}//${apiHost}:8000`
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

export default api;
