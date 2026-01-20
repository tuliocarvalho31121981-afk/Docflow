// Types e Interfaces do Cockpit do Médico

import { CardListItem, BriefingPaciente, HistoricoConsulta, SOAPResponse, ConsultaResponse, SinaisVitais } from '@/lib/api';

// Interface para exame laboratorial
export interface ExameLaboratorial {
  categoria: string;
  nome: string;
  valor: number;
  unidade: string;
  min: number | null;
  max: number | null;
  data: string;
}

// Interface para anamnese
export interface Anamnese {
  data_preenchimento: string;
  queixa_principal: string;
  inicio_sintomas: string;
  fatores_piora: string;
  fatores_melhora: string;
  sintomas_associados: Array<{ sintoma: string; presente: boolean }>;
  habitos: {
    tabagismo: string;
    etilismo: string;
    atividade_fisica: string;
    sono: string;
    alimentacao: string;
  };
  historico_familiar: Array<{ parentesco: string; condicao: string }>;
  medicamentos_atuais: Array<{
    nome: string;
    posologia: string;
    horario: string;
    tomando: boolean;
    obs?: string;
  }>;
  observacoes_paciente?: string;
  observacoes_medico?: string;
}

// Props dos componentes
export interface FilaAtendimentoProps {
  pacientes: CardListItem[];
  pacienteSelecionado: CardListItem | null;
  onSelectPaciente: (paciente: CardListItem) => void;
  loading: boolean;
}

export interface ColunaColapsavelProps {
  titulo: string;
  icon: React.ComponentType<{ className?: string }>;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  widthExpanded?: string;
  widthCollapsed?: string;
  iconColor?: string;
}

export interface PainelExameFisicoInferiorProps {
  sinaisVitais: SinaisVitais;
  onChange: (sinais: SinaisVitais) => void;
  onSave: () => void;
  saving: boolean;
  disabled: boolean;
  saved: boolean;
  expanded: boolean;
  onToggle: () => void;
}

export interface ModalHistoricoConsultaProps {
  isOpen: boolean;
  onClose: () => void;
  consulta: HistoricoConsulta | null;
  pacienteNome?: string;
}

export interface PainelExameFisicoProps {
  sinaisVitais: SinaisVitais;
  onChange: (sinais: SinaisVitais) => void;
  onSave: () => void;
  saving: boolean;
  disabled: boolean;
  saved?: boolean;
}

export interface PainelTranscricaoProps {
  transcricao: string;
  gravando: boolean;
  tempoGravacao: number;
  onToggleGravacao: () => void;
  disabled: boolean;
}

export interface SecaoAnamneseProps {
  anamnese: Anamnese | null;
  expanded: boolean;
  onToggle: () => void;
  validado?: boolean;
  onConferi?: () => void;
  onEditar?: (dados: any) => void;
}

export interface SecaoExamesLabProps {
  exames: ExameLaboratorial[];
  expanded: boolean;
  onToggle: () => void;
}

export interface PainelPreparadoProps {
  briefing: BriefingPaciente | null;
  historico: HistoricoConsulta[];
  anamnese: Anamnese | null;
  examesLab: ExameLaboratorial[];
  loading: boolean;
  onVerHistorico: (consulta: HistoricoConsulta) => void;
  validacoes: {
    anamnese: boolean;
    antecedentes: boolean;
    medicamentos: boolean;
    alergias: boolean;
  };
  onConferi: (secao: 'anamnese' | 'antecedentes' | 'medicamentos' | 'alergias') => void;
  onEditar: (secao: string, dados: any) => void;
}

export interface SOAPFieldProps {
  label: string;
  campo: string;
  valor?: string;
  placeholder: string;
  icon: any;
  isEditing: boolean;
  isSaving: boolean;
  justSaved: boolean;
  editValue: string;
  onStartEdit: () => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
  onChangeValue: (value: string) => void;
}

export interface PainelSOAPProps {
  soap: SOAPResponse | null;
  consulta: ConsultaResponse | null;
  onValidar: () => void;
  onEditar: (campo: string, valor: string) => void;
  loading: boolean;
  validando: boolean;
  savingField?: string | null;
  savedField?: string | null;
}

export interface ToolbarProps {
  onReceita: () => void;
  onAtestado: () => void;
  onExames: () => void;
  onEncaminhamento: () => void;
  onFinalizar: () => void;
  disabled: boolean;
  finalizando: boolean;
}

// Estados de validação
export interface ValidacoesState {
  anamnese: boolean;
  antecedentes: boolean;
  medicamentos: boolean;
  alergias: boolean;
}

// Re-exportar tipos da API
export type {
  CardListItem,
  BriefingPaciente,
  HistoricoConsulta,
  SOAPResponse,
  ConsultaResponse,
  SinaisVitais,
};
