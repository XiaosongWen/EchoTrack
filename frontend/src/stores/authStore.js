import { create } from "zustand";
import { supabase } from "../utils/supabase";

export const useAuthStore = create((set, get) => ({
  user: null,
  session: null,
  loading: true,
  error: null,

  init: async () => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) throw error;

      set({
        session,
        user: session?.user ?? null,
        loading: false,
      });

      // Listen for auth state changes
      supabase.auth.onAuthStateChange((_event, currentSession) => {
        set({
          session: currentSession,
          user: currentSession?.user ?? null,
          loading: false,
        });
      });
    } catch (err) {
      set({ error: err.message, loading: false });
    }
  },

  signIn: async (email, password) => {
    set({ loading: true, error: null });
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) {
      set({ error: error.message, loading: false });
      return { success: false, error: error.message };
    }

    set({
      session: data.session,
      user: data.user,
      loading: false,
      error: null,
    });
    return { success: true };
  },

  signOut: async () => {
    set({ loading: true });
    await supabase.auth.signOut();
    set({ session: null, user: null, loading: false, error: null });
  },

  getToken: () => {
    return get().session?.access_token || null;
  },
}));
