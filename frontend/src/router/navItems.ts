import {
  LayoutDashboard,
  ListChecks,
  Users,
  FlaskConical,
  ShieldCheck,
  FileText,
  Settings,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  path: string;
  icon: LucideIcon; // ícone Lucide (stroke 2px, outline) - Manual de Identidade Visual v1.0, seção 9
  implementado: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard, implementado: true },
  { label: "Acompanhamento", path: "/acompanhamento", icon: ListChecks, implementado: true },
  { label: "Pacientes", path: "/pacientes", icon: Users, implementado: true },
  { label: "Exames", path: "/exames", icon: FlaskConical, implementado: true },
  { label: "CCIH", path: "/ccih", icon: ShieldCheck, implementado: true },
  { label: "Relatórios", path: "/relatorios", icon: FileText, implementado: true },
  { label: "Configurações", path: "/configuracoes", icon: Settings, implementado: true },
];
