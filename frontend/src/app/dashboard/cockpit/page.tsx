'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  User, ClipboardList, FileText, Mic, Stethoscope,
  RefreshCw, Eye, Square, X, Printer, Download, Edit3, Save
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { api, CardListItem, BriefingPaciente, HistoricoConsulta, SOAPResponse, ConsultaResponse, SinaisVitais } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { ModeloSelector } from '@/components/modelos';

// Imports locais
import { getGlassStyles, getTextStyles } from './styles';
import { ExameLaboratorial, Anamnese, ValidacoesState } from './types';
import {
  MOCK_PACIENTES_FILA,
  MOCK_BRIEFING,
  MOCK_HISTORICO,
  MOCK_SOAP,
  MOCK_CONSULTA,
  MOCK_ANAMNESE,
  MOCK_EXAMES_LAB,
  MOCK_TRANSCRICAO,
} from './mocks';
import {
  ColunaColapsavel,
  PainelExameFisicoInferior,
  PainelSOAP,
  PainelPreparado,
  ModalHistoricoConsulta,
  ModalEdicao,
  Toolbar,
} from './components';
import { useTranscricao } from './hooks';

export default function CockpitPage() {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const { user } = useAppStore();

  // Mock Data Toggle - ATIVAR para visualização
  const [useMockData, setUseMockData] = useState(true);

  // States
  const [pacientesFila, setPacientesFila] = useState<CardListItem[]>([]);
  const [pacienteSelecionado, setPacienteSelecionado] = useState<CardListItem | null>(null);
  const [briefing, setBriefing] = useState<BriefingPaciente | null>(null);
  const [historico, setHistorico] = useState<HistoricoConsulta[]>([]);
  const [consulta, setConsulta] = useState<ConsultaResponse | null>(null);
  const [soap, setSoap] = useState<SOAPResponse | null>(null);
  const [sinaisVitais, setSinaisVitais] = useState<SinaisVitais>({});
  const [anamnese, setAnamnese] = useState<Anamnese | null>(null);
  const [examesLab, setExamesLab] = useState<ExameLaboratorial[]>([]);

  // Hook de transcrição
  const {
    transcricao,
    setTranscricao,
    gravando,
    processando: processandoTranscricao,
    tempoGravacao,
    erro: erroTranscricao,
    toggleGravacao,
  } = useTranscricao({
    useMockData,
    consultaId: consulta?.id,
  });

  // Loading states
  const [loadingFila, setLoadingFila] = useState(true);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [loadingSOAP, setLoadingSOAP] = useState(false);
  const [validandoSOAP, setValidandoSOAP] = useState(false);
  const [finalizandoConsulta, setFinalizandoConsulta] = useState(false);
  const [salvandoSinais, setSalvandoSinais] = useState(false);
  const [sinaisSalvos, setSinaisSalvos] = useState(false);
  const [savingField, setSavingField] = useState<string | null>(null);
  const [savedField, setSavedField] = useState<string | null>(null);

  // Modals
  const [showModeloSelector, setShowModeloSelector] = useState(false);
  const [modeloCategoria, setModeloCategoria] = useState<string | undefined>();
  const [documentoGerado, setDocumentoGerado] = useState<string | null>(null);
  const [historicoSelecionado, setHistoricoSelecionado] = useState<HistoricoConsulta | null>(null);
  const [showHistoricoModal, setShowHistoricoModal] = useState(false);

  // Estados de expansão das colunas (lateral) e painel inferior (vertical)
  const [colunaFilaExpanded, setColunaFilaExpanded] = useState(true);
  const [colunaHistoricoExpanded, setColunaHistoricoExpanded] = useState(true);
  const [colunaSoapExpanded, setColunaSoapExpanded] = useState(true);
  const [colunaTranscricaoExpanded, setColunaTranscricaoExpanded] = useState(true);
  const [painelExameFisicoExpanded, setPainelExameFisicoExpanded] = useState(true);

  // Estados de validação/conferência obrigatória
  const [validacoes, setValidacoes] = useState<ValidacoesState>({
    anamnese: false,
    antecedentes: false,
    medicamentos: false,
    alergias: false,
  });

  // Estados de edição
  const [editandoSecao, setEditandoSecao] = useState<string | null>(null);
  const [dadosEdicao, setDadosEdicao] = useState<any>(null);
  const [salvandoEdicao, setSalvandoEdicao] = useState(false);

  // Reset validações quando troca de paciente
  useEffect(() => {
    setValidacoes({
      anamnese: false,
      antecedentes: false,
      medicamentos: false,
      alergias: false,
    });
  }, [pacienteSelecionado]);

  // Handler para marcar como conferido
  const handleConferi = (secao: keyof ValidacoesState) => {
    setValidacoes(prev => ({ ...prev, [secao]: true }));
  };

  // Handler para abrir edição
  const handleAbrirEdicao = (secao: string, dados: any) => {
    setEditandoSecao(secao);
    setDadosEdicao(dados);
  };

  // Handler para salvar edição
  const handleSalvarEdicao = async () => {
    if (!editandoSecao) return;

    try {
      setSalvandoEdicao(true);

      // Simular salvamento - aqui chamaria API real
      await new Promise(resolve => setTimeout(resolve, 500));

      // Atualizar dados locais baseado na seção
      if (editandoSecao === 'anamnese' && anamnese) {
        setAnamnese({ ...anamnese, ...dadosEdicao });
      } else if (editandoSecao === 'medicamentos' && briefing) {
        setBriefing({ ...briefing, medicamentos_uso: dadosEdicao });
      } else if (editandoSecao === 'antecedentes' && briefing) {
        setBriefing({ ...briefing, antecedentes: dadosEdicao });
      } else if (editandoSecao === 'alergias' && briefing) {
        setBriefing({ ...briefing, alergias: dadosEdicao });
      }

      setEditandoSecao(null);
      setDadosEdicao(null);
    } catch (error) {
      console.error('Erro ao salvar:', error);
    } finally {
      setSalvandoEdicao(false);
    }
  };

  // Verificar se todas as validações foram feitas
  const todasValidacoes = Object.values(validacoes).every(v => v);
  const validacoesPendentes = Object.entries(validacoes)
    .filter(([_, v]) => !v)
    .map(([k]) => {
      const labels: Record<string, string> = {
        anamnese: 'Anamnese',
        antecedentes: 'Antecedentes',
        medicamentos: 'Medicamentos',
        alergias: 'Alergias'
      };
      return labels[k];
    });

  // Carregar fila de atendimento
  const carregarFila = useCallback(async () => {
    try {
      setLoadingFila(true);

      if (useMockData) {
        setPacientesFila(MOCK_PACIENTES_FILA);
        const pacienteEmAtendimento = MOCK_PACIENTES_FILA.find(p => p.coluna === 'em_atendimento');
        if (pacienteEmAtendimento && !pacienteSelecionado) {
          setPacienteSelecionado(pacienteEmAtendimento);
          setBriefing(MOCK_BRIEFING);
          setHistorico(MOCK_HISTORICO);
          setConsulta(MOCK_CONSULTA);
          setSoap(MOCK_SOAP);
          setSinaisVitais(MOCK_SOAP.exame_fisico || {});
          setTranscricao(MOCK_TRANSCRICAO);
          setAnamnese(MOCK_ANAMNESE);
          setExamesLab(MOCK_EXAMES_LAB);
        }
        setLoadingFila(false);
        return;
      }

      const response = await api.getCardsFase2();
      const todosPacientes: CardListItem[] = [];
      if (response.colunas) {
        Object.values(response.colunas).forEach((cards) => {
          todosPacientes.push(...cards);
        });
      }
      todosPacientes.sort((a, b) => {
        if (!a.hora_agendamento) return 1;
        if (!b.hora_agendamento) return -1;
        return a.hora_agendamento.localeCompare(b.hora_agendamento);
      });
      setPacientesFila(todosPacientes);
    } catch (error) {
      console.error('Erro ao carregar fila:', error);
      if (useMockData) {
        setPacientesFila(MOCK_PACIENTES_FILA);
      }
    } finally {
      setLoadingFila(false);
    }
  }, [useMockData, pacienteSelecionado, setTranscricao]);

  // Carregar dados do paciente selecionado
  const carregarDadosPaciente = useCallback(async (paciente: CardListItem) => {
    // Usar o id do card como referência (em produção, o card pode ter relação com paciente)
    const pacienteId = paciente.id;
    if (!pacienteId) {
      console.warn('Paciente sem ID');
      return;
    }

    try {
      setLoadingBriefing(true);
      setLoadingSOAP(true);

      if (useMockData) {
        await new Promise(resolve => setTimeout(resolve, 300));

        if (paciente.id === 'mock-1') {
          setBriefing(MOCK_BRIEFING);
          setHistorico(MOCK_HISTORICO);
          setConsulta(MOCK_CONSULTA);
          setSoap(MOCK_SOAP);
          setSinaisVitais(MOCK_SOAP.exame_fisico || {});
          setTranscricao(MOCK_TRANSCRICAO);
          setAnamnese(MOCK_ANAMNESE);
          setExamesLab(MOCK_EXAMES_LAB);
        } else {
          setBriefing({
            ...MOCK_BRIEFING,
            paciente_id: pacienteId,
            nome: paciente.paciente_nome || 'Paciente',
            idade: Math.floor(Math.random() * 40) + 30,
            alergias: [],
            alertas: [],
            medicamentos_uso: [],
            exames_pendentes: [],
            antecedentes: 'Sem antecedentes relevantes informados.'
          });
          setHistorico([]);
          setConsulta(null);
          setSoap(null);
          setSinaisVitais({});
          setTranscricao('');
          setAnamnese(null);
          setExamesLab([]);
        }
        setLoadingBriefing(false);
        setLoadingSOAP(false);
        return;
      }

      const [briefingData, historicoData] = await Promise.all([
        api.getBriefingPaciente(pacienteId).catch(() => null),
        api.getHistoricoPaciente(pacienteId).catch(() => []),
      ]);

      setBriefing(briefingData);
      setHistorico(historicoData || []);
    } catch (error) {
      console.error('Erro ao carregar dados do paciente:', error);
    } finally {
      setLoadingBriefing(false);
      setLoadingSOAP(false);
    }
  }, [useMockData, setTranscricao]);

  // Selecionar paciente
  const handleSelectPaciente = (paciente: CardListItem) => {
    setPacienteSelecionado(paciente);
    setBriefing(null);
    setHistorico([]);
    setConsulta(null);
    setSoap(null);
    setSinaisVitais({});
    setTranscricao('');
    carregarDadosPaciente(paciente);
  };

  // Ver histórico
  const handleVerHistorico = (consulta: HistoricoConsulta) => {
    setHistoricoSelecionado(consulta);
    setShowHistoricoModal(true);
  };

  // Validar SOAP
  const handleValidarSOAP = async () => {
    if (!soap) return;

    try {
      setValidandoSOAP(true);
      if (!useMockData) {
        await api.validarSOAP(soap.id);
      }
      setSoap(prev => prev ? { ...prev, revisado_por_medico: true } : null);
    } catch (error) {
      console.error('Erro ao validar SOAP:', error);
    } finally {
      setValidandoSOAP(false);
    }
  };

  // Editar campo do SOAP
  const handleEditarSOAP = async (campo: string, valor: string) => {
    if (!soap) return;

    try {
      setSavingField(campo);
      setSavedField(null);

      if (!useMockData) {
        await api.atualizarSOAP(soap.id, {
          [campo]: valor,
          revisado_por_medico: true
        });
      }

      setSoap(prev => prev ? {
        ...prev,
        [campo]: valor,
        revisado_por_medico: true
      } : null);

      setSavedField(campo);
      setTimeout(() => setSavedField(null), 2000);
    } catch (error) {
      console.error('Erro ao editar SOAP:', error);
    } finally {
      setSavingField(null);
    }
  };

  // Salvar sinais vitais
  const handleSalvarSinaisVitais = async () => {
    if (!soap) return;

    try {
      setSalvandoSinais(true);
      if (!useMockData) {
        await api.atualizarSOAP(soap.id, { exame_fisico: sinaisVitais });
      }
      setSoap(prev => prev ? { ...prev, exame_fisico: sinaisVitais } : null);
      setSinaisSalvos(true);
      setTimeout(() => setSinaisSalvos(false), 2000);
    } catch (error) {
      console.error('Erro ao salvar sinais vitais:', error);
    } finally {
      setSalvandoSinais(false);
    }
  };

  // Finalizar consulta
  const handleFinalizarConsulta = async () => {
    if (!consulta) return;

    if (!todasValidacoes) {
      alert(`Você precisa confirmar que revisou:\n\n• ${validacoesPendentes.join('\n• ')}\n\nClique no botão ✓ em cada seção do Histórico do Paciente para confirmar.`);
      if (!colunaHistoricoExpanded) {
        setColunaHistoricoExpanded(true);
      }
      return;
    }

    try {
      setFinalizandoConsulta(true);
      await api.finalizarConsulta(consulta.id);
      await carregarFila();
      setPacienteSelecionado(null);
      setBriefing(null);
      setHistorico([]);
      setConsulta(null);
      setSoap(null);
      setSinaisVitais({});
    } catch (error) {
      console.error('Erro ao finalizar consulta:', error);
    } finally {
      setFinalizandoConsulta(false);
    }
  };

  // Abrir modelo selector para tipo específico
  const handleAbrirModelo = (categoria: string) => {
    setModeloCategoria(categoria);
    setShowModeloSelector(true);
  };

  // Inicial load
  useEffect(() => {
    carregarFila();
    const interval = setInterval(carregarFila, 30000);
    return () => clearInterval(interval);
  }, [carregarFila]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 p-4">
      <div className="max-w-[1600px] mx-auto h-[calc(100vh-2rem)] flex flex-col gap-4">
        {/* Header */}
        <div className={cn('flex items-center justify-between p-4', glass.glass, 'rounded-2xl')}>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <Stethoscope className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className={cn('text-2xl font-bold', text.primary)}>Cockpit do Médico</h1>
              <p className={cn('text-sm', text.muted)}>
                {new Date().toLocaleDateString('pt-BR', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long'
                })}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setUseMockData(!useMockData)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 transition-all',
                useMockData
                  ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
              )}
            >
              <Eye className="w-3 h-3" />
              {useMockData ? 'Demo ON' : 'Demo OFF'}
            </button>
            <div className={cn('px-4 py-2 rounded-xl', glass.glassSubtle)}>
              <p className={cn('text-sm', text.muted)}>Médico</p>
              <p className={cn('font-medium', text.primary)}>{user?.name || 'Dr(a). Carlos Eduardo'}</p>
            </div>
            <button
              onClick={carregarFila}
              className={cn('p-2 rounded-lg transition-colors', glass.glassSubtle, 'hover:bg-white/10')}
            >
              <RefreshCw className={cn('w-5 h-5', text.muted)} />
            </button>
          </div>
        </div>

        {/* Main Content - Layout com 4 colunas colapsáveis + painel inferior */}
        <div className="flex-1 flex flex-col gap-4 min-h-0 overflow-hidden">
          {/* Área das 4 colunas horizontais */}
          <div className="flex-1 flex gap-2 min-h-0 overflow-hidden">
            {/* Coluna 1: Fila de Atendimento */}
            <ColunaColapsavel
              titulo="Fila de Atendimento"
              icon={ClipboardList}
              expanded={colunaFilaExpanded}
              onToggle={() => setColunaFilaExpanded(!colunaFilaExpanded)}
              widthExpanded="w-72"
              widthCollapsed="w-14"
              iconColor="from-amber-500 to-orange-600"
            >
              <div className="p-4 flex flex-col h-full">
                <div className="flex items-center justify-between mb-3">
                  <p className={cn('text-xs', text.muted)}>{pacientesFila.length} pacientes hoje</p>
                  <button
                    onClick={carregarFila}
                    className={cn('p-1.5 rounded-lg transition-colors hover:bg-white/10')}
                  >
                    <RefreshCw className={cn('w-4 h-4', text.muted)} />
                  </button>
                </div>
                {loadingFila ? (
                  <div className="flex-1 flex items-center justify-center">
                    <RefreshCw className={cn('w-6 h-6 animate-spin', text.muted)} />
                  </div>
                ) : pacientesFila.length === 0 ? (
                  <div className="flex-1 flex flex-col items-center justify-center gap-2">
                    <User className={cn('w-12 h-12', text.muted)} />
                    <p className={cn('text-sm text-center', text.muted)}>Nenhum paciente</p>
                  </div>
                ) : (
                  <div className="flex-1 overflow-y-auto space-y-2">
                    {pacientesFila.map((paciente) => (
                      <button
                        key={paciente.id}
                        onClick={() => handleSelectPaciente(paciente)}
                        className={cn(
                          'w-full p-3 rounded-xl text-left transition-all',
                          pacienteSelecionado?.id === paciente.id
                            ? 'bg-amber-500/20 ring-2 ring-amber-500'
                            : cn(glass.glassSubtle, 'hover:bg-white/10')
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                            <span className="text-white font-medium">
                              {paciente.paciente_nome?.charAt(0) || '?'}
                            </span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className={cn('font-medium truncate text-sm', text.primary)}>
                              {paciente.paciente_nome || 'Paciente'}
                            </p>
                            <p className={cn('text-xs', text.muted)}>
                              {paciente.hora_agendamento || '--:--'}
                            </p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </ColunaColapsavel>

            {/* Coluna 2: Histórico do Paciente */}
            <ColunaColapsavel
              titulo="Histórico do Paciente"
              icon={User}
              expanded={colunaHistoricoExpanded}
              onToggle={() => setColunaHistoricoExpanded(!colunaHistoricoExpanded)}
              widthExpanded="flex-1 min-w-[350px]"
              widthCollapsed="w-14"
              iconColor="from-blue-500 to-purple-600"
            >
              <div className="flex-1 overflow-y-auto min-h-0">
                <PainelPreparado
                  briefing={briefing}
                  historico={historico}
                  anamnese={anamnese}
                  examesLab={examesLab}
                  loading={loadingBriefing}
                  onVerHistorico={handleVerHistorico}
                  validacoes={validacoes}
                  onConferi={handleConferi}
                  onEditar={handleAbrirEdicao}
                />
              </div>
            </ColunaColapsavel>

            {/* Coluna 3: Prontuário SOAP */}
            <ColunaColapsavel
              titulo="Prontuário SOAP"
              icon={FileText}
              expanded={colunaSoapExpanded}
              onToggle={() => setColunaSoapExpanded(!colunaSoapExpanded)}
              widthExpanded="flex-1 min-w-[400px]"
              widthCollapsed="w-14"
              iconColor="from-emerald-500 to-green-600"
            >
              <div className="flex-1 overflow-y-auto min-h-0">
                <PainelSOAP
                  soap={soap}
                  consulta={consulta}
                  onValidar={handleValidarSOAP}
                  onEditar={handleEditarSOAP}
                  loading={loadingSOAP}
                  validando={validandoSOAP}
                  savingField={savingField}
                  savedField={savedField}
                />
              </div>
            </ColunaColapsavel>

            {/* Coluna 4: Transcrição da Consulta */}
            <ColunaColapsavel
              titulo="Transcrição da Consulta"
              icon={Mic}
              expanded={colunaTranscricaoExpanded}
              onToggle={() => setColunaTranscricaoExpanded(!colunaTranscricaoExpanded)}
              widthExpanded="flex-1 min-w-[350px]"
              widthCollapsed="w-14"
              iconColor="from-violet-500 to-purple-600"
            >
              <div className="flex-1 flex flex-col min-h-0 p-4">
                <div className="flex items-center justify-between mb-4 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    {gravando && (
                      <span className="flex items-center gap-2 text-red-400 text-sm">
                        <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        {Math.floor(tempoGravacao / 60).toString().padStart(2, '0')}:{(tempoGravacao % 60).toString().padStart(2, '0')}
                      </span>
                    )}
                    {processandoTranscricao && (
                      <span className="flex items-center gap-2 text-amber-400 text-sm">
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        Transcrevendo...
                      </span>
                    )}
                  </div>
                  <button
                    onClick={toggleGravacao}
                    disabled={!pacienteSelecionado || processandoTranscricao}
                    className={cn(
                      'px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all',
                      gravando
                        ? 'bg-red-500 hover:bg-red-600 text-white'
                        : 'bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white',
                      'disabled:opacity-50 disabled:cursor-not-allowed'
                    )}
                  >
                    {gravando ? (
                      <>
                        <Square className="w-4 h-4" />
                        Parar
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4" />
                        Gravar
                      </>
                    )}
                  </button>
                </div>

                {/* Erro de transcrição */}
                {erroTranscricao && (
                  <div className="mb-3 p-3 rounded-lg bg-red-500/20 border border-red-500/30">
                    <p className="text-sm text-red-400">{erroTranscricao}</p>
                  </div>
                )}

                {/* Indicador de modo */}
                {!useMockData && !consulta && pacienteSelecionado && (
                  <div className="mb-3 p-3 rounded-lg bg-amber-500/20 border border-amber-500/30">
                    <p className="text-xs text-amber-400">
                      ⚠️ Inicie uma consulta para habilitar transcrição automática via Whisper
                    </p>
                  </div>
                )}

                {transcricao ? (
                  <div className={cn('p-4 rounded-xl flex-1 overflow-y-auto min-h-0', glass.glassDark)}>
                    <pre className={cn('text-sm whitespace-pre-wrap font-sans', text.secondary)}>
                      {transcricao}
                    </pre>
                  </div>
                ) : processandoTranscricao ? (
                  <div className={cn('p-8 rounded-xl text-center flex-1 flex flex-col items-center justify-center', glass.glassDark)}>
                    <RefreshCw className={cn('w-12 h-12 mb-3 animate-spin', text.muted)} />
                    <p className={cn('text-sm', text.muted)}>
                      Processando áudio com Whisper...
                    </p>
                  </div>
                ) : (
                  <div className={cn('p-8 rounded-xl text-center flex-1 flex flex-col items-center justify-center', glass.glassDark)}>
                    <Mic className={cn('w-12 h-12 mb-3', text.muted)} />
                    <p className={cn('text-sm', text.muted)}>
                      {!pacienteSelecionado
                        ? 'Selecione um paciente'
                        : 'Clique em Gravar para iniciar'}
                    </p>
                    {!useMockData && (
                      <p className={cn('text-xs mt-2', text.muted)}>
                        Modo: Whisper API (Groq)
                      </p>
                    )}
                  </div>
                )}
              </div>
            </ColunaColapsavel>
          </div>

          {/* Painel Inferior: Exame Físico / Medições */}
          <PainelExameFisicoInferior
            sinaisVitais={sinaisVitais}
            onChange={setSinaisVitais}
            onSave={handleSalvarSinaisVitais}
            saving={salvandoSinais}
            disabled={!pacienteSelecionado}
            saved={sinaisSalvos}
            expanded={painelExameFisicoExpanded}
            onToggle={() => setPainelExameFisicoExpanded(!painelExameFisicoExpanded)}
          />
        </div>

        {/* Toolbar */}
        <Toolbar
          onReceita={() => handleAbrirModelo('Receitas')}
          onAtestado={() => handleAbrirModelo('Atestados')}
          onExames={() => handleAbrirModelo('Exames')}
          onEncaminhamento={() => handleAbrirModelo('Orientações Médicas')}
          onFinalizar={handleFinalizarConsulta}
          disabled={!pacienteSelecionado}
          finalizando={finalizandoConsulta}
        />

        {/* Modal Histórico */}
        <ModalHistoricoConsulta
          isOpen={showHistoricoModal}
          onClose={() => setShowHistoricoModal(false)}
          consulta={historicoSelecionado}
          pacienteNome={briefing?.nome}
        />

        {/* Modal de Edição de Seções */}
        <ModalEdicao
          isOpen={!!editandoSecao}
          secao={editandoSecao}
          dados={dadosEdicao}
          salvando={salvandoEdicao}
          onClose={() => {
            setEditandoSecao(null);
            setDadosEdicao(null);
          }}
          onSave={handleSalvarEdicao}
          onChangeDados={setDadosEdicao}
        />

        {/* Modelo Selector Modal */}
        <ModeloSelector
          isOpen={showModeloSelector}
          onClose={() => setShowModeloSelector(false)}
          onSelect={(modelo, conteudoProcessado) => {
            setDocumentoGerado(conteudoProcessado);
            setShowModeloSelector(false);
          }}
          pacienteData={briefing ? {
            nome: briefing.nome,
            telefone: briefing.telefone,
            data_nascimento: briefing.data_nascimento,
            convenio: briefing.convenio,
          } : undefined}
          categoriaFiltro={modeloCategoria as any}
          titulo={`Selecionar ${modeloCategoria || 'Documento'}`}
        />

        {/* Preview do documento gerado */}
        {documentoGerado && (
          <div className={cn('fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm')}>
            <div className={cn('w-full max-w-2xl max-h-[80vh] overflow-hidden', glass.glassStrong, 'rounded-2xl')}>
              {/* Header */}
              <div className={cn('flex items-center justify-between p-4 border-b border-white/10')}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-600 flex items-center justify-center">
                    <FileText className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className={cn('font-semibold', text.primary)}>Documento Gerado</h3>
                    <p className={cn('text-xs', text.muted)}>{briefing?.nome || 'Paciente'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      const printWindow = window.open('', '_blank');
                      if (printWindow) {
                        printWindow.document.write(`
                          <html>
                            <head>
                              <title>Documento - ${briefing?.nome || 'Paciente'}</title>
                              <style>
                                body { font-family: Arial, sans-serif; padding: 40px; line-height: 1.6; }
                                pre { white-space: pre-wrap; font-family: inherit; }
                              </style>
                            </head>
                            <body><pre>${documentoGerado}</pre></body>
                          </html>
                        `);
                        printWindow.document.close();
                        printWindow.print();
                      }
                    }}
                    className={cn('px-3 py-2 rounded-lg flex items-center gap-2', glass.glassSubtle, text.primary, 'hover:bg-white/10')}
                    title="Imprimir"
                  >
                    <Printer className="w-4 h-4" />
                    Imprimir
                  </button>
                  <button
                    onClick={() => {
                      const blob = new Blob([documentoGerado], { type: 'text/plain' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `documento-${briefing?.nome?.replace(/\s+/g, '-').toLowerCase() || 'paciente'}-${new Date().toISOString().split('T')[0]}.txt`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className={cn('px-3 py-2 rounded-lg flex items-center gap-2', glass.glassSubtle, text.primary, 'hover:bg-white/10')}
                    title="Download"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                  <button
                    onClick={() => setDocumentoGerado(null)}
                    className={cn('p-2 rounded-lg', glass.glassSubtle, text.muted, 'hover:bg-white/10')}
                    title="Fechar"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Conteúdo */}
              <div className="p-6 overflow-auto max-h-[60vh]">
                <div className={cn('p-6 rounded-xl bg-white/5 border border-white/10')}>
                  <pre className={cn('text-sm whitespace-pre-wrap font-sans', text.secondary)}>
                    {documentoGerado}
                  </pre>
                </div>
              </div>

              {/* Footer */}
              <div className={cn('flex items-center justify-between p-4 border-t border-white/10')}>
                <p className={cn('text-xs', text.muted)}>
                  Gerado em {new Date().toLocaleString('pt-BR')}
                </p>
                <button
                  onClick={() => setDocumentoGerado(null)}
                  className={cn('px-4 py-2 rounded-lg', glass.glassSubtle, text.primary, 'hover:bg-white/10')}
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
