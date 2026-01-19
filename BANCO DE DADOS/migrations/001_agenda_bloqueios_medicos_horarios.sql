-- ============================================================================
-- MIGRAÇÃO: Criação das tabelas agenda_bloqueios e medicos_horarios
-- ============================================================================
-- Data: 2024
-- Descrição: Cria as tabelas para bloqueios de agenda e horários dos médicos
-- ============================================================================

-- Verificar se a função update_updated_at existe (necessária para triggers)
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 1. MEDICOS_HORARIOS
-- ============================================================================
-- Template semanal de cada médico. Define quando ele atende.
-- Nome alternativo: horarios_disponiveis (mantido para compatibilidade)

CREATE TABLE IF NOT EXISTS medicos_horarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    medico_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Dia da semana (0=Domingo, 1=Segunda, ..., 6=Sábado)
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),

    -- Período
    hora_inicio TIME NOT NULL,
    hora_fim TIME NOT NULL,

    -- Configurações do período
    intervalo_minutos INTEGER DEFAULT 30,       -- Duração padrão do slot
    vagas_por_horario INTEGER DEFAULT 1,        -- Quantos pacientes por slot (geralmente 1)

    -- Tipos de consulta aceitos neste horário
    tipos_consulta_ids UUID[] DEFAULT '{}',     -- Se vazio, aceita todos

    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Validação: hora_fim > hora_inicio
    CONSTRAINT medicos_horarios_horario_valido CHECK (hora_fim > hora_inicio)
);

-- Indexes para medicos_horarios
CREATE INDEX IF NOT EXISTS idx_medicos_horarios_clinica ON medicos_horarios(clinica_id);
CREATE INDEX IF NOT EXISTS idx_medicos_horarios_medico ON medicos_horarios(medico_id);
CREATE INDEX IF NOT EXISTS idx_medicos_horarios_dia ON medicos_horarios(dia_semana);
CREATE INDEX IF NOT EXISTS idx_medicos_horarios_ativo ON medicos_horarios(ativo) WHERE ativo = true;

-- Trigger updated_at para medicos_horarios
DROP TRIGGER IF EXISTS trigger_medicos_horarios_updated_at ON medicos_horarios;
CREATE TRIGGER trigger_medicos_horarios_updated_at
    BEFORE UPDATE ON medicos_horarios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Comentários
COMMENT ON TABLE medicos_horarios IS 'Horários semanais de disponibilidade dos médicos';
COMMENT ON COLUMN medicos_horarios.dia_semana IS '0=Domingo, 1=Segunda, 2=Terça, 3=Quarta, 4=Quinta, 5=Sexta, 6=Sábado';
COMMENT ON COLUMN medicos_horarios.intervalo_minutos IS 'Duração padrão de cada slot de agendamento';
COMMENT ON COLUMN medicos_horarios.vagas_por_horario IS 'Quantos pacientes podem ser agendados no mesmo horário';
COMMENT ON COLUMN medicos_horarios.tipos_consulta_ids IS 'Array de UUIDs dos tipos de consulta aceitos. Vazio = aceita todos';

-- ============================================================================
-- 2. AGENDA_BLOQUEIOS
-- ============================================================================
-- Exceções: férias, feriados, compromissos, etc.
-- Nome alternativo: bloqueios_agenda (mantido para compatibilidade)

CREATE TABLE IF NOT EXISTS agenda_bloqueios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,

    -- Escopo do bloqueio
    medico_id UUID REFERENCES users(id) ON DELETE CASCADE,  -- NULL = bloqueio para toda a clínica

    -- Período
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    hora_inicio TIME,                           -- NULL = dia inteiro
    hora_fim TIME,                              -- NULL = dia inteiro

    -- Identificação
    motivo VARCHAR(255) NOT NULL,               -- Ex: "Férias", "Congresso", "Feriado"
    tipo VARCHAR(50) DEFAULT 'bloqueio' CHECK (tipo IN ('bloqueio', 'feriado', 'ferias', 'congresso', 'pessoal', 'outro')),

    -- Recorrência (para feriados anuais)
    recorrente_anual BOOLEAN DEFAULT false,     -- Repete todo ano na mesma data?

    -- Controle
    ativo BOOLEAN DEFAULT true,                 -- Para soft delete
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),        -- Quem criou o bloqueio

    -- Validação
    CONSTRAINT agenda_bloqueios_data_valida CHECK (data_fim >= data_inicio),
    CONSTRAINT agenda_bloqueios_hora_valida CHECK (
        (hora_inicio IS NULL AND hora_fim IS NULL) OR
        (hora_inicio IS NOT NULL AND hora_fim IS NOT NULL AND hora_fim > hora_inicio)
    )
);

-- Indexes para agenda_bloqueios
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_clinica ON agenda_bloqueios(clinica_id);
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_medico ON agenda_bloqueios(medico_id);
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_data ON agenda_bloqueios(data_inicio, data_fim);
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_periodo ON agenda_bloqueios(data_inicio, data_fim, medico_id);
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_ativo ON agenda_bloqueios(ativo) WHERE ativo = true;
CREATE INDEX IF NOT EXISTS idx_agenda_bloqueios_tipo ON agenda_bloqueios(tipo);

-- Trigger updated_at para agenda_bloqueios
DROP TRIGGER IF EXISTS trigger_agenda_bloqueios_updated_at ON agenda_bloqueios;
CREATE TRIGGER trigger_agenda_bloqueios_updated_at
    BEFORE UPDATE ON agenda_bloqueios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Comentários
COMMENT ON TABLE agenda_bloqueios IS 'Bloqueios de agenda (férias, feriados, compromissos)';
COMMENT ON COLUMN agenda_bloqueios.medico_id IS 'NULL = bloqueio para toda a clínica, UUID = bloqueio específico do médico';
COMMENT ON COLUMN agenda_bloqueios.hora_inicio IS 'NULL = bloqueio para o dia inteiro';
COMMENT ON COLUMN agenda_bloqueios.recorrente_anual IS 'Se true, repete todo ano na mesma data (útil para feriados)';

-- ============================================================================
-- RLS (Row Level Security) - Se necessário
-- ============================================================================
-- Descomente se usar RLS no Supabase

-- ALTER TABLE medicos_horarios ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE agenda_bloqueios ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Usuários podem ver horários da própria clínica"
--     ON medicos_horarios FOR SELECT
--     USING (clinica_id IN (
--         SELECT clinica_id FROM users WHERE id = auth.uid()
--     ));

-- CREATE POLICY "Usuários podem ver bloqueios da própria clínica"
--     ON agenda_bloqueios FOR SELECT
--     USING (clinica_id IN (
--         SELECT clinica_id FROM users WHERE id = auth.uid()
--     ));

-- ============================================================================
-- FIM DA MIGRAÇÃO
-- ============================================================================
