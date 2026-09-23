import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import type { ReactNode } from "react";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import LiveNetwork from "./pages/LiveNetwork";
import Incidents from "./pages/Incidents";
import IncidentDetail from "./pages/IncidentDetail";
import Customers from "./pages/Customers";
import Devices from "./pages/Devices";
import Topology from "./pages/Topology";
import Technicians from "./pages/Technicians";
import Analytics from "./pages/Analytics";
import Notifications from "./pages/Notifications";
import UssdSimulator from "./pages/UssdSimulator";
import Settings from "./pages/Settings";

function RequireAuth({ children }: { children: ReactNode }) {
  const location = useLocation();
  const token = localStorage.getItem("netpulse_token");
  if (!token) return <Navigate to="/login" state={{ from: location }} replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<RequireAuth><Dashboard /></RequireAuth>} />
      <Route path="/live-network" element={<RequireAuth><LiveNetwork /></RequireAuth>} />
      <Route path="/incidents" element={<RequireAuth><Incidents /></RequireAuth>} />
      <Route path="/incidents/:id" element={<RequireAuth><IncidentDetail /></RequireAuth>} />
      <Route path="/customers" element={<RequireAuth><Customers /></RequireAuth>} />
      <Route path="/devices" element={<RequireAuth><Devices /></RequireAuth>} />
      <Route path="/topology" element={<RequireAuth><Topology /></RequireAuth>} />
      <Route path="/technicians" element={<RequireAuth><Technicians /></RequireAuth>} />
      <Route path="/analytics" element={<RequireAuth><Analytics /></RequireAuth>} />
      <Route path="/notifications" element={<RequireAuth><Notifications /></RequireAuth>} />
      <Route path="/ussd" element={<RequireAuth><UssdSimulator /></RequireAuth>} />
      <Route path="/settings" element={<RequireAuth><Settings /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
