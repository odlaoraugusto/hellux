import { Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PacientesListPage from "./pages/PacientesListPage";
import PacienteFormPage from "./pages/PacienteFormPage";
import ExamesListPage from "./pages/ExamesListPage";
import PainelAcompanhamentoPage from "./pages/PainelAcompanhamentoPage";
import CcihPage from "./pages/CcihPage";
import RelatoriosPage from "./pages/RelatoriosPage";
import ConfiguracoesPage from "./pages/ConfiguracoesPage";
import ProtectedRoute from "./components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />

      <Route
        path="/acompanhamento"
        element={<ProtectedRoute><PainelAcompanhamentoPage /></ProtectedRoute>}
      />

      <Route path="/pacientes" element={<ProtectedRoute><PacientesListPage /></ProtectedRoute>} />
      <Route path="/pacientes/novo" element={<ProtectedRoute><PacienteFormPage /></ProtectedRoute>} />
      <Route path="/pacientes/:id/editar" element={<ProtectedRoute><PacienteFormPage /></ProtectedRoute>} />

      <Route path="/exames/*" element={<ProtectedRoute><ExamesListPage /></ProtectedRoute>} />

      <Route path="/ccih" element={<ProtectedRoute><CcihPage /></ProtectedRoute>} />
      <Route path="/relatorios" element={<ProtectedRoute><RelatoriosPage /></ProtectedRoute>} />
      <Route path="/configuracoes" element={<ProtectedRoute><ConfiguracoesPage /></ProtectedRoute>} />
    </Routes>
  );
}
