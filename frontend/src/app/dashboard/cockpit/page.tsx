'use client';

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  User, Clock, AlertTriangle, Pill, FileText, Stethoscope,
  CheckCircle, XCircle, Edit3, ChevronDown, ChevronRight, ChevronLeft, ChevronUp,
  Activity, Heart, Thermometer, Scale, Ruler, Droplet,
  Plus, Send, Printer, Download, RefreshCw, Play, Square,
  ClipboardList, FileCheck, TestTube, ArrowRight, Sparkles,
  History, Calendar, Phone, Building2, Eye, X, Zap,
  Percent, Timer, Waves, Save, Mic, MicOff, Volume2, Users
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  api,
  CardKanbanResponse,
  CardListItem,
  BriefingPaciente,
  HistoricoConsulta,
  SOAPResponse,
  ConsultaResponse,
  SinaisVitais
} from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { ModeloSelector } from '@/components/modelos';

// ==========================================
// MOCK DATA - Dados de exemplo para visualização
// ==========================================

const MOCK_PACIENTES_FILA: CardListItem[] = [
  {
    id: 'mock-1',
    paciente_id: 'pac-001',
    paciente_nome: 'Maria Silva Santos',
    hora_agendamento: '08:30',
    tipo_consulta: 'Retorno',
    coluna: 'em_atendimento',
    tempo_espera_minutos: 5
  },
  {
    id: 'mock-2',
    paciente_id: 'pac-002',
    paciente_nome: 'João Carlos Oliveira',
    hora_agendamento: '09:00',
    tipo_consulta: 'Primeira Consulta',
    coluna: 'em_espera',
    tempo_espera_minutos: 12
  },
  {
    id: 'mock-3',
    paciente_id: 'pac-003',
    paciente_nome: 'Ana Paula Ferreira',
    hora_agendamento: '09:30',
    tipo_consulta: 'Retorno',
    coluna: 'aguardando_checkin',
    tempo_espera_minutos: 0
  },
  {
    id: 'mock-4',
    paciente_id: 'pac-004',
    paciente_nome: 'Roberto Mendes',
    hora_agendamento: '10:00',
    tipo_consulta: 'Avaliação Cardiológica',
    coluna: 'aguardando_checkin',
    tempo_espera_minutos: 0
  },
  {
    id: 'mock-5',
    paciente_id: 'pac-005',
    paciente_nome: 'Fernanda Lima Costa',
    hora_agendamento: '10:30',
    tipo_consulta: 'Retorno',
    coluna: 'aguardando_checkin',
    tempo_espera_minutos: 0
  }
];

const MOCK_BRIEFING: BriefingPaciente = {
  paciente_id: 'pac-001',
  nome: 'Maria Silva Santos',
  idade: 58,
  sexo: 'Feminino',
  telefone: '(11) 99123-4567',
  convenio: 'Unimed',
  data_nascimento: '1966-03-15',
  alergias: ['Dipirona', 'AAS'],
  medicamentos_uso: [
    'Losartana 50mg - 1x ao dia',
    'Atenolol 25mg - 1x ao dia',
    'Sinvastatina 20mg - à noite',
    'AAS 100mg - 1x ao dia (suspenso por alergia)'
  ],
  antecedentes: 'Hipertensão arterial há 10 anos. Dislipidemia em tratamento. Pai faleceu de IAM aos 62 anos. Mãe diabética. Nega tabagismo. Etilismo social ocasional. Sedentária.',
  exames_pendentes: [
    { id: 'ex-1', descricao: 'Ecocardiograma', tipo: 'Imagem', data_solicitacao: '2024-01-10' },
    { id: 'ex-2', descricao: 'Holter 24h', tipo: 'Monitoramento', data_solicitacao: '2024-01-10' }
  ],
  alertas: [
    '⚠️ Alergia a Dipirona e AAS - não prescrever!',
    '🔴 PA elevada na última consulta (160x100)'
  ]
};

const MOCK_HISTORICO: HistoricoConsulta[] = [
  {
    id: 'cons-001',
    data: '2024-01-10',
    medico_nome: 'Carlos Eduardo',
    motivo: 'Consulta de rotina - Hipertensão',
    diagnostico: 'Hipertensão arterial sistêmica estágio 1',
    tem_soap: true,
    tem_receita: true,
    tem_exames: true
  },
  {
    id: 'cons-002',
    data: '2023-10-15',
    medico_nome: 'Carlos Eduardo',
    motivo: 'Avaliação de exames',
    diagnostico: 'Dislipidemia mista',
    tem_soap: true,
    tem_receita: true,
    tem_exames: false
  },
  {
    id: 'cons-003',
    data: '2023-07-20',
    medico_nome: 'Ana Lucia',
    motivo: 'Palpitações',
    diagnostico: 'Extrassístoles ventriculares benignas',
    tem_soap: true,
    tem_receita: false,
    tem_exames: true
  }
];

const MOCK_SOAP: SOAPResponse = {
  id: 'soap-001',
  consulta_id: 'cons-atual',
  subjetivo: `Paciente refere cansaço aos médios esforços há cerca de 2 semanas. Relata dispneia ao subir escadas e ao caminhar distâncias maiores. Nega dor precordial, síncope ou pré-síncope. Refere que está tomando os medicamentos regularmente, mas às vezes esquece o Atenolol. Nega edema de membros inferiores. Relata que a alimentação está "mais ou menos" - tem comido mais sal e gordura nas últimas semanas por conta de viagem.

Questionada sobre sono, refere sono regular, cerca de 6-7 horas por noite, sem despertares noturnos. Nega ortopneia ou dispneia paroxística noturna.`,
  objetivo: `Paciente em bom estado geral, lúcida, orientada, corada, hidratada, anictérica, acianótica.

PA: 148/92 mmHg (sentada, braço E)
FC: 76 bpm, regular
FR: 16 irpm
SpO2: 97% em ar ambiente
Peso: 72 kg | Altura: 1,62m | IMC: 27,4 kg/m²

ACV: Bulhas rítmicas, normofonéticas, sem sopros. Ictus não palpável.
AR: MV presente bilateralmente, sem RA.
Abdome: Plano, flácido, indolor, sem visceromegalias.
MMII: Sem edema, pulsos pediosos palpáveis e simétricos.`,
  avaliacao: `1. Hipertensão arterial sistêmica - atualmente com controle subótimo (PA 148x92). Possível não aderência medicamentosa (esquecimento do Atenolol) associada a transgressão dietética recente.

2. Dislipidemia em tratamento - aguardar resultados de exames para reavaliação.

3. Dispneia aos esforços - a investigar. Pode estar relacionada ao descontrole pressórico e/ou sobrecarga ventricular. Importante avaliar ecocardiograma solicitado.

CID-10 Principal: I10 - Hipertensão essencial (primária)`,
  plano: `1. Reforçar importância da aderência medicamentosa. Orientar uso de alarme/app para lembrete.

2. Orientação dietética: reduzir consumo de sal (< 5g/dia) e gorduras saturadas. Encaminhar para nutricionista.

3. Manter medicações atuais:
   - Losartana 50mg 1x/dia
   - Atenolol 25mg 1x/dia
   - Sinvastatina 20mg à noite

4. Solicitar exames: Perfil lipídico, função renal, eletrólitos.

5. Aguardar resultado do Ecocardiograma e Holter já solicitados.

6. Retorno em 30 dias com exames ou antes se piora dos sintomas.

7. Alertas: Procurar PS se dor torácica, dispneia intensa ou síncope.`,
  exame_fisico: {
    pa_sistolica: 148,
    pa_diastolica: 92,
    fc: 76,
    fr: 16,
    temperatura: 36.2,
    saturacao: 97,
    peso: 72,
    altura: 162,
    imc: 27.4,
    glicemia: 102
  },
  cids: [
    { codigo: 'I10', descricao: 'Hipertensão essencial (primária)', tipo: 'principal' },
    { codigo: 'E78.5', descricao: 'Hiperlipidemia não especificada', tipo: 'secundario' },
    { codigo: 'R06.0', descricao: 'Dispneia', tipo: 'secundario' }
  ],
  gerado_por_ia: true,
  revisado_por_medico: false,
  assinado: false
};

const MOCK_CONSULTA: ConsultaResponse = {
  id: 'cons-atual',
  paciente_id: 'pac-001',
  data: new Date().toISOString(),
  status: 'em_andamento'
};

// Anamnese preenchida pelo paciente
const MOCK_ANAMNESE = {
  data_preenchimento: '2024-01-19T07:45:00',
  queixa_principal: 'Cansaço aos esforços e falta de ar ao subir escadas há 2 semanas',
  inicio_sintomas: 'Há aproximadamente 2 semanas',
  fatores_piora: 'Esforço físico, subir escadas, caminhadas longas',
  fatores_melhora: 'Repouso',
  sintomas_associados: [
    { sintoma: 'Falta de ar', presente: true },
    { sintoma: 'Dor no peito', presente: false },
    { sintoma: 'Palpitações', presente: false },
    { sintoma: 'Tontura', presente: false },
    { sintoma: 'Desmaio', presente: false },
    { sintoma: 'Inchaço nas pernas', presente: false },
    { sintoma: 'Tosse', presente: false },
    { sintoma: 'Cansaço', presente: true },
  ],
  habitos: {
    tabagismo: 'Nunca fumou',
    etilismo: 'Social (1-2x por mês)',
    atividade_fisica: 'Sedentária',
    sono: '6-7 horas por noite, sem problemas',
    alimentacao: 'Regular, mas com excesso de sal nas últimas semanas',
  },
  historico_familiar: [
    { parentesco: 'Pai', condicao: 'Infarto aos 62 anos (falecido)' },
    { parentesco: 'Mãe', condicao: 'Diabetes tipo 2' },
    { parentesco: 'Irmão', condicao: 'Hipertensão' },
  ],
  medicamentos_atuais: [
    { nome: 'Losartana 50mg', posologia: '1x ao dia', horario: 'Manhã', tomando: true },
    { nome: 'Atenolol 25mg', posologia: '1x ao dia', horario: 'Manhã', tomando: false, obs: 'Esquece às vezes' },
    { nome: 'Sinvastatina 20mg', posologia: '1x ao dia', horario: 'Noite', tomando: true },
  ],
  observacoes_paciente: 'Viajei nas últimas semanas e acabei comendo mais sal e gordura do que deveria. Sei que não é bom para a pressão.',
};

// Resumo de exames laboratoriais
const MOCK_EXAMES_LAB: ExameLaboratorial[] = [
  // Perfil Lipídico
  { categoria: 'Perfil Lipídico', nome: 'Colesterol Total', valor: 245, unidade: 'mg/dL', min: null, max: 200, data: '2024-01-15' },
  { categoria: 'Perfil Lipídico', nome: 'HDL', valor: 42, unidade: 'mg/dL', min: 40, max: null, data: '2024-01-15' },
  { categoria: 'Perfil Lipídico', nome: 'LDL', valor: 165, unidade: 'mg/dL', min: null, max: 130, data: '2024-01-15' },
  { categoria: 'Perfil Lipídico', nome: 'Triglicerídeos', valor: 190, unidade: 'mg/dL', min: null, max: 150, data: '2024-01-15' },
  // Função Renal
  { categoria: 'Função Renal', nome: 'Creatinina', valor: 0.9, unidade: 'mg/dL', min: 0.6, max: 1.2, data: '2024-01-15' },
  { categoria: 'Função Renal', nome: 'Ureia', valor: 38, unidade: 'mg/dL', min: 15, max: 40, data: '2024-01-15' },
  { categoria: 'Função Renal', nome: 'TFG', valor: 78, unidade: 'mL/min', min: 90, max: null, data: '2024-01-15' },
  // Eletrólitos
  { categoria: 'Eletrólitos', nome: 'Sódio', valor: 142, unidade: 'mEq/L', min: 136, max: 145, data: '2024-01-15' },
  { categoria: 'Eletrólitos', nome: 'Potássio', valor: 4.8, unidade: 'mEq/L', min: 3.5, max: 5.0, data: '2024-01-15' },
  // Glicemia
  { categoria: 'Glicemia', nome: 'Glicose Jejum', valor: 112, unidade: 'mg/dL', min: 70, max: 99, data: '2024-01-15' },
  { categoria: 'Glicemia', nome: 'Hemoglobina Glicada', valor: 6.2, unidade: '%', min: null, max: 5.7, data: '2024-01-15' },
  // Hemograma
  { categoria: 'Hemograma', nome: 'Hemoglobina', valor: 13.8, unidade: 'g/dL', min: 12.0, max: 16.0, data: '2024-01-15' },
  { categoria: 'Hemograma', nome: 'Hematócrito', valor: 41, unidade: '%', min: 36, max: 46, data: '2024-01-15' },
  // Função Hepática
  { categoria: 'Função Hepática', nome: 'TGO (AST)', valor: 28, unidade: 'U/L', min: null, max: 40, data: '2024-01-15' },
  { categoria: 'Função Hepática', nome: 'TGP (ALT)', valor: 32, unidade: 'U/L', min: null, max: 41, data: '2024-01-15' },
  // Cardíacos
  { categoria: 'Marcadores Cardíacos', nome: 'BNP', valor: 85, unidade: 'pg/mL', min: null, max: 100, data: '2024-01-15' },
  { categoria: 'Marcadores Cardíacos', nome: 'Troponina I', valor: 0.01, unidade: 'ng/mL', min: null, max: 0.04, data: '2024-01-15' },
];

// Tipo para exame laboratorial
interface ExameLaboratorial {
  categoria: string;
  nome: string;
  valor: number;
  unidade: string;
  min: number | null;
  max: number | null;
  data: string;
}

const MOCK_TRANSCRICAO = `[00:00] Dr. Carlos: Bom dia, dona Maria. Como a senhora está se sentindo?

[00:05] Paciente: Bom dia, doutor. Olha, não estou muito bem não. Tenho sentido um cansaço danado essas últimas duas semanas.

[00:12] Dr. Carlos: Cansaço? Me conta mais. Quando acontece esse cansaço?

[00:18] Paciente: É quando eu faço as coisas, sabe? Subir a escada de casa já me deixa ofegante. Antes eu subia numa boa.

[00:28] Dr. Carlos: Entendo. E dor no peito, a senhora sentiu alguma vez?

[00:33] Paciente: Não, doutor. Dor no peito graças a Deus não.

[00:38] Dr. Carlos: E os medicamentos, está tomando todos direitinho?

[00:42] Paciente: Ah doutor, às vezes eu esqueço aquele... como é o nome... Atenolol. Esse eu esqueço de vez em quando.

[00:52] Dr. Carlos: Hmm, entendi. É importante tomar todos os dias, viu? E a alimentação, como está?

[00:58] Paciente: Pois é, viajei mês passado e comi muita besteira. Sei que não pode, mas...

[01:05] Dr. Carlos: Pois é, o sal e a gordura atrapalham bastante o controle da pressão. Vou medir a pressão agora...

[01:15] Dr. Carlos: 148 por 92. Está um pouco elevada. Precisa melhorar esse controle.

[01:22] Paciente: E o que eu faço, doutor?

[01:25] Dr. Carlos: Vamos manter os medicamentos, mas a senhora precisa tomar todos os dias sem falta. Vou dar umas orientações...`;

// ==========================================
// STYLES - Liquid Glass
// ==========================================

function getGlassStyles() {
  return {
    glass: 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl',
    glassStrong: 'bg-white/15 backdrop-blur-2xl border border-white/25 shadow-2xl',
    glassSubtle: 'bg-white/5 backdrop-blur-lg border border-white/10',
    glassDark: 'bg-black/20 backdrop-blur-xl border border-white/10',
  };
}

function getTextStyles() {
  return {
    primary: 'text-white',
    secondary: 'text-white/80',
    muted: 'text-white/60',
    accent: 'text-amber-400',
  };
}

// ==========================================
// COMPONENT: FilaAtendimento (Sidebar)
// ==========================================

interface FilaAtendimentoProps {
  pacientes: CardListItem[];
  pacienteSelecionado: CardListItem | null;
  onSelectPaciente: (paciente: CardListItem) => void;
  loading: boolean;
}

function FilaAtendimento({ pacientes, pacienteSelecionado, onSelectPaciente, loading }: FilaAtendimentoProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  const getStatusColor = (coluna: string) => {
    switch (coluna) {
      case 'aguardando_checkin': return 'bg-blue-500';
      case 'em_espera': return 'bg-yellow-500';
      case 'em_atendimento': return 'bg-green-500';
      case 'finalizado': return 'bg-gray-500';
      default: return 'bg-gray-400';
    }
  };

  const getStatusLabel = (coluna: string) => {
    switch (coluna) {
      case 'aguardando_checkin': return 'Aguard. Check-in';
      case 'em_espera': return 'Em Espera';
      case 'em_atendimento': return 'Em Atendimento';
      case 'finalizado': return 'Finalizado';
      default: return coluna;
    }
  };

  return (
    <div className={cn('w-72 flex-shrink-0 flex flex-col h-full', glass.glass, 'rounded-2xl p-4')}>
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
          <ClipboardList className="w-4 h-4 text-white" />
        </div>
        <div>
          <h2 className={cn('font-semibold', text.primary)}>Fila de Atendimento</h2>
          <p className={cn('text-xs', text.muted)}>{pacientes.length} pacientes hoje</p>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <RefreshCw className={cn('w-6 h-6 animate-spin', text.muted)} />
        </div>
      ) : pacientes.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center gap-2">
          <User className={cn('w-12 h-12', text.muted)} />
          <p className={cn('text-sm text-center', text.muted)}>Nenhum paciente na fila</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-2">
          {pacientes.map((paciente) => (
            <button
              key={paciente.id}
              onClick={() => onSelectPaciente(paciente)}
              className={cn(
                'w-full p-3 rounded-xl text-left transition-all',
                pacienteSelecionado?.id === paciente.id
                  ? 'bg-amber-500/20 ring-2 ring-amber-500'
                  : cn(glass.glassSubtle, 'hover:bg-white/10')
              )}
            >
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                  <span className="text-white font-medium">
                    {paciente.paciente_nome?.charAt(0) || '?'}
                  </span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className={cn('font-medium truncate', text.primary)}>
                    {paciente.paciente_nome || 'Paciente'}
                  </p>
                  <p className={cn('text-xs', text.muted)}>
                    {paciente.hora_agendamento || '--:--'} • {paciente.tipo_consulta || 'Consulta'}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={cn('w-2 h-2 rounded-full', getStatusColor(paciente.coluna))} />
                    <span className={cn('text-xs', text.secondary)}>
                      {getStatusLabel(paciente.coluna)}
                    </span>
                    {paciente.tempo_espera_minutos && paciente.tempo_espera_minutos > 0 && (
                      <span className={cn('text-xs', text.muted)}>
                        • {paciente.tempo_espera_minutos}min
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ==========================================
// COMPONENT: ColunaColapsavel (Expansão Lateral)
// ==========================================

interface ColunaColapsavelProps {
  titulo: string;
  icon: React.ComponentType<{ className?: string }>;
  expanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
  widthExpanded?: string;
  widthCollapsed?: string;
  iconColor?: string;
}

function ColunaColapsavel({
  titulo,
  icon: Icon,
  expanded,
  onToggle,
  children,
  widthExpanded = 'w-80',
  widthCollapsed = 'w-14',
  iconColor = 'from-blue-500 to-purple-600'
}: ColunaColapsavelProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  return (
    <div
      className={cn(
        'flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out overflow-hidden',
        glass.glass,
        'rounded-2xl',
        expanded ? widthExpanded : widthCollapsed
      )}
    >
      {expanded ? (
        // Modo Expandido - Mostra conteúdo completo
        <>
          <div className={cn('flex items-center justify-between p-4 border-b border-white/10', glass.glassSubtle)}>
            <div className="flex items-center gap-3">
              <div className={cn('w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center', iconColor)}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <h2 className={cn('font-bold', text.primary)}>{titulo}</h2>
            </div>
            <button
              onClick={onToggle}
              className={cn('p-2 rounded-lg transition-colors hover:bg-white/10', text.muted)}
              title="Minimizar"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            {children}
          </div>
        </>
      ) : (
        // Modo Colapsado - Mostra apenas ícone com tooltip
        <button
          onClick={onToggle}
          className="flex-1 flex flex-col items-center justify-center gap-2 hover:bg-white/5 transition-colors group relative"
          title={titulo}
        >
          <div className={cn('w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center', iconColor)}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          {/* Tooltip */}
          <div className={cn(
            'absolute left-full ml-2 px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50',
            glass.glassSolid
          )}>
            <span className={cn('text-sm font-medium', text.primary)}>{titulo}</span>
          </div>
        </button>
      )}
    </div>
  );
}

// ==========================================
// COMPONENT: PainelExameFisicoInferior (Expansão Vertical)
// ==========================================

interface PainelExameFisicoInferiorProps {
  sinaisVitais: SinaisVitais;
  onChange: (sinais: SinaisVitais) => void;
  onSave: () => void;
  saving: boolean;
  disabled: boolean;
  saved: boolean;
  expanded: boolean;
  onToggle: () => void;
}

function PainelExameFisicoInferior({
  sinaisVitais,
  onChange,
  onSave,
  saving,
  disabled,
  saved,
  expanded,
  onToggle
}: PainelExameFisicoInferiorProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  const handleChange = (field: keyof SinaisVitais, value: string) => {
    onChange({ ...sinaisVitais, [field]: value });
  };

  return (
    <div
      className={cn(
        'w-full transition-all duration-300 ease-in-out overflow-hidden',
        glass.glass,
        'rounded-2xl',
        expanded ? 'h-48' : 'h-14'
      )}
    >
      {/* Header - sempre visível */}
      <div
        onClick={onToggle}
        className={cn(
          'flex items-center justify-between p-4 cursor-pointer hover:bg-white/5 transition-colors',
          expanded && 'border-b border-white/10'
        )}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className={cn('font-bold', text.primary)}>Exame Físico / Medições</h2>
            {!expanded && sinaisVitais.pressao_arterial && (
              <p className={cn('text-xs', text.muted)}>
                PA: {sinaisVitais.pressao_arterial} | FC: {sinaisVitais.frequencia_cardiaca || '--'} | T: {sinaisVitais.temperatura || '--'}°C
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {expanded && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSave();
              }}
              disabled={disabled || saving}
              className={cn(
                'px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all',
                'bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {saving ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              Salvar
            </button>
          )}
          {saved && (
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs">
              <CheckCircle className="w-3 h-3" />
              Salvo
            </span>
          )}
          {expanded ? (
            <ChevronDown className={cn('w-5 h-5', text.muted)} />
          ) : (
            <ChevronUp className={cn('w-5 h-5', text.muted)} />
          )}
        </div>
      </div>

      {/* Content - visível quando expandido */}
      {expanded && (
        <div className="p-4 grid grid-cols-6 gap-4">
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>Pressão Arterial</label>
            <input
              type="text"
              placeholder="120/80"
              value={sinaisVitais.pressao_arterial || ''}
              onChange={(e) => handleChange('pressao_arterial', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>FC (bpm)</label>
            <input
              type="text"
              placeholder="72"
              value={sinaisVitais.frequencia_cardiaca || ''}
              onChange={(e) => handleChange('frequencia_cardiaca', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>FR (irpm)</label>
            <input
              type="text"
              placeholder="16"
              value={sinaisVitais.frequencia_respiratoria || ''}
              onChange={(e) => handleChange('frequencia_respiratoria', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>Temp (°C)</label>
            <input
              type="text"
              placeholder="36.5"
              value={sinaisVitais.temperatura || ''}
              onChange={(e) => handleChange('temperatura', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>Peso (kg)</label>
            <input
              type="text"
              placeholder="70"
              value={sinaisVitais.peso || ''}
              onChange={(e) => handleChange('peso', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>Altura (cm)</label>
            <input
              type="text"
              placeholder="170"
              value={sinaisVitais.altura || ''}
              onChange={(e) => handleChange('altura', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// COMPONENT: ModalHistoricoConsulta
// ==========================================

interface ModalHistoricoConsultaProps {
  isOpen: boolean;
  onClose: () => void;
  consulta: HistoricoConsulta | null;
  pacienteNome?: string;
}

function ModalHistoricoConsulta({ isOpen, onClose, consulta, pacienteNome }: ModalHistoricoConsultaProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [detalhes, setDetalhes] = useState<{
    soap?: SOAPResponse;
    receitas?: any[];
    exames?: any[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && consulta) {
      carregarDetalhes();
    }
  }, [isOpen, consulta]);

  const carregarDetalhes = async () => {
    if (!consulta) return;

    try {
      setLoading(true);
      // Carregar SOAP da consulta
      const soap = await api.getSOAP(consulta.id).catch(() => null);
      // Carregar receitas
      const receitas = await api.getReceitas(consulta.id).catch(() => []);

      setDetalhes({ soap: soap || undefined, receitas: receitas || [] });
    } catch (error) {
      console.error('Erro ao carregar detalhes:', error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />
      <div className={cn('relative w-full max-w-4xl max-h-[85vh] overflow-hidden', glass.glassStrong, 'rounded-2xl')}>
        {/* Header */}
        <div className={cn('flex items-center justify-between p-4 border-b border-white/10')}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <History className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className={cn('text-lg font-bold', text.primary)}>
                Consulta de {consulta ? new Date(consulta.data).toLocaleDateString('pt-BR') : ''}
              </h2>
              <p className={cn('text-sm', text.muted)}>
                {pacienteNome} {consulta?.medico_nome && `• Dr(a). ${consulta.medico_nome}`}
              </p>
            </div>
          </div>
          <button onClick={onClose} className={cn('p-2 rounded-lg hover:bg-white/10', text.muted)}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto max-h-[calc(85vh-80px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className={cn('w-8 h-8 animate-spin', text.muted)} />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Motivo */}
              {consulta?.motivo && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-2', text.primary)}>Motivo da Consulta</h3>
                  <p className={cn('text-sm', text.secondary)}>{consulta.motivo}</p>
                </div>
              )}

              {/* SOAP */}
              {detalhes?.soap && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-3', text.primary)}>Prontuário SOAP</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {detalhes.soap.subjetivo && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-blue-400 font-medium">[S] Subjetivo</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.subjetivo}</p>
                      </div>
                    )}
                    {detalhes.soap.objetivo && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-green-400 font-medium">[O] Objetivo</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.objetivo}</p>
                      </div>
                    )}
                    {detalhes.soap.avaliacao && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-purple-400 font-medium">[A] Avaliação</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.avaliacao}</p>
                      </div>
                    )}
                    {detalhes.soap.plano && (
                      <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-amber-400 font-medium">[P] Plano</span>
                        </div>
                        <p className={cn('text-sm whitespace-pre-wrap', text.secondary)}>{detalhes.soap.plano}</p>
                      </div>
                    )}
                  </div>

                  {/* Sinais Vitais */}
                  {detalhes.soap.exame_fisico && (
                    <div className="mt-4">
                      <h4 className={cn('font-medium mb-2', text.primary)}>Sinais Vitais</h4>
                      <div className="flex flex-wrap gap-3">
                        {detalhes.soap.exame_fisico.pa_sistolica && detalhes.soap.exame_fisico.pa_diastolica && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>PA:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.pa_sistolica}/{detalhes.soap.exame_fisico.pa_diastolica} mmHg</span>
                          </div>
                        )}
                        {detalhes.soap.exame_fisico.fc && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>FC:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.fc} bpm</span>
                          </div>
                        )}
                        {detalhes.soap.exame_fisico.peso && (
                          <div className={cn('px-3 py-2 rounded-lg', glass.glassDark)}>
                            <span className={text.muted}>Peso:</span>{' '}
                            <span className={text.primary}>{detalhes.soap.exame_fisico.peso} kg</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* CIDs */}
                  {detalhes.soap.cids && detalhes.soap.cids.length > 0 && (
                    <div className="mt-4">
                      <h4 className={cn('font-medium mb-2', text.primary)}>Diagnósticos (CID-10)</h4>
                      <div className="flex flex-wrap gap-2">
                        {detalhes.soap.cids.map((cid, i) => (
                          <span key={i} className={cn('px-2 py-1 rounded text-sm',
                            cid.tipo === 'principal' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'
                          )}>
                            {cid.codigo} - {cid.descricao}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Receitas */}
              {detalhes?.receitas && detalhes.receitas.length > 0 && (
                <div className={cn('p-4 rounded-xl', glass.glassSubtle)}>
                  <h3 className={cn('font-medium mb-3', text.primary)}>Receitas</h3>
                  {detalhes.receitas.map((receita: any, i: number) => (
                    <div key={i} className={cn('p-3 rounded-lg mb-2', glass.glassDark)}>
                      <div className="flex items-center gap-2 mb-2">
                        <Pill className="w-4 h-4 text-green-400" />
                        <span className={cn('font-medium', text.primary)}>Receita {receita.tipo}</span>
                      </div>
                      <div className="space-y-1">
                        {receita.itens?.map((item: any, j: number) => (
                          <p key={j} className={cn('text-sm', text.secondary)}>
                            • {item.medicamento} {item.concentracao} - {item.posologia}
                          </p>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* Sem dados */}
              {!detalhes?.soap && (!detalhes?.receitas || detalhes.receitas.length === 0) && (
                <div className={cn('p-8 text-center', glass.glassSubtle, 'rounded-xl')}>
                  <FileText className={cn('w-12 h-12 mx-auto mb-3', text.muted)} />
                  <p className={text.muted}>Nenhum registro detalhado para esta consulta</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// COMPONENT: PainelExameFisico (Medições)
// ==========================================

interface PainelExameFisicoProps {
  sinaisVitais: SinaisVitais;
  onChange: (sinais: SinaisVitais) => void;
  onSave: () => void;
  saving: boolean;
  disabled: boolean;
  saved?: boolean;
}

function PainelExameFisico({ sinaisVitais, onChange, onSave, saving, disabled, saved }: PainelExameFisicoProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [expanded, setExpanded] = useState(true);
  const [showSaved, setShowSaved] = useState(false);

  // Mostrar indicador de salvo quando saved mudar para true
  useEffect(() => {
    if (saved) {
      setShowSaved(true);
      const timer = setTimeout(() => setShowSaved(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [saved]);

  const handleChange = (campo: keyof SinaisVitais, valor: string) => {
    const numValue = valor === '' ? undefined : parseFloat(valor);
    onChange({ ...sinaisVitais, [campo]: numValue });
  };

  // Calcular IMC automaticamente
  useEffect(() => {
    if (sinaisVitais.peso && sinaisVitais.altura) {
      const alturaMetros = sinaisVitais.altura / 100;
      const imc = sinaisVitais.peso / (alturaMetros * alturaMetros);
      if (Math.abs((sinaisVitais.imc || 0) - imc) > 0.1) {
        onChange({ ...sinaisVitais, imc: Math.round(imc * 10) / 10 });
      }
    }
  }, [sinaisVitais.peso, sinaisVitais.altura]);

  const InputField = ({
    label,
    campo,
    icon: Icon,
    unit,
    placeholder,
    color = 'text-white'
  }: {
    label: string;
    campo: keyof SinaisVitais;
    icon: any;
    unit: string;
    placeholder: string;
    color?: string;
  }) => (
    <div className={cn('p-3 rounded-lg', glass.glassDark)}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={cn('w-4 h-4', color)} />
        <span className={cn('text-xs font-medium', text.muted)}>{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={sinaisVitais[campo] ?? ''}
          onChange={(e) => handleChange(campo, e.target.value)}
          disabled={disabled}
          placeholder={placeholder}
          className={cn(
            'w-full bg-transparent text-lg font-bold outline-none',
            text.primary,
            'placeholder:text-white/30',
            'disabled:opacity-50'
          )}
        />
        <span className={cn('text-sm', text.muted)}>{unit}</span>
      </div>
    </div>
  );

  return (
    <div className={cn('rounded-2xl overflow-hidden', glass.glass)}>
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className={cn('w-full flex items-center justify-between p-4', glass.glassSubtle)}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-pink-600 flex items-center justify-center">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div className="text-left">
            <h2 className={cn('font-bold', text.primary)}>Exame Físico / Medições</h2>
            <p className={cn('text-xs', text.muted)}>Preencha os dados coletados na consulta</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {showSaved && (
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs animate-fade-in">
              <CheckCircle className="w-3 h-3" />
              Salvo
            </span>
          )}
          {!disabled && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                onSave();
              }}
              disabled={saving}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium flex items-center gap-2',
                'bg-gradient-to-r from-green-500 to-emerald-600',
                'hover:from-green-600 hover:to-emerald-700',
                'text-white',
                'disabled:opacity-50',
                showSaved && 'ring-2 ring-green-500/50'
              )}
            >
              {saving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
              Salvar
            </button>
          )}
          {expanded ? (
            <ChevronDown className={cn('w-5 h-5', text.muted)} />
          ) : (
            <ChevronRight className={cn('w-5 h-5', text.muted)} />
          )}
        </div>
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {/* Sinais Vitais */}
          <div className="mb-4">
            <h3 className={cn('text-sm font-medium mb-3 flex items-center gap-2', text.secondary)}>
              <Heart className="w-4 h-4 text-red-400" />
              Sinais Vitais
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-red-400" />
                  <span className={cn('text-xs font-medium', text.muted)}>Pressão Arterial</span>
                </div>
                <div className="flex items-center gap-1">
                  <input
                    type="number"
                    value={sinaisVitais.pa_sistolica ?? ''}
                    onChange={(e) => handleChange('pa_sistolica', e.target.value)}
                    disabled={disabled}
                    placeholder="120"
                    className={cn(
                      'w-14 bg-transparent text-lg font-bold outline-none text-center',
                      text.primary,
                      'placeholder:text-white/30'
                    )}
                  />
                  <span className={text.muted}>/</span>
                  <input
                    type="number"
                    value={sinaisVitais.pa_diastolica ?? ''}
                    onChange={(e) => handleChange('pa_diastolica', e.target.value)}
                    disabled={disabled}
                    placeholder="80"
                    className={cn(
                      'w-14 bg-transparent text-lg font-bold outline-none text-center',
                      text.primary,
                      'placeholder:text-white/30'
                    )}
                  />
                  <span className={cn('text-sm', text.muted)}>mmHg</span>
                </div>
              </div>
              <InputField label="Freq. Cardíaca" campo="fc" icon={Heart} unit="bpm" placeholder="72" color="text-pink-400" />
              <InputField label="Freq. Respiratória" campo="fr" icon={Waves} unit="irpm" placeholder="16" color="text-cyan-400" />
              <InputField label="Temperatura" campo="temperatura" icon={Thermometer} unit="°C" placeholder="36.5" color="text-orange-400" />
              <InputField label="Saturação O₂" campo="saturacao" icon={Droplet} unit="%" placeholder="98" color="text-blue-400" />
              <InputField label="Glicemia" campo="glicemia" icon={Zap} unit="mg/dL" placeholder="100" color="text-yellow-400" />
            </div>
          </div>

          {/* Antropometria */}
          <div className="mb-4">
            <h3 className={cn('text-sm font-medium mb-3 flex items-center gap-2', text.secondary)}>
              <Scale className="w-4 h-4 text-green-400" />
              Antropometria
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <InputField label="Peso" campo="peso" icon={Scale} unit="kg" placeholder="70" color="text-green-400" />
              <InputField label="Altura" campo="altura" icon={Ruler} unit="cm" placeholder="170" color="text-purple-400" />
              <div className={cn('p-3 rounded-lg', glass.glassDark)}>
                <div className="flex items-center gap-2 mb-2">
                  <Percent className="w-4 h-4 text-amber-400" />
                  <span className={cn('text-xs font-medium', text.muted)}>IMC (calculado)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn('text-lg font-bold',
                    sinaisVitais.imc
                      ? sinaisVitais.imc < 18.5 ? 'text-blue-400'
                        : sinaisVitais.imc < 25 ? 'text-green-400'
                        : sinaisVitais.imc < 30 ? 'text-yellow-400'
                        : 'text-red-400'
                      : text.muted
                  )}>
                    {sinaisVitais.imc?.toFixed(1) || '--'}
                  </span>
                  <span className={cn('text-sm', text.muted)}>kg/m²</span>
                </div>
              </div>
            </div>
          </div>

          {/* Observações sobre exames */}
          <div>
            <h3 className={cn('text-sm font-medium mb-3 flex items-center gap-2', text.secondary)}>
              <FileText className="w-4 h-4 text-blue-400" />
              Exames Realizados (ECG, Bioimpedância, etc.)
            </h3>
            <div className={cn('p-3 rounded-lg', glass.glassDark)}>
              <p className={cn('text-xs mb-2', text.muted)}>
                Descreva os resultados de exames realizados na consulta
              </p>
              <textarea
                disabled={disabled}
                placeholder="Ex: ECG normal, ritmo sinusal. Bioimpedância: 22% gordura corporal..."
                className={cn(
                  'w-full min-h-[80px] bg-transparent resize-none outline-none',
                  text.primary,
                  'placeholder:text-white/30',
                  'disabled:opacity-50'
                )}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// COMPONENT: PainelTranscricao
// ==========================================

interface PainelTranscricaoProps {
  transcricao: string;
  gravando: boolean;
  tempoGravacao: number;
  onToggleGravacao: () => void;
  disabled: boolean;
}

function PainelTranscricao({ transcricao, gravando, tempoGravacao, onToggleGravacao, disabled }: PainelTranscricaoProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [expanded, setExpanded] = useState(true);

  const formatTempo = (segundos: number) => {
    const min = Math.floor(segundos / 60);
    const sec = segundos % 60;
    return `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
  };

  return (
    <div className={cn('rounded-2xl overflow-hidden', glass.glass)}>
      {/* Header */}
      <div className={cn('w-full flex items-center justify-between p-4', glass.glassSubtle)}>
        <div
          className="flex items-center gap-3 cursor-pointer flex-1"
          onClick={() => setExpanded(!expanded)}
        >
          <div className={cn(
            'w-10 h-10 rounded-xl flex items-center justify-center transition-all',
            gravando
              ? 'bg-gradient-to-br from-red-500 to-red-600 animate-pulse'
              : 'bg-gradient-to-br from-violet-500 to-purple-600'
          )}>
            {gravando ? <Mic className="w-5 h-5 text-white" /> : <Volume2 className="w-5 h-5 text-white" />}
          </div>
          <div className="text-left">
            <h2 className={cn('font-bold', text.primary)}>Transcrição da Consulta</h2>
            <p className={cn('text-xs flex items-center gap-2', text.muted)}>
              {gravando ? (
                <>
                  <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                  Gravando... {formatTempo(tempoGravacao)}
                </>
              ) : transcricao ? (
                'Transcrição disponível'
              ) : (
                'Clique para iniciar gravação'
              )}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onToggleGravacao}
            disabled={disabled}
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
          <button
            onClick={() => setExpanded(!expanded)}
            className="p-1 hover:bg-white/10 rounded transition-all"
          >
            {expanded ? (
              <ChevronDown className={cn('w-5 h-5', text.muted)} />
            ) : (
              <ChevronRight className={cn('w-5 h-5', text.muted)} />
            )}
          </button>
        </div>
      </div>

      {/* Content */}
      {expanded && (
        <div className="p-4">
          {transcricao ? (
            <div className={cn('p-4 rounded-xl max-h-64 overflow-y-auto', glass.glassDark)}>
              <pre className={cn('text-sm whitespace-pre-wrap font-sans', text.secondary)}>
                {transcricao}
              </pre>
            </div>
          ) : (
            <div className={cn('p-8 rounded-xl text-center', glass.glassDark)}>
              <Mic className={cn('w-12 h-12 mx-auto mb-3', text.muted)} />
              <p className={cn('text-sm', text.muted)}>
                {disabled
                  ? 'Selecione um paciente para iniciar a gravação'
                  : 'Clique em "Gravar" para iniciar a transcrição em tempo real da consulta'
                }
              </p>
              <p className={cn('text-xs mt-2', text.muted)}>
                A IA irá transcrever a conversa e gerar o SOAP automaticamente
              </p>
            </div>
          )}

          {/* Legenda */}
          {transcricao && (
            <div className={cn('flex items-center gap-4 mt-3 text-xs', text.muted)}>
              <span className="flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-400" />
                Transcrição por IA (Whisper)
              </span>
              <span>•</span>
              <span>SOAP gerado automaticamente</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ==========================================
// COMPONENT: SecaoAnamnese
// ==========================================

interface SecaoAnamneseProps {
  anamnese: typeof MOCK_ANAMNESE | null;
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

// ==========================================
// COMPONENT: SecaoExamesLab
// ==========================================

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

// ==========================================
// COMPONENT: PainelPreparado (Esquerda)
// ==========================================

interface PainelPreparadoProps {
  briefing: BriefingPaciente | null;
  historico: HistoricoConsulta[];
  anamnese: typeof MOCK_ANAMNESE | null;
  examesLab: ExameLaboratorial[];
  loading: boolean;
  onVerHistorico: (consulta: HistoricoConsulta) => void;
  // Props de validação
  validacoes: {
    anamnese: boolean;
    antecedentes: boolean;
    medicamentos: boolean;
    alergias: boolean;
  };
  onConferi: (secao: 'anamnese' | 'antecedentes' | 'medicamentos' | 'alergias') => void;
  onEditar: (secao: string, dados: any) => void;
}

function PainelPreparado({ briefing, historico, anamnese, examesLab, loading, onVerHistorico, validacoes, onConferi, onEditar }: PainelPreparadoProps) {
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

        {/* ANAMNESE - Nova seção */}
        <SecaoAnamnese
          anamnese={anamnese}
          expanded={expandedSections.anamnese}
          onToggle={() => toggleSection('anamnese')}
          validado={validacoes.anamnese}
          onConferi={() => onConferi('anamnese')}
          onEditar={(dados) => onEditar('anamnese', dados)}
        />

        {/* EXAMES LABORATORIAIS - Nova seção */}
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

        {/* Histórico de Consultas - COM BOTÃO VER DETALHES */}
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

// ==========================================
// COMPONENT: SOAPField (Campo editável do SOAP)
// ==========================================

interface SOAPFieldProps {
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

function SOAPField({
  label,
  campo,
  valor,
  placeholder,
  icon: Icon,
  isEditing,
  isSaving,
  justSaved,
  editValue,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onChangeValue
}: SOAPFieldProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  return (
    <div className={cn(
      'rounded-lg overflow-hidden transition-all',
      glass.glassSubtle,
      justSaved && 'ring-2 ring-green-500/50'
    )}>
      <div className={cn('flex items-center justify-between p-3 border-b border-white/10')}>
        <div className="flex items-center gap-2">
          <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center',
            campo === 'subjetivo' ? 'bg-blue-500/20' :
            campo === 'objetivo' ? 'bg-green-500/20' :
            campo === 'avaliacao' ? 'bg-purple-500/20' :
            'bg-amber-500/20'
          )}>
            <Icon className={cn('w-4 h-4',
              campo === 'subjetivo' ? 'text-blue-400' :
              campo === 'objetivo' ? 'text-green-400' :
              campo === 'avaliacao' ? 'text-purple-400' :
              'text-amber-400'
            )} />
          </div>
          <span className={cn('font-medium', text.primary)}>[{label.charAt(0)}] {label}</span>
          {justSaved && (
            <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-green-500/20 text-green-400 text-xs animate-fade-in">
              <CheckCircle className="w-3 h-3" />
              Salvo
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {isSaving && (
            <RefreshCw className={cn('w-4 h-4 animate-spin', text.muted)} />
          )}
          {!isEditing && !isSaving && (
            <button
              onClick={onStartEdit}
              className={cn('p-1 rounded hover:bg-white/10 transition-colors', text.muted)}
              title="Editar"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
      <div className="p-3">
        {isEditing ? (
          <div className="space-y-2">
            <textarea
              value={editValue}
              onChange={(e) => onChangeValue(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Escape') {
                  onCancelEdit();
                } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                  e.preventDefault();
                  onSaveEdit();
                }
              }}
              className={cn(
                'w-full min-h-[120px] p-3 rounded-lg resize-none',
                'bg-black/20 border border-white/20',
                text.primary,
                'focus:outline-none focus:ring-2 focus:ring-amber-500',
                'transition-all'
              )}
              placeholder={placeholder}
              autoFocus
            />
            <div className="flex items-center justify-between">
              <p className={cn('text-xs', text.muted)}>
                Pressione Esc para cancelar, Ctrl+Enter para salvar
              </p>
              <div className="flex gap-2">
                <button
                  onClick={onCancelEdit}
                  className={cn('px-3 py-1.5 rounded-lg text-sm flex items-center gap-1', glass.glassSubtle, text.secondary, 'hover:bg-white/10')}
                >
                  <X className="w-3 h-3" />
                  Cancelar
                </button>
                <button
                  onClick={onSaveEdit}
                  className="px-3 py-1.5 rounded-lg text-sm bg-gradient-to-r from-amber-500 to-orange-600 text-white flex items-center gap-1 hover:from-amber-600 hover:to-orange-700 transition-all"
                >
                  <Save className="w-3 h-3" />
                  Salvar
                </button>
              </div>
            </div>
          </div>
        ) : (
          <p className={cn(
            'text-sm whitespace-pre-wrap',
            valor ? text.secondary : text.muted,
            isSaving && 'opacity-50'
          )}>
            {valor || placeholder}
          </p>
        )}
      </div>
    </div>
  );
}

// ==========================================
// COMPONENT: PainelSOAP (Direita)
// ==========================================

interface PainelSOAPProps {
  soap: SOAPResponse | null;
  consulta: ConsultaResponse | null;
  onValidar: () => void;
  onEditar: (campo: string, valor: string) => void;
  loading: boolean;
  validando: boolean;
  savingField?: string | null;
  savedField?: string | null;
}

function PainelSOAP({ soap, consulta, onValidar, onEditar, loading, validando, savingField, savedField }: PainelSOAPProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const handleStartEdit = (campo: string, valorAtual: string) => {
    setEditingField(campo);
    setEditValue(valorAtual || '');
  };

  const handleSaveEdit = () => {
    if (editingField) {
      onEditar(editingField, editValue);
      setEditingField(null);
      setEditValue('');
    }
  };

  const handleCancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  if (loading) {
    return (
      <div className={cn('flex-1 flex items-center justify-center', glass.glass, 'rounded-2xl')}>
        <RefreshCw className={cn('w-8 h-8 animate-spin', text.muted)} />
      </div>
    );
  }

  if (!consulta) {
    return (
      <div className={cn('flex-1 flex flex-col items-center justify-center gap-4', glass.glass, 'rounded-2xl')}>
        <Stethoscope className={cn('w-16 h-16', text.muted)} />
        <p className={cn('text-lg', text.muted)}>Inicie o atendimento para registrar</p>
      </div>
    );
  }

  return (
    <div className={cn('flex-1 flex flex-col min-h-0', glass.glass, 'rounded-2xl')}>
      {/* Header */}
      <div className={cn('p-4 border-b border-white/10 flex-shrink-0', glass.glassSubtle)}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className={cn('text-lg font-bold', text.primary)}>Prontuário SOAP</h2>
              <p className={cn('text-xs', text.muted)}>
                {soap?.gerado_por_ia && (
                  <span className="flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-amber-400" />
                    Gerado por IA - aguardando validação
                  </span>
                )}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {soap?.revisado_por_medico ? (
              <span className={cn(
                'px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1',
                'bg-green-500/20 text-green-400 border border-green-500/30'
              )}>
                <CheckCircle className="w-3 h-3" />
                Validado
              </span>
            ) : (
              <button
                onClick={onValidar}
                disabled={validando}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                  'bg-gradient-to-r from-green-500 to-emerald-600',
                  'hover:from-green-600 hover:to-emerald-700',
                  'text-white shadow-lg',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'flex items-center gap-2'
                )}
              >
                {validando ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                Validar SOAP
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Campos SOAP */}
      <div className="flex-1 overflow-y-auto min-h-0 p-4 space-y-3">
        <SOAPField
          label="Subjetivo"
          campo="subjetivo"
          valor={soap?.subjetivo}
          placeholder="Queixas e história relatada pelo paciente..."
          icon={User}
          isEditing={editingField === 'subjetivo'}
          isSaving={savingField === 'subjetivo'}
          justSaved={savedField === 'subjetivo'}
          editValue={editValue}
          onStartEdit={() => handleStartEdit('subjetivo', soap?.subjetivo || '')}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          onChangeValue={setEditValue}
        />
        <SOAPField
          label="Objetivo"
          campo="objetivo"
          valor={soap?.objetivo}
          placeholder="Exame físico e achados objetivos..."
          icon={Stethoscope}
          isEditing={editingField === 'objetivo'}
          isSaving={savingField === 'objetivo'}
          justSaved={savedField === 'objetivo'}
          editValue={editValue}
          onStartEdit={() => handleStartEdit('objetivo', soap?.objetivo || '')}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          onChangeValue={setEditValue}
        />
        <SOAPField
          label="Avaliação"
          campo="avaliacao"
          valor={soap?.avaliacao}
          placeholder="Hipótese diagnóstica e raciocínio clínico..."
          icon={Activity}
          isEditing={editingField === 'avaliacao'}
          isSaving={savingField === 'avaliacao'}
          justSaved={savedField === 'avaliacao'}
          editValue={editValue}
          onStartEdit={() => handleStartEdit('avaliacao', soap?.avaliacao || '')}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          onChangeValue={setEditValue}
        />
        <SOAPField
          label="Plano"
          campo="plano"
          valor={soap?.plano}
          placeholder="Conduta, prescrições e orientações..."
          icon={ClipboardList}
          isEditing={editingField === 'plano'}
          isSaving={savingField === 'plano'}
          justSaved={savedField === 'plano'}
          editValue={editValue}
          onStartEdit={() => handleStartEdit('plano', soap?.plano || '')}
          onSaveEdit={handleSaveEdit}
          onCancelEdit={handleCancelEdit}
          onChangeValue={setEditValue}
        />

        {/* CIDs */}
        {soap?.cids && soap.cids.length > 0 && (
          <div className={cn('rounded-lg p-4', glass.glassSubtle)}>
            <div className="flex items-center gap-2 mb-3">
              <FileCheck className="w-4 h-4 text-amber-400" />
              <span className={cn('font-medium', text.primary)}>Diagnósticos (CID-10)</span>
            </div>
            <div className="space-y-2">
              {soap.cids.map((cid, i) => (
                <div key={i} className={cn('flex items-center gap-2 text-sm', text.secondary)}>
                  <span className={cn(
                    'px-2 py-0.5 rounded text-xs font-mono',
                    cid.tipo === 'principal' ? 'bg-amber-500/20 text-amber-400' : 'bg-gray-500/20 text-gray-400'
                  )}>
                    {cid.codigo}
                  </span>
                  <span>{cid.descricao}</span>
                  {cid.tipo === 'principal' && (
                    <span className={cn('text-xs', text.muted)}>(Principal)</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ==========================================
// COMPONENT: Toolbar (Ações)
// ==========================================

interface ToolbarProps {
  onReceita: () => void;
  onAtestado: () => void;
  onExames: () => void;
  onEncaminhamento: () => void;
  onFinalizar: () => void;
  disabled: boolean;
  finalizando: boolean;
}

function Toolbar({
  onReceita,
  onAtestado,
  onExames,
  onEncaminhamento,
  onFinalizar,
  disabled,
  finalizando
}: ToolbarProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  const tools = [
    { icon: Pill, label: 'Receita', onClick: onReceita, color: 'from-blue-500 to-cyan-600' },
    { icon: FileText, label: 'Atestado', onClick: onAtestado, color: 'from-green-500 to-emerald-600' },
    { icon: TestTube, label: 'Exames', onClick: onExames, color: 'from-purple-500 to-violet-600' },
    { icon: ArrowRight, label: 'Encaminhar', onClick: onEncaminhamento, color: 'from-orange-500 to-red-600' },
  ];

  return (
    <div className={cn('flex items-center justify-between p-4', glass.glass, 'rounded-2xl')}>
      <div className="flex items-center gap-2">
        {tools.map((tool) => (
          <button
            key={tool.label}
            onClick={tool.onClick}
            disabled={disabled}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl transition-all',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              glass.glassSubtle,
              'hover:bg-white/10'
            )}
          >
            <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br', tool.color)}>
              <tool.icon className="w-4 h-4 text-white" />
            </div>
            <span className={cn('text-sm font-medium', text.primary)}>{tool.label}</span>
          </button>
        ))}
      </div>

      <button
        onClick={onFinalizar}
        disabled={disabled || finalizando}
        className={cn(
          'flex items-center gap-2 px-6 py-3 rounded-xl transition-all',
          'bg-gradient-to-r from-green-500 to-emerald-600',
          'hover:from-green-600 hover:to-emerald-700',
          'text-white font-medium shadow-lg',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {finalizando ? (
          <RefreshCw className="w-5 h-5 animate-spin" />
        ) : (
          <CheckCircle className="w-5 h-5" />
        )}
        Finalizar Consulta
      </button>
    </div>
  );
}

// ==========================================
// MAIN PAGE COMPONENT
// ==========================================

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
  const [anamnese, setAnamnese] = useState<typeof MOCK_ANAMNESE | null>(null);
  const [examesLab, setExamesLab] = useState<ExameLaboratorial[]>([]);

  // Transcrição states
  const [transcricao, setTranscricao] = useState<string>('');
  const [gravando, setGravando] = useState(false);
  const [tempoGravacao, setTempoGravacao] = useState(0);

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
  const [validacoes, setValidacoes] = useState({
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
  const handleConferi = (secao: keyof typeof validacoes) => {
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

      // Se useMockData está ativo, usar dados de exemplo
      if (useMockData) {
        setPacientesFila(MOCK_PACIENTES_FILA);
        // Auto-selecionar primeiro paciente (em atendimento) para demonstração
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

      // Flatten all columns into a single list, sorted by hora
      const todosPacientes: CardListItem[] = [];
      if (response.colunas) {
        Object.values(response.colunas).forEach((cards) => {
          todosPacientes.push(...cards);
        });
      }

      // Sort by hora_agendamento
      todosPacientes.sort((a, b) => {
        if (!a.hora_agendamento) return 1;
        if (!b.hora_agendamento) return -1;
        return a.hora_agendamento.localeCompare(b.hora_agendamento);
      });

      setPacientesFila(todosPacientes);
    } catch (error) {
      console.error('Erro ao carregar fila:', error);
      // Fallback para mock data em caso de erro
      if (useMockData) {
        setPacientesFila(MOCK_PACIENTES_FILA);
      }
    } finally {
      setLoadingFila(false);
    }
  }, [useMockData, pacienteSelecionado]);

  // Carregar dados do paciente selecionado
  const carregarDadosPaciente = useCallback(async (paciente: CardListItem) => {
    if (!paciente.paciente_id) {
      console.warn('Paciente sem ID');
      return;
    }

    try {
      setLoadingBriefing(true);
      setLoadingSOAP(true);

      // Se useMockData está ativo, usar dados de exemplo
      if (useMockData) {
        // Simular delay de carregamento
        await new Promise(resolve => setTimeout(resolve, 300));

        // Para o primeiro paciente (mock-1), usar dados completos
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
          // Para outros pacientes, briefing parcial (simulando paciente diferente)
          setBriefing({
            ...MOCK_BRIEFING,
            paciente_id: paciente.paciente_id!,
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

      // Carregar briefing e histórico em paralelo
      const [briefingData, historicoData] = await Promise.all([
        api.getBriefingPaciente(paciente.paciente_id).catch(() => null),
        api.getHistoricoPaciente(paciente.paciente_id).catch(() => []),
      ]);

      setBriefing(briefingData);
      setHistorico(historicoData || []);
    } catch (error) {
      console.error('Erro ao carregar dados do paciente:', error);
    } finally {
      setLoadingBriefing(false);
      setLoadingSOAP(false);
    }
  }, [useMockData]);

  // Selecionar paciente
  const handleSelectPaciente = (paciente: CardListItem) => {
    setPacienteSelecionado(paciente);
    setBriefing(null);
    setHistorico([]);
    setConsulta(null);
    setSoap(null);
    setSinaisVitais({});
    setTranscricao('');
    setGravando(false);
    setTempoGravacao(0);
    carregarDadosPaciente(paciente);
  };

  // Referência para o MediaRecorder
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Simulação de frases para transcrição em tempo real (modo demo)
  const transcricaoSimulada = [
    '[{time}] Dr. Carlos: Bom dia! Como está se sentindo hoje?',
    '[{time}] Paciente: Bom dia, doutor. Estou me sentindo um pouco cansada.',
    '[{time}] Dr. Carlos: Entendo. Esse cansaço começou quando?',
    '[{time}] Paciente: Há cerca de duas semanas, principalmente quando subo escadas.',
    '[{time}] Dr. Carlos: Está sentindo falta de ar também?',
    '[{time}] Paciente: Sim, um pouco. Quando faço esforço.',
    '[{time}] Dr. Carlos: Vamos verificar sua pressão agora.',
    '[{time}] Dr. Carlos: A pressão está um pouco elevada, 148 por 92.',
    '[{time}] Paciente: É mesmo? Será que é por causa do sal?',
    '[{time}] Dr. Carlos: Pode ser. Vamos revisar sua medicação.',
  ];

  // Toggle gravação
  const handleToggleGravacao = async () => {
    if (gravando) {
      // Parar gravação
      setGravando(false);

      if (!useMockData && mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
        // Em produção, após parar a gravação, os chunks de áudio seriam
        // enviados para a API Whisper para transcrição
      }
    } else {
      // Iniciar gravação
      setGravando(true);
      setTempoGravacao(0);

      if (useMockData) {
        // Modo demo: limpar transcrição anterior para simular nova gravação
        setTranscricao('');
      } else {
        // Modo real: iniciar captura de áudio
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          const mediaRecorder = new MediaRecorder(stream);
          mediaRecorderRef.current = mediaRecorder;
          audioChunksRef.current = [];

          mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
              audioChunksRef.current.push(event.data);
            }
          };

          mediaRecorder.onstop = async () => {
            // Aqui seria feito o envio para a API Whisper
            const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
            console.log('Áudio gravado:', audioBlob.size, 'bytes');
            // TODO: Enviar para api.transcreverAudio(audioBlob)
            stream.getTracks().forEach(track => track.stop());
          };

          mediaRecorder.start(1000); // Capturar em chunks de 1 segundo
        } catch (error) {
          console.error('Erro ao acessar microfone:', error);
          setGravando(false);
        }
      }
    }
  };

  // Timer da gravação + simulação de transcrição em tempo real (modo demo)
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (gravando) {
      interval = setInterval(() => {
        setTempoGravacao(prev => {
          const novoTempo = prev + 1;

          // Modo demo: adicionar frase simulada a cada 5 segundos
          if (useMockData && novoTempo % 5 === 0) {
            const fraseIndex = Math.floor(novoTempo / 5) - 1;
            if (fraseIndex < transcricaoSimulada.length) {
              const min = Math.floor(novoTempo / 60);
              const sec = novoTempo % 60;
              const timeStr = `${min.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`;
              const frase = transcricaoSimulada[fraseIndex].replace('{time}', timeStr);
              setTranscricao(prev => prev ? prev + '\n' + frase : frase);
            }
          }

          return novoTempo;
        });
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [gravando, useMockData]);

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

      // No modo demo, apenas atualiza estado local (mock data não tem UUID válido)
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

      // No modo demo, apenas atualiza estado local (mock data não tem UUID válido)
      if (!useMockData) {
        // Atualizar SOAP e marcar como revisado pelo médico
        await api.atualizarSOAP(soap.id, {
          [campo]: valor,
          revisado_por_medico: true
        });
      }

      // Atualizar estado local
      setSoap(prev => prev ? {
        ...prev,
        [campo]: valor,
        revisado_por_medico: true
      } : null);

      // Mostrar feedback de sucesso
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

      // No modo demo, apenas atualiza estado local
      if (!useMockData) {
        await api.atualizarSOAP(soap.id, { exame_fisico: sinaisVitais });
      }

      setSoap(prev => prev ? { ...prev, exame_fisico: sinaisVitais } : null);

      // Mostrar feedback de salvo
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

    // Verificar se todas as validações foram feitas
    if (!todasValidacoes) {
      alert(`Você precisa confirmar que revisou:\n\n• ${validacoesPendentes.join('\n• ')}\n\nClique no botão ✓ em cada seção do Histórico do Paciente para confirmar.`);
      // Abrir coluna de histórico se estiver fechada
      if (!colunaHistoricoExpanded) {
        setColunaHistoricoExpanded(true);
      }
      return;
    }

    try {
      setFinalizandoConsulta(true);
      await api.finalizarConsulta(consulta.id);
      // Recarregar fila
      await carregarFila();
      // Limpar seleção
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

    // Refresh a cada 30 segundos
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
            {/* Toggle Mock Data - Para demonstração */}
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
              <p className={cn('font-medium', text.primary)}>{user?.nome || 'Dr(a). Carlos Eduardo'}</p>
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
                  </div>
                  <button
                    onClick={handleToggleGravacao}
                    disabled={!pacienteSelecionado}
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
                {transcricao ? (
                  <div className={cn('p-4 rounded-xl flex-1 overflow-y-auto min-h-0', glass.glassDark)}>
                    <pre className={cn('text-sm whitespace-pre-wrap font-sans', text.secondary)}>
                      {transcricao}
                    </pre>
                  </div>
                ) : (
                  <div className={cn('p-8 rounded-xl text-center flex-1 flex flex-col items-center justify-center', glass.glassDark)}>
                    <Mic className={cn('w-12 h-12 mb-3', text.muted)} />
                    <p className={cn('text-sm', text.muted)}>
                      {!pacienteSelecionado
                        ? 'Selecione um paciente'
                        : 'Clique em Gravar para iniciar'}
                    </p>
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
        {editandoSecao && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className={cn('w-full max-w-lg max-h-[80vh] overflow-hidden', glass.glassStrong, 'rounded-2xl')}>
              {/* Header */}
              <div className={cn('flex items-center justify-between p-4 border-b border-white/10')}>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-600 flex items-center justify-center">
                    <Edit3 className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className={cn('font-semibold', text.primary)}>
                      Editar {editandoSecao === 'anamnese' ? 'Anamnese' :
                              editandoSecao === 'medicamentos' ? 'Medicamentos' :
                              editandoSecao === 'antecedentes' ? 'Antecedentes' :
                              editandoSecao === 'alergias' ? 'Alergias' : 'Seção'}
                    </h3>
                    <p className={cn('text-xs', text.muted)}>Atualize as informações do paciente</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setEditandoSecao(null);
                    setDadosEdicao(null);
                  }}
                  className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.muted)}
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Content */}
              <div className="p-4 max-h-[60vh] overflow-y-auto">
                {editandoSecao === 'alergias' && (
                  <div className="space-y-3">
                    <p className={cn('text-sm', text.secondary)}>
                      Alergias atuais: {Array.isArray(dadosEdicao) ? dadosEdicao.join(', ') : 'Nenhuma'}
                    </p>
                    <textarea
                      className={cn(
                        'w-full h-32 p-3 rounded-xl text-sm resize-none',
                        glass.glassDark,
                        text.primary,
                        'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                      )}
                      placeholder="Digite as alergias separadas por vírgula (ex: Dipirona, AAS, Penicilina)"
                      defaultValue={Array.isArray(dadosEdicao) ? dadosEdicao.join(', ') : ''}
                      onChange={(e) => setDadosEdicao(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                    />
                  </div>
                )}

                {editandoSecao === 'medicamentos' && (
                  <div className="space-y-3">
                    <p className={cn('text-sm', text.secondary)}>
                      Medicamentos atuais: {Array.isArray(dadosEdicao) ? dadosEdicao.length : 0}
                    </p>
                    <textarea
                      className={cn(
                        'w-full h-40 p-3 rounded-xl text-sm resize-none',
                        glass.glassDark,
                        text.primary,
                        'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                      )}
                      placeholder="Digite os medicamentos, um por linha (ex: Losartana 50mg 1x/dia)"
                      defaultValue={Array.isArray(dadosEdicao) ? dadosEdicao.join('\n') : ''}
                      onChange={(e) => setDadosEdicao(e.target.value.split('\n').map(s => s.trim()).filter(Boolean))}
                    />
                  </div>
                )}

                {editandoSecao === 'antecedentes' && (
                  <div className="space-y-3">
                    <p className={cn('text-sm', text.secondary)}>
                      Antecedentes pessoais e patológicos
                    </p>
                    <textarea
                      className={cn(
                        'w-full h-40 p-3 rounded-xl text-sm resize-none',
                        glass.glassDark,
                        text.primary,
                        'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                      )}
                      placeholder="Descreva os antecedentes do paciente (ex: HAS há 10 anos, DM2 há 5 anos, IAM em 2020...)"
                      defaultValue={typeof dadosEdicao === 'string' ? dadosEdicao : ''}
                      onChange={(e) => setDadosEdicao(e.target.value)}
                    />
                  </div>
                )}

                {editandoSecao === 'anamnese' && (
                  <div className="space-y-3">
                    <p className={cn('text-sm', text.secondary)}>
                      Edição da anamnese (queixa principal e detalhes)
                    </p>
                    <div className="space-y-3">
                      <div>
                        <label className={cn('text-xs font-medium', text.muted)}>Queixa Principal</label>
                        <textarea
                          className={cn(
                            'w-full h-20 p-3 rounded-xl text-sm resize-none mt-1',
                            glass.glassDark,
                            text.primary,
                            'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                          )}
                          placeholder="Descreva a queixa principal"
                          defaultValue={dadosEdicao?.queixa_principal || ''}
                          onChange={(e) => setDadosEdicao({ ...dadosEdicao, queixa_principal: e.target.value })}
                        />
                      </div>
                      <div>
                        <label className={cn('text-xs font-medium', text.muted)}>Observações adicionais</label>
                        <textarea
                          className={cn(
                            'w-full h-20 p-3 rounded-xl text-sm resize-none mt-1',
                            glass.glassDark,
                            text.primary,
                            'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                          )}
                          placeholder="Observações adicionadas pelo médico"
                          defaultValue={dadosEdicao?.observacoes_medico || ''}
                          onChange={(e) => setDadosEdicao({ ...dadosEdicao, observacoes_medico: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Footer */}
              <div className={cn('flex items-center justify-end gap-3 p-4 border-t border-white/10')}>
                <button
                  onClick={() => {
                    setEditandoSecao(null);
                    setDadosEdicao(null);
                  }}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    glass.glass,
                    'hover:bg-white/10',
                    text.secondary
                  )}
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSalvarEdicao}
                  disabled={salvandoEdicao}
                  className={cn(
                    'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                    'bg-gradient-to-r from-amber-500 to-orange-600',
                    'hover:from-amber-600 hover:to-orange-700',
                    'text-white',
                    'disabled:opacity-50'
                  )}
                >
                  {salvandoEdicao ? (
                    <span className="flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Salvando...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Save className="w-4 h-4" />
                      Salvar
                    </span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

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
