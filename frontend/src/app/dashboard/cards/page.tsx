'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  RefreshCw,
  Filter,
  Phone,
  Clock,
  AlertCircle,
  CheckCircle2,
  User,
  Calendar,
  ChevronRight,
  X,
  Target
} from 'lucide-react';
import { api, type CardKanbanResponse, type CardResponse, type ChecklistItem as ApiChecklistItem } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

// ==========================================
// TIPOS
// ==========================================

interface ChecklistResumo {
  total: number;
  concluidos: number;
  obrigatorios_pendentes: number;
}

interface CardListItem {
  id: string;
  paciente_nome?: string;
  paciente_telefone?: string;
  tipo_card: string;
  fase: number;
  status: string;
  prioridade: string;
  cor_alerta?: string;
  data_agendamento?: string;
  hora_agendamento?: string;
  medico_id?: string;
  intencao_inicial?: string;
  em_reativacao: boolean;
  tentativa_reativacao: number;
  ultima_interacao?: string;
  checklist_total: number;
  checklist_concluidos: number;
  checklist_pode_avancar: boolean;
}

interface CardKanban {
  fase: number;
  fase_nome: string;
  cards: CardListItem[];
  total: number;
  em_reativacao: number;
  aguardando_confirmacao: number;
}

interface CardResponse {
  id: string;
  clinica_id: string;
  paciente_id?: string;
  paciente_nome?: string;
  paciente_telefone?: string;
  tipo_card: string;
  fase: number;
  status: string;
  prioridade: string;
  cor_alerta?: string;
  observacoes?: string;
  agendamento_id?: string;
  medico_id?: string;
  data_agendamento?: string;
  hora_agendamento?: string;
  tipo_consulta?: string;
  origem?: string;
  intencao_inicial?: string;
  motivo_saida?: string;
  em_reativacao: boolean;
  tentativa_reativacao: number;
  ultima_interacao?: string;
  convenio_validado: boolean;
  convenio_status?: string;
  no_show: boolean;
  is_derivado: boolean;
  card_origem_id?: string;
  card_derivado_id?: string;
  fase0_em?: string;
  fase1_em?: string;
  fase2_em?: string;
  fase3_em?: string;
  concluido_em?: string;
  created_at: string;
  updated_at: string;
  checklist?: ChecklistResumo;
}

interface ChecklistItem {
  id: string;
  card_id: string;
  fase: number;
  item_key: string;
  descricao: string;
  obrigatorio: boolean;
  concluido: boolean;
  concluido_em?: string;
  concluido_por?: string;
  ordem: number;
}

// ==========================================
// CONSTANTES
// ==========================================

const FASES = [
  { id: 0, nome: 'Pré-Agendamento', icone: '📋', cor: 'bg-blue-500' },
  { id: 1, nome: 'Pré-Consulta', icone: '📅', cor: 'bg-yellow-500' },
  { id: 2, nome: 'Dia da Consulta', icone: '🏥', cor: 'bg-purple-500' },
  { id: 3, nome: 'Pós-Consulta', icone: '✅', cor: 'bg-green-500' },
];

const INTENCOES: Record<string, { label: string; color: string }> = {
  marcar: { label: 'Marcar Consulta', color: 'text-blue-600' },
  saber_valor: { label: 'Saber Valor', color: 'text-green-600' },
  saber_convenio: { label: 'Saber Convênio', color: 'text-purple-600' },
  faq: { label: 'FAQ', color: 'text-gray-600' },
};

// ==========================================
// PÁGINA PRINCIPAL
// ==========================================

export default function CardsPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  const [faseAtual, setFaseAtual] = useState(0);
  const [kanban, setKanban] = useState<CardKanban | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCard, setSelectedCard] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const carregarKanban = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // O backend retorna CardKanban diretamente (fase, fase_nome, cards, total, etc)
      // O tipo CardKanbanResponse no api.ts está desatualizado, então fazemos cast
      const data = await api.getCardsKanban(faseAtual) as unknown as CardKanban;
      console.log('[KANBAN] Dados recebidos:', data);
      setKanban(data);
    } catch (err) {
      console.error('[KANBAN] Erro:', err);
      setError(err instanceof Error ? err.message : 'Erro ao carregar cards');
    } finally {
      setLoading(false);
    }
  }, [faseAtual]);

  useEffect(() => {
    carregarKanban();
  }, [carregarKanban]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await carregarKanban();
    setRefreshing(false);
  };

  const faseConfig = FASES.find(f => f.id === faseAtual) || FASES[0];

  return (
    <div className="p-6 pb-8 overflow-y-auto">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={cn('text-2xl font-bold', text.primary)}>Kanban de Atendimento</h1>
            <p className={cn('text-sm', text.muted)}>Gerencie o fluxo de atendimento dos pacientes</p>
          </div>
        </div>

        {/* Tabs de Fases */}
        <div className={cn(glass.glassStrong, 'rounded-2xl p-4 mb-6')}>
          <div className="flex items-center justify-between mb-4">
            <h2 className={cn('text-lg font-semibold', text.primary)}>Fases do Kanban</h2>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className={cn(
                glass.glass,
                'flex items-center gap-2 px-4 py-2 rounded-lg transition-all hover:bg-white/20',
                text.secondary
              )}
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Atualizar
            </button>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            {FASES.map((fase) => (
              <button
                key={fase.id}
                onClick={() => setFaseAtual(fase.id)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
                  faseAtual === fase.id
                    ? `${fase.cor} text-white shadow-lg`
                    : cn(glass.glass, 'hover:bg-white/20', text.secondary)
                )}
              >
                <span>{fase.icone}</span>
                <span>{fase.nome}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Kanban Board */}
        {loading ? (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-12 flex items-center justify-center')}>
            <div className={cn('flex items-center gap-3', text.secondary)}>
              <RefreshCw className="w-6 h-6 animate-spin" />
              <span>Carregando cards...</span>
            </div>
          </div>
        ) : error ? (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-12 flex items-center justify-center')}>
            <div className="text-center">
              <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-3" />
              <p className={cn('mb-4', text.primary)}>{error}</p>
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-gradient-to-r from-violet-500 to-purple-600 text-white rounded-lg hover:from-violet-600 hover:to-purple-700 transition-all"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        ) : (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-6')}>
            {/* Header da Fase */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{faseConfig.icone}</span>
                <div>
                  <h2 className={cn('text-xl font-bold', text.primary)}>
                    {kanban?.fase_nome || faseConfig.nome}
                  </h2>
                  <p className={cn('text-sm', text.muted)}>
                    {kanban?.total || 0} cards
                    {kanban?.em_reativacao ? ` • ${kanban.em_reativacao} em reativação` : ''}
                  </p>
                </div>
              </div>
            </div>

            {/* Grid de Cards */}
            {kanban?.cards && kanban.cards.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {kanban.cards.map((card) => (
                  <CardItem
                    key={card.id}
                    card={card}
                    onClick={() => setSelectedCard(card.id)}
                    glass={glass}
                    text={text}
                    cn={cn}
                    isDark={isDark}
                  />
                ))}
              </div>
            ) : (
              <div className={cn('text-center py-12', text.muted)}>
                <p className="text-lg">Nenhum card nesta fase</p>
                <p className="text-sm mt-1">Cards aparecerão aqui quando houver pacientes nesta etapa</p>
              </div>
            )}
          </div>
        )}

        {/* Modal de Detalhes */}
        {selectedCard && (
          <CardModal
            cardId={selectedCard}
            onClose={() => setSelectedCard(null)}
            onUpdated={handleRefresh}
          />
        )}
      </div>
    </div>
  );
}

// ==========================================
// COMPONENTE CARD ITEM
// ==========================================

interface CardItemProps {
  card: CardListItem;
  onClick: () => void;
  glass: ReturnType<typeof getGlassStyles>;
  text: ReturnType<typeof getTextStyles>;
  cn: typeof import('@/lib/utils').cn;
  isDark: boolean;
}

function CardItem({ card, onClick, glass, text, cn, isDark }: CardItemProps) {
  const intencaoConfig = card.intencao_inicial
    ? INTENCOES[card.intencao_inicial]
    : null;

  const formatarTempo = (isoString?: string) => {
    if (!isoString) return null;
    const date = new Date(isoString);
    const agora = new Date();
    const diffMs = agora.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHoras = Math.floor(diffMins / 60);
    const diffDias = Math.floor(diffHoras / 24);

    if (diffMins < 60) return `${diffMins}min`;
    if (diffHoras < 24) return `${diffHoras}h`;
    return `${diffDias}d`;
  };

  const prioridadeColor: Record<string, string> = {
    baixa: 'border-l-gray-300',
    normal: 'border-l-blue-400',
    alta: 'border-l-orange-400',
    urgente: 'border-l-red-500',
  };

  const checklistPercentual = card.checklist_total > 0
    ? Math.round((card.checklist_concluidos / card.checklist_total) * 100)
    : 0;

  return (
    <div
      onClick={onClick}
      className={cn(
        glass.glass,
        'rounded-xl border-l-4 p-4 cursor-pointer hover:bg-white/20 transition-all',
        prioridadeColor[card.prioridade] || 'border-l-white/20'
      )}
    >
      {/* Header do Card */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <User className={cn('w-4 h-4', text.muted)} />
          <span className={cn('font-medium truncate max-w-[180px]', text.primary)}>
            {card.paciente_nome || 'Sem nome'}
          </span>
        </div>

        {card.em_reativacao && (
          <span className="text-xs bg-orange-500/20 text-orange-400 px-2 py-0.5 rounded-full border border-orange-500/30">
            Reat. {card.tentativa_reativacao}
          </span>
        )}
      </div>

      {/* Telefone */}
      {card.paciente_telefone && (
        <div className={cn('flex items-center gap-2 text-xs mb-2', text.muted)}>
          <Phone className="w-3 h-3" />
          <span>{card.paciente_telefone}</span>
        </div>
      )}

      {/* Tipo de Card */}
      <div className="mb-2">
        <span className={cn(
          'text-xs px-2 py-0.5 rounded-full',
          card.tipo_card === 'retorno'
            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
            : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
        )}>
          {card.tipo_card === 'retorno' ? 'Retorno' : 'Primeira Consulta'}
        </span>
      </div>

      {/* Intenção */}
      {intencaoConfig && (
        <div className={cn('text-xs mb-2', intencaoConfig.color)}>
          {intencaoConfig.label}
        </div>
      )}

      {/* Data/Hora do Agendamento (se tiver) */}
      {card.data_agendamento && (
        <div className={cn(glass.glass, 'flex items-center gap-2 text-xs mb-2 rounded px-2 py-1', text.secondary)}>
          <Calendar className="w-3 h-3" />
          <span>
            {new Date(card.data_agendamento).toLocaleDateString('pt-BR')}
            {card.hora_agendamento && ` às ${card.hora_agendamento.slice(0, 5)}`}
          </span>
        </div>
      )}

      {/* Checklist Progress */}
      {card.checklist_total > 0 && (
        <div className="mb-2">
          <div className={cn('flex items-center justify-between text-xs mb-1', text.muted)}>
            <span>Checklist</span>
            <span>{card.checklist_concluidos}/{card.checklist_total}</span>
          </div>
          <div className={cn('w-full rounded-full h-1.5', isDark ? 'bg-white/10' : 'bg-black/10')}>
            <div
              className={cn(
                'h-1.5 rounded-full',
                card.checklist_pode_avancar ? 'bg-green-500' : 'bg-blue-500'
              )}
              style={{ width: `${checklistPercentual}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className={cn('flex items-center justify-between pt-2 border-t', isDark ? 'border-white/10' : 'border-black/10')}>
        {/* Pode avançar */}
        {card.checklist_pode_avancar && (
          <div className="flex items-center gap-1 text-xs text-green-400">
            <CheckCircle2 className="w-3 h-3" />
            <span>Pronto</span>
          </div>
        )}

        {/* Última interação */}
        {card.ultima_interacao && (
          <div className={cn('flex items-center gap-1 text-xs ml-auto', text.muted)}>
            <Clock className="w-3 h-3" />
            <span>{formatarTempo(card.ultima_interacao)}</span>
          </div>
        )}
      </div>

      {/* Alerta */}
      {card.cor_alerta && (
        <div
          className="mt-2 h-1 rounded-full"
          style={{ backgroundColor: card.cor_alerta }}
        />
      )}
    </div>
  );
}

// ==========================================
// COMPONENTE CARD MODAL
// ==========================================

interface CardModalProps {
  cardId: string;
  onClose: () => void;
  onUpdated: () => void;
}

function CardModal({ cardId, onClose, onUpdated }: CardModalProps) {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  const [card, setCard] = useState<CardResponse | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'detalhes' | 'checklist'>('detalhes');

  useEffect(() => {
    carregarCard();
  }, [cardId]);

  const carregarCard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [cardData, checklistData] = await Promise.all([
        api.getCard(cardId),
        api.getCardChecklist(cardId).catch(() => []),
      ]);

      // Adaptar tipos se necessário
      setCard(cardData as CardResponse);
      // O backend retorna ChecklistItem com item_key e ordem
      // O tipo do api.ts tem tipo e posicao, então fazemos o mapeamento
      setChecklist(checklistData.map(item => ({
        id: item.id,
        card_id: item.card_id,
        fase: item.fase,
        item_key: (item as any).item_key || item.tipo || '',
        descricao: item.descricao,
        obrigatorio: item.obrigatorio,
        concluido: item.concluido,
        concluido_em: item.concluido_em,
        concluido_por: item.concluido_por_user || (item as any).concluido_por,
        ordem: (item as any).ordem || item.posicao || 0,
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao carregar card');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleChecklist = async (item: ChecklistItem) => {
    try {
      await api.updateChecklistItem(cardId, item.id, !item.concluido);

      setChecklist(prev =>
        prev.map(i => i.id === item.id ? { ...i, concluido: !i.concluido } : i)
      );
      onUpdated();
    } catch (err) {
      console.error('Erro ao atualizar checklist:', err);
    }
  };

  const handleMoverFase = async (novaFase: number) => {
    try {
      // Determinar coluna baseada na fase (simplificado - pode precisar ajuste)
      const colunasPorFase: Record<number, string> = {
        0: 'pre_agendamento',
        1: 'pre_consulta',
        2: 'aguardando_checkin',
        3: 'pendente_documentos',
      };

      await api.moverCard(cardId, {
        coluna: colunasPorFase[novaFase] || 'pre_agendamento',
        posicao: 0,
      });
      onUpdated();
      onClose();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Erro ao mover card');
    }
  };

  if (loading) {
    return (
      <ModalWrapper onClose={onClose} glass={glass} text={text} cn={cn}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className={cn('w-8 h-8 animate-spin', 'text-violet-500')} />
        </div>
      </ModalWrapper>
    );
  }

  if (error || !card) {
    return (
      <ModalWrapper onClose={onClose} glass={glass} text={text} cn={cn}>
        <div className="flex flex-col items-center justify-center h-64">
          <AlertCircle className="w-12 h-12 text-red-500 mb-3" />
          <p className={cn(text.primary)}>{error || 'Card não encontrado'}</p>
        </div>
      </ModalWrapper>
    );
  }

  const faseConfig = FASES.find(f => f.id === card.fase) || FASES[0];

  return (
    <ModalWrapper onClose={onClose} glass={glass} text={text} cn={cn}>
      {/* Header */}
      <div className={cn(glass.glassStrong, 'px-6 py-4 border-b')}>
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <User className={cn('w-5 h-5', text.muted)} />
              <h2 className={cn('text-xl font-bold', text.primary)}>
                {card.paciente_nome || 'Sem nome'}
              </h2>
            </div>
            {card.paciente_telefone && (
              <div className={cn('flex items-center gap-2 text-sm', text.muted)}>
                <Phone className="w-4 h-4" />
                <span>{card.paciente_telefone}</span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className={cn(glass.glass, 'p-2 rounded-lg transition-all hover:bg-white/20')}
          >
            <X className={cn('w-5 h-5', text.muted)} />
          </button>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2 mt-3">
          <span className={cn('px-3 py-1 rounded-full text-sm font-medium', faseConfig.cor, 'text-white')}>
            {faseConfig.icone} {faseConfig.nome}
          </span>
          <span className={cn(
            'px-3 py-1 rounded-full text-sm font-medium',
            card.tipo_card === 'retorno'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
              : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          )}>
            {card.tipo_card === 'retorno' ? 'Retorno' : 'Primeira Consulta'}
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className={cn('flex border-b', isDark ? 'border-white/10' : 'border-black/10')}>
        <button
          onClick={() => setActiveTab('detalhes')}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'detalhes'
              ? 'border-violet-500 text-violet-400'
              : cn('border-transparent', text.muted, 'hover:' + text.secondary)
          )}
        >
          Detalhes
        </button>
        <button
          onClick={() => setActiveTab('checklist')}
          className={cn(
            'px-4 py-3 text-sm font-medium border-b-2 transition-colors',
            activeTab === 'checklist'
              ? 'border-violet-500 text-violet-400'
              : cn('border-transparent', text.muted, 'hover:' + text.secondary)
          )}
        >
          Checklist ({checklist.filter(c => c.concluido).length}/{checklist.length})
        </button>
      </div>

      {/* Content */}
      <div className={cn('p-6 overflow-y-auto max-h-[60vh]', glass.glass)}>
        {activeTab === 'detalhes' && (
          <div className="space-y-6">
            {/* Ações - Mover Fase */}
            <div>
              <h4 className={cn('font-medium mb-2', text.primary)}>Mover para Fase</h4>
              <div className="flex gap-2 flex-wrap">
                {FASES.map((fase) => (
                  <button
                    key={fase.id}
                    onClick={() => handleMoverFase(fase.id)}
                    disabled={fase.id === card.fase}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-1 transition-all',
                      fase.id === card.fase
                        ? cn(glass.glass, text.muted, 'cursor-not-allowed')
                        : cn(fase.cor, 'text-white hover:opacity-90')
                    )}
                  >
                    <span>{fase.icone}</span>
                    <span>{fase.nome}</span>
                    {fase.id === card.fase && <span className="text-xs">(atual)</span>}
                  </button>
                ))}
              </div>
            </div>

            {/* Info do Agendamento */}
            {card.data_agendamento && (
              <div className={cn(glass.glass, 'rounded-lg p-4')}>
                <h4 className={cn('font-medium mb-2 flex items-center gap-2', text.primary)}>
                  <Calendar className="w-4 h-4" />
                  Consulta Agendada
                </h4>
                <div className={cn('grid grid-cols-2 gap-4 text-sm', text.secondary)}>
                  <div>
                    <span>Data:</span>
                    <span className="ml-2">
                      {new Date(card.data_agendamento).toLocaleDateString('pt-BR')}
                    </span>
                  </div>
                  {card.hora_agendamento && (
                    <div>
                      <span>Hora:</span>
                      <span className="ml-2">{card.hora_agendamento}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Grid de Informações */}
            <div className="grid grid-cols-2 gap-4">
              <InfoItem label="Status" value={card.status} text={text} cn={cn} />
              <InfoItem label="Prioridade" value={card.prioridade} text={text} cn={cn} />
              <InfoItem label="Origem" value={card.origem || '-'} text={text} cn={cn} />
              {card.intencao_inicial && (
                <InfoItem label="Intenção" value={card.intencao_inicial} text={text} cn={cn} />
              )}
              {card.convenio_status && (
                <InfoItem label="Convênio" value={card.convenio_status} text={text} cn={cn} />
              )}
              {card.motivo_saida && (
                <InfoItem label="Motivo Saída" value={card.motivo_saida} text={text} cn={cn} />
              )}
            </div>

            {/* Timestamps */}
            <div className={cn('border-t pt-4', isDark ? 'border-white/10' : 'border-black/10')}>
              <h4 className={cn('font-medium mb-3', text.primary)}>Linha do Tempo</h4>
              <div className={cn('space-y-2 text-sm', text.secondary)}>
                <TimelineItem label="Criado em" date={card.created_at} text={text} cn={cn} />
                {card.fase0_em && <TimelineItem label="Fase 0" date={card.fase0_em} text={text} cn={cn} />}
                {card.fase1_em && <TimelineItem label="Fase 1" date={card.fase1_em} text={text} cn={cn} />}
                {card.fase2_em && <TimelineItem label="Fase 2" date={card.fase2_em} text={text} cn={cn} />}
                {card.fase3_em && <TimelineItem label="Fase 3" date={card.fase3_em} text={text} cn={cn} />}
                {card.concluido_em && <TimelineItem label="Concluído" date={card.concluido_em} text={text} cn={cn} />}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'checklist' && (
          <div className="space-y-2">
            {checklist.length === 0 ? (
              <div className={cn('text-center py-8', text.muted)}>
                Nenhum item no checklist
              </div>
            ) : (
              checklist.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleToggleChecklist(item)}
                  className={cn(
                    glass.glass,
                    'flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all hover:bg-white/20'
                  )}
                >
                  {item.concluido ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400 flex-shrink-0" />
                  ) : (
                    <div className={cn('w-5 h-5 border-2 rounded-full flex-shrink-0', isDark ? 'border-white/30' : 'border-black/30')} />
                  )}
                  <div className="flex-1">
                    <p className={cn(
                      'font-medium',
                      item.concluido ? 'text-green-400 line-through' : text.primary
                    )}>
                      {item.descricao}
                    </p>
                    {item.obrigatorio && !item.concluido && (
                      <span className="text-xs text-orange-400">Obrigatório</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </ModalWrapper>
  );
}

// ==========================================
// COMPONENTES AUXILIARES
// ==========================================

function ModalWrapper({
  children,
  onClose,
  glass,
  text,
  cn
}: {
  children: React.ReactNode;
  onClose: () => void;
  glass: ReturnType<typeof getGlassStyles>;
  text: ReturnType<typeof getTextStyles>;
  cn: typeof import('@/lib/utils').cn;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className={cn(glass.glassSolid, 'relative rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden border')}>
        {children}
      </div>
    </div>
  );
}

function InfoItem({
  label,
  value,
  text,
  cn
}: {
  label: string;
  value: string;
  text: ReturnType<typeof getTextStyles>;
  cn: typeof import('@/lib/utils').cn;
}) {
  return (
    <div>
      <span className={cn('text-xs uppercase tracking-wide', text.muted)}>{label}</span>
      <p className={cn('font-medium capitalize', text.primary)}>{value}</p>
    </div>
  );
}

function TimelineItem({
  label,
  date,
  text,
  cn
}: {
  label: string;
  date?: string;
  text: ReturnType<typeof getTextStyles>;
  cn: typeof import('@/lib/utils').cn;
}) {
  if (!date) return null;

  return (
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 bg-violet-400 rounded-full" />
      <span className={cn('w-24', text.muted)}>{label}</span>
      <span className={text.primary}>
        {new Date(date).toLocaleString('pt-BR')}
      </span>
    </div>
  );
}
