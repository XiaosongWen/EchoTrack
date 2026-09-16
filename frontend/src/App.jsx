import React, { useEffect } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Login from "./views/Login";
import DailyLog from "./views/DailyLog";
import Commitments from "./views/Commitments";
import Photos from "./views/Photos";
import Videos from "./views/Videos";
import Books from "./views/Books";
import Documents from "./views/Documents";
import Knowledge from "./views/Knowledge";
import { useAuthStore } from "./stores/authStore";

export default function App() {
  const init = useAuthStore((state) => state.init);

  useEffect(() => {
    init();
  }, [init]);

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<DailyLog />} />
                <Route path="/commitments" element={<Commitments />} />
                <Route path="/commitments/:tab" element={<Commitments />} />
                <Route path="/photos" element={<Photos />} />
                <Route path="/videos" element={<Videos />} />
                <Route path="/books" element={<Books />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/knowledge" element={<Knowledge />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}
