'use client';

import { useState, useEffect } from 'react';
import {
  api,
  CardResponse,
  ChecklistItem,
  CardHistoricoItem,
  COLUNAS_POR_FASE,
  INTENCOES
} from '@/lib/api';
import {
  X,
  User,
  Phone,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  History,
  FileText,
  MessageSquare,
  ChevronRight,
  AlertCircle,
  RefreshCw,
  Edit2,
  Move
} from 'lucide-react';

interface CardModalProps {
  cardId: string;
  onClose: () => void;
  onUpdated: () => void;
}

type TabType = 'detalhes' | 'checklist' | 'historico' | 'mensagens';

export function CardModal({ cardId, onClose, onUpdated }: CardModalProps) {
  const [card, setCard] = useState<CardResponse | null>(null);
  const [checklist, setChecklist] = useState<ChecklistItem[]>([]);
  const [historico, setHistorico] = useState<CardHistoricoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('detalhes');
  const [showMoveModal, setShowMoveModal] = useState(false);

  useEffect(() => {
    carregarCard();
  }, [cardId]);

  const carregarCard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [cardData, checklistData, historicoData] = await Promise.all([
        api.getCard(cardId),
        api.getCardChecklist(cardId).catch(() => []),
        api.getCardHistorico(cardId).catch(() => []),
      ]);

      setCard(cardData);
      setChecklist(checklistData);
      setHistorico(historicoData);
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

  const handleMoveCard = async (novaColuna: string) => {
    try {
      await api.moverCard(cardId, { coluna: novaColuna });
      await carregarCard();
      onUpdated();
      setShowMoveModal(false);
    } catch (err) {
      console.error('Erro ao mover card:', err);
    }
  };

  if (loading) {
    return (
      <ModalWrapper onClose={onClose}>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
        </div>
      </ModalWrapper>
    );
  }

  if (error || !card) {
    return (
      <ModalWrapper onClose={onClose}>
        <div className="flex flex-col items-center justify-center h-64">
          <AlertCircle className="w-12 h-12 text-red-500 mb-3" />
          <p className="text-gray-600">{error || 'Card não encontrado'}</p>
        </div>
      </ModalWrapper>
    );
  }

  const colunaConfig = COLUNAS_POR_FASE[card.fase]?.[card.coluna];
  const intencaoConfig = card.intencao_inicial
    ? INTENCOES[card.intencao_inicial as keyof typeof INTENCOES]
    : null;

  return (
    <ModalWrapper onClose={onClose}>
      {/* Header */}
      <div className="px-6 py-4 border-b bg-gray-50">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <User className="w-5 h-5 text-gray-400" />
              <h2 className="text-xl font-bold text-gray-900">
                {card.paciente_nome || 'Sem nome'}
              </h2>
            </div>
            {card.paciente_telefone && (
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <Phone className="w-4 h-4" />
                <span>{card.paciente_telefone}</span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Status Badge */}
        <div className="flex items-center gap-2 mt-3">
          {colunaConfig && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${colunaConfig.color} text-gray-700`}>
              {colunaConfig.label}
            </span>
          )}
          {intencaoConfig && (
            <span className={`px-3 py-1 rounded-full text-sm font-medium bg-gray-100 ${intencaoConfig.color}`}>
              {intencaoConfig.label}
            </span>
          )}
          {card.tentativa_reativacao > 0 && (
            <span className="px-3 py-1 rounded-full text-sm font-medium bg-orange-100 text-orange-700">
              Reativação {card.tentativa_reativacao}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {[
          { id: 'detalhes', label: 'Detalhes', icon: FileText },
          { id: 'checklist', label: 'Checklist', icon: CheckCircle2 },
          { id: 'historico', label: 'Histórico', icon: History },
          { id: 'mensagens', label: 'Mensagens', icon: MessageSquare },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as TabType)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 overflow-y-auto max-h-[60vh]">
        {activeTab === 'detalhes' && (
          <TabDetalhes card={card} onMoveClick={() => setShowMoveModal(true)} />
        )}
        {activeTab === 'checklist' && (
          <TabChecklist checklist={checklist} onToggle={handleToggleChecklist} />
        )}
        {activeTab === 'historico' && (
          <TabHistorico historico={historico} />
        )}
        {activeTab === 'mensagens' && (
          <TabMensagens cardId={cardId} />
        )}
      </div>

      {/* Move Modal */}
      {showMoveModal && (
        <MoveCardModal
          card={card}
          onClose={() => setShowMoveModal(false)}
          onMove={handleMoveCard}
        />
      )}
    </ModalWrapper>
  );
}

// ==========================================
// Wrapper do Modal
// ==========================================

function ModalWrapper({ children, onClose }: { children: React.ReactNode; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/50"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
        {children}
      </div>
    </div>
  );
}

// ==========================================
// Tab Detalhes
// ==========================================

function TabDetalhes({ card, onMoveClick }: { card: CardResponse; onMoveClick: () => void }) {
  return (
    <div className="space-y-6">
      {/* Ações */}
      <div className="flex gap-2">
        <button
          onClick={onMoveClick}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Move className="w-4 h-4" />
          Mover Card
        </button>
        <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
          <Edit2 className="w-4 h-4" />
          Editar
        </button>
      </div>

      {/* Informações do Agendamento */}
      {card.data_agendamento && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2 flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            Consulta Agendada
          </h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-blue-600">Data:</span>
              <span className="ml-2 text-blue-900">
                {new Date(card.data_agendamento).toLocaleDateString('pt-BR')}
              </span>
            </div>
            {card.hora_agendamento && (
              <div>
                <span className="text-blue-600">Hora:</span>
                <span className="ml-2 text-blue-900">{card.hora_agendamento.slice(0, 5)}</span>
              </div>
            )}
            {card.tipo_consulta && (
              <div>
                <span className="text-blue-600">Tipo:</span>
                <span className="ml-2 text-blue-900">{card.tipo_consulta}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Grid de Informações */}
      <div className="grid grid-cols-2 gap-4">
        <InfoItem label="Status" value={card.status} />
        <InfoItem label="Prioridade" value={card.prioridade} />
        <InfoItem label="Origem" value={card.origem || '-'} />
        <InfoItem label="Fase" value={`Fase ${card.fase}`} />
        {card.convenio_status && (
          <InfoItem label="Convênio" value={card.convenio_status} />
        )}
        {card.motivo_saida && (
          <InfoItem label="Motivo Saída" value={card.motivo_saida} />
        )}
      </div>

      {/* Timestamps */}
      <div className="border-t pt-4">
        <h4 className="font-medium text-gray-900 mb-3">Linha do Tempo</h4>
        <div className="space-y-2 text-sm">
          <TimelineItem
            label="Criado em"
            date={card.created_at}
          />
          {card.fase0_em && (
            <TimelineItem
              label="Fase 0 em"
              date={card.fase0_em}
            />
          )}
          {card.fase1_em && (
            <TimelineItem
              label="Fase 1 em"
              date={card.fase1_em}
            />
          )}
          {card.fase2_em && (
            <TimelineItem
              label="Fase 2 em"
              date={card.fase2_em}
            />
          )}
          {card.fase3_em && (
            <TimelineItem
              label="Fase 3 em"
              date={card.fase3_em}
            />
          )}
          {card.concluido_em && (
            <TimelineItem
              label="Concluído em"
              date={card.concluido_em}
            />
          )}
          <TimelineItem
            label="Última interação"
            date={card.ultima_interacao}
          />
        </div>
      </div>

      {/* Observações */}
      {card.observacoes && (
        <div className="border-t pt-4">
          <h4 className="font-medium text-gray-900 mb-2">Observações</h4>
          <p className="text-gray-600 text-sm">{card.observacoes}</p>
        </div>
      )}
    </div>
  );
}

function InfoItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span className="text-xs text-gray-500 uppercase tracking-wide">{label}</span>
      <p className="text-gray-900 font-medium capitalize">{value}</p>
    </div>
  );
}

function TimelineItem({ label, date }: { label: string; date?: string }) {
  if (!date) return null;

  return (
    <div className="flex items-center gap-3">
      <div className="w-2 h-2 bg-blue-400 rounded-full" />
      <span className="text-gray-500 w-32">{label}</span>
      <span className="text-gray-900">
        {new Date(date).toLocaleString('pt-BR')}
      </span>
    </div>
  );
}

// ==========================================
// Tab Checklist
// ==========================================

function TabChecklist({
  checklist,
  onToggle
}: {
  checklist: ChecklistItem[];
  onToggle: (item: ChecklistItem) => void;
}) {
  if (checklist.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>Nenhum item no checklist</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {checklist.map((item) => (
        <div
          key={item.id}
          onClick={() => onToggle(item)}
          className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
            item.concluido
              ? 'bg-green-50 hover:bg-green-100'
              : 'bg-gray-50 hover:bg-gray-100'
          }`}
        >
          {item.concluido ? (
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
          ) : (
            <Circle className="w-5 h-5 text-gray-400 flex-shrink-0" />
          )}
          <div className="flex-1">
            <p className={`font-medium ${item.concluido ? 'text-green-800 line-through' : 'text-gray-900'}`}>
              {item.descricao}
            </p>
            {item.obrigatorio && (
              <span className="text-xs text-orange-600">Obrigatório</span>
            )}
          </div>
          {item.concluido && item.concluido_em && (
            <span className="text-xs text-gray-400">
              {new Date(item.concluido_em).toLocaleDateString('pt-BR')}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

// ==========================================
// Tab Histórico
// ==========================================

function TabHistorico({ historico }: { historico: CardHistoricoItem[] }) {
  if (historico.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <History className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>Nenhum evento no histórico</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {historico.map((item) => (
        <div key={item.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <div className="w-3 h-3 bg-blue-400 rounded-full" />
            <div className="w-0.5 h-full bg-gray-200" />
          </div>
          <div className="pb-4">
            <p className="font-medium text-gray-900">{item.descricao}</p>
            <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
              <span>{new Date(item.created_at).toLocaleString('pt-BR')}</span>
              {item.user_nome && (
                <>
                  <span>•</span>
                  <span>{item.user_nome}</span>
                </>
              )}
              {item.automatico && (
                <>
                  <span>•</span>
                  <span className="text-blue-600">Automático</span>
                </>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

// ==========================================
// Tab Mensagens
// ==========================================

function TabMensagens({ cardId }: { cardId: string }) {
  const [mensagens, setMensagens] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const carregar = async () => {
      try {
        const data = await api.getCardMensagens(cardId);
        setMensagens(data);
      } catch (err) {
        console.error('Erro ao carregar mensagens:', err);
      } finally {
        setLoading(false);
      }
    };
    carregar();
  }, [cardId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <RefreshCw className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (mensagens.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <MessageSquare className="w-12 h-12 mx-auto mb-3 text-gray-300" />
        <p>Nenhuma mensagem registrada</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {mensagens.map((msg) => (
        <div
          key={msg.id}
          className={`p-3 rounded-lg ${
            msg.direcao === 'entrada'
              ? 'bg-gray-100 mr-8'
              : 'bg-blue-100 ml-8'
          }`}
        >
          <p className="text-sm text-gray-900">{msg.conteudo}</p>
          <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
            <span>{msg.canal}</span>
            <span>•</span>
            <span>{new Date(msg.created_at).toLocaleString('pt-BR')}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

// ==========================================
// Modal de Mover Card
// ==========================================

function MoveCardModal({
  card,
  onClose,
  onMove
}: {
  card: CardResponse;
  onClose: () => void;
  onMove: (coluna: string) => void;
}) {
  const colunas = COLUNAS_POR_FASE[card.fase] || {};

  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative bg-white rounded-xl shadow-xl p-6 w-80">
        <h3 className="font-bold text-lg mb-4">Mover para</h3>
        <div className="space-y-2">
          {Object.entries(colunas).map(([colunaId, config]) => (
            <button
              key={colunaId}
              onClick={() => onMove(colunaId)}
              disabled={colunaId === card.coluna}
              className={`w-full text-left px-4 py-3 rounded-lg flex items-center justify-between transition-colors ${
                colunaId === card.coluna
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : `${config.color} hover:opacity-80`
              }`}
            >
              <span className="font-medium">{config.label}</span>
              {colunaId === card.coluna && (
                <span className="text-xs">Atual</span>
              )}
              {colunaId !== card.coluna && (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="w-full mt-4 px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
