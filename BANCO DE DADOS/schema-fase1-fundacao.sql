-- ============================================================================
-- FASE 1: FUNDAÇÃO
-- ============================================================================
-- Tabelas base que todo o sistema depende
-- Ordem de criação: clinicas → perfis → users → pacientes
-- ============================================================================

-- ============================================================================
-- 1. CLINICAS
-- ============================================================================
-- Tenant principal. Todos os dados pertencem a uma clínica.
-- Mesmo com uma clínica só, essa estrutura permite escalar depois.

CREATE TABLE clinicas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação
    nome VARCHAR(255) NOT NULL,
    nome_fantasia VARCHAR(255),
    cnpj VARCHAR(14) UNIQUE,                    -- Sem pontuação
    
    -- Contato
    telefone VARCHAR(20),
    email VARCHAR(255),
    
    -- Endereço
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(8),                             -- Sem pontuação
    
    -- Configurações
    fuso_horario VARCHAR(50) DEFAULT 'America/Sao_Paulo',
    logo_url TEXT,                              -- URL no storage
    
    -- Configurações financeiras
    saldo_minimo_alerta DECIMAL(10,2) DEFAULT 5000.00,
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_clinicas_cnpj ON clinicas(cnpj);

-- Trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_clinicas_updated_at
    BEFORE UPDATE ON clinicas
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 2. PERFIS
-- ============================================================================
-- Define o que cada tipo de usuário pode fazer.
-- Permissões armazenadas como JSONB para flexibilidade.

CREATE TABLE perfis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(100) NOT NULL,                 -- Ex: "Médico", "Secretária"
    descricao TEXT,
    
    -- Permissões por módulo
    -- Formato: { "modulo": "CLEX" } onde C=Create, L=List/Read, E=Edit, X=Delete
    permissoes JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Flags especiais
    is_admin BOOLEAN DEFAULT false,             -- Acesso total (exceto prontuário)
    is_medico BOOLEAN DEFAULT false,            -- Pode acessar prontuário
    is_sistema BOOLEAN DEFAULT false,           -- Perfil interno (não editável)
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(clinica_id, nome)
);

-- Index
CREATE INDEX idx_perfis_clinica ON perfis(clinica_id);

-- Trigger updated_at
CREATE TRIGGER trigger_perfis_updated_at
    BEFORE UPDATE ON perfis
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Comentário sobre estrutura de permissões
COMMENT ON COLUMN perfis.permissoes IS '
Exemplo de estrutura:
{
    "prontuario": "CLEX",      -- Create, List, Edit, Delete (só médico)
    "agenda": "CLE",           -- Create, List, Edit (sem delete)
    "financeiro": "L",         -- Apenas visualizar
    "usuarios": "-",           -- Sem acesso
    "relatorios": "L"          -- Apenas visualizar
}

Módulos possíveis:
- prontuario
- agenda
- pacientes
- financeiro
- estoque
- convenios
- usuarios
- relatorios
- configuracoes
';


-- ============================================================================
-- 3. USERS
-- ============================================================================
-- Funcionários da clínica. Quem acessa o sistema via login.
-- Integrado com Supabase Auth (auth.users)

CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    perfil_id UUID NOT NULL REFERENCES perfis(id),
    
    -- Identificação
    nome VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),                       -- Para 2FA via SMS
    
    -- Dados profissionais (se aplicável)
    crm VARCHAR(20),                            -- Se médico
    crm_uf CHAR(2),                             -- UF do CRM
    coren VARCHAR(20),                          -- Se enfermagem
    especialidade VARCHAR(100),                 -- Se médico
    
    -- Configurações de acesso
    horario_acesso_inicio TIME,                 -- Restrição de horário
    horario_acesso_fim TIME,
    dias_acesso INTEGER[] DEFAULT '{1,2,3,4,5}', -- 0=Dom, 1=Seg, ..., 6=Sab
    
    -- Configurações pessoais
    avatar_url TEXT,
    preferencias JSONB DEFAULT '{}'::jsonb,     -- Tema, notificações, etc
    
    -- Controle
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'bloqueado')),
    ultimo_acesso TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(email),
    UNIQUE(crm, crm_uf)                         -- CRM único por UF
);

-- Indexes
CREATE INDEX idx_users_clinica ON users(clinica_id);
CREATE INDEX idx_users_perfil ON users(perfil_id);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

-- Trigger updated_at
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 4. PACIENTES
-- ============================================================================
-- Clientes da clínica. Acesso externo via WhatsApp/links.
-- NÃO tem login no sistema.

CREATE TABLE pacientes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinica_id UUID NOT NULL REFERENCES clinicas(id) ON DELETE CASCADE,
    
    -- Identificação
    nome VARCHAR(255) NOT NULL,
    nome_social VARCHAR(255),                   -- Nome preferido
    cpf VARCHAR(11) UNIQUE,                     -- Sem pontuação
    rg VARCHAR(20),
    data_nascimento DATE,
    sexo CHAR(1) CHECK (sexo IN ('M', 'F', 'O')), -- M=Masc, F=Fem, O=Outro
    
    -- Contato (principal canal: WhatsApp)
    telefone VARCHAR(20) NOT NULL,              -- WhatsApp principal
    telefone_secundario VARCHAR(20),
    email VARCHAR(255),
    aceita_whatsapp BOOLEAN DEFAULT true,
    aceita_email BOOLEAN DEFAULT true,
    
    -- Endereço
    logradouro VARCHAR(255),
    numero VARCHAR(20),
    complemento VARCHAR(100),
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    uf CHAR(2),
    cep VARCHAR(8),
    
    -- Dados médicos básicos (visível para todos)
    tipo_sanguineo VARCHAR(5),                  -- A+, O-, etc
    
    -- Contato de emergência
    emergencia_nome VARCHAR(255),
    emergencia_telefone VARCHAR(20),
    emergencia_parentesco VARCHAR(50),
    
    -- Origem/Marketing
    como_conheceu VARCHAR(100),                 -- Indicação, Google, Instagram, etc
    indicado_por UUID REFERENCES pacientes(id), -- Se foi indicação de outro paciente
    
    -- Controle
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'bloqueado')),
    motivo_bloqueio TEXT,                       -- Se bloqueado, por quê
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Quem criou (funcionário OU próprio paciente via WhatsApp)
    created_by_user UUID REFERENCES users(id),
    created_by_self BOOLEAN DEFAULT false       -- true = paciente se cadastrou sozinho
);

-- Indexes
CREATE INDEX idx_pacientes_clinica ON pacientes(clinica_id);
CREATE INDEX idx_pacientes_cpf ON pacientes(cpf);
CREATE INDEX idx_pacientes_telefone ON pacientes(telefone);
CREATE INDEX idx_pacientes_nome ON pacientes(nome);
CREATE INDEX idx_pacientes_status ON pacientes(status);

-- Trigger updated_at
CREATE TRIGGER trigger_pacientes_updated_at
    BEFORE UPDATE ON pacientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();


-- ============================================================================
-- 5. PACIENTES_ALERGIAS
-- ============================================================================
-- Separado porque pode ter múltiplas e é dado CRÍTICO (visível em tudo)

CREATE TABLE pacientes_alergias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    -- Alergia
    substancia VARCHAR(255) NOT NULL,           -- Ex: "Dipirona", "Sulfa", "Frutos do mar"
    tipo VARCHAR(50),                           -- Medicamento, Alimento, Outro
    gravidade VARCHAR(20) DEFAULT 'moderada' CHECK (gravidade IN ('leve', 'moderada', 'grave')),
    reacao TEXT,                                -- Descrição da reação
    
    -- Controle
    confirmada BOOLEAN DEFAULT false,           -- Confirmada por médico
    confirmada_por UUID REFERENCES users(id),
    confirmada_em TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id),
    created_by_self BOOLEAN DEFAULT false,
    
    -- Não pode duplicar alergia pro mesmo paciente
    UNIQUE(paciente_id, substancia)
);

-- Index
CREATE INDEX idx_alergias_paciente ON pacientes_alergias(paciente_id);


-- ============================================================================
-- 6. PACIENTES_MEDICAMENTOS
-- ============================================================================
-- Medicamentos de uso contínuo. Dado ALTO (visível para médico + enfermagem)

CREATE TABLE pacientes_medicamentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES pacientes(id) ON DELETE CASCADE,
    
    -- Medicamento
    nome VARCHAR(255) NOT NULL,                 -- Ex: "Losartana 50mg"
    principio_ativo VARCHAR(255),               -- Ex: "Losartana Potássica"
    dosagem VARCHAR(100),                       -- Ex: "50mg"
    posologia VARCHAR(255),                     -- Ex: "1x ao dia, manhã"
    motivo TEXT,                                -- Ex: "Hipertensão"
    
    -- Período
    data_inicio DATE,
    data_fim DATE,                              -- NULL = uso contínuo
    uso_continuo BOOLEAN DEFAULT true,
    
    -- Prescritor
    prescrito_por VARCHAR(255),                 -- Nome do médico (pode ser externo)
    prescrito_por_user UUID REFERENCES users(id), -- Se foi médico da clínica
    
    -- Controle
    ativo BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by_user UUID REFERENCES users(id),
    created_by_self BOOLEAN DEFAULT false
);

-- Index
CREATE INDEX idx_medicamentos_paciente ON pacientes_medicamentos(paciente_id);
CREATE INDEX idx_medicamentos_ativo ON pacientes_medicamentos(paciente_id, ativo);


-- ============================================================================
-- 7. PERFIS PADRÃO (SEED)
-- ============================================================================
-- Função para criar perfis padrão quando uma clínica é criada

CREATE OR REPLACE FUNCTION criar_perfis_padrao(p_clinica_id UUID)
RETURNS void AS $$
BEGIN
    -- Administrador
    INSERT INTO perfis (clinica_id, nome, descricao, is_admin, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Administrador',
        'Acesso total ao sistema, exceto prontuário médico',
        true,
        true,
        '{
            "agenda": "CLEX",
            "pacientes": "CLEX",
            "financeiro": "CLEX",
            "estoque": "CLEX",
            "convenios": "CLEX",
            "usuarios": "CLEX",
            "relatorios": "L",
            "configuracoes": "CLEX"
        }'::jsonb
    );
    
    -- Médico
    INSERT INTO perfis (clinica_id, nome, descricao, is_medico, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Médico',
        'Acesso ao prontuário dos seus pacientes. Prescreve, atesta, solicita exames.',
        true,
        true,
        '{
            "prontuario": "CLEX",
            "agenda": "LE",
            "pacientes": "LE",
            "financeiro": "-",
            "estoque": "L",
            "convenios": "L",
            "usuarios": "-",
            "relatorios": "L",
            "configuracoes": "-"
        }'::jsonb
    );
    
    -- Enfermagem
    INSERT INTO perfis (clinica_id, nome, descricao, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Enfermagem',
        'Triagem, sinais vitais, alergias. Sem acesso a diagnóstico.',
        true,
        '{
            "prontuario": "L",
            "agenda": "L",
            "pacientes": "LE",
            "financeiro": "-",
            "estoque": "LE",
            "convenios": "-",
            "usuarios": "-",
            "relatorios": "-",
            "configuracoes": "-"
        }'::jsonb
    );
    
    -- Secretária
    INSERT INTO perfis (clinica_id, nome, descricao, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Secretária',
        'Agenda, cadastro, convênios, financeiro básico. Sem acesso a prontuário.',
        true,
        '{
            "prontuario": "-",
            "agenda": "CLEX",
            "pacientes": "CLE",
            "financeiro": "CLE",
            "estoque": "CLE",
            "convenios": "CLE",
            "usuarios": "-",
            "relatorios": "L",
            "configuracoes": "-"
        }'::jsonb
    );
    
    -- Financeiro
    INSERT INTO perfis (clinica_id, nome, descricao, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Financeiro',
        'Contas a pagar/receber, faturamento, conciliação. Sem acesso clínico.',
        true,
        '{
            "prontuario": "-",
            "agenda": "L",
            "pacientes": "L",
            "financeiro": "CLEX",
            "estoque": "L",
            "convenios": "CLEX",
            "usuarios": "-",
            "relatorios": "L",
            "configuracoes": "-"
        }'::jsonb
    );
    
    -- Recepção
    INSERT INTO perfis (clinica_id, nome, descricao, is_sistema, permissoes)
    VALUES (
        p_clinica_id,
        'Recepção',
        'Apenas agenda e check-in. Acesso mínimo.',
        true,
        '{
            "prontuario": "-",
            "agenda": "CLE",
            "pacientes": "L",
            "financeiro": "-",
            "estoque": "-",
            "convenios": "-",
            "usuarios": "-",
            "relatorios": "-",
            "configuracoes": "-"
        }'::jsonb
    );
    
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- 8. TRIGGER: CRIAR PERFIS AO CRIAR CLÍNICA
-- ============================================================================

CREATE OR REPLACE FUNCTION on_clinica_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM criar_perfis_padrao(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_clinica_criar_perfis
    AFTER INSERT ON clinicas
    FOR EACH ROW
    EXECUTE FUNCTION on_clinica_created();


-- ============================================================================
-- 9. ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Habilita RLS em todas as tabelas
ALTER TABLE clinicas ENABLE ROW LEVEL SECURITY;
ALTER TABLE perfis ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes_alergias ENABLE ROW LEVEL SECURITY;
ALTER TABLE pacientes_medicamentos ENABLE ROW LEVEL SECURITY;

-- Policy: Usuário só vê dados da sua clínica
CREATE POLICY "Users veem sua clinica" ON clinicas
    FOR ALL USING (
        id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "Users veem perfis da sua clinica" ON perfis
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "Users veem users da sua clinica" ON users
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "Users veem pacientes da sua clinica" ON pacientes
    FOR ALL USING (
        clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
    );

CREATE POLICY "Users veem alergias de pacientes da sua clinica" ON pacientes_alergias
    FOR ALL USING (
        paciente_id IN (
            SELECT id FROM pacientes 
            WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        )
    );

CREATE POLICY "Users veem medicamentos de pacientes da sua clinica" ON pacientes_medicamentos
    FOR ALL USING (
        paciente_id IN (
            SELECT id FROM pacientes 
            WHERE clinica_id IN (SELECT clinica_id FROM users WHERE id = auth.uid())
        )
    );


-- ============================================================================
-- FIM DA FASE 1
-- ============================================================================
