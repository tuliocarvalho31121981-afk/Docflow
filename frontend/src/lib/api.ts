const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/v1';

interface RequestOptions extends RequestInit {
  token?: string;
}

/**
 * Verifica se um token JWT está expirado.
 * Decodifica o payload do JWT e verifica o campo 'exp'.
 * @param token Token JWT
 * @returns true se o token estiver expirado ou inválido, false caso contrário
 */
function isTokenExpired(token: string | null): boolean {
  if (!token) return true;

  try {
    // JWT tem 3 partes: header.payload.signature
    const parts = token.split('.');
    if (parts.length !== 3) return true;

    // Decodifica o payload (segunda parte)
    const payload = parts[1];

    // Adiciona padding se necessário (base64url pode não ter padding)
    const paddedPayload = payload + '='.repeat((4 - payload.length % 4) % 4);

    // Decodifica base64url para string
    const decodedPayload = atob(paddedPayload.replace(/-/g, '+').replace(/_/g, '/'));
    const payloadData = JSON.parse(decodedPayload);

    // Verifica expiração
    const exp = payloadData.exp;
    if (!exp) return false; // Se não tiver exp, assume que não expira (improvável, mas seguro)

    // exp é um timestamp em segundos, converte para milissegundos e compara
    const expirationTime = exp * 1000;
    const now = Date.now();

    // Adiciona margem de 60 segundos para evitar problemas de sincronização
    const leeway = 60 * 1000; // 60 segundos em milissegundos

    return now >= (expirationTime - leeway);
  } catch (error) {
    // Se houver erro ao decodificar, assume que está expirado
    console.warn('[API] Erro ao verificar expiração do token:', error);
    return true;
  }
}

/**
 * Limpa tokens expirados do localStorage e sessionStorage.
 */
export function clearExpiredTokens(): void {
  const localStorageToken = localStorage.getItem('auth_token');
  const sessionStorageToken = sessionStorage.getItem('auth_token');

  if (localStorageToken && isTokenExpired(localStorageToken)) {
    console.log('[API] Removendo token expirado do localStorage');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
  }

  if (sessionStorageToken && isTokenExpired(sessionStorageToken)) {
    console.log('[API] Removendo token expirado do sessionStorage');
    sessionStorage.removeItem('auth_token');
    sessionStorage.removeItem('refresh_token');
  }
}

class ApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  setToken(token: string | null) {
    // Se o token estiver expirado, não define
    if (token && isTokenExpired(token)) {
      console.warn('[API] Tentativa de definir token expirado, removendo...');
      this.token = null;
      // Limpa tokens expirados do storage
      clearExpiredTokens();
    } else {
      this.token = token;
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestOptions = {}
  ): Promise<T> {
    const { token, ...fetchOptions } = options;

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    const authToken = token || this.token;
    if (authToken) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${authToken}`;
    }

    const url = `${this.baseUrl}${endpoint}`;
    console.log('[API] Request:', {
      method: options.method || 'GET',
      url,
      hasToken: !!authToken,
      tokenPreview: authToken ? `${authToken.substring(0, 20)}...` : 'none'
    });

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers,
      });

      console.log('[API] Response status:', response.status, response.statusText);
      console.log('[API] Response ok?', response.ok);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[API] Error response body:', errorText);
        let error;
        try {
          error = JSON.parse(errorText);
        } catch {
          error = { detail: errorText || 'Request failed' };
        }
        throw new Error(error.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log('[API] Response data:', data);
      return data;
    } catch (err) {
      console.error('[API] Request failed:', err);
      if (err instanceof TypeError && err.message.includes('fetch')) {
        console.error('[API] Possível erro de CORS ou servidor offline');
      }
      throw err;
    }
  }

  // Auth
  async login(email: string, password: string, clinicaId: string) {
    // Backend espera JSON com email e senha (não form-data)
    return this.request<{
      access_token: string;
      refresh_token: string;
      token_type: string;
      expires_in: number;
      user: {
        id: string;
        nome: string;
        email: string;
        tipo?: string;
        clinica_id: string;
        clinica_nome: string;
        perfil: {
          id: string;
          nome: string;
          permissoes: Record<string, any>;
        };
      };
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email,
        senha: password,
      }),
    });
  }

  async getMe() {
    return this.request('/auth/me');
  }

  // Clinicas
  async getClinicas() {
    return this.request('/clinicas');
  }

  // ==========================================
  // CARDS - Kanban Fase 0-3
  // ==========================================

  async getCardsKanban(fase: number, data?: string, medicoId?: string) {
    const params = new URLSearchParams();
    if (data) params.append('data', data);
    if (medicoId) params.append('medico_id', medicoId);
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request<CardKanbanResponse>(`/cards/kanban/${fase}${queryString}`);
  }

  async getCards(filters?: CardFilters) {
    const params = new URLSearchParams();
    if (filters?.data) params.append('data', filters.data);
    if (filters?.medicoId) params.append('medico_id', filters.medicoId);
    if (filters?.pacienteId) params.append('paciente_id', filters.pacienteId);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.fase !== undefined) params.append('fase', filters.fase.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.perPage) params.append('per_page', filters.perPage.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request<CardListResponse>(`/cards${queryString}`);
  }

  async getCard(cardId: string) {
    return this.request<CardResponse>(`/cards/${cardId}`);
  }

  async updateCard(cardId: string, data: CardUpdateRequest) {
    return this.request<CardResponse>(`/cards/${cardId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async moverCard(cardId: string, data: CardMoverRequest) {
    return this.request<CardResponse>(`/cards/${cardId}/mover`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getCardChecklist(cardId: string) {
    return this.request<ChecklistItem[]>(`/cards/${cardId}/checklist`);
  }

  async updateChecklistItem(cardId: string, itemId: string, concluido: boolean) {
    return this.request<ChecklistItem>(`/cards/${cardId}/checklist/${itemId}`, {
      method: 'PATCH',
      body: JSON.stringify({ concluido }),
    });
  }

  async getCardHistorico(cardId: string) {
    return this.request<CardHistoricoItem[]>(`/cards/${cardId}/historico`);
  }

  async getCardDocumentos(cardId: string) {
    return this.request<CardDocumento[]>(`/cards/${cardId}/documentos`);
  }

  async getCardMensagens(cardId: string) {
    return this.request<CardMensagem[]>(`/cards/${cardId}/mensagens`);
  }

  // ==========================================
  // AGENDA
  // ==========================================

  async getAgendamentos(filters?: {
    data?: string;
    data_inicio?: string;
    data_fim?: string;
    medico_id?: string;
    paciente_id?: string;
    status?: string;
    page?: number;
    per_page?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.data) params.append('data', filters.data);
    if (filters?.data_inicio) params.append('data_inicio', filters.data_inicio);
    if (filters?.data_fim) params.append('data_fim', filters.data_fim);
    if (filters?.medico_id) params.append('medico_id', filters.medico_id);
    if (filters?.paciente_id) params.append('paciente_id', filters.paciente_id);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.per_page) params.append('per_page', filters.per_page.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request(`/agenda/agendamentos${queryString}`);
  }

  async getAgendamento(id: string) {
    return this.request(`/agenda/${id}`);
  }

  async createAgendamento(data: any) {
    return this.request('/agenda/agendamentos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateAgendamento(id: string, data: any) {
    return this.request(`/agenda/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async updateAgendamentoStatus(id: string, status: string, motivo_cancelamento?: string) {
    return this.request(`/agenda/${id}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status, motivo_cancelamento }),
    });
  }

  async confirmarAgendamento(id: string) {
    return this.request(`/agenda/${id}/confirmar`, {
      method: 'POST',
    });
  }

  async cancelarAgendamento(id: string, motivo?: string) {
    return this.request(`/agenda/${id}/cancelar`, {
      method: 'POST',
      body: JSON.stringify({ motivo }),
    });
  }

  async getMetricas(data?: string) {
    const params = data ? `?data=${data}` : '';
    return this.request(`/agenda/metricas${params}`);
  }

  async getSlotsDisponiveis(data_inicio: string, data_fim?: string, medico_id?: string, tipo_consulta_id?: string) {
    const params = new URLSearchParams();
    params.append('data_inicio', data_inicio);
    if (data_fim) params.append('data_fim', data_fim);
    if (medico_id) params.append('medico_id', medico_id);
    if (tipo_consulta_id) params.append('tipo_consulta_id', tipo_consulta_id);
    return this.request(`/agenda/slots?${params.toString()}`);
  }

  async getTiposConsulta() {
    return this.request('/agenda/tipos-consulta');
  }

  async getMedicos() {
    return this.request('/usuarios?tipo=medico');
  }

  // Mantido para compatibilidade
  async getAgenda(date?: string) {
    return this.getAgendamentos({ data: date });
  }

  // Pacientes
  async getPacientes(search?: string) {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.request(`/pacientes${params}`);
  }

  async getPaciente(id: string) {
    return this.request(`/pacientes/${id}`);
  }

  async createPaciente(data: any) {
    return this.request('/pacientes', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Governança
  async getValidacoesPendentes() {
    return this.request('/governanca/validacoes?status=pendente');
  }

  async processarValidacao(id: string, resultado: 'aprovado' | 'corrigido' | 'rejeitado', correcoes?: any) {
    return this.request(`/governanca/validacoes/${id}/validar`, {
      method: 'POST',
      body: JSON.stringify({ resultado, correcoes }),
    });
  }

  async getGovernancaDashboard() {
    return this.request('/governanca/dashboard');
  }

  // Chat/Simulador
  async enviarMensagemSimulador(telefone: string, mensagem: string, nomePaciente?: string) {
    return this.request<ChatResponse>('/chat/mensagem', {
      method: 'POST',
      body: JSON.stringify({
        telefone,
        mensagem,
        nome_paciente: nomePaciente,
        simulado: true
      }),
    });
  }

  async getConversas() {
    return this.request<ConversasResponse>('/chat/conversas');
  }

  async getConversa(telefone: string) {
    return this.request<ConversaDetalhe>(`/chat/conversas/${telefone}`);
  }

  async testarInterpretacao(mensagem: string) {
    return this.request<TesteInterpretacao>(`/chat/teste?mensagem=${encodeURIComponent(mensagem)}`, {
      method: 'POST',
    });
  }

  async getLLMConfig() {
    return this.request<LLMConfig>('/chat/config');
  }

  // Dashboard
  async getDashboardStats() {
    return this.request('/dashboard/stats');
  }

  // ==========================================
  // MODELOS DE DOCUMENTOS
  // ==========================================

  async getModelosDocumentos(filters?: {
    categoria?: string;
    search?: string;
    ativo?: boolean;
    page?: number;
    per_page?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.categoria) params.append('categoria', filters.categoria);
    if (filters?.search) params.append('search', filters.search);
    if (filters?.ativo !== undefined) params.append('ativo', filters.ativo.toString());
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.per_page) params.append('per_page', filters.per_page.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request<ModelosDocumentosResponse>(`/modelos-documentos${queryString}`);
  }

  async getModeloDocumento(id: string) {
    return this.request<ModeloDocumento>(`/modelos-documentos/${id}`);
  }

  async createModeloDocumento(data: ModeloDocumentoCreate) {
    return this.request<ModeloDocumento>('/modelos-documentos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateModeloDocumento(id: string, data: ModeloDocumentoUpdate) {
    return this.request<ModeloDocumento>(`/modelos-documentos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async deleteModeloDocumento(id: string) {
    return this.request(`/modelos-documentos/${id}`, {
      method: 'DELETE',
    });
  }

  async duplicarModeloDocumento(id: string, novoTitulo?: string) {
    return this.request<ModeloDocumento>(`/modelos-documentos/${id}/duplicar`, {
      method: 'POST',
      body: JSON.stringify({ novo_titulo: novoTitulo }),
    });
  }

  async reativarModeloDocumento(id: string) {
    return this.request<ModeloDocumento>(`/modelos-documentos/${id}/reativar`, {
      method: 'POST',
    });
  }

  async getModelosDocumentosPorCategoria() {
    return this.request<ModelosPorCategoriaResponse>('/modelos-documentos/por-categoria');
  }

  async getModelosDocumentosContagem() {
    return this.request<ModelosContagemResponse>('/modelos-documentos/contagem');
  }

  // ==========================================
  // PRONTUÁRIO / COCKPIT DO MÉDICO
  // ==========================================

  // Briefing pré-consulta (dados já preparados)
  async getBriefingPaciente(pacienteId: string) {
    return this.request<BriefingPaciente>(`/prontuario/pacientes/${pacienteId}/briefing`);
  }

  // Histórico de consultas do paciente
  async getHistoricoPaciente(pacienteId: string) {
    return this.request<HistoricoConsulta[]>(`/prontuario/pacientes/${pacienteId}/historico`);
  }

  // Consultas
  async getConsultas(filters?: {
    paciente_id?: string;
    medico_id?: string;
    data_inicio?: string;
    data_fim?: string;
    status?: string;
    page?: number;
    per_page?: number;
  }) {
    const params = new URLSearchParams();
    if (filters?.paciente_id) params.append('paciente_id', filters.paciente_id);
    if (filters?.medico_id) params.append('medico_id', filters.medico_id);
    if (filters?.data_inicio) params.append('data_inicio', filters.data_inicio);
    if (filters?.data_fim) params.append('data_fim', filters.data_fim);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.per_page) params.append('per_page', filters.per_page.toString());
    const queryString = params.toString() ? `?${params.toString()}` : '';
    return this.request<ConsultasResponse>(`/prontuario/consultas${queryString}`);
  }

  async getConsulta(consultaId: string) {
    return this.request<ConsultaResponse>(`/prontuario/consultas/${consultaId}`);
  }

  async iniciarConsulta(data: IniciarConsultaRequest) {
    return this.request<ConsultaResponse>('/prontuario/consultas/iniciar', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async finalizarConsulta(consultaId: string) {
    return this.request<ConsultaResponse>(`/prontuario/consultas/${consultaId}/finalizar`, {
      method: 'POST',
    });
  }

  // SOAP
  async getSOAP(consultaId: string) {
    return this.request<SOAPResponse>(`/prontuario/consultas/${consultaId}/soap`);
  }

  async criarSOAP(data: SOAPCreate) {
    return this.request<SOAPResponse>('/prontuario/soap', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async atualizarSOAP(soapId: string, data: SOAPUpdate) {
    return this.request<SOAPResponse>(`/prontuario/soap/${soapId}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  }

  async validarSOAP(soapId: string) {
    return this.request<SOAPResponse>(`/prontuario/soap/${soapId}`, {
      method: 'PATCH',
      body: JSON.stringify({ revisado_por_medico: true }),
    });
  }

  // Receitas
  async criarReceita(data: ReceitaCreate) {
    return this.request<ReceitaResponse>('/prontuario/receitas', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getReceitas(consultaId: string) {
    return this.request<ReceitaResponse[]>(`/prontuario/receitas?consulta_id=${consultaId}`);
  }

  // Atestados
  async criarAtestado(data: AtestadoCreate) {
    return this.request<AtestadoResponse>('/prontuario/atestados', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Exames
  async solicitarExame(data: ExameSolicitadoCreate) {
    return this.request<ExameSolicitadoResponse>('/prontuario/exames', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async solicitarExamesBatch(data: ExameSolicitadoCreate[]) {
    return this.request<ExameSolicitadoResponse[]>('/prontuario/exames/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async getExamesPendentes(pacienteId: string) {
    return this.request<ExameSolicitadoResponse[]>(`/prontuario/pacientes/${pacienteId}/exames-pendentes`);
  }

  // Encaminhamentos
  async criarEncaminhamento(data: EncaminhamentoCreate) {
    return this.request<EncaminhamentoResponse>('/prontuario/encaminhamentos', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Agenda - Ações do cockpit
  async registrarChegada(agendamentoId: string) {
    return this.request<AgendamentoResponse>(`/agenda/${agendamentoId}/chegada`, {
      method: 'POST',
    });
  }

  async iniciarAtendimento(agendamentoId: string) {
    return this.request<AgendamentoResponse>(`/agenda/${agendamentoId}/iniciar`, {
      method: 'POST',
    });
  }

  async finalizarAtendimento(agendamentoId: string) {
    return this.request<AgendamentoResponse>(`/agenda/${agendamentoId}/finalizar`, {
      method: 'POST',
    });
  }

  async marcarFalta(agendamentoId: string) {
    return this.request<AgendamentoResponse>(`/agenda/${agendamentoId}/falta`, {
      method: 'POST',
    });
  }

  // Cards Fase 2 (pacientes em atendimento)
  async getCardsFase2() {
    return this.request<CardKanbanResponse>('/cards/kanban/2');
  }

  // ==========================================
  // TRANSCRIÇÃO DE ÁUDIO (WHISPER)
  // ==========================================

  /**
   * Faz upload de áudio e transcreve usando Whisper (via Groq).
   * @param consultaId ID da consulta
   * @param audioBlob Blob do áudio gravado
   * @returns Transcrição do áudio
   */
  async transcreverAudio(consultaId: string, audioBlob: Blob): Promise<TranscricaoResponse> {
    const formData = new FormData();
    formData.append('audio_file', audioBlob, 'audio.webm');

    const url = `${this.baseUrl}/prontuario/transcricoes/upload?consulta_id=${consultaId}`;

    const headers: HeadersInit = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    console.log('[API] Enviando áudio para transcrição:', {
      url,
      audioSize: audioBlob.size,
      audioType: audioBlob.type,
    });

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[API] Erro na transcrição:', errorText);
      throw new Error(`Erro na transcrição: ${response.status}`);
    }

    const data = await response.json();
    console.log('[API] Transcrição recebida:', data);
    return data;
  }

  /**
   * Envia chunk de áudio para transcrição em tempo real (streaming).
   * @param consultaId ID da consulta
   * @param audioChunk Blob do chunk de áudio
   * @param chunkIndex Índice do chunk
   * @param isFinal Se é o último chunk
   */
  async enviarChunkAudio(
    consultaId: string,
    audioChunk: Blob,
    chunkIndex: number,
    isFinal: boolean = false
  ): Promise<{ status: string; transcricao_parcial?: string }> {
    const formData = new FormData();
    formData.append('audio_chunk', audioChunk, `chunk_${chunkIndex}.webm`);

    const params = new URLSearchParams({
      consulta_id: consultaId,
      chunk_index: chunkIndex.toString(),
      is_final: isFinal.toString(),
    });

    const url = `${this.baseUrl}/prontuario/transcricoes/audio-chunk?${params}`;

    const headers: HeadersInit = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Erro ao enviar chunk: ${response.status} - ${errorText}`);
    }

    return response.json();
  }
}

// ==========================================
// TYPES - Cards
// ==========================================

export interface CardFilters {
  data?: string;
  medicoId?: string;
  pacienteId?: string;
  status?: string;
  fase?: number;
  page?: number;
  perPage?: number;
}

export interface CardListItem {
  id: string;
  fase: number;
  coluna: string;
  status: string;
  prioridade: string;
  cor_alerta?: string;
  paciente_nome?: string;
  paciente_telefone?: string;
  intencao_inicial?: string;
  ultima_interacao?: string;
  tentativa_reativacao: number;
  data_agendamento?: string;
  hora_agendamento?: string;
  tipo_consulta?: string;
  medico_id?: string;
  checklist_total: number;
  checklist_concluido: number;
  tempo_espera_minutos?: number;
}

export interface CardKanbanResponse {
  fase: number;
  colunas: Record<string, CardListItem[]>;
  total_cards: number;
}

export interface CardListResponse {
  items: CardListItem[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface CardResponse {
  id: string;
  clinica_id: string;
  agendamento_id?: string;
  paciente_id?: string;
  medico_id?: string;
  fase: number;
  coluna: string;
  posicao: number;
  status: string;
  prioridade: string;
  cor_alerta?: string;
  observacoes?: string;
  intencao_inicial?: string;
  motivo_saida?: string;
  ultima_interacao?: string;
  tentativa_reativacao: number;
  convenio_validado: boolean;
  convenio_status?: string;
  origem?: string;
  fase0_em?: string;
  fase1_em?: string;
  fase2_em?: string;
  fase3_em?: string;
  concluido_em?: string;
  is_derivado: boolean;
  card_origem_id?: string;
  card_derivado_id?: string;
  paciente_nome?: string;
  paciente_telefone?: string;
  data_agendamento?: string;
  hora_agendamento?: string;
  tipo_consulta?: string;
  created_at: string;
  updated_at: string;
}

export interface CardUpdateRequest {
  prioridade?: string;
  coluna?: string;
  posicao?: number;
  cor_alerta?: string;
  observacoes?: string;
  intencao_inicial?: string;
  motivo_saida?: string;
  convenio_status?: string;
}

export interface CardMoverRequest {
  coluna: string;
  posicao?: number;
  motivo_saida?: string;
}

export interface ChecklistItem {
  id: string;
  card_id: string;
  fase: number;
  tipo: string;
  descricao: string;
  obrigatorio: boolean;
  concluido: boolean;
  concluido_em?: string;
  concluido_por_user?: string;
  concluido_por_paciente: boolean;
  concluido_por_sistema: boolean;
  referencia_tipo?: string;
  referencia_id?: string;
  posicao: number;
}

export interface CardHistoricoItem {
  id: string;
  card_id: string;
  tipo: string;
  descricao: string;
  dados_anteriores?: Record<string, any>;
  dados_novos?: Record<string, any>;
  user_id?: string;
  user_nome?: string;
  automatico: boolean;
  created_at: string;
}

export interface CardDocumento {
  id: string;
  card_id: string;
  tipo: string;
  nome: string;
  descricao?: string;
  storage_path: string;
  mime_type?: string;
  tamanho_bytes?: number;
  exame_tipo?: string;
  exame_data?: string;
  exame_laboratorio?: string;
  match_status?: string;
  uploaded_by_user?: string;
  uploaded_by_paciente: boolean;
  created_at: string;
}

export interface CardMensagem {
  id: string;
  card_id: string;
  direcao: string;
  canal: string;
  tipo: string;
  conteudo: string;
  template?: string;
  status: string;
  enviado_em?: string;
  lido_em?: string;
  created_at: string;
}

// ==========================================
// TYPES - Chat
// ==========================================

export interface ChatResponse {
  id: string;
  resposta: string;
  interpretacao: {
    intencao: string;
    confianca: number;
    dados: {
      data?: string;
      hora?: string;
      nome?: string;
      medico?: string;
      motivo?: string;
    };
    requer_mais_info: boolean;
    pergunta_followup?: string;
  };
  acoes: Array<{
    tipo: string;
    sucesso: boolean;
    detalhes: Record<string, any>;
    erro?: string;
  }>;
  validacao_pendente: boolean;
  validacao_id?: string;
  tempo_processamento_ms: number;
}

export interface ConversasResponse {
  conversas: Array<{
    telefone: string;
    paciente_nome?: string;
    ultima_mensagem: string;
    timestamp: string;
    nao_lidas: number;
  }>;
  total: number;
}

export interface ConversaDetalhe {
  telefone: string;
  paciente_id?: string;
  paciente_nome?: string;
  total_mensagens: number;
  ultima_mensagem?: string;
  mensagens: Array<{
    id: string;
    tipo: 'paciente' | 'sistema';
    conteudo: string;
    timestamp: string;
    interpretacao?: any;
  }>;
}

export interface TesteInterpretacao {
  mensagem: string;
  interpretacao: ChatResponse['interpretacao'];
}

export interface LLMConfig {
  llm_provider: string;
  model: string;
  status: string;
  versao: string;
  funcionalidades: {
    agendamento: boolean;
    funil_leads: boolean;
    governanca: boolean;
    multi_turno: boolean;
  };
  erro?: string;
}

// ==========================================
// CONSTANTS - Colunas do Kanban
// ==========================================

export const COLUNAS_FASE_0 = {
  pre_agendamento: { label: 'Pré-Agendamento', color: 'bg-blue-100' },
  aguardando_autorizacao: { label: 'Aguard. Autorização', color: 'bg-yellow-100' },
  aguardando_horario: { label: 'Aguard. Horário', color: 'bg-purple-100' },
  reativacao_1: { label: 'Reativação 1', color: 'bg-orange-100' },
  reativacao_2: { label: 'Reativação 2', color: 'bg-orange-200' },
  reativacao_3: { label: 'Reativação 3', color: 'bg-red-100' },
  perdido: { label: 'Perdido', color: 'bg-gray-200' },
};

export const COLUNAS_FASE_1 = {
  pre_consulta: { label: 'Pré-Consulta', color: 'bg-blue-100' },
  pendente_anamnese: { label: 'Pend. Anamnese', color: 'bg-yellow-100' },
  pendente_confirmacao: { label: 'Pend. Confirmação', color: 'bg-orange-100' },
  pronto: { label: 'Pronto', color: 'bg-green-100' },
};

export const COLUNAS_FASE_2 = {
  aguardando_checkin: { label: 'Aguard. Check-in', color: 'bg-blue-100' },
  em_espera: { label: 'Em Espera', color: 'bg-yellow-100' },
  em_atendimento: { label: 'Em Atendimento', color: 'bg-purple-100' },
  finalizado: { label: 'Finalizado', color: 'bg-green-100' },
};

export const COLUNAS_FASE_3 = {
  pendente_documentos: { label: 'Pend. Documentos', color: 'bg-yellow-100' },
  pendente_pagamento: { label: 'Pend. Pagamento', color: 'bg-orange-100' },
  concluido: { label: 'Concluído', color: 'bg-green-100' },
};

export const COLUNAS_POR_FASE: Record<number, Record<string, { label: string; color: string }>> = {
  0: COLUNAS_FASE_0,
  1: COLUNAS_FASE_1,
  2: COLUNAS_FASE_2,
  3: COLUNAS_FASE_3,
};

export const FASES = [
  { id: 0, label: 'Pré-Agendamento', icon: '📋' },
  { id: 1, label: 'Pré-Consulta', icon: '📅' },
  { id: 2, label: 'Dia da Consulta', icon: '🏥' },
  { id: 3, label: 'Pós-Consulta', icon: '✅' },
];

export const INTENCOES = {
  marcar: { label: 'Marcar Consulta', color: 'text-blue-600' },
  saber_valor: { label: 'Saber Valor', color: 'text-green-600' },
  saber_convenio: { label: 'Saber Convênio', color: 'text-purple-600' },
  faq: { label: 'FAQ', color: 'text-gray-600' },
  remarcar: { label: 'Remarcar', color: 'text-orange-600' },
  cancelar: { label: 'Cancelar', color: 'text-red-600' },
  enviar_exames: { label: 'Enviar Exames', color: 'text-cyan-600' },
  anamnese: { label: 'Anamnese', color: 'text-indigo-600' },
};

// ==========================================
// TYPES - Modelos de Documentos
// ==========================================

export type CategoriaDocumento = 'Atestados' | 'Exames' | 'Orientações Médicas' | 'Receitas' | 'Outros';

export interface ModeloDocumento {
  id: string;
  clinica_id: string;
  categoria: CategoriaDocumento;
  titulo: string;
  conteudo: string;
  uso_exclusivo_usuario_id?: string;
  ativo: boolean;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ModeloDocumentoCreate {
  categoria: CategoriaDocumento;
  titulo: string;
  conteudo: string;
  uso_exclusivo_usuario_id?: string;
}

export interface ModeloDocumentoUpdate {
  categoria?: CategoriaDocumento;
  titulo?: string;
  conteudo?: string;
  uso_exclusivo_usuario_id?: string;
  ativo?: boolean;
}

export interface ModelosDocumentosResponse {
  items: ModeloDocumento[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface ModelosPorCategoriaResponse {
  categorias: Record<string, ModeloDocumento[]>;
  total: number;
}

export interface ModelosContagemResponse {
  contagem: Record<string, number>;
  total: number;
}

export const CATEGORIAS_DOCUMENTO: Record<CategoriaDocumento, { label: string; color: string; icon: string }> = {
  'Atestados': { label: 'Atestados', color: 'bg-blue-500', icon: '📋' },
  'Exames': { label: 'Exames', color: 'bg-green-500', icon: '🔬' },
  'Orientações Médicas': { label: 'Orientações Médicas', color: 'bg-purple-500', icon: '📝' },
  'Receitas': { label: 'Receitas', color: 'bg-orange-500', icon: '💊' },
  'Outros': { label: 'Outros', color: 'bg-gray-500', icon: '📄' },
};

// ==========================================
// TYPES - Prontuário / Cockpit
// ==========================================

export interface BriefingPaciente {
  paciente_id: string;
  nome: string;
  idade: number;
  sexo?: string;
  data_nascimento?: string;
  telefone?: string;
  convenio?: string;
  alergias: string[];
  medicamentos_uso: string[];
  antecedentes?: string;
  ultima_consulta?: {
    data: string;
    motivo?: string;
    medico?: string;
  };
  exames_pendentes: Array<{
    id: string;
    tipo: string;
    descricao: string;
    data_solicitacao: string;
  }>;
  alertas: string[];
}

export interface HistoricoConsulta {
  id: string;
  data: string;
  medico_nome?: string;
  tipo_consulta?: string;
  motivo?: string;
  diagnostico?: string;
  tem_soap: boolean;
  tem_receita: boolean;
  tem_atestado: boolean;
  tem_exames: boolean;
}

export interface ConsultaResponse {
  id: string;
  clinica_id: string;
  paciente_id: string;
  medico_id: string;
  agendamento_id?: string;
  data_consulta: string;
  hora_inicio?: string;
  hora_fim?: string;
  tipo_consulta?: string;
  status: 'agendada' | 'em_andamento' | 'finalizada' | 'cancelada';
  motivo?: string;
  observacoes?: string;
  paciente_nome?: string;
  medico_nome?: string;
  created_at: string;
  updated_at: string;
}

export interface ConsultasResponse {
  items: ConsultaResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface IniciarConsultaRequest {
  paciente_id: string;
  medico_id?: string;
  agendamento_id?: string;
  tipo_consulta?: string;
  motivo?: string;
}

export interface SinaisVitais {
  pa_sistolica?: number;
  pa_diastolica?: number;
  fc?: number;
  fr?: number;
  temperatura?: number;
  saturacao?: number;
  peso?: number;
  altura?: number;
  imc?: number;
  glicemia?: number;
}

export interface CID {
  codigo: string;
  descricao: string;
  tipo: 'principal' | 'secundario';
}

export interface SOAPResponse {
  id: string;
  consulta_id: string;
  subjetivo?: string;
  objetivo?: string;
  avaliacao?: string;
  plano?: string;
  exame_fisico?: SinaisVitais;
  cids: CID[];
  gerado_por_ia: boolean;
  revisado_por_medico: boolean;
  assinado: boolean;
  assinado_em?: string;
  created_at: string;
  updated_at: string;
}

export interface SOAPCreate {
  consulta_id: string;
  subjetivo?: string;
  objetivo?: string;
  avaliacao?: string;
  plano?: string;
  exame_fisico?: SinaisVitais;
  cids?: CID[];
  gerado_por_ia?: boolean;
}

export interface SOAPUpdate {
  subjetivo?: string;
  objetivo?: string;
  avaliacao?: string;
  plano?: string;
  exame_fisico?: SinaisVitais;
  cids?: CID[];
  revisado_por_medico?: boolean;
  assinado?: boolean;
}

export interface ItemReceita {
  medicamento: string;
  concentracao?: string;
  forma?: string;
  quantidade?: number;
  posologia: string;
  duracao?: string;
}

export interface ReceitaCreate {
  consulta_id: string;
  paciente_id: string;
  medico_id?: string;
  tipo: 'simples' | 'especial' | 'antimicrobiano';
  itens: ItemReceita[];
  observacoes?: string;
}

export interface ReceitaResponse {
  id: string;
  consulta_id: string;
  paciente_id: string;
  medico_id: string;
  tipo: string;
  itens: ItemReceita[];
  observacoes?: string;
  assinado: boolean;
  created_at: string;
}

export interface AtestadoCreate {
  consulta_id: string;
  paciente_id: string;
  medico_id?: string;
  tipo: 'comparecimento' | 'afastamento' | 'aptidao' | 'acompanhante' | 'medico';
  data_inicio?: string;
  data_fim?: string;
  dias?: number;
  cid?: string;
  observacoes?: string;
}

export interface AtestadoResponse {
  id: string;
  consulta_id: string;
  paciente_id: string;
  medico_id: string;
  tipo: string;
  data_inicio?: string;
  data_fim?: string;
  dias?: number;
  cid?: string;
  observacoes?: string;
  assinado: boolean;
  created_at: string;
}

export interface ExameSolicitadoCreate {
  consulta_id: string;
  paciente_id: string;
  medico_id?: string;
  tipo: 'laboratorial' | 'imagem' | 'cardiologico';
  descricao: string;
  urgente?: boolean;
  observacoes?: string;
}

export interface ExameSolicitadoResponse {
  id: string;
  consulta_id: string;
  paciente_id: string;
  medico_id: string;
  tipo: string;
  descricao: string;
  urgente: boolean;
  status: 'solicitado' | 'agendado' | 'realizado' | 'resultado_disponivel';
  observacoes?: string;
  created_at: string;
}

export interface EncaminhamentoCreate {
  consulta_id: string;
  paciente_id: string;
  medico_id?: string;
  especialidade: string;
  motivo: string;
  urgente?: boolean;
  observacoes?: string;
}

export interface EncaminhamentoResponse {
  id: string;
  consulta_id: string;
  paciente_id: string;
  medico_id: string;
  especialidade: string;
  motivo: string;
  urgente: boolean;
  observacoes?: string;
  created_at: string;
}

export interface AgendamentoResponse {
  id: string;
  clinica_id: string;
  paciente_id: string;
  medico_id: string;
  data: string;
  hora_inicio: string;
  hora_fim?: string;
  tipo_consulta?: string;
  status: 'agendado' | 'confirmado' | 'chegou' | 'em_atendimento' | 'finalizado' | 'falta' | 'cancelado';
  confirmado: boolean;
  paciente_nome?: string;
  medico_nome?: string;
  created_at: string;
  updated_at: string;
}

// Transcrição de áudio
export interface TranscricaoResponse {
  id: string;
  consulta_id: string;
  texto: string;
  duracao_segundos?: number;
  idioma?: string;
  confianca?: number;
  modelo_usado?: string;
  created_at: string;
  updated_at: string;
}

export const api = new ApiClient(API_URL);

// Hook para usar em componentes
export function useApi() {
  return api;
}
