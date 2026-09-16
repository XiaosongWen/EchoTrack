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

export default client;
