'use client';

import { useState } from 'react';
import {
  User, AlertTriangle, Pill, History, Calendar, Phone, Building2, Eye,
  ChevronDown, ChevronRight, ClipboardList, TestTube, Edit3, CheckCircle, RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { HistoricoConsulta } from '@/lib/api';
import { getGlassStyles, getTextStyles } from '../styles';
import { PainelPreparadoProps, ExameLaboratorial, Anamnese } from '../types';

// Componente SecaoAnamnese
interface SecaoAnamneseProps {
  anamnese: Anamnese | null;
  expanded: boolean;
  onToggle: () => void;
  validado?: boolean;
  onConferi?: () => void;
  onEditar?: (dados: any) => void;
}

function SecaoAnamnese({ anamnese, expanded, onToggle, validado = false, onConferi, onEditar }: SecaoAnamneseProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  if (!anamnese) return null;

  return (
    <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
      <div className={cn('w-full flex items-center justify-between p-3 rounded-lg transition-colors hover:bg-white/5')}>
        <button
          onClick={onToggle}
          className="flex items-center gap-2 flex-1"
        >
          <ClipboardList className={cn('w-4 h-4 text-green-400')} />
          <span className={cn('font-medium', text.primary)}>Anamnese</span>
          <span className="px-2 py-0.5 rounded-full text-xs bg-green-500/20 text-green-400">
            Preenchida
          </span>
          {expanded ? (
            <ChevronDown className={cn('w-4 h-4 ml-auto', text.muted)} />
          ) : (
            <ChevronRight className={cn('w-4 h-4 ml-auto', text.muted)} />
          )}
        </button>

        {/* Botões de Editar e Conferi */}
        <div className="flex items-center gap-1 ml-2">
          {onEditar && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditar(anamnese);
              }}
              className={cn('p-1.5 rounded-lg transition-colors hover:bg-white/10', text.muted)}
              title="Editar"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          )}
          {onConferi && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (!validado) onConferi();
              }}
              disabled={validado}
              className={cn(
                'p-1.5 rounded-lg transition-colors',
                validado
                  ? 'bg-green-500/20 text-green-400 cursor-default'
                  : 'hover:bg-amber-500/20 text-amber-400 hover:text-amber-300'
              )}
              title={validado ? 'Conferido ✓' : 'Clique para confirmar que revisou'}
            >
              {validado ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertTriangle className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          {/* Queixa Principal */}
          <div className={cn('p-3 rounded-lg', glass.glassDark)}>
            <p className={cn('text-xs font-medium mb-1', text.accent)}>Queixa Principal</p>
            <p className={cn('text-sm', text.primary)}>{anamnese.queixa_principal}</p>
          </div>

          {/* Detalhes da Queixa */}
          <div className="grid grid-cols-2 gap-2">
            <div className={cn('p-2 rounded-lg', glass.glassDark)}>
              <p className={cn('text-xs', text.muted)}>Início</p>
              <p className={cn('text-sm', text.secondary)}>{anamnese.inicio_sintomas}</p>
            </div>
            <div className={cn('p-2 rounded-lg', glass.glassDark)}>
              <p className={cn('text-xs', text.muted)}>Piora com</p>
              <p className={cn('text-sm', text.secondary)}>{anamnese.fatores_piora}</p>
            </div>
          </div>

          {/* Sintomas Associados */}
          <div>
            <p className={cn('text-xs font-medium mb-2', text.muted)}>Sintomas Associados</p>
            <div className="flex flex-wrap gap-1.5">
              {anamnese.sintomas_associados.map((s, i) => (
                <span
                  key={i}
                  className={cn(
                    'px-2 py-1 rounded-full text-xs',
                    s.presente
                      ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      : 'bg-gray-500/10 text-gray-500'
                  )}
                >
                  {s.presente ? '✓' : '−'} {s.sintoma}
                </span>
              ))}
            </div>
          </div>

          {/* Hábitos */}
          <div>
            <p className={cn('text-xs font-medium mb-2', text.muted)}>Hábitos de Vida</p>
            <div className="grid grid-cols-2 gap-2">
              <div className={cn('p-2 rounded-lg', glass.glassDark)}>
                <p className={cn('text-xs', text.muted)}>Tabagismo</p>
                <p className={cn('text-xs', text.secondary)}>{anamnese.habitos.tabagismo}</p>
              </div>
              <div className={cn('p-2 rounded-lg', glass.glassDark)}>
                <p className={cn('text-xs', text.muted)}>Etilismo</p>
                <p className={cn('text-xs', text.secondary)}>{anamnese.habitos.etilismo}</p>
              </div>
              <div className={cn('p-2 rounded-lg', glass.glassDark)}>
                <p className={cn('text-xs', text.muted)}>Atividade Física</p>
                <p className={cn('text-xs', text.secondary)}>{anamnese.habitos.atividade_fisica}</p>
              </div>
              <div className={cn('p-2 rounded-lg', glass.glassDark)}>
                <p className={cn('text-xs', text.muted)}>Alimentação</p>
                <p className={cn('text-xs', text.secondary)}>{anamnese.habitos.alimentacao}</p>
              </div>
            </div>
          </div>

          {/* Histórico Familiar */}
          <div>
            <p className={cn('text-xs font-medium mb-2', text.muted)}>Histórico Familiar</p>
            <div className="space-y-1">
              {anamnese.historico_familiar.map((h, i) => (
                <div key={i} className={cn('flex items-center gap-2 text-xs', text.secondary)}>
                  <span className={cn('font-medium', text.primary)}>{h.parentesco}:</span>
                  <span>{h.condicao}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Adesão aos Medicamentos */}
          <div>
            <p className={cn('text-xs font-medium mb-2', text.muted)}>Adesão aos Medicamentos</p>
            <div className="space-y-1">
              {anamnese.medicamentos_atuais.map((m, i) => (
                <div
                  key={i}
                  className={cn(
                    'flex items-center justify-between p-2 rounded-lg text-xs',
                    glass.glassDark,
                    !m.tomando && 'border border-amber-500/30'
                  )}
                >
                  <span className={text.secondary}>{m.nome} - {m.posologia}</span>
                  <span className={m.tomando ? 'text-green-400' : 'text-amber-400'}>
                    {m.tomando ? '✓ Tomando' : `⚠ ${m.obs || 'Não toma'}`}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Observações do Paciente */}
          {anamnese.observacoes_paciente && (
            <div className={cn('p-3 rounded-lg border border-blue-500/30', glass.glassDark)}>
              <p className={cn('text-xs font-medium mb-1 text-blue-400')}>Observações do Paciente</p>
              <p className={cn('text-sm italic', text.secondary)}>"{anamnese.observacoes_paciente}"</p>
            </div>
          )}

          {/* Data de preenchimento */}
          <p className={cn('text-xs text-right', text.muted)}>
            Preenchido em {new Date(anamnese.data_preenchimento).toLocaleString('pt-BR')}
          </p>

          {/* Aviso de validação */}
          {onConferi && !validado && (
            <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" />
              Confirme que revisou a anamnese
            </p>
          )}
        </div>
      )}
    </div>
  );
}

// Componente SecaoExamesLab
interface SecaoExamesLabProps {
  exames: ExameLaboratorial[];
  expanded: boolean;
  onToggle: () => void;
}

function SecaoExamesLab({ exames, expanded, onToggle }: SecaoExamesLabProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  if (!exames || exames.length === 0) return null;

  // Verificar se valor está fora do padrão
  const isAlterado = (exame: ExameLaboratorial): 'alto' | 'baixo' | 'normal' => {
    if (exame.max !== null && exame.valor > exame.max) return 'alto';
    if (exame.min !== null && exame.valor < exame.min) return 'baixo';
    return 'normal';
  };

  // Contar alterados
  const alterados = exames.filter(e => isAlterado(e) !== 'normal').length;

  // Agrupar por categoria
  const categorias = exames.reduce((acc, exame) => {
    if (!acc[exame.categoria]) acc[exame.categoria] = [];
    acc[exame.categoria].push(exame);
    return acc;
  }, {} as Record<string, ExameLaboratorial[]>);

  return (
    <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
      <button
        onClick={onToggle}
        className={cn('w-full flex items-center justify-between p-3 rounded-lg transition-colors hover:bg-white/5')}
      >
        <div className="flex items-center gap-2">
          <TestTube className={cn('w-4 h-4 text-purple-400')} />
          <span className={cn('font-medium', text.primary)}>Exames Laboratoriais</span>
          {alterados > 0 && (
            <span className="px-2 py-0.5 rounded-full text-xs bg-red-500/20 text-red-400">
              {alterados} alterado{alterados > 1 ? 's' : ''}
            </span>
          )}
        </div>
        {expanded ? (
          <ChevronDown className={cn('w-4 h-4', text.muted)} />
        ) : (
          <ChevronRight className={cn('w-4 h-4', text.muted)} />
        )}
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-3">
          {Object.entries(categorias).map(([categoria, examesCategoria]) => (
            <div key={categoria}>
              <p className={cn('text-xs font-medium mb-2 flex items-center gap-2', text.muted)}>
                {categoria}
                {examesCategoria.some(e => isAlterado(e) !== 'normal') && (
                  <AlertTriangle className="w-3 h-3 text-amber-400" />
                )}
              </p>
              <div className={cn('rounded-lg overflow-hidden', glass.glassDark)}>
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className={cn('text-left p-2 font-medium', text.muted)}>Exame</th>
                      <th className={cn('text-center p-2 font-medium', text.muted)}>Resultado</th>
                      <th className={cn('text-center p-2 font-medium', text.muted)}>Referência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {examesCategoria.map((exame, i) => {
                      const status = isAlterado(exame);
                      return (
                        <tr
                          key={i}
                          className={cn(
                            'border-b border-white/5 last:border-0',
                            status !== 'normal' && 'bg-red-500/10'
                          )}
                        >
                          <td className={cn('p-2', text.secondary)}>{exame.nome}</td>
                          <td className={cn(
                            'p-2 text-center font-bold',
                            status === 'alto' ? 'text-red-400' :
                            status === 'baixo' ? 'text-blue-400' :
                            'text-green-400'
                          )}>
                            {exame.valor} {exame.unidade}
                            {status === 'alto' && ' ↑'}
                            {status === 'baixo' && ' ↓'}
                          </td>
                          <td className={cn('p-2 text-center', text.muted)}>
                            {exame.min !== null && exame.max !== null
                              ? `${exame.min} - ${exame.max}`
                              : exame.max !== null
                              ? `< ${exame.max}`
                              : exame.min !== null
                              ? `> ${exame.min}`
                              : '-'
                            } {exame.unidade}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ))}

          {/* Legenda */}
          <div className={cn('flex items-center gap-4 text-xs pt-2', text.muted)}>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-red-400" /> Acima
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-blue-400" /> Abaixo
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-green-400" /> Normal
            </span>
          </div>

          {/* Data dos exames */}
          <p className={cn('text-xs text-right', text.muted)}>
            Exames de {new Date(exames[0].data).toLocaleDateString('pt-BR')}
          </p>
        </div>
      )}
    </div>
  );
}

// Componente Principal PainelPreparado
export function PainelPreparado({ briefing, historico, anamnese, examesLab, loading, onVerHistorico, validacoes, onConferi, onEditar }: PainelPreparadoProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    anamnese: true,
    examesLab: false,
    medicamentos: true,
    alergias: true,
    antecedentes: true,
    historico: true,
    exames: false,
  });

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  if (loading) {
    return (
      <div className={cn('flex-1 flex items-center justify-center', glass.glass, 'rounded-2xl')}>
        <RefreshCw className={cn('w-8 h-8 animate-spin', text.muted)} />
      </div>
    );
  }

  if (!briefing) {
    return (
      <div className={cn('flex-1 flex flex-col items-center justify-center gap-4', glass.glass, 'rounded-2xl')}>
        <User className={cn('w-16 h-16', text.muted)} />
        <p className={cn('text-lg', text.muted)}>Selecione um paciente da fila</p>
      </div>
    );
  }

  const SectionHeader = ({
    title,
    icon: Icon,
    section,
    badge,
    badgeColor = 'bg-amber-500',
    editavel = false,
    validavel = false,
    validado = false,
    dados = null,
  }: {
    title: string;
    icon: any;
    section: string;
    badge?: number | string;
    badgeColor?: string;
    editavel?: boolean;
    validavel?: boolean;
    validado?: boolean;
    dados?: any;
  }) => (
    <div className={cn(
      'w-full flex items-center justify-between p-3 rounded-lg transition-colors',
      'hover:bg-white/5'
    )}>
      <button
        onClick={() => toggleSection(section)}
        className="flex items-center gap-2 flex-1"
      >
        <Icon className={cn('w-4 h-4', text.accent)} />
        <span className={cn('font-medium', text.primary)}>{title}</span>
        {badge !== undefined && (
          <span className={cn('px-2 py-0.5 rounded-full text-xs text-white', badgeColor)}>
            {badge}
          </span>
        )}
        {expandedSections[section] ? (
          <ChevronDown className={cn('w-4 h-4 ml-auto', text.muted)} />
        ) : (
          <ChevronRight className={cn('w-4 h-4 ml-auto', text.muted)} />
        )}
      </button>

      {/* Botões de Editar e Conferi */}
      {(editavel || validavel) && (
        <div className="flex items-center gap-1 ml-2">
          {editavel && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEditar(section, dados);
              }}
              className={cn(
                'p-1.5 rounded-lg transition-colors hover:bg-white/10',
                text.muted
              )}
              title="Editar"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          )}
          {validavel && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (!validado) {
                  onConferi(section as 'anamnese' | 'antecedentes' | 'medicamentos' | 'alergias');
                }
              }}
              disabled={validado}
              className={cn(
                'p-1.5 rounded-lg transition-colors',
                validado
                  ? 'bg-green-500/20 text-green-400 cursor-default'
                  : 'hover:bg-amber-500/20 text-amber-400 hover:text-amber-300'
              )}
              title={validado ? 'Conferido ✓' : 'Clique para confirmar que revisou'}
            >
              {validado ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertTriangle className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );

  return (
    <div className={cn('flex-1 flex flex-col min-h-0', glass.glass, 'rounded-2xl')}>
      {/* Header do Paciente */}
      <div className={cn('p-4 border-b border-white/10', glass.glassSubtle)}>
        <div className="flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white text-xl font-bold">
              {briefing.nome.charAt(0)}
            </span>
          </div>
          <div className="flex-1">
            <h2 className={cn('text-xl font-bold', text.primary)}>{briefing.nome}</h2>
            <div className={cn('flex items-center gap-4 text-sm', text.secondary)}>
              <span>{briefing.idade} anos</span>
              {briefing.sexo && <span>• {briefing.sexo}</span>}
              {briefing.convenio && (
                <span className="flex items-center gap-1">
                  <Building2 className="w-3 h-3" />
                  {briefing.convenio}
                </span>
              )}
            </div>
            {briefing.telefone && (
              <div className={cn('flex items-center gap-1 text-sm mt-1', text.muted)}>
                <Phone className="w-3 h-3" />
                {briefing.telefone}
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className={cn(
              'px-3 py-1 rounded-full text-xs font-medium',
              'bg-green-500/20 text-green-400 border border-green-500/30'
            )}>
              ✅ Preparado
            </span>
          </div>
        </div>

        {/* Alertas */}
        {briefing.alertas && briefing.alertas.length > 0 && (
          <div className="mt-3 p-2 rounded-lg bg-red-500/20 border border-red-500/30">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400" />
              <span className="text-red-400 text-sm font-medium">Alertas</span>
            </div>
            <ul className="mt-1 space-y-1">
              {briefing.alertas.map((alerta, i) => (
                <li key={i} className="text-red-300 text-sm">• {alerta}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Conteúdo Scrollável */}
      <div className="flex-1 overflow-y-auto min-h-0 p-4 space-y-2">
        {/* Alergias - Sempre visível com validação obrigatória */}
        <div className={cn('rounded-lg overflow-hidden', briefing.alergias && briefing.alergias.length > 0 ? 'bg-red-500/10 border border-red-500/30' : glass.glassSubtle)}>
          <SectionHeader
            title="Alergias"
            icon={AlertTriangle}
            section="alergias"
            badge={briefing.alergias?.length || 0}
            badgeColor="bg-red-500"
            editavel={true}
            validavel={true}
            validado={validacoes.alergias}
            dados={briefing.alergias || []}
          />
          {expandedSections.alergias !== false && (
            <div className="px-3 pb-3">
              {briefing.alergias && briefing.alergias.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {briefing.alergias.map((alergia, i) => (
                    <span key={i} className="px-2 py-1 rounded-full text-xs bg-red-500/20 text-red-300 border border-red-500/30">
                      {alergia}
                    </span>
                  ))}
                </div>
              ) : (
                <p className={cn('text-sm', text.muted)}>Nenhuma alergia informada</p>
              )}
              {!validacoes.alergias && (
                <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Confirme que revisou as alergias
                </p>
              )}
            </div>
          )}
        </div>

        {/* ANAMNESE */}
        <SecaoAnamnese
          anamnese={anamnese}
          expanded={expandedSections.anamnese}
          onToggle={() => toggleSection('anamnese')}
          validado={validacoes.anamnese}
          onConferi={() => onConferi('anamnese')}
          onEditar={(dados) => onEditar('anamnese', dados)}
        />

        {/* EXAMES LABORATORIAIS */}
        <SecaoExamesLab
          exames={examesLab}
          expanded={expandedSections.examesLab}
          onToggle={() => toggleSection('examesLab')}
        />

        {/* Medicamentos em Uso */}
        <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
          <SectionHeader
            title="Medicamentos em Uso"
            icon={Pill}
            section="medicamentos"
            badge={briefing.medicamentos_uso?.length || 0}
            badgeColor="bg-blue-500"
            editavel={true}
            validavel={true}
            validado={validacoes.medicamentos}
            dados={briefing.medicamentos_uso || []}
          />
          {expandedSections.medicamentos && (
            <div className="px-3 pb-3">
              {briefing.medicamentos_uso && briefing.medicamentos_uso.length > 0 ? (
                <div className="space-y-1">
                  {briefing.medicamentos_uso.map((med, i) => (
                    <div key={i} className={cn('flex items-center gap-2 text-sm', text.secondary)}>
                      <Pill className="w-3 h-3 text-blue-400" />
                      <span>{med}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className={cn('text-sm', text.muted)}>Nenhum medicamento informado</p>
              )}
              {!validacoes.medicamentos && (
                <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Confirme que revisou os medicamentos
                </p>
              )}
            </div>
          )}
        </div>

        {/* Antecedentes */}
        <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
          <SectionHeader
            title="Antecedentes"
            icon={History}
            section="antecedentes"
            editavel={true}
            validavel={true}
            validado={validacoes.antecedentes}
            dados={briefing.antecedentes || ''}
          />
          {expandedSections.antecedentes !== false && (
            <div className="px-3 pb-3">
              {briefing.antecedentes ? (
                <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>
                  {briefing.antecedentes}
                </p>
              ) : (
                <p className={cn('text-sm', text.muted)}>Nenhum antecedente informado</p>
              )}
              {!validacoes.antecedentes && (
                <p className="text-xs text-amber-400 mt-2 flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  Confirme que revisou os antecedentes
                </p>
              )}
            </div>
          )}
        </div>

        {/* Histórico de Consultas */}
        <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
          <SectionHeader
            title="Histórico de Consultas"
            icon={Calendar}
            section="historico"
            badge={historico.length}
            badgeColor="bg-blue-500"
          />
          {expandedSections.historico && (
            <div className="px-3 pb-3">
              {historico.length > 0 ? (
                <div className="space-y-2">
                  {historico.map((consulta) => (
                    <div
                      key={consulta.id}
                      className={cn('p-3 rounded-lg cursor-pointer transition-all hover:bg-white/10', glass.glassDark)}
                      onClick={() => onVerHistorico(consulta)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className={cn('text-sm font-medium', text.primary)}>
                            {new Date(consulta.data).toLocaleDateString('pt-BR')}
                          </span>
                          {consulta.medico_nome && (
                            <span className={cn('text-xs', text.muted)}>
                              Dr(a). {consulta.medico_nome}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          {consulta.tem_soap && (
                            <span className="px-1.5 py-0.5 rounded text-xs bg-blue-500/20 text-blue-400">SOAP</span>
                          )}
                          {consulta.tem_receita && (
                            <span className="px-1.5 py-0.5 rounded text-xs bg-green-500/20 text-green-400">RX</span>
                          )}
                          {consulta.tem_exames && (
                            <span className="px-1.5 py-0.5 rounded text-xs bg-purple-500/20 text-purple-400">EX</span>
                          )}
                          <Eye className={cn('w-4 h-4', text.muted)} />
                        </div>
                      </div>
                      {consulta.motivo && (
                        <p className={cn('text-xs mt-1', text.muted)}>{consulta.motivo}</p>
                      )}
                      {consulta.diagnostico && (
                        <p className={cn('text-xs mt-1', text.secondary)}>
                          Diagnóstico: {consulta.diagnostico}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className={cn('text-sm', text.muted)}>Primeira consulta</p>
              )}
            </div>
          )}
        </div>

        {/* Exames Pendentes */}
        <div className={cn('rounded-lg overflow-hidden', glass.glassSubtle)}>
          <SectionHeader
            title="Exames Pendentes"
            icon={TestTube}
            section="exames"
            badge={briefing.exames_pendentes?.length || 0}
            badgeColor="bg-purple-500"
          />
          {expandedSections.exames && (
            <div className="px-3 pb-3">
              {briefing.exames_pendentes && briefing.exames_pendentes.length > 0 ? (
                <div className="space-y-2">
                  {briefing.exames_pendentes.map((exame) => (
                    <div key={exame.id} className={cn('flex items-center justify-between text-sm', text.secondary)}>
                      <span className="flex items-center gap-2">
                        <TestTube className="w-3 h-3 text-purple-400" />
                        {exame.descricao}
                      </span>
                      <span className={text.muted}>{exame.tipo}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className={cn('text-sm', text.muted)}>Nenhum exame pendente</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
