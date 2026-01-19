'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  FileText,
  Plus,
  Edit,
  Trash2,
  RefreshCw,
  AlertCircle,
  X,
  Copy,
  Search,
  Filter,
  RotateCcw,
  Eye,
  Check,
} from 'lucide-react';
import { api, ModeloDocumento, CategoriaDocumento, CATEGORIAS_DOCUMENTO } from '@/lib/api';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

// Categorias disponíveis
const CATEGORIAS: CategoriaDocumento[] = ['Atestados', 'Exames', 'Orientações Médicas', 'Receitas', 'Outros'];

export default function ModelosDocumentosPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  // Estados
  const [modelos, setModelos] = useState<ModeloDocumento[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categoriaFiltro, setCategoriaFiltro] = useState<CategoriaDocumento | ''>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [mostrarInativos, setMostrarInativos] = useState(false);

  // Modal states
  const [modalAberto, setModalAberto] = useState(false);
  const [modalTipo, setModalTipo] = useState<'criar' | 'editar' | 'visualizar'>('criar');
  const [modeloSelecionado, setModeloSelecionado] = useState<ModeloDocumento | null>(null);
  const [salvando, setSalvando] = useState(false);

  // Form states
  const [formCategoria, setFormCategoria] = useState<CategoriaDocumento>('Receitas');
  const [formTitulo, setFormTitulo] = useState('');
  const [formConteudo, setFormConteudo] = useState('');

  // Carregar modelos
  const carregarModelos = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.getModelosDocumentos({
        categoria: categoriaFiltro || undefined,
        search: searchTerm || undefined,
        ativo: mostrarInativos ? undefined : true,
      });
      setModelos(response.items || []);
    } catch (err) {
      console.error('Erro ao carregar modelos:', err);
      setError(err instanceof Error ? err.message : 'Erro ao carregar modelos');
    } finally {
      setLoading(false);
    }
  }, [categoriaFiltro, searchTerm, mostrarInativos]);

  useEffect(() => {
    carregarModelos();
  }, [carregarModelos]);

  // Abrir modal para criar
  const abrirModalCriar = () => {
    setModalTipo('criar');
    setModeloSelecionado(null);
    setFormCategoria('Receitas');
    setFormTitulo('');
    setFormConteudo('');
    setModalAberto(true);
  };

  // Abrir modal para editar
  const abrirModalEditar = (modelo: ModeloDocumento) => {
    setModalTipo('editar');
    setModeloSelecionado(modelo);
    setFormCategoria(modelo.categoria);
    setFormTitulo(modelo.titulo);
    setFormConteudo(modelo.conteudo);
    setModalAberto(true);
  };

  // Abrir modal para visualizar
  const abrirModalVisualizar = (modelo: ModeloDocumento) => {
    setModalTipo('visualizar');
    setModeloSelecionado(modelo);
    setFormCategoria(modelo.categoria);
    setFormTitulo(modelo.titulo);
    setFormConteudo(modelo.conteudo);
    setModalAberto(true);
  };

  // Fechar modal
  const fecharModal = () => {
    setModalAberto(false);
    setModeloSelecionado(null);
  };

  // Salvar (criar ou atualizar)
  const handleSalvar = async () => {
    if (!formTitulo.trim() || !formConteudo.trim()) {
      alert('Preencha todos os campos obrigatórios');
      return;
    }

    try {
      setSalvando(true);
      if (modalTipo === 'criar') {
        await api.createModeloDocumento({
          categoria: formCategoria,
          titulo: formTitulo,
          conteudo: formConteudo,
        });
      } else if (modalTipo === 'editar' && modeloSelecionado) {
        await api.updateModeloDocumento(modeloSelecionado.id, {
          categoria: formCategoria,
          titulo: formTitulo,
          conteudo: formConteudo,
        });
      }
      fecharModal();
      carregarModelos();
    } catch (err) {
      console.error('Erro ao salvar:', err);
      alert(err instanceof Error ? err.message : 'Erro ao salvar');
    } finally {
      setSalvando(false);
    }
  };

  // Excluir (soft delete)
  const handleExcluir = async (modelo: ModeloDocumento) => {
    if (!confirm(`Deseja realmente excluir o modelo "${modelo.titulo}"?`)) {
      return;
    }

    try {
      await api.deleteModeloDocumento(modelo.id);
      carregarModelos();
    } catch (err) {
      console.error('Erro ao excluir:', err);
      alert(err instanceof Error ? err.message : 'Erro ao excluir');
    }
  };

  // Duplicar
  const handleDuplicar = async (modelo: ModeloDocumento) => {
    try {
      await api.duplicarModeloDocumento(modelo.id, `${modelo.titulo} (Cópia)`);
      carregarModelos();
    } catch (err) {
      console.error('Erro ao duplicar:', err);
      alert(err instanceof Error ? err.message : 'Erro ao duplicar');
    }
  };

  // Reativar
  const handleReativar = async (modelo: ModeloDocumento) => {
    try {
      await api.reativarModeloDocumento(modelo.id);
      carregarModelos();
    } catch (err) {
      console.error('Erro ao reativar:', err);
      alert(err instanceof Error ? err.message : 'Erro ao reativar');
    }
  };

  // Filtrar modelos por busca local (além do filtro da API)
  const modelosFiltrados = modelos;

  // Agrupar por categoria para exibição
  const modelosPorCategoria = modelosFiltrados.reduce((acc, modelo) => {
    if (!acc[modelo.categoria]) {
      acc[modelo.categoria] = [];
    }
    acc[modelo.categoria].push(modelo);
    return acc;
  }, {} as Record<string, ModeloDocumento[]>);

  return (
    <div className="p-6 pb-32 overflow-y-auto h-full">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500 to-yellow-600 flex items-center justify-center shadow-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className={cn('text-2xl font-bold', text.primary)}>Modelos de Documentos</h1>
              <p className={cn('text-sm', text.muted)}>
                {modelos.length} modelo{modelos.length !== 1 ? 's' : ''} disponíve{modelos.length !== 1 ? 'is' : 'l'}
              </p>
            </div>
          </div>
          <button
            onClick={abrirModalCriar}
            className={cn(
              glass.glassSolid,
              'flex items-center gap-2 px-4 py-2.5 rounded-xl',
              'hover:scale-105 transition-all duration-200',
              'bg-gradient-to-r from-amber-500 to-yellow-600 text-white font-medium'
            )}
          >
            <Plus className="w-4 h-4" />
            Novo Modelo
          </button>
        </div>

        {/* Filtros */}
        <div className={cn(glass.glassStrong, 'rounded-2xl p-4 mb-6')}>
          <div className="flex flex-wrap gap-4 items-center">
            {/* Busca */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className={cn('absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4', text.muted)} />
              <input
                type="text"
                placeholder="Buscar por título..."
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

            {/* Filtro por categoria */}
            <div className="flex items-center gap-2">
              <Filter className={cn('w-4 h-4', text.muted)} />
              <select
                value={categoriaFiltro}
                onChange={(e) => setCategoriaFiltro(e.target.value as CategoriaDocumento | '')}
                className={cn(
                  'px-4 py-2.5 rounded-xl',
                  glass.glass,
                  'border border-white/10',
                  'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                  text.primary,
                  'bg-transparent'
                )}
              >
                <option value="">Todas as categorias</option>
                {CATEGORIAS.map((cat) => (
                  <option key={cat} value={cat}>
                    {CATEGORIAS_DOCUMENTO[cat].icon} {cat}
                  </option>
                ))}
              </select>
            </div>

            {/* Toggle inativos */}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={mostrarInativos}
                onChange={(e) => setMostrarInativos(e.target.checked)}
                className="w-4 h-4 rounded border-white/20 bg-white/10 text-amber-500 focus:ring-amber-500/50"
              />
              <span className={cn('text-sm', text.secondary)}>Mostrar inativos</span>
            </label>

            {/* Refresh */}
            <button
              onClick={carregarModelos}
              className={cn(
                'p-2.5 rounded-xl',
                glass.glass,
                'hover:bg-white/10 transition-colors'
              )}
              title="Atualizar"
            >
              <RefreshCw className={cn('w-4 h-4', text.secondary)} />
            </button>
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-12 flex items-center justify-center')}>
            <RefreshCw className="w-8 h-8 animate-spin text-amber-500" />
          </div>
        ) : error ? (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-12 flex flex-col items-center justify-center')}>
            <AlertCircle className="w-12 h-12 text-red-500 mb-3" />
            <p className={cn('text-lg mb-4', text.primary)}>{error}</p>
            <button
              onClick={carregarModelos}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-xl',
                'bg-amber-500 text-white hover:bg-amber-600 transition-colors'
              )}
            >
              <RefreshCw className="w-4 h-4" />
              Tentar novamente
            </button>
          </div>
        ) : modelos.length === 0 ? (
          <div className={cn(glass.glassStrong, 'rounded-2xl p-12 text-center')}>
            <FileText className={cn('w-16 h-16 mx-auto mb-4', text.muted)} />
            <p className={cn('text-lg mb-2', text.secondary)}>Nenhum modelo encontrado</p>
            <p className={cn('text-sm mb-6', text.muted)}>
              {categoriaFiltro || searchTerm
                ? 'Tente ajustar os filtros de busca'
                : 'Crie seu primeiro modelo de documento'}
            </p>
            <button
              onClick={abrirModalCriar}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-xl mx-auto',
                'bg-gradient-to-r from-amber-500 to-yellow-600 text-white'
              )}
            >
              <Plus className="w-4 h-4" />
              Criar Modelo
            </button>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Exibir por categoria ou lista simples */}
            {categoriaFiltro ? (
              // Lista simples quando há filtro de categoria
              <div className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
                <div className="grid gap-4 p-4">
                  {modelosFiltrados.map((modelo) => (
                    <ModeloCard
                      key={modelo.id}
                      modelo={modelo}
                      isDark={isDark}
                      glass={glass}
                      text={text}
                      onEditar={() => abrirModalEditar(modelo)}
                      onVisualizar={() => abrirModalVisualizar(modelo)}
                      onExcluir={() => handleExcluir(modelo)}
                      onDuplicar={() => handleDuplicar(modelo)}
                      onReativar={() => handleReativar(modelo)}
                    />
                  ))}
                </div>
              </div>
            ) : (
              // Agrupado por categoria
              Object.entries(modelosPorCategoria).map(([categoria, modelosCategoria]) => (
                <div key={categoria} className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
                  <div className={cn('px-4 py-3 border-b', isDark ? 'border-white/10' : 'border-gray-200')}>
                    <div className="flex items-center gap-2">
                      <span className="text-xl">
                        {CATEGORIAS_DOCUMENTO[categoria as CategoriaDocumento]?.icon || '📄'}
                      </span>
                      <h2 className={cn('font-semibold', text.primary)}>{categoria}</h2>
                      <span className={cn('text-sm px-2 py-0.5 rounded-full', glass.glass, text.muted)}>
                        {modelosCategoria.length}
                      </span>
                    </div>
                  </div>
                  <div className="grid gap-4 p-4">
                    {modelosCategoria.map((modelo) => (
                      <ModeloCard
                        key={modelo.id}
                        modelo={modelo}
                        isDark={isDark}
                        glass={glass}
                        text={text}
                        onEditar={() => abrirModalEditar(modelo)}
                        onVisualizar={() => abrirModalVisualizar(modelo)}
                        onExcluir={() => handleExcluir(modelo)}
                        onDuplicar={() => handleDuplicar(modelo)}
                        onReativar={() => handleReativar(modelo)}
                      />
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Modal */}
      {modalAberto && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={fecharModal}
          />

          {/* Modal content */}
          <div
            className={cn(
              'relative w-full max-w-3xl max-h-[90vh] overflow-hidden',
              glass.glassSolid,
              'rounded-3xl shadow-2xl',
              'flex flex-col'
            )}
          >
            {/* Header */}
            <div className={cn('px-6 py-4 border-b flex items-center justify-between', isDark ? 'border-white/10' : 'border-gray-200')}>
              <h2 className={cn('text-xl font-bold', text.primary)}>
                {modalTipo === 'criar' && 'Novo Modelo'}
                {modalTipo === 'editar' && 'Editar Modelo'}
                {modalTipo === 'visualizar' && 'Visualizar Modelo'}
              </h2>
              <button
                onClick={fecharModal}
                className={cn('p-2 rounded-xl hover:bg-white/10 transition-colors', text.muted)}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Categoria */}
              <div>
                <label className={cn('block text-sm font-medium mb-2', text.secondary)}>
                  Categoria *
                </label>
                <select
                  value={formCategoria}
                  onChange={(e) => setFormCategoria(e.target.value as CategoriaDocumento)}
                  disabled={modalTipo === 'visualizar'}
                  className={cn(
                    'w-full px-4 py-3 rounded-xl',
                    glass.glass,
                    'border border-white/10',
                    'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                    text.primary,
                    'bg-transparent',
                    modalTipo === 'visualizar' && 'opacity-60 cursor-not-allowed'
                  )}
                >
                  {CATEGORIAS.map((cat) => (
                    <option key={cat} value={cat}>
                      {CATEGORIAS_DOCUMENTO[cat].icon} {cat}
                    </option>
                  ))}
                </select>
              </div>

              {/* Título */}
              <div>
                <label className={cn('block text-sm font-medium mb-2', text.secondary)}>
                  Título *
                </label>
                <input
                  type="text"
                  value={formTitulo}
                  onChange={(e) => setFormTitulo(e.target.value)}
                  disabled={modalTipo === 'visualizar'}
                  placeholder="Ex: Atestado de Comparecimento"
                  className={cn(
                    'w-full px-4 py-3 rounded-xl',
                    glass.glass,
                    'border border-white/10',
                    'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                    text.primary,
                    'placeholder:text-white/30',
                    modalTipo === 'visualizar' && 'opacity-60 cursor-not-allowed'
                  )}
                />
              </div>

              {/* Conteúdo */}
              <div className="flex-1">
                <label className={cn('block text-sm font-medium mb-2', text.secondary)}>
                  Conteúdo do Modelo *
                </label>
                <p className={cn('text-xs mb-2', text.muted)}>
                  Use {'{'}{'{'} variável {'}'}{'}' } para campos dinâmicos. Ex: {'{'}{'{'} nome_paciente {'}'}{'}'}, {'{'}{'{'} data_atual {'}'}{'}'}, {'{'}{'{'} medico_nome {'}'}{'}'}
                </p>
                <textarea
                  value={formConteudo}
                  onChange={(e) => setFormConteudo(e.target.value)}
                  disabled={modalTipo === 'visualizar'}
                  rows={15}
                  placeholder="Digite o conteúdo do modelo aqui..."
                  className={cn(
                    'w-full px-4 py-3 rounded-xl',
                    glass.glass,
                    'border border-white/10',
                    'focus:outline-none focus:ring-2 focus:ring-amber-500/50',
                    text.primary,
                    'placeholder:text-white/30',
                    'font-mono text-sm',
                    'resize-none',
                    modalTipo === 'visualizar' && 'opacity-60 cursor-not-allowed'
                  )}
                />
              </div>
            </div>

            {/* Footer */}
            <div className={cn('px-6 py-4 border-t flex justify-end gap-3', isDark ? 'border-white/10' : 'border-gray-200')}>
              <button
                onClick={fecharModal}
                className={cn(
                  'px-4 py-2.5 rounded-xl',
                  glass.glass,
                  'hover:bg-white/10 transition-colors',
                  text.secondary
                )}
              >
                {modalTipo === 'visualizar' ? 'Fechar' : 'Cancelar'}
              </button>
              {modalTipo !== 'visualizar' && (
                <button
                  onClick={handleSalvar}
                  disabled={salvando || !formTitulo.trim() || !formConteudo.trim()}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2.5 rounded-xl',
                    'bg-gradient-to-r from-amber-500 to-yellow-600 text-white font-medium',
                    'hover:opacity-90 transition-opacity',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  {salvando ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4" />
                  )}
                  {salvando ? 'Salvando...' : 'Salvar'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// Componente do Card de Modelo
interface ModeloCardProps {
  modelo: ModeloDocumento;
  isDark: boolean;
  glass: ReturnType<typeof getGlassStyles>;
  text: ReturnType<typeof getTextStyles>;
  onEditar: () => void;
  onVisualizar: () => void;
  onExcluir: () => void;
  onDuplicar: () => void;
  onReativar: () => void;
}

function ModeloCard({
  modelo,
  isDark,
  glass,
  text,
  onEditar,
  onVisualizar,
  onExcluir,
  onDuplicar,
  onReativar,
}: ModeloCardProps) {
  return (
    <div
      className={cn(
        'p-4 rounded-xl',
        glass.glass,
        'hover:bg-white/5 transition-colors',
        !modelo.ativo && 'opacity-60'
      )}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className={cn('font-medium truncate', text.primary)}>
              {modelo.titulo}
            </h3>
            {!modelo.ativo && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-red-500/20 text-red-400">
                Inativo
              </span>
            )}
          </div>
          <p className={cn('text-sm line-clamp-2', text.muted)}>
            {modelo.conteudo ? `${modelo.conteudo.substring(0, 150)}...` : 'Sem conteúdo'}
          </p>
          <p className={cn('text-xs mt-2', text.muted)}>
            Atualizado em {new Date(modelo.updated_at).toLocaleDateString('pt-BR')}
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={onVisualizar}
            className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.muted)}
            title="Visualizar"
          >
            <Eye className="w-4 h-4" />
          </button>
          {modelo.ativo ? (
            <>
              <button
                onClick={onEditar}
                className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.muted)}
                title="Editar"
              >
                <Edit className="w-4 h-4" />
              </button>
              <button
                onClick={onDuplicar}
                className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.muted)}
                title="Duplicar"
              >
                <Copy className="w-4 h-4" />
              </button>
              <button
                onClick={onExcluir}
                className={cn('p-2 rounded-lg hover:bg-red-500/20 transition-colors text-red-400')}
                title="Excluir"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </>
          ) : (
            <button
              onClick={onReativar}
              className={cn('p-2 rounded-lg hover:bg-green-500/20 transition-colors text-green-400')}
              title="Reativar"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
