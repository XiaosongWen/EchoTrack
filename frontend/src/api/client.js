import axios from "axios";
import { supabase } from "../utils/supabase";

const client = axios.create({
  baseURL: "/api/v1",
});

client.interceptors.request.use(async (config) => {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    if (session?.access_token) {
      config.headers.Authorization = `Bearer ${session.access_token}`;
    }
  } catch (error) {
    console.error("Failed to attach Supabase auth token", error);
  }
  return config;
});

// Handle expired tokens and 401 Unauthorized seamlessly
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const { data: { session }, error: refreshError } = await supabase.auth.refreshSession();
        if (session?.access_token && !refreshError) {
          originalRequest.headers.Authorization = `Bearer ${session.access_token}`;
          return client(originalRequest);
        }
      } catch (refreshErr) {
        console.error("Session refresh failed:", refreshErr);
      }
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
