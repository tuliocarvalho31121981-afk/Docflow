'use client';

import { useState } from 'react';
import {
  User, Stethoscope, Activity, ClipboardList, FileText, FileCheck,
  CheckCircle, Edit3, RefreshCw, Save, X, Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { getGlassStyles, getTextStyles } from '../styles';
import { PainelSOAPProps, SOAPFieldProps } from '../types';

// Componente SOAPField
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

// Componente Principal PainelSOAP
export function PainelSOAP({ soap, consulta, onValidar, onEditar, loading, validando, savingField, savedField }: PainelSOAPProps) {
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
