export interface LogAuditoria {
  id: string;
  usuario_id: string | null;
  usuario_login: string | null;
  metodo: string;
  caminho: string;
  status_code: number;
  ip_origem: string | null;
  criado_em: string;
}

export interface LogAuditoriaListagem {
  total: number;
  page: number;
  page_size: number;
  items: LogAuditoria[];
}
