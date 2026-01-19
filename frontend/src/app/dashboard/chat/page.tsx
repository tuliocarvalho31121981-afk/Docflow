'use client';

import { useState, useRef, useEffect } from 'react';
import { 
  MessageCircle, Send, User, Bot, CheckCircle, XCircle, 
  AlertCircle, Clock, Zap, Plus, RefreshCw, ExternalLink,
  Phone, ChevronRight, Sparkles, Activity, Shield
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';
import { api, ChatResponse } from '@/lib/api';

// Tipos
interface Mensagem {
  id: string;
  tipo: 'paciente' | 'sistema';
  conteudo: string;
  timestamp: Date;
  interpretacao?: ChatResponse['interpretacao'];
  acoes?: ChatResponse['acoes'];
  tempoMs?: number;
  validacaoId?: string;
}

interface PacienteSimulado {
  nome: string;
  telefone: string;
}

// Pacientes de exemplo para simulação
const PACIENTES_EXEMPLO: PacienteSimulado[] = [
  { nome: 'Maria Silva', telefone: '11999887766' },
  { nome: 'João Santos', telefone: '11988776655' },
  { nome: 'Ana Oliveira', telefone: '11977665544' },
];

// Mensagens de exemplo para teste rápido
const MENSAGENS_EXEMPLO = [
  'Oi, quero marcar uma consulta',
  'Quero agendar para segunda-feira às 14h',
  'Confirmo minha consulta',
  'Preciso cancelar minha consulta',
  'Cheguei na clínica',
  'Qual o endereço da clínica?',
  'Quanto custa a consulta?',
];

export default function SimuladorPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);
  
  // Estado
  const [paciente, setPaciente] = useState<PacienteSimulado>(PACIENTES_EXEMPLO[0]);
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [inputMensagem, setInputMensagem] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [ultimaResposta, setUltimaResposta] = useState<ChatResponse | null>(null);
  const [llmProvider, setLlmProvider] = useState<string>('...');
  const [mostrarNovoPaciente, setMostrarNovoPaciente] = useState(false);
  const [novoPaciente, setNovoPaciente] = useState({ nome: '', telefone: '' });
  const [erro, setErro] = useState<string | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Scroll para última mensagem
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensagens]);

  // Buscar config do LLM
  useEffect(() => {
    api.getLLMConfig()
      .then(config => setLlmProvider(config.provider))
      .catch(() => setLlmProvider('não conectado'));
  }, []);

  // Enviar mensagem
  const enviarMensagem = async () => {
    if (!inputMensagem.trim() || enviando) return;

    setErro(null);
    const msgPaciente: Mensagem = {
      id: Date.now().toString(),
      tipo: 'paciente',
      conteudo: inputMensagem,
      timestamp: new Date(),
    };

    setMensagens(prev => [...prev, msgPaciente]);
    setInputMensagem('');
    setEnviando(true);

    try {
      const response = await api.enviarMensagemSimulador(
        paciente.telefone,
        inputMensagem,
        paciente.nome
      );

      const msgSistema: Mensagem = {
        id: response.id,
        tipo: 'sistema',
        conteudo: response.resposta,
        timestamp: new Date(),
        interpretacao: response.interpretacao,
        acoes: response.acoes,
        tempoMs: response.tempo_processamento_ms,
        validacaoId: response.validacao_id,
      };

      setMensagens(prev => [...prev, msgSistema]);
      setUltimaResposta(response);
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Falha ao processar';
      setErro(errorMsg);
      const msgErro: Mensagem = {
        id: Date.now().toString(),
        tipo: 'sistema',
        conteudo: `❌ Erro ao processar. Verifique se o backend está rodando.`,
        timestamp: new Date(),
      };
      setMensagens(prev => [...prev, msgErro]);
    } finally {
      setEnviando(false);
      inputRef.current?.focus();
    }
  };

  // Limpar chat
  const limparChat = () => {
    setMensagens([]);
    setUltimaResposta(null);
    setErro(null);
  };

  // Adicionar novo paciente
  const adicionarPaciente = () => {
    if (novoPaciente.nome && novoPaciente.telefone) {
      const novo = { ...novoPaciente };
      PACIENTES_EXEMPLO.push(novo);
      setPaciente(novo);
      setNovoPaciente({ nome: '', telefone: '' });
      setMostrarNovoPaciente(false);
      limparChat();
    }
  };

  // Cor do badge de confiança
  const getConfiancaColor = (confianca: number) => {
    if (confianca >= 80) return 'text-green-400 bg-green-500/20';
    if (confianca >= 60) return 'text-yellow-400 bg-yellow-500/20';
    return 'text-red-400 bg-red-500/20';
  };

  // Cor do badge de intenção
  const getIntencaoColor = (intencao: string) => {
    const colors: Record<string, string> = {
      AGENDAR: 'bg-blue-500/20 text-blue-400',
      CONFIRMAR: 'bg-green-500/20 text-green-400',
      CANCELAR: 'bg-red-500/20 text-red-400',
      REMARCAR: 'bg-orange-500/20 text-orange-400',
      CHECK_IN: 'bg-purple-500/20 text-purple-400',
      INFORMACAO: 'bg-cyan-500/20 text-cyan-400',
      SAUDACAO: 'bg-pink-500/20 text-pink-400',
      DESPEDIDA: 'bg-gray-500/20 text-gray-400',
      DESCONHECIDO: 'bg-gray-500/20 text-gray-400',
    };
    return colors[intencao] || 'bg-gray-500/20 text-gray-400';
  };

  return (
    <div className="p-6 h-[calc(100vh-120px)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
            <MessageCircle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={cn('text-2xl font-bold', text.primary)}>Simulador de Chat</h1>
            <p className={cn('text-sm', text.muted)}>
              Teste o atendimento automático • LLM: <span className="text-violet-400">{llmProvider}</span>
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={limparChat}
            className={cn(glass.glass, 'px-3 py-2 rounded-xl flex items-center gap-2 hover:bg-white/10 transition-colors')}
          >
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Limpar</span>
          </button>
        </div>
      </div>

      {/* Erro de conexão */}
      {erro && (
        <div className="mb-4 p-3 bg-red-500/20 border border-red-500/30 rounded-xl flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-400" />
          <span className="text-sm text-red-200">{erro}</span>
          <button onClick={() => setErro(null)} className="ml-auto text-red-400 hover:text-red-300">
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Seletor de Paciente */}
      <div className={cn(glass.glass, 'rounded-2xl p-4 mb-4')}>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-violet-400" />
            <span className={cn('text-sm font-medium', text.secondary)}>Simulando como:</span>
          </div>
          
          <div className="flex gap-2 flex-wrap">
            {PACIENTES_EXEMPLO.map((p) => (
              <button
                key={p.telefone}
                onClick={() => { setPaciente(p); limparChat(); }}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm transition-all',
                  paciente.telefone === p.telefone
                    ? 'bg-violet-500/30 text-violet-300 ring-1 ring-violet-500/50'
                    : 'bg-white/5 text-white/60 hover:bg-white/10'
                )}
              >
                {p.nome}
              </button>
            ))}
            
            <button
              onClick={() => setMostrarNovoPaciente(!mostrarNovoPaciente)}
              className="px-3 py-1.5 rounded-lg text-sm bg-white/5 text-white/60 hover:bg-white/10 flex items-center gap-1"
            >
              <Plus className="w-4 h-4" />
              Novo
            </button>
          </div>

          <div className={cn('flex items-center gap-2 ml-auto', text.muted)}>
            <Phone className="w-4 h-4" />
            <span className="text-sm font-mono">{paciente.telefone}</span>
          </div>
        </div>

        {/* Form novo paciente */}
        {mostrarNovoPaciente && (
          <div className="mt-4 pt-4 border-t border-white/10 flex gap-3">
            <input
              type="text"
              placeholder="Nome"
              value={novoPaciente.nome}
              onChange={(e) => setNovoPaciente(p => ({ ...p, nome: e.target.value }))}
              className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30"
            />
            <input
              type="text"
              placeholder="Telefone (só números)"
              value={novoPaciente.telefone}
              onChange={(e) => setNovoPaciente(p => ({ ...p, telefone: e.target.value.replace(/\D/g, '') }))}
              className="flex-1 bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/30"
            />
            <button
              onClick={adicionarPaciente}
              className="px-4 py-2 bg-violet-500 hover:bg-violet-600 rounded-lg text-sm font-medium transition-colors"
            >
              Adicionar
            </button>
          </div>
        )}
      </div>

      {/* Main Content - Split View */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 h-[calc(100%-180px)]">
        
        {/* Painel Esquerdo - Chat do Paciente */}
        <div className={cn(glass.glassStrong, 'rounded-2xl flex flex-col overflow-hidden')}>
          <div className="p-4 border-b border-white/10">
            <h2 className={cn('font-semibold flex items-center gap-2', text.primary)}>
              <User className="w-5 h-5 text-green-400" />
              Visão do Paciente
            </h2>
            <p className={cn('text-xs mt-1', text.muted)}>Simule mensagens como se fosse o paciente</p>
          </div>

          {/* Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {mensagens.length === 0 ? (
              <div className="text-center py-8">
                <MessageCircle className="w-12 h-12 mx-auto text-white/20 mb-3" />
                <p className={cn('text-sm', text.muted)}>Envie uma mensagem para começar</p>
                
                {/* Sugestões */}
                <div className="mt-4 space-y-2">
                  <p className={cn('text-xs', text.muted)}>Sugestões:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {MENSAGENS_EXEMPLO.slice(0, 4).map((msg, i) => (
                      <button
                        key={i}
                        onClick={() => setInputMensagem(msg)}
                        className="px-3 py-1 bg-white/5 hover:bg-white/10 rounded-full text-xs text-white/60 transition-colors"
                      >
                        {msg}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              mensagens.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    'max-w-[85%] rounded-2xl p-3',
                    msg.tipo === 'paciente'
                      ? 'ml-auto bg-violet-500/30 rounded-br-sm'
                      : 'mr-auto bg-white/10 rounded-bl-sm'
                  )}
                >
                  <p className="text-sm text-white">{msg.conteudo}</p>
                  <p className={cn('text-xs mt-1', text.muted)}>
                    {msg.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    {msg.tempoMs && (
                      <span className="ml-2 text-violet-400">• {msg.tempoMs}ms</span>
                    )}
                  </p>
                </div>
              ))
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-white/10">
            <div className="flex gap-2">
              <input
                ref={inputRef}
                type="text"
                value={inputMensagem}
                onChange={(e) => setInputMensagem(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && enviarMensagem()}
                placeholder="Digite como paciente..."
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder:text-white/30 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
                disabled={enviando}
              />
              <button
                onClick={enviarMensagem}
                disabled={enviando || !inputMensagem.trim()}
                className={cn(
                  'px-4 py-3 rounded-xl font-medium transition-all flex items-center gap-2',
                  enviando || !inputMensagem.trim()
                    ? 'bg-white/10 text-white/30 cursor-not-allowed'
                    : 'bg-violet-500 hover:bg-violet-600 text-white'
                )}
              >
                {enviando ? (
                  <RefreshCw className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            
            {/* Sugestões rápidas */}
            <div className="flex gap-2 mt-2 overflow-x-auto pb-1">
              {MENSAGENS_EXEMPLO.map((msg, i) => (
                <button
                  key={i}
                  onClick={() => setInputMensagem(msg)}
                  className="px-2 py-1 bg-white/5 hover:bg-white/10 rounded-lg text-xs text-white/50 whitespace-nowrap transition-colors"
                >
                  {msg}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Painel Direito - Visão do Sistema */}
        <div className={cn(glass.glassStrong, 'rounded-2xl flex flex-col overflow-hidden')}>
          <div className="p-4 border-b border-white/10">
            <h2 className={cn('font-semibold flex items-center gap-2', text.primary)}>
              <Bot className="w-5 h-5 text-blue-400" />
              Visão do Sistema
            </h2>
            <p className={cn('text-xs mt-1', text.muted)}>Veja como o sistema interpretou e reagiu</p>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {!ultimaResposta ? (
              <div className="text-center py-8">
                <Sparkles className="w-12 h-12 mx-auto text-white/20 mb-3" />
                <p className={cn('text-sm', text.muted)}>Aguardando processamento...</p>
                <p className={cn('text-xs mt-2', text.muted)}>
                  Envie uma mensagem para ver a interpretação do sistema
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Interpretação */}
                <div className={cn(glass.glass, 'rounded-xl p-4')}>
                  <h3 className={cn('text-sm font-semibold mb-3 flex items-center gap-2', text.primary)}>
                    <Sparkles className="w-4 h-4 text-yellow-400" />
                    Interpretação (LLM)
                  </h3>
                  
                  <div className="space-y-3">
                    {/* Intenção */}
                    <div className="flex items-center justify-between">
                      <span className={cn('text-sm', text.muted)}>Intenção:</span>
                      <span className={cn('px-3 py-1 rounded-full text-sm font-medium', getIntencaoColor(ultimaResposta.interpretacao.intencao))}>
                        {ultimaResposta.interpretacao.intencao}
                      </span>
                    </div>
                    
                    {/* Confiança */}
                    <div className="flex items-center justify-between">
                      <span className={cn('text-sm', text.muted)}>Confiança:</span>
                      <span className={cn('px-3 py-1 rounded-full text-sm font-medium', getConfiancaColor(ultimaResposta.interpretacao.confianca))}>
                        {ultimaResposta.interpretacao.confianca}%
                      </span>
                    </div>
                    
                    {/* Dados Extraídos */}
                    {Object.entries(ultimaResposta.interpretacao.dados || {}).some(([_, v]) => v) && (
                      <div>
                        <span className={cn('text-sm', text.muted)}>Dados extraídos:</span>
                        <div className="mt-2 space-y-1">
                          {Object.entries(ultimaResposta.interpretacao.dados).map(([key, value]) => (
                            value && (
                              <div key={key} className="flex items-center gap-2 text-sm">
                                <ChevronRight className="w-3 h-3 text-violet-400" />
                                <span className="text-white/50">{key}:</span>
                                <span className="text-white">{String(value)}</span>
                              </div>
                            )
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Requer mais info */}
                    {ultimaResposta.interpretacao.requer_mais_info && (
                      <div className="flex items-start gap-2 p-2 bg-yellow-500/10 rounded-lg">
                        <AlertCircle className="w-4 h-4 text-yellow-400 mt-0.5" />
                        <span className="text-sm text-yellow-200">
                          Precisa de mais informações
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Ações Executadas */}
                {ultimaResposta.acoes && ultimaResposta.acoes.length > 0 && (
                  <div className={cn(glass.glass, 'rounded-xl p-4')}>
                    <h3 className={cn('text-sm font-semibold mb-3 flex items-center gap-2', text.primary)}>
                      <Activity className="w-4 h-4 text-green-400" />
                      Ações Executadas
                    </h3>
                    
                    <div className="space-y-2">
                      {ultimaResposta.acoes.map((acao, i) => (
                        <div key={i} className="flex items-start gap-2">
                          {acao.sucesso ? (
                            <CheckCircle className="w-4 h-4 text-green-400 mt-0.5" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400 mt-0.5" />
                          )}
                          <div className="flex-1 min-w-0">
                            <span className="text-sm text-white">{acao.tipo}</span>
                            {acao.detalhes && Object.keys(acao.detalhes).length > 0 && (
                              <div className="text-xs text-white/50 mt-1 truncate">
                                {JSON.stringify(acao.detalhes, null, 0).slice(0, 80)}
                                {JSON.stringify(acao.detalhes).length > 80 && '...'}
                              </div>
                            )}
                            {acao.erro && (
                              <div className="text-xs text-red-400 mt-1">{acao.erro}</div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Governança */}
                <div className={cn(glass.glass, 'rounded-xl p-4')}>
                  <h3 className={cn('text-sm font-semibold mb-3 flex items-center gap-2', text.primary)}>
                    <Shield className="w-4 h-4 text-violet-400" />
                    Governança
                  </h3>
                  
                  {ultimaResposta.validacao_pendente ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse" />
                        <span className="text-sm text-yellow-200">Validação pendente criada</span>
                      </div>
                      <a
                        href="/dashboard/governanca"
                        className="flex items-center gap-2 text-sm text-violet-400 hover:text-violet-300 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        Ver na Governança
                      </a>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-white/50">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm">Sem validação (saudação/despedida)</span>
                    </div>
                  )}
                </div>

                {/* Tempo */}
                <div className="flex items-center justify-center gap-2 text-white/40 text-sm">
                  <Clock className="w-4 h-4" />
                  Processado em {ultimaResposta.tempo_processamento_ms}ms
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
