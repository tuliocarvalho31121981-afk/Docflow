'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Search,
  X,
  ChevronRight,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { api, ModeloDocumento, CategoriaDocumento, CATEGORIAS_DOCUMENTO } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

// Categorias disponíveis
const CATEGORIAS: CategoriaDocumento[] = ['Atestados', 'Exames', 'Orientações Médicas', 'Receitas', 'Outros'];

interface ModeloSelectorProps {
  isOpen: boolean;
  onClose: () => void;
  onSelect: (modelo: ModeloDocumento, conteudoProcessado: string) => void;
  /** Dados do paciente para substituir variáveis no modelo */
  pacienteData?: {
    nome?: string;
    cpf?: string;
    data_nascimento?: string;
    telefone?: string;
    endereco?: string;
    convenio?: string;
    [key: string]: string | undefined;
  };
  /** Dados adicionais para substituir variáveis */
  dadosAdicionais?: Record<string, string>;
  /** Filtrar por categoria específica */
  categoriaFiltro?: CategoriaDocumento;
  /** Título do modal */
  titulo?: string;
}

/**
 * Componente de seleção de modelos de documentos.
 * Pode ser usado em qualquer parte do sistema para selecionar um modelo
 * e obter o conteúdo processado com as variáveis substituídas.
 */
export function ModeloSelector({
  isOpen,
  onClose,
  onSelect,
  pacienteData,
  dadosAdicionais,
  categoriaFiltro,
  titulo = 'Selecionar Modelo',
}: ModeloSelectorProps) {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  const [modelos, setModelos] = useState<ModeloDocumento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoriaAtiva, setCategoriaAtiva] = useState<CategoriaDocumento | ''>(categoriaFiltro || '');
  const [modeloSelecionado, setModeloSelecionado] = useState<ModeloDocumento | null>(null);
  const [previewConteudo, setPreviewConteudo] = useState('');

  // Carregar modelos
  const carregarModelos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getModelosDocumentos({
        categoria: categoriaAtiva || undefined,
        search: searchTerm || undefined,
        ativo: true,
      });
      setModelos(response.items || []);
    } catch (err) {
      console.error('Erro ao carregar modelos:', err);
      setError(err instanceof Error ? err.message : 'Erro ao carregar modelos');
    } finally {
      setLoading(false);
    }
  }, [categoriaAtiva, searchTerm]);

  useEffect(() => {
    if (isOpen) {
      carregarModelos();
    }
  }, [isOpen, carregarModelos]);

  // Processar variáveis do modelo
  const processarVariaveis = useCallback((conteudo: string): string => {
    let resultado = conteudo;

    // Data atual
    const hoje = new Date();
    const dataAtual = hoje.toLocaleDateString('pt-BR');
    const horaAtual = hoje.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    // Variáveis padrão
    const variaveis: Record<string, string> = {
      data_atual: dataAtual,
      hora_atual: horaAtual,
      data_extenso: hoje.toLocaleDateString('pt-BR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }),
      ...dadosAdicionais,
    };

    // Dados do paciente
    if (pacienteData) {
      Object.entries(pacienteData).forEach(([key, value]) => {
        if (value) {
          variaveis[`paciente_${key}`] = value;
          // Também aceita nome_paciente, cpf_paciente etc
          variaveis[`${key}_paciente`] = value;
        }
      });
      // Atalhos comuns
      if (pacienteData.nome) {
        variaveis['nome_paciente'] = pacienteData.nome;
        variaveis['paciente'] = pacienteData.nome;
      }
    }

    // Substituir todas as variáveis {{ variavel }}
    resultado = resultado.replace(/\{\{\s*(\w+)\s*\}\}/g, (match, varName) => {
      return variaveis[varName] || match;
    });

    return resultado;
  }, [pacienteData, dadosAdicionais]);

  // Atualizar preview quando modelo selecionado muda
  useEffect(() => {
    if (modeloSelecionado && modeloSelecionado.conteudo) {
      setPreviewConteudo(processarVariaveis(modeloSelecionado.conteudo));
    } else {
      setPreviewConteudo('');
    }
  }, [modeloSelecionado, processarVariaveis]);

  // Confirmar seleção
  const handleConfirmar = () => {
    if (modeloSelecionado) {
      onSelect(modeloSelecionado, previewConteudo);
      onClose();
    }
  };

  // Agrupar por categoria
  const modelosPorCategoria = modelos.reduce((acc, modelo) => {
    if (!acc[modelo.categoria]) {
      acc[modelo.categoria] = [];
    }
    acc[modelo.categoria].push(modelo);
    return acc;
  }, {} as Record<string, ModeloDocumento[]>);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={cn(
          'relative w-full max-w-5xl max-h-[90vh]',
          glass.glassSolid,
          'rounded-3xl shadow-2xl',
          'flex flex-col overflow-hidden'
        )}
      >
        {/* Header */}
        <div className={cn('px-6 py-4 border-b flex items-center justify-between', isDark ? 'border-white/10' : 'border-gray-200')}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center">
              <FileText className="w-5 h-5 text-white" />
            </div>
            <h2 className={cn('text-xl font-bold', text.primary)}>{titulo}</h2>
          </div>
          <button
            onClick={onClose}
            className={cn('p-2 rounded-xl hover:bg-white/10 transition-colors', text.muted)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 flex overflow-hidden">
          {/* Lista de modelos */}
          <div className={cn('w-1/2 border-r overflow-hidden flex flex-col', isDark ? 'border-white/10' : 'border-gray-200')}>
            {/* Filtros */}
            <div className="p-4 space-y-3">
              {/* Busca */}
              <div className="relative">
                <Search className={cn('absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4', text.muted)} />
                <input
                  type="text"
                  placeholder="Buscar modelo..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className={cn(
                    'w-full pl-10 pr-4 py-2.5 rounded-xl',
                    glass.glass,
                    'border border-white/10',
                    'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                    text.primary,
                    'placeholder:text-white/30'
                  )}
                />
              </div>

              {/* Categorias */}
              {!categoriaFiltro && (
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => setCategoriaAtiva('')}
                    className={cn(
                      'px-3 py-1.5 rounded-lg text-sm transition-colors',
                      categoriaAtiva === ''
                        ? 'bg-amber-500 text-white'
                        : cn(glass.glass, 'hover:bg-white/10', text.secondary)
                    )}
                  >
                    Todas
                  </button>
                  {CATEGORIAS.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setCategoriaAtiva(cat)}
                      className={cn(
                        'px-3 py-1.5 rounded-lg text-sm transition-colors',
                        categoriaAtiva === cat
                          ? 'bg-amber-500 text-white'
                          : cn(glass.glass, 'hover:bg-white/10', text.secondary)
                      )}
                    >
                      {CATEGORIAS_DOCUMENTO[cat].icon} {cat}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Lista */}
            <div className="flex-1 overflow-y-auto p-4 pt-0">
              {loading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="w-6 h-6 animate-spin text-amber-500" />
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <AlertCircle className="w-10 h-10 text-red-500 mb-2" />
                  <p className={cn('text-sm', text.muted)}>{error}</p>
                </div>
              ) : modelos.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12">
                  <FileText className={cn('w-10 h-10 mb-2', text.muted)} />
                  <p className={cn('text-sm', text.muted)}>Nenhum modelo encontrado</p>
                </div>
              ) : categoriaAtiva ? (
                // Lista simples quando há filtro
                <div className="space-y-2">
                  {modelos.map((modelo) => (
                    <ModeloItem
                      key={modelo.id}
                      modelo={modelo}
                      isSelected={modeloSelecionado?.id === modelo.id}
                      onClick={() => setModeloSelecionado(modelo)}
                      isDark={isDark}
                      glass={glass}
                      text={text}
                    />
                  ))}
                </div>
              ) : (
                // Agrupado por categoria
                <div className="space-y-4">
                  {Object.entries(modelosPorCategoria).map(([categoria, modelosCategoria]) => (
                    <div key={categoria}>
                      <h3 className={cn('text-sm font-medium mb-2 flex items-center gap-2', text.secondary)}>
                        <span>{CATEGORIAS_DOCUMENTO[categoria as CategoriaDocumento]?.icon}</span>
                        {categoria}
                      </h3>
                      <div className="space-y-2">
                        {modelosCategoria.map((modelo) => (
                          <ModeloItem
                            key={modelo.id}
                            modelo={modelo}
                            isSelected={modeloSelecionado?.id === modelo.id}
                            onClick={() => setModeloSelecionado(modelo)}
                            isDark={isDark}
                            glass={glass}
                            text={text}
                          />
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Preview */}
          <div className="w-1/2 flex flex-col overflow-hidden">
            <div className={cn('px-4 py-3 border-b', isDark ? 'border-white/10' : 'border-gray-200')}>
              <h3 className={cn('font-medium', text.primary)}>
                {modeloSelecionado ? 'Preview do Documento' : 'Selecione um modelo'}
              </h3>
              {modeloSelecionado && (
                <p className={cn('text-xs', text.muted)}>
                  As variáveis serão substituídas pelos dados do paciente
                </p>
              )}
            </div>
            <div className="flex-1 overflow-y-auto p-4">
              {modeloSelecionado ? (
                <div
                  className={cn(
                    'p-6 rounded-xl',
                    glass.glass,
                    'font-mono text-sm whitespace-pre-wrap',
                    text.primary
                  )}
                >
                  {previewConteudo}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-full">
                  <FileText className={cn('w-16 h-16 mb-4', text.muted)} />
                  <p className={cn('text-sm', text.muted)}>
                    Selecione um modelo à esquerda para ver o preview
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={cn('px-6 py-4 border-t flex justify-end gap-3', isDark ? 'border-white/10' : 'border-gray-200')}>
          <button
            onClick={onClose}
            className={cn(
              'px-4 py-2.5 rounded-xl',
              glass.glass,
              'hover:bg-white/10 transition-colors',
              text.secondary
            )}
          >
            Cancelar
          </button>
          <button
            onClick={handleConfirmar}
            disabled={!modeloSelecionado}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 rounded-xl',
              'bg-gradient-to-r from-amber-500 to-yellow-600 text-white font-medium',
              'hover:opacity-90 transition-opacity',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            Usar Modelo
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Componente do item de modelo
interface ModeloItemProps {
  modelo: ModeloDocumento;
  isSelected: boolean;
  onClick: () => void;
  isDark: boolean;
  glass: ReturnType<typeof getGlassStyles>;
  text: ReturnType<typeof getTextStyles>;
}

function ModeloItem({ modelo, isSelected, onClick, isDark, glass, text }: ModeloItemProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'w-full text-left p-3 rounded-xl transition-all',
        isSelected
          ? 'bg-amber-500/20 ring-2 ring-amber-500'
          : cn(glass.glass, 'hover:bg-white/10')
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0',
            isSelected ? 'bg-amber-500' : glass.glassStrong
          )}
        >
          <span className="text-sm">
            {CATEGORIAS_DOCUMENTO[modelo.categoria]?.icon || '📄'}
          </span>
        </div>
        <div className="flex-1 min-w-0">
          <h4 className={cn('font-medium truncate', text.primary)}>
            {modelo.titulo}
          </h4>
          <p className={cn('text-xs line-clamp-1', text.muted)}>
            {modelo.conteudo ? `${modelo.conteudo.substring(0, 80)}...` : 'Sem conteúdo'}
          </p>
        </div>
      </div>
    </button>
  );
}

export default ModeloSelector;
