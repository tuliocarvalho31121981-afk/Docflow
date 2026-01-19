-- =============================================================================
-- SEED: Modelos de Documentos / Receituários
-- Extraído do sistema MEDX em 19/01/2026
-- =============================================================================

-- Variável para a clínica (DAG Serviços Médicos)
DO $$
DECLARE
    v_clinica_id UUID := 'a9a6f406-3b46-4dab-b810-6c25d62f743b';
BEGIN

-- =============================================================================
-- ATESTADOS
-- =============================================================================

INSERT INTO modelos_documentos (clinica_id, categoria, titulo, conteudo) VALUES
(v_clinica_id, 'Atestados', 'Aptidão física',
'ATESTADO

Atesto para os devidos fins, que o paciente supra citado encontra-se apto para a prática de atividades físicas não competitivas, de acordo com exame exclusivamente clínico.

Atenciosamente'),

(v_clinica_id, 'Atestados', 'Dispensa do trabalho',
'ATESTADO

Atesto para os devidos fins, que o paciente supra citado esteve sob cuidados médicos no período de ________________.

Atenciosamente,'),

(v_clinica_id, 'Atestados', 'Licença dia (repouso)',
'ATESTADO

ATESTO PARA OS DEVIDOS FINS QUE O PACIENTE ACIMA FOI POR MIM ATENDIDO HOJE NECESSITANDO O MESMO DE TERAPÊUTICA ADEQUADA E REPOUSO NO DIA DE HOJE.'),

(v_clinica_id, 'Atestados', 'Recibo',
'RECIBO

Recebi a quantia de R$ __________ (______________________ Reais) do Sr(a) supra citado(a), referente aos honorários de consulta médica.');

-- =============================================================================
-- EXAMES
-- =============================================================================

INSERT INTO modelos_documentos (clinica_id, categoria, titulo, conteudo) VALUES
(v_clinica_id, 'Exames', 'ECO DCV VENOSO TESTE',
'DOPPLER COLORIDO DE CAROTIDAS E VERTEBRAIS
DOPPLER COLORIDO VENOSO DOS MEMBROS INFERIORES
TESTE ERGOMETRICO

IND: AVALIAÇÃO CARDIOLÓGICA / PVM ? / LIPOTÍMIA A ESCLARECER / VARIZES / DOR NOS MMII / EDEMA'),

(v_clinica_id, 'Exames', 'Exame de Sangue Nutrição',
'Solicito os seguintes exames:

Vitamina B12
Vitamina D
Vitamina C
Ferro
Ferritina
Transferrina
Selênio
Magnésio
Manganês
Zinco
Alumínio
Mercúrio
Chumbo
Potássio
Sódio'),

(v_clinica_id, 'Exames', 'Fezes e urina',
'Solicito os seguintes exames:

FEZES
Parasitológico de Fezes (MIF)
Sangue oculto nas fezes

URINA
Elementos Anormais e Sedimentos'),

(v_clinica_id, 'Exames', 'Ginecológico',
'Solicito os seguintes exames:

Mamografia (preferencialmente > 35 anos)
U.S.G. das Mamas (preferencialmente < 35 anos)
Preventivo de Câncer de Colo de Útero'),

(v_clinica_id, 'Exames', 'MAPA - Avaliação Terapêutica',
'SOLICITO

MAPA 24 H

IND: HAS – AVALIAÇÃO TERAPEUTICA'),

(v_clinica_id, 'Exames', 'MAPA - Jaleco Branco',
'SOLICITO

MAPA 24 H

IND: HIPERTENSÃO DO JALECO BRANCO'),

(v_clinica_id, 'Exames', 'PFR - Prova Função Respiratória',
'SOLICITO

PROVA DE FUNÇÃO RESPIRATORIA

IND: DISPNÉIA + TABAGISMO'),

(v_clinica_id, 'Exames', 'Sangue Homem',
'Solicito os seguintes exames:

Hemograma
Glicose, Uréia, Creatinina e Ácido Úrico
Fibrinogênio
Ferritina
Proteína C reativa (ultra-sensível)
Homocisteína
Apolipoproteína A1, B e E
Lipidograma (Colesterol total, HDL, LDL, VLDL, triglicerídeos)
Transaminases e Gama gt
Bilirrubinas
Proteínas totais e frações
Testosterona total e livre
FSH, LH e Estradiol'),

(v_clinica_id, 'Exames', 'Sangue Mulher',
'Solicito os seguintes exames:

Hemograma
Glicose, Uréia, Creatinina e Ácido Úrico
Fibrinogênio
Ferritina
Proteína C reativa (ultra-sensível)
Homocisteína
Apolipoproteína A1, B e E
Lipidograma (Colesterol total, HDL, LDL, VLDL, triglicerídeos)
Transaminases e Gama gt
Bilirrubinas
Proteínas totais e frações
Testosterona total e livre
FSH, LH e Estradiol'),

(v_clinica_id, 'Exames', 'Teste Ergométrico',
'SOLICITO

TESTE ERGOMÉTRICO

IND: AVALIAÇÃO DA P.A AO ESFORÇO'),

(v_clinica_id, 'Exames', 'Tomografia Computadorizada Tórax',
'SOLICITO

TOMOGRAFIA COMPUTADORIZADA DE TORAX

IND: DISPNEIA DESPROPORCIONAL AO ESFORÇO + TABAGISTA COM CARGA TABAGICA ELEVADA > 50 MAÇOS ANO E TOSSE CRONICA'),

(v_clinica_id, 'Exames', 'USG Abdome',
'SOLICITO

USG ABDOMINAL TOTAL

IND: DOR ABDOMINAL DIFUSA A ESCLARECER'),

(v_clinica_id, 'Exames', 'USG Abdome e Tireoide',
'SOLICITO

USG ABDOMINAL TOTAL
USG TIREOIDE COM DOPPLER COLORIDO

IND: AVALIAÇÃO DE DOR ABDOMINAL DIFUSA À ESCLARECER E NODULOS A PALPACAO DA TIREOIDE');

-- =============================================================================
-- ORIENTAÇÕES MÉDICAS
-- =============================================================================

INSERT INTO modelos_documentos (clinica_id, categoria, titulo, conteudo) VALUES
(v_clinica_id, 'Orientações Médicas', 'Ansiedade e Estresse',
'ANSIEDADE E ESTRESSE

O estilo de vida contribui de forma fundamental para o tratamento e prevenção dos estados ansiosos. A alimentação equilibrada, manter distância do tabagismo e das bebidas alcoólicas, o equilíbrio entre atividade física e descanso, a descoberta de atividades físicas prazerosas como esportes, a qualidade do sono, o relacionamento harmônico em casa e no trabalho, atividades altruístas, enfim, todos os fatores que contribuem para melhoria da qualidade de vida e combatem a ansiedade.

Recomendações:

1- Medicamentos fitoterápicos - Opte como última alternativa, por medicamentos que não causem dependência química nem efeitos colaterais

2- Sono profundo - É durante a fase de sono profundo que o organismo recupera suas energias. Portanto, um sono profundo é fundamental para termos tranquilidade, ânimo e energia. Acordar pela manhã bem disposto é um passo importante para combater a ansiedade. Para uma boa noite de sono, precisamos de um ambiente o mais isento possível de ruídos, luminosidade e energia eletromagnética de aparelhos eletrônicos. Chás adoçados e leite quente acompanhando um bom livro, são ótimos para iniciar uma boa noite de sono.

3- Dieta sem açúcar - O açúcar e os carboidratos simples como doces e bolos produzem níveis elevados de insulina no sangue que favorece a ansiedade.

4- O estresse crônico faz com que o organismo produza principalmente adrenalina e cortisol, que além de deprimirem profundamente o sistema imunológico promovem um desajuste em todo o sistema hormonal. Doenças como a hipertensão arterial e a gastrite são exemplos do efeito deletério ao organismo da perpetuação dos estados de tensão mental e emocional. Pratique regularmente alguma atividade que relaxe a mente como Meditação, Yoga, Relaxamento.'),

(v_clinica_id, 'Orientações Médicas', 'Constipação Intestinal',
'CONSTIPAÇÃO INTESTINAL

Para o bom funcionamento do nosso organismo, manutenção da saúde e longevidade com qualidade de vida, é de vital importância a eliminação das toxinas e resíduos do metabolismo. Para que isso ocorra é necessário termos, no mínimo, uma eliminação do conteúdo intestinal todos os dias. O resultado do acúmulo de toxinas em decorrência da irregularidade no trânsito intestinal, reflete-se das formas mais variadas: Acne, envelhecimento precoce da pele, digestão lenta, má assimilação com carência de nutrientes, fadiga crônica, colon irritável, tensão pré-menstrual, irritabilidade, câncer, são alguns exemplos.

Causas de Constipação:
- Alimento refinado com baixos teores de fibra
- Quantidades insuficientes de líquidos
- Vida sedentária
- Medicamentos: antiácidos, antidepressivos, anticonvulsivantes, diuréticos etc.

Recomendações para prevenção e tratamento:

1- Regularizar o ritmo intestinal, indo ao banheiro no mesmo horário todos os dias, mesmo sem vontade.

2- Beber pelo menos 2 litros de água mineral de boa qualidade ao dia.

3- Praticar atividades físicas regulares.

4- Misturar quantidades iguais de Semente de linhaça + Farelo de trigo + Farelo de aveia e bater no liquidificador - Tomar 1 colher de sopa no alimento ou em suco.'),

(v_clinica_id, 'Orientações Médicas', 'Injetáveis IM',
'USO INTRAMUSCULAR

L-ARGININA 50% + LIDOCAINA 1% - 2ML --------- 10 AMPOLAS
L-ORNITINA 300 MG - 2 ML -------------------------- 10 AMPOLAS
L-CARNITINA 600 MG - 2 ML ------------------------- 10 AMPOLAS
INOSITOL 10% + TAURINA 10% - 2 ML ------------ 10 AMPOLAS
HMB 150 MG - 2 ML -------------------------------------- 10 AMPOLAS

APLICAR EM REGIÃO GLÚTEA 1 X SEMANA POR 10 SEMANAS');

-- =============================================================================
-- RECEITAS (Templates em branco para prescrições)
-- =============================================================================

INSERT INTO modelos_documentos (clinica_id, categoria, titulo, conteudo) VALUES
(v_clinica_id, 'Receitas', 'Receita Simples',
'USO ORAL                                    USO CONTÍNUO

1- _________________________________________________

2- _________________________________________________

3- _________________________________________________

4- _________________________________________________

5- _________________________________________________'),

(v_clinica_id, 'Receitas', 'Receita com Vitaminas do Complexo B',
'USO ORAL                                    USO CONTÍNUO

1- _______________________________________________

2-
   Tiamina           20mg        Riboflavina        10mg
   Niacinamida       15mg        Ac Pantotenico     20mg
   Piridoxina        25mg        5MTHF              0,5mg
   Paba              30mg        Biotina            50 mcg
   Metilcobalamina   1000mcg

   Mande 30 cápsulas            Tomar uma cápsula ao dia.

3- _______________________________________________');

END $$;

-- Verificar inserção
SELECT categoria, COUNT(*) as total
FROM modelos_documentos
GROUP BY categoria
ORDER BY categoria;
