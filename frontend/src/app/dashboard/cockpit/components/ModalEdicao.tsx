'use client';

import { Edit3, X, Save, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getGlassStyles, getTextStyles } from '../styles';
import { Anamnese } from '../types';

interface ModalEdicaoProps {
  isOpen: boolean;
  secao: string | null;
  dados: any;
  salvando: boolean;
  onClose: () => void;
  onSave: () => void;
  onChangeDados: (dados: any) => void;
}

export function ModalEdicao({
  isOpen,
  secao,
  dados,
  salvando,
  onClose,
  onSave,
  onChangeDados
}: ModalEdicaoProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  if (!isOpen || !secao) return null;

  const getTitulo = () => {
    switch (secao) {
      case 'anamnese': return 'Anamnese';
      case 'medicamentos': return 'Medicamentos';
      case 'antecedentes': return 'Antecedentes';
      case 'alergias': return 'Alergias';
      default: return 'Seção';
    }
  };

  return (
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
                Editar {getTitulo()}
              </h3>
              <p className={cn('text-xs', text.muted)}>Atualize as informações do paciente</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={cn('p-2 rounded-lg hover:bg-white/10 transition-colors', text.muted)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 max-h-[60vh] overflow-y-auto">
          {secao === 'alergias' && (
            <div className="space-y-3">
              <p className={cn('text-sm', text.secondary)}>
                Alergias atuais: {Array.isArray(dados) ? dados.join(', ') : 'Nenhuma'}
              </p>
              <textarea
                className={cn(
                  'w-full h-32 p-3 rounded-xl text-sm resize-none',
                  glass.glassDark,
                  text.primary,
                  'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                )}
                placeholder="Digite as alergias separadas por vírgula (ex: Dipirona, AAS, Penicilina)"
                defaultValue={Array.isArray(dados) ? dados.join(', ') : ''}
                onChange={(e) => onChangeDados(e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
              />
            </div>
          )}

          {secao === 'medicamentos' && (
            <div className="space-y-3">
              <p className={cn('text-sm', text.secondary)}>
                Medicamentos atuais: {Array.isArray(dados) ? dados.length : 0}
              </p>
              <textarea
                className={cn(
                  'w-full h-40 p-3 rounded-xl text-sm resize-none',
                  glass.glassDark,
                  text.primary,
                  'focus:outline-none focus:ring-2 focus:ring-amber-500/50'
                )}
                placeholder="Digite os medicamentos, um por linha (ex: Losartana 50mg 1x/dia)"
                defaultValue={Array.isArray(dados) ? dados.join('\n') : ''}
                onChange={(e) => onChangeDados(e.target.value.split('\n').map(s => s.trim()).filter(Boolean))}
              />
            </div>
          )}

          {secao === 'antecedentes' && (
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
                defaultValue={typeof dados === 'string' ? dados : ''}
                onChange={(e) => onChangeDados(e.target.value)}
              />
            </div>
          )}

          {secao === 'anamnese' && (
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
                    defaultValue={dados?.queixa_principal || ''}
                    onChange={(e) => onChangeDados({ ...dados, queixa_principal: e.target.value })}
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
                    defaultValue={dados?.observacoes_medico || ''}
                    onChange={(e) => onChangeDados({ ...dados, observacoes_medico: e.target.value })}
                  />
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className={cn('flex items-center justify-end gap-3 p-4 border-t border-white/10')}>
          <button
            onClick={onClose}
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
            onClick={onSave}
            disabled={salvando}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              'bg-gradient-to-r from-amber-500 to-orange-600',
              'hover:from-amber-600 hover:to-orange-700',
              'text-white',
              'disabled:opacity-50'
            )}
          >
            {salvando ? (
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
  );
}
