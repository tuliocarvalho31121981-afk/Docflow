'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Calendar,
  Clock,
  User,
  Phone,
  Filter,
  Plus,
  CheckCircle2,
  X,
  MapPin,
  Play,
  Square,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { api } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

// ==========================================
// TIPOS
// ==========================================

interface Agendamento {
  id: string;
  paciente_id: string;
  paciente_nome: string;
  paciente_telefone: string;
  medico_id: string;
  medico_nome: string;
  tipo_consulta_id: string;
  tipo_consulta_nome: string;
  tipo_consulta_cor: string;
  data: string;
  hora_inicio: string;
  hora_fim: string;
  status: string;
  observacoes?: string;
  convenio_nome?: string;
  primeira_vez: boolean;
  card_id?: string;
}

interface Medico {
  id: string;
  nome: string;
  email: string;
}

interface Metricas {
  data: string;
  total_agendados: number;
  total_confirmados: number;
  total_aguardando: number;
  total_em_atendimento: number;
  total_atendidos: number;
  total_faltas: number;
  total_cancelados: number;
  taxa_ocupacao: number;
  horarios_disponiveis: number;
}

// ==========================================
// STATUS E CORES
// ==========================================

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: any }> = {
  agendado: { label: 'Agendado', color: 'bg-gray-100 text-gray-700', icon: Clock },
  confirmado: { label: 'Confirmado', color: 'bg-blue-100 text-blue-700', icon: CheckCircle2 },
  aguardando: { label: 'Aguardando', color: 'bg-yellow-100 text-yellow-700', icon: MapPin },
  em_atendimento: { label: 'Em Atendimento', color: 'bg-purple-100 text-purple-700', icon: Play },
  atendido: { label: 'Atendido', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  faltou: { label: 'Faltou', color: 'bg-red-100 text-red-700', icon: X },
  cancelado: { label: 'Cancelado', color: 'bg-gray-100 text-gray-500', icon: X },
};

// ==========================================
// PÁGINA PRINCIPAL
// ==========================================

export default function AgendaPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  // Estado
  const [dataAtual, setDataAtual] = useState(new Date());
  const [agendamentos, setAgendamentos] = useState<Agendamento[]>([]);
  const [medicos, setMedicos] = useState<Medico[]>([]);
  const [medicosSelecionados, setMedicosSelecionados] = useState<string[]>([]); // [] = todos
  const [metricas, setMetricas] = useState<Metricas | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Carregar dados
  const carregarDados = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Garante que o token está configurado antes de fazer chamadas
      const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
      if (token) {
        api.setToken(token);
      }

      const dataStr = dataAtual.toISOString().split('T')[0];

      // Carrega médicos
      const medicosData = await api.getMedicos() as { usuarios?: Medico[] } | Medico[];
      // ListaUsuariosResponse tem campo "usuarios", não é array direto
      const medicosList = (Array.isArray(medicosData) ? medicosData : medicosData?.usuarios || []) as Medico[];
      // Garantir que todos os IDs sejam strings
      const medicosNormalizados = medicosList.map(medico => ({
        ...medico,
        id: String(medico.id)
      }));
      console.log('🔍 DEBUG Médicos carregados:', medicosNormalizados);
      console.log('🔍 DEBUG Primeiro médico completo:', JSON.stringify(medicosNormalizados[0], null, 2));
      setMedicos(medicosNormalizados);

      // Carrega agendamentos
      const filters: any = { data: dataStr, per_page: 100 };
      const agendamentosData = await api.getAgendamentos(filters) as { items?: Agendamento[]; data?: Agendamento[] } | Agendamento[];
      // PaginatedResponse usa "items" não "data"
      let agendamentosList = Array.isArray(agendamentosData)
        ? agendamentosData
        : (agendamentosData?.items || agendamentosData?.data || []);

      // Filtra no frontend se múltiplos médicos selecionados
      if (medicosSelecionados.length > 0) {
        agendamentosList = agendamentosList.filter((ag: Agendamento) =>
          medicosSelecionados.includes(String(ag.medico_id))
        );
      }
      setAgendamentos(agendamentosList);

      // Carrega métricas
      const metricasData = await api.getMetricas(dataStr) as Metricas | null;
      setMetricas(metricasData || null);
    } catch (err: any) {
      console.error('Erro ao carregar agenda:', err);

      // Se for erro 401 (não autorizado), pode ser token expirado
      if (err.message?.includes('401') || err.message?.includes('Unauthorized')) {
        console.error('Token pode estar expirado. Verifique o console do navegador para mais detalhes.');
        setError('Sessão expirada. Por favor, faça login novamente.');
        // Opcionalmente, redirecionar para login após um tempo
        // setTimeout(() => router.push('/'), 2000);
      } else {
        setError(err.message || 'Erro ao carregar agenda');
      }
    } finally {
      setLoading(false);
    }
  }, [dataAtual, medicosSelecionados]);

  useEffect(() => {
    carregarDados();
  }, [carregarDados]);


  // Navegação de data
  const mudarData = (dias: number) => {
    const novaData = new Date(dataAtual);
    novaData.setDate(novaData.getDate() + dias);
    setDataAtual(novaData);
  };

  const irParaHoje = () => {
    setDataAtual(new Date());
  };

  // Filtro de médicos
  const toggleMedico = useCallback((medicoId: string) => {
    if (medicoId === 'todos') {
      setMedicosSelecionados([]); // [] = todos
    } else {
      setMedicosSelecionados([medicoId]); // Seleciona apenas um médico
    }
  }, []);

  const selecionarTodos = () => {
    setMedicosSelecionados([]); // [] = todos
  };

  // Ações rápidas
  const handleConfirmar = async (id: string) => {
    try {
      await api.confirmarAgendamento(id);
      carregarDados();
    } catch (err: any) {
      alert('Erro ao confirmar: ' + err.message);
    }
  };

  const handleCancelar = async (id: string) => {
    if (!confirm('Cancelar este agendamento?')) return;
    try {
      await api.cancelarAgendamento(id);
      carregarDados();
    } catch (err: any) {
      alert('Erro ao cancelar: ' + err.message);
    }
  };

  const handleChegada = async (id: string) => {
    try {
      await api.registrarChegada(id);
      carregarDados();
    } catch (err: any) {
      alert('Erro ao registrar chegada: ' + err.message);
    }
  };

  const handleIniciar = async (id: string) => {
    try {
      await api.iniciarAtendimento(id);
      carregarDados();
    } catch (err: any) {
      alert('Erro ao iniciar atendimento: ' + err.message);
    }
  };

  const handleFinalizar = async (id: string) => {
    try {
      await api.finalizarAtendimento(id);
      carregarDados();
    } catch (err: any) {
      alert('Erro ao finalizar atendimento: ' + err.message);
    }
  };

  // Formatação
  const formatarData = (data: Date) => {
    return new Intl.DateTimeFormat('pt-BR', {
      weekday: 'long',
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    }).format(data);
  };

  const formatarHora = (hora: string) => {
    return hora.substring(0, 5);
  };

  const isHoje = dataAtual.toDateString() === new Date().toDateString();

  return (
    <div className="p-6 pb-8 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg">
            <Calendar className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={cn('text-2xl font-bold', text.primary)}>Agenda</h1>
            <p className={cn('text-sm', text.muted)}>Gerenciar consultas</p>
          </div>
        </div>
        <button
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-xl font-medium transition-all',
            glass.glassSolid,
            'hover:scale-105 active:scale-95'
          )}
        >
          <Plus className="w-4 h-4" />
          Agendar
        </button>
      </div>

      {/* Navegação de Data */}
      <div className={cn('flex items-center justify-between mb-6', glass.glassStrong, 'rounded-2xl p-4')}>
        <div className="flex items-center gap-4">
          <button
            onClick={() => mudarData(-1)}
            className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.secondary)}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="text-center">
            <div className={cn('text-lg font-semibold', text.primary)}>{formatarData(dataAtual)}</div>
            {isHoje && <div className={cn('text-xs mt-1', text.muted)}>Hoje</div>}
          </div>
          <button
            onClick={() => mudarData(1)}
            className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.secondary)}
          >
            <ChevronRight className="w-5 h-5" />
          </button>
          {!isHoje && (
            <button
              onClick={irParaHoje}
              className={cn('ml-4 px-3 py-1 rounded-lg text-sm', glass.glass, 'hover:bg-white/10')}
            >
              Hoje
            </button>
          )}
        </div>

        {/* Filtro de Médicos */}
        <div className="flex items-center gap-2">
          <Filter className={cn('w-4 h-4', text.secondary)} />
          <select
            value={medicosSelecionados.length === 0 ? 'todos' : medicosSelecionados[0] || 'todos'}
            onChange={(e) => {
              const value = e.target.value;
              console.log('🔍 Select mudou para:', value);
              toggleMedico(value);
            }}
            className={cn(
              'px-4 py-2 rounded-xl text-sm font-medium cursor-pointer',
              glass.glassSolid,
              'hover:bg-white/10 transition-colors',
              text.secondary,
              'border-0 outline-none',
              'bg-no-repeat bg-right pr-10',
              isDark
                ? 'bg-[url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%23ffffff\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'/%3E%3C/svg%3E")]'
                : 'bg-[url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' fill=\'none\' viewBox=\'0 0 24 24\' stroke=\'%23000000\'%3E%3Cpath stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M19 9l-7 7-7-7\'/%3E%3C/svg%3E")]'
            )}
            style={{
              minWidth: '220px',
              appearance: 'none',
              WebkitAppearance: 'none',
              MozAppearance: 'none',
              backgroundColor: isDark ? 'rgba(0, 0, 0, 0.6)' : 'rgba(255, 255, 255, 0.8)',
              color: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgb(82, 82, 82)',
            }}
          >
            <option
              value="todos"
              style={{
                backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                color: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgb(82, 82, 82)',
              }}
            >
              Todos os Médicos ({medicos.length})
            </option>
            {medicos.map((medico) => (
              <option
                key={medico.id}
                value={medico.id}
                style={{
                  backgroundColor: isDark ? 'rgba(0, 0, 0, 0.8)' : 'rgba(255, 255, 255, 0.9)',
                  color: isDark ? 'rgba(255, 255, 255, 0.7)' : 'rgb(82, 82, 82)',
                }}
              >
                {medico.nome}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Métricas */}
      {metricas && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <MetricaCard label="Agendados" valor={metricas.total_agendados} cor="blue" glass={glass} text={text} />
          <MetricaCard label="Confirmados" valor={metricas.total_confirmados} cor="green" glass={glass} text={text} />
          <MetricaCard label="Aguardando" valor={metricas.total_aguardando} cor="yellow" glass={glass} text={text} />
          <MetricaCard label="Faltas" valor={metricas.total_faltas} cor="red" glass={glass} text={text} />
          <MetricaCard label="Ocupação" valor={`${metricas.taxa_ocupacao}%`} cor="purple" glass={glass} text={text} />
        </div>
      )}

      {/* Lista de Agendamentos */}
      {loading ? (
        <div className={cn(glass.glassStrong, 'rounded-2xl p-8 text-center')}>
          <div className={cn('text-lg', text.secondary)}>Carregando...</div>
        </div>
      ) : error ? (
        <div className={cn(glass.glassStrong, 'rounded-2xl p-8 text-center')}>
          <AlertCircle className={cn('w-12 h-12 mx-auto mb-4', text.muted)} />
          <div className={cn('text-lg font-semibold mb-2', text.primary)}>Erro ao carregar agenda</div>
          <div className={cn('text-sm', text.muted)}>{error}</div>
        </div>
      ) : agendamentos.length === 0 ? (
        <div className={cn(glass.glassStrong, 'rounded-2xl p-8 text-center')}>
          <Calendar className={cn('w-12 h-12 mx-auto mb-4', text.muted)} />
          <div className={cn('text-lg font-semibold mb-2', text.primary)}>Nenhum agendamento</div>
          <div className={cn('text-sm', text.muted)}>Não há agendamentos para esta data</div>
        </div>
      ) : (
        <div className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className={cn('border-b', isDark ? 'border-white/10' : 'border-gray-200')}>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>HORA</th>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>MÉDICO</th>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>PACIENTE</th>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>TIPO</th>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>STATUS</th>
                  <th className={cn('text-left p-4 font-semibold text-sm', text.secondary)}>AÇÕES</th>
                </tr>
              </thead>
              <tbody>
                {agendamentos.map((ag) => {
                  const statusConfig = STATUS_CONFIG[ag.status] || STATUS_CONFIG.agendado;
                  const StatusIcon = statusConfig.icon;
                  return (
                    <tr
                      key={ag.id}
                      className={cn(
                        'border-b transition-colors hover:bg-white/5',
                        isDark ? 'border-white/5' : 'border-gray-100'
                      )}
                    >
                      <td className="p-4">
                        <div className={cn('font-mono font-semibold', text.primary)}>{formatarHora(ag.hora_inicio)}</div>
                      </td>
                      <td className="p-4">
                        <div className={cn('text-sm', text.secondary)}>{ag.medico_nome}</div>
                      </td>
                      <td className="p-4">
                        <div className={cn('font-medium', text.primary)}>{ag.paciente_nome}</div>
                        <div className={cn('text-xs flex items-center gap-1 mt-1', text.muted)}>
                          <Phone className="w-3 h-3" />
                          {ag.paciente_telefone}
                        </div>
                      </td>
                      <td className="p-4">
                        <div
                          className="inline-flex items-center gap-2 px-2 py-1 rounded-lg text-xs font-medium"
                          style={{ backgroundColor: ag.tipo_consulta_cor + '20', color: ag.tipo_consulta_cor }}
                        >
                          {ag.tipo_consulta_nome}
                        </div>
                      </td>
                      <td className="p-4">
                        <div
                          className={cn(
                            'inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-xs font-medium',
                            statusConfig.color
                          )}
                        >
                          <StatusIcon className="w-3 h-3" />
                          {statusConfig.label}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-1">
                          {ag.status === 'agendado' && (
                            <button
                              onClick={() => handleConfirmar(ag.id)}
                              className={cn('p-1.5 rounded hover:bg-white/10 transition-colors', text.secondary)}
                              title="Confirmar"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                            </button>
                          )}
                          {ag.status === 'confirmado' && (
                            <button
                              onClick={() => handleChegada(ag.id)}
                              className={cn('p-1.5 rounded hover:bg-white/10 transition-colors', text.secondary)}
                              title="Registrar Chegada"
                            >
                              <MapPin className="w-4 h-4" />
                            </button>
                          )}
                          {ag.status === 'aguardando' && (
                            <button
                              onClick={() => handleIniciar(ag.id)}
                              className={cn('p-1.5 rounded hover:bg-white/10 transition-colors', text.secondary)}
                              title="Iniciar Atendimento"
                            >
                              <Play className="w-4 h-4" />
                            </button>
                          )}
                          {ag.status === 'em_atendimento' && (
                            <button
                              onClick={() => handleFinalizar(ag.id)}
                              className={cn('p-1.5 rounded hover:bg-white/10 transition-colors', text.secondary)}
                              title="Finalizar Atendimento"
                            >
                              <Square className="w-4 h-4" />
                            </button>
                          )}
                          {!['atendido', 'cancelado', 'faltou'].includes(ag.status) && (
                            <button
                              onClick={() => handleCancelar(ag.id)}
                              className={cn('p-1.5 rounded hover:bg-white/10 transition-colors text-red-500')}
                              title="Cancelar"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// COMPONENTE: CARDE DE MÉTRICA
// ==========================================

function MetricaCard({
  label,
  valor,
  cor,
  glass,
  text,
}: {
  label: string;
  valor: number | string;
  cor: string;
  glass: any;
  text: any;
}) {
  const cores: Record<string, string> = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    yellow: 'from-yellow-500 to-yellow-600',
    red: 'from-red-500 to-red-600',
    purple: 'from-purple-500 to-purple-600',
  };

  return (
    <div className={cn(glass.glassStrong, 'rounded-2xl p-4')}>
      <div className={cn('text-2xl font-bold mb-1 bg-gradient-to-r', cores[cor], 'bg-clip-text text-transparent')}>
        {valor}
      </div>
      <div className={cn('text-xs font-medium', text.muted)}>{label}</div>
    </div>
  );
}
