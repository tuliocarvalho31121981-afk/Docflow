// Dados de Mock para desenvolvimento do Cockpit do Médico

import { CardListItem, BriefingPaciente, HistoricoConsulta, SOAPResponse, ConsultaResponse } from '@/lib/api';
import { ExameLaboratorial, Anamnese } from './types';

export const MOCK_PACIENTES_FILA: CardListItem[] = [
  {
    id: 'mock-1',
    fase: 2,
    coluna: 'em_atendimento',
    status: 'em_atendimento',
    prioridade: 'normal',
    paciente_nome: 'Maria Silva Santos',
    paciente_telefone: '(11) 99123-4567',
    hora_agendamento: '08:30',
    tipo_consulta: 'Retorno',
    tentativa_reativacao: 0,
    checklist_total: 5,
    checklist_concluido: 5,
    tempo_espera_minutos: 5
  },
  {
    id: 'mock-2',
    fase: 2,
    coluna: 'em_espera',
    status: 'aguardando',
    prioridade: 'alta',
    cor_alerta: 'yellow',
    paciente_nome: 'João Carlos Oliveira',
    paciente_telefone: '(11) 98765-4321',
    hora_agendamento: '09:00',
    tipo_consulta: 'Primeira Consulta',
    tentativa_reativacao: 0,
    checklist_total: 5,
    checklist_concluido: 4,
    tempo_espera_minutos: 12
  },
  {
    id: 'mock-3',
    fase: 2,
    coluna: 'aguardando_checkin',
    status: 'aguardando_checkin',
    prioridade: 'normal',
    paciente_nome: 'Ana Paula Ferreira',
    paciente_telefone: '(11) 91234-5678',
    hora_agendamento: '09:30',
    tipo_consulta: 'Retorno',
    tentativa_reativacao: 0,
    checklist_total: 5,
    checklist_concluido: 5,
    tempo_espera_minutos: 0
  },
  {
    id: 'mock-4',
    fase: 2,
    coluna: 'aguardando_checkin',
    status: 'aguardando_checkin',
    prioridade: 'normal',
    paciente_nome: 'Roberto Mendes',
    paciente_telefone: '(11) 95555-1234',
    hora_agendamento: '10:00',
    tipo_consulta: 'Avaliação Cardiológica',
    tentativa_reativacao: 0,
    checklist_total: 5,
    checklist_concluido: 3,
    tempo_espera_minutos: 0
  },
  {
    id: 'mock-5',
    fase: 2,
    coluna: 'aguardando_checkin',
    status: 'aguardando_checkin',
    prioridade: 'normal',
    paciente_nome: 'Fernanda Lima Costa',
    paciente_telefone: '(11) 94444-5555',
    hora_agendamento: '10:30',
    tipo_consulta: 'Retorno',
    tentativa_reativacao: 0,
    checklist_total: 5,
    checklist_concluido: 5,
    tempo_espera_minutos: 0
  }
];

export const MOCK_BRIEFING: BriefingPaciente = {
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

export const MOCK_HISTORICO: HistoricoConsulta[] = [
  {
    id: 'cons-001',
    data: '2024-01-10',
    medico_nome: 'Carlos Eduardo',
    motivo: 'Consulta de rotina - Hipertensão',
    diagnostico: 'Hipertensão arterial sistêmica estágio 1',
    tem_soap: true,
    tem_receita: true,
    tem_atestado: false,
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
    tem_atestado: false,
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
    tem_atestado: true,
    tem_exames: true
  }
];

export const MOCK_SOAP: SOAPResponse = {
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
  assinado: false,
  created_at: '2024-01-19T08:30:00',
  updated_at: '2024-01-19T09:15:00'
};

export const MOCK_CONSULTA: ConsultaResponse = {
  id: 'cons-atual',
  clinica_id: 'clinica-001',
  paciente_id: 'pac-001',
  medico_id: 'medico-001',
  data_consulta: new Date().toISOString().split('T')[0],
  hora_inicio: '08:30',
  tipo_consulta: 'Retorno',
  status: 'em_andamento',
  paciente_nome: 'Maria Silva Santos',
  medico_nome: 'Dr. Carlos Eduardo',
  created_at: '2024-01-19T08:00:00',
  updated_at: '2024-01-19T08:30:00'
};

export const MOCK_ANAMNESE: Anamnese = {
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

export const MOCK_EXAMES_LAB: ExameLaboratorial[] = [
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

export const MOCK_TRANSCRICAO = `[00:00] Dr. Carlos: Bom dia, dona Maria. Como a senhora está se sentindo?

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

// Simulação de frases para transcrição em tempo real (modo demo)
export const TRANSCRICAO_SIMULADA = [
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
