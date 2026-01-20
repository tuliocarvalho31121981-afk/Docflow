"""
Prontuário - Router
Endpoints da API de prontuário médico.

PERMISSÕES:
- prontuario: C=criar, L=ler, E=editar, X=deletar
- Apenas usuários com perfil is_medico=true podem acessar
"""
from __future__ import annotations

from datetime import date
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, UploadFile, File, HTTPException

from app.core.schemas import PaginatedResponse, SuccessResponse
from app.core.security import CurrentUser, require_permission
from app.prontuario.schemas import (
    # Consultas
    ConsultaCreate,
    ConsultaUpdate,
    ConsultaResponse,
    ConsultaListItem,
    ConsultaIniciar,
    ConsultaFinalizar,
    # Transcrições
    TranscricaoCreate,
    TranscricaoUpdate,
    TranscricaoResponse,
    # SOAP
    ProntuarioSOAPCreate,
    ProntuarioSOAPUpdate,
    ProntuarioSOAPResponse,
    # Receitas
    ReceitaCreate,
    ReceitaUpdate,
    ReceitaResponse,
    # Atestados
    AtestadoCreate,
    AtestadoUpdate,
    AtestadoResponse,
    # Exames
    ExameSolicitadoCreate,
    ExameSolicitadoUpdate,
    ExameSolicitadoResponse,
    ExameSolicitadoBatch,
    # Encaminhamentos
    EncaminhamentoCreate,
    EncaminhamentoUpdate,
    EncaminhamentoResponse,
    # Outros
    BriefingPaciente,
    HistoricoConsulta,
)
from app.prontuario.service import prontuario_service

router = APIRouter(prefix="/prontuario", tags=["Prontuário"])


# ============================================================================
# CONSULTAS
# ============================================================================

@router.get(
    "/consultas",
    response_model=PaginatedResponse[ConsultaListItem],
    summary="Listar Consultas",
)
async def list_consultas(
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    medico_id: Optional[UUID] = Query(default=None, description="Filtrar por médico"),
    data_inicio: Optional[date] = Query(default=None, description="Data inicial"),
    data_fim: Optional[date] = Query(default=None, description="Data final"),
    status: Optional[str] = Query(default=None, description="Status da consulta"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista consultas com filtros."""
    return await prontuario_service.list_consultas(
        current_user=current_user,
        paciente_id=str(paciente_id) if paciente_id else None,
        medico_id=str(medico_id) if medico_id else None,
        data_inicio=data_inicio,
        data_fim=data_fim,
        status=status,
        page=page,
        per_page=per_page
    )


@router.get(
    "/consultas/{consulta_id}",
    response_model=ConsultaResponse,
    summary="Obter Consulta",
)
async def get_consulta(
    consulta_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca consulta por ID."""
    return await prontuario_service.get_consulta(
        id=str(consulta_id),
        current_user=current_user
    )


@router.post(
    "/consultas",
    response_model=ConsultaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Consulta",
)
async def create_consulta(
    data: ConsultaCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Cria nova consulta."""
    return await prontuario_service.create_consulta(
        data=data,
        current_user=current_user
    )


@router.post(
    "/consultas/iniciar",
    response_model=ConsultaResponse,
    summary="Iniciar Consulta",
)
async def iniciar_consulta(
    data: ConsultaIniciar,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Inicia consulta a partir de um agendamento.

    - Cria registro na tabela consultas
    - Atualiza status do agendamento para 'em_atendimento'
    - Registra hora de início
    """
    return await prontuario_service.iniciar_consulta(
        agendamento_id=str(data.agendamento_id),
        current_user=current_user
    )


@router.patch(
    "/consultas/{consulta_id}",
    response_model=ConsultaResponse,
    summary="Atualizar Consulta",
)
async def update_consulta(
    consulta_id: UUID,
    data: ConsultaUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza dados da consulta."""
    return await prontuario_service.update_consulta(
        id=str(consulta_id),
        data=data,
        current_user=current_user
    )


@router.post(
    "/consultas/{consulta_id}/finalizar",
    response_model=ConsultaResponse,
    summary="Finalizar Consulta",
)
async def finalizar_consulta(
    consulta_id: UUID,
    data: Optional[ConsultaFinalizar] = None,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """
    Finaliza consulta.

    - Registra hora de fim
    - Atualiza status para 'finalizada'
    - Atualiza agendamento para 'atendido'
    """
    return await prontuario_service.finalizar_consulta(
        id=str(consulta_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# TRANSCRIÇÕES
# ============================================================================

@router.get(
    "/consultas/{consulta_id}/transcricao",
    response_model=TranscricaoResponse,
    summary="Obter Transcrição",
)
async def get_transcricao(
    consulta_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca transcrição de uma consulta."""
    transcricao = await prontuario_service.get_transcricao(
        consulta_id=str(consulta_id),
        current_user=current_user
    )

    if not transcricao:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Transcrição não encontrada")

    return transcricao


@router.post(
    "/transcricoes",
    response_model=TranscricaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Transcrição",
)
async def create_transcricao(
    data: TranscricaoCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Cria transcrição para uma consulta."""
    return await prontuario_service.create_transcricao(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/transcricoes/{transcricao_id}",
    response_model=TranscricaoResponse,
    summary="Atualizar Transcrição",
)
async def update_transcricao(
    transcricao_id: UUID,
    data: TranscricaoUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza transcrição."""
    return await prontuario_service.update_transcricao(
        id=str(transcricao_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# PRONTUÁRIO SOAP
# ============================================================================

@router.get(
    "/consultas/{consulta_id}/soap",
    response_model=ProntuarioSOAPResponse,
    summary="Obter SOAP",
)
async def get_soap(
    consulta_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca prontuário SOAP de uma consulta."""
    soap = await prontuario_service.get_soap(
        consulta_id=str(consulta_id),
        current_user=current_user
    )

    if not soap:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SOAP não encontrado")

    return soap


@router.post(
    "/soap",
    response_model=ProntuarioSOAPResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar SOAP",
)
async def create_soap(
    data: ProntuarioSOAPCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Cria prontuário SOAP."""
    return await prontuario_service.create_soap(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/soap/{soap_id}",
    response_model=ProntuarioSOAPResponse,
    summary="Atualizar SOAP",
)
async def update_soap(
    soap_id: UUID,
    data: ProntuarioSOAPUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza prontuário SOAP."""
    return await prontuario_service.update_soap(
        id=str(soap_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# RECEITAS
# ============================================================================

@router.get(
    "/receitas",
    response_model=PaginatedResponse[ReceitaResponse],
    summary="Listar Receitas",
)
async def list_receitas(
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    consulta_id: Optional[UUID] = Query(default=None, description="Filtrar por consulta"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista receitas."""
    return await prontuario_service.list_receitas(
        current_user=current_user,
        paciente_id=str(paciente_id) if paciente_id else None,
        consulta_id=str(consulta_id) if consulta_id else None,
        page=page,
        per_page=per_page
    )


@router.get(
    "/receitas/{receita_id}",
    response_model=ReceitaResponse,
    summary="Obter Receita",
)
async def get_receita(
    receita_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca receita por ID."""
    return await prontuario_service.get_receita(
        id=str(receita_id),
        current_user=current_user
    )


@router.post(
    "/receitas",
    response_model=ReceitaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Receita",
)
async def create_receita(
    data: ReceitaCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Cria receita médica.

    Tipos:
    - simples: receita comum
    - especial: receita de controle especial (azul/amarela)
    - antimicrobiano: receita de antimicrobiano
    """
    return await prontuario_service.create_receita(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/receitas/{receita_id}",
    response_model=ReceitaResponse,
    summary="Atualizar Receita",
)
async def update_receita(
    receita_id: UUID,
    data: ReceitaUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza receita."""
    return await prontuario_service.update_receita(
        id=str(receita_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# ATESTADOS
# ============================================================================

@router.get(
    "/atestados",
    response_model=PaginatedResponse[AtestadoResponse],
    summary="Listar Atestados",
)
async def list_atestados(
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    consulta_id: Optional[UUID] = Query(default=None, description="Filtrar por consulta"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista atestados."""
    return await prontuario_service.list_atestados(
        current_user=current_user,
        paciente_id=str(paciente_id) if paciente_id else None,
        consulta_id=str(consulta_id) if consulta_id else None,
        page=page,
        per_page=per_page
    )


@router.get(
    "/atestados/{atestado_id}",
    response_model=AtestadoResponse,
    summary="Obter Atestado",
)
async def get_atestado(
    atestado_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca atestado por ID."""
    return await prontuario_service.get_atestado(
        id=str(atestado_id),
        current_user=current_user
    )


@router.post(
    "/atestados",
    response_model=AtestadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Atestado",
)
async def create_atestado(
    data: AtestadoCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Cria atestado médico.

    Tipos:
    - comparecimento: atesta que compareceu à consulta
    - afastamento: atesta dias de afastamento
    - aptidao: apto para atividade
    - acompanhante: para acompanhante de paciente
    """
    return await prontuario_service.create_atestado(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/atestados/{atestado_id}",
    response_model=AtestadoResponse,
    summary="Atualizar Atestado",
)
async def update_atestado(
    atestado_id: UUID,
    data: AtestadoUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza atestado."""
    return await prontuario_service.update_atestado(
        id=str(atestado_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# EXAMES SOLICITADOS
# ============================================================================

@router.get(
    "/exames",
    response_model=PaginatedResponse[ExameSolicitadoResponse],
    summary="Listar Exames Solicitados",
)
async def list_exames(
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    consulta_id: Optional[UUID] = Query(default=None, description="Filtrar por consulta"),
    status: Optional[str] = Query(default=None, description="Filtrar por status"),
    para_retorno: Optional[bool] = Query(default=None, description="Apenas para retorno"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista exames solicitados."""
    return await prontuario_service.list_exames(
        current_user=current_user,
        paciente_id=str(paciente_id) if paciente_id else None,
        consulta_id=str(consulta_id) if consulta_id else None,
        status=status,
        para_retorno=para_retorno,
        page=page,
        per_page=per_page
    )


@router.get(
    "/exames/{exame_id}",
    response_model=ExameSolicitadoResponse,
    summary="Obter Exame",
)
async def get_exame(
    exame_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca exame por ID."""
    return await prontuario_service.get_exame(
        id=str(exame_id),
        current_user=current_user
    )


@router.post(
    "/exames",
    response_model=ExameSolicitadoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar Exame",
)
async def create_exame(
    data: ExameSolicitadoCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Solicita exame."""
    return await prontuario_service.create_exame(
        data=data,
        current_user=current_user
    )


@router.post(
    "/exames/batch",
    response_model=List[ExameSolicitadoResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Solicitar Múltiplos Exames",
)
async def create_exames_batch(
    data: ExameSolicitadoBatch,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Solicita múltiplos exames de uma vez."""
    return await prontuario_service.create_exames_batch(
        consulta_id=str(data.consulta_id),
        paciente_id=str(data.paciente_id),
        medico_id=str(data.medico_id),
        exames=data.exames,
        para_retorno=data.para_retorno,
        current_user=current_user
    )


@router.patch(
    "/exames/{exame_id}",
    response_model=ExameSolicitadoResponse,
    summary="Atualizar Exame",
)
async def update_exame(
    exame_id: UUID,
    data: ExameSolicitadoUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza status do exame."""
    return await prontuario_service.update_exame(
        id=str(exame_id),
        data=data,
        current_user=current_user
    )


@router.get(
    "/pacientes/{paciente_id}/exames-pendentes",
    response_model=List[ExameSolicitadoResponse],
    summary="Exames Pendentes",
)
async def get_exames_pendentes(
    paciente_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista exames pendentes de um paciente."""
    return await prontuario_service.get_exames_pendentes(
        paciente_id=str(paciente_id),
        current_user=current_user
    )


# ============================================================================
# ENCAMINHAMENTOS
# ============================================================================

@router.get(
    "/encaminhamentos",
    response_model=PaginatedResponse[EncaminhamentoResponse],
    summary="Listar Encaminhamentos",
)
async def list_encaminhamentos(
    paciente_id: Optional[UUID] = Query(default=None, description="Filtrar por paciente"),
    consulta_id: Optional[UUID] = Query(default=None, description="Filtrar por consulta"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista encaminhamentos."""
    return await prontuario_service.list_encaminhamentos(
        current_user=current_user,
        paciente_id=str(paciente_id) if paciente_id else None,
        consulta_id=str(consulta_id) if consulta_id else None,
        page=page,
        per_page=per_page
    )


@router.get(
    "/encaminhamentos/{encaminhamento_id}",
    response_model=EncaminhamentoResponse,
    summary="Obter Encaminhamento",
)
async def get_encaminhamento(
    encaminhamento_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Busca encaminhamento por ID."""
    return await prontuario_service.get_encaminhamento(
        id=str(encaminhamento_id),
        current_user=current_user
    )


@router.post(
    "/encaminhamentos",
    response_model=EncaminhamentoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar Encaminhamento",
)
async def create_encaminhamento(
    data: EncaminhamentoCreate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """Cria encaminhamento para especialista."""
    return await prontuario_service.create_encaminhamento(
        data=data,
        current_user=current_user
    )


@router.patch(
    "/encaminhamentos/{encaminhamento_id}",
    response_model=EncaminhamentoResponse,
    summary="Atualizar Encaminhamento",
)
async def update_encaminhamento(
    encaminhamento_id: UUID,
    data: EncaminhamentoUpdate,
    current_user: CurrentUser = Depends(require_permission("prontuario", "E"))
):
    """Atualiza encaminhamento."""
    return await prontuario_service.update_encaminhamento(
        id=str(encaminhamento_id),
        data=data,
        current_user=current_user
    )


# ============================================================================
# BRIEFING E HISTÓRICO
# ============================================================================

@router.get(
    "/pacientes/{paciente_id}/briefing",
    response_model=BriefingPaciente,
    summary="Briefing Pré-Consulta",
)
async def get_briefing(
    paciente_id: UUID,
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """
    Prepara briefing do paciente para o médico.

    Inclui:
    - Dados básicos (nome, idade, sexo)
    - Alergias (IMPORTANTE!)
    - Medicamentos em uso
    - Última consulta
    - Exames pendentes
    - Alertas
    """
    return await prontuario_service.get_briefing(
        paciente_id=str(paciente_id),
        current_user=current_user
    )


@router.get(
    "/pacientes/{paciente_id}/historico",
    response_model=List[HistoricoConsulta],
    summary="Histórico de Consultas",
)
async def get_historico(
    paciente_id: UUID,
    limit: int = Query(default=10, ge=1, le=50, description="Limite de registros"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "L"))
):
    """Lista histórico de consultas do paciente."""
    return await prontuario_service.get_historico(
        paciente_id=str(paciente_id),
        current_user=current_user,
        limit=limit
    )


# ============================================================================
# TRANSCRIÇÃO DE ÁUDIO (WHISPER)
# ============================================================================

@router.post(
    "/transcricoes/upload",
    response_model=TranscricaoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload e Transcrição de Áudio",
)
async def upload_audio_transcricao(
    consulta_id: UUID = Query(..., description="ID da consulta"),
    audio_file: UploadFile = File(..., description="Arquivo de áudio"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Faz upload de áudio e transcreve usando Whisper (via Groq).

    Formatos suportados: mp3, mp4, m4a, wav, webm, ogg, flac
    Tamanho máximo: 25MB

    O áudio é transcrito em tempo real e o resultado é salvo
    na tabela de transcrições.
    """
    return await prontuario_service.upload_and_transcribe(
        consulta_id=str(consulta_id),
        audio_file=audio_file,
        current_user=current_user
    )


@router.post(
    "/transcricoes/audio-chunk",
    response_model=dict,
    summary="Enviar Chunk de Áudio (Streaming)",
)
async def upload_audio_chunk(
    consulta_id: UUID = Query(..., description="ID da consulta"),
    chunk_index: int = Query(..., description="Índice do chunk"),
    is_final: bool = Query(default=False, description="Se é o último chunk"),
    audio_chunk: UploadFile = File(..., description="Chunk de áudio"),
    current_user: CurrentUser = Depends(require_permission("prontuario", "C"))
):
    """
    Recebe chunks de áudio para transcrição em tempo real.

    Use este endpoint para enviar áudio em pedaços durante a gravação.
    Quando is_final=True, o sistema processa todos os chunks acumulados.
    """
    return await prontuario_service.process_audio_chunk(
        consulta_id=str(consulta_id),
        chunk_index=chunk_index,
        is_final=is_final,
        audio_chunk=audio_chunk,
        current_user=current_user
    )
