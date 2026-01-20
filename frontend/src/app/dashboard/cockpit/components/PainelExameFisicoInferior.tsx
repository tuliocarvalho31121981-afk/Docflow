'use client';

import { Activity, ChevronDown, ChevronUp, Save, CheckCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SinaisVitais } from '@/lib/api';
import { getGlassStyles, getTextStyles } from '../styles';
import { PainelExameFisicoInferiorProps } from '../types';

export function PainelExameFisicoInferior({
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
    const numValue = value ? parseFloat(value) : undefined;
    onChange({ ...sinaisVitais, [field]: numValue });
  };

  // Formata pressão arterial para exibição
  const pressaoFormatada = sinaisVitais.pa_sistolica && sinaisVitais.pa_diastolica
    ? `${sinaisVitais.pa_sistolica}/${sinaisVitais.pa_diastolica}`
    : '--';

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
            {!expanded && (sinaisVitais.pa_sistolica || sinaisVitais.fc) && (
              <p className={cn('text-xs', text.muted)}>
                PA: {pressaoFormatada} | FC: {sinaisVitais.fc || '--'} | T: {sinaisVitais.temperatura || '--'}°C
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
            <label className={cn('text-xs font-medium', text.muted)}>PA Sistólica</label>
            <input
              type="text"
              placeholder="120"
              value={sinaisVitais.pa_sistolica || ''}
              onChange={(e) => handleChange('pa_sistolica', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>PA Diastólica</label>
            <input
              type="text"
              placeholder="80"
              value={sinaisVitais.pa_diastolica || ''}
              onChange={(e) => handleChange('pa_diastolica', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>FC (bpm)</label>
            <input
              type="text"
              placeholder="72"
              value={sinaisVitais.fc || ''}
              onChange={(e) => handleChange('fc', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>FR (irpm)</label>
            <input
              type="text"
              placeholder="16"
              value={sinaisVitais.fr || ''}
              onChange={(e) => handleChange('fr', e.target.value)}
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
          <div className="flex flex-col gap-1">
            <label className={cn('text-xs font-medium', text.muted)}>SpO2 (%)</label>
            <input
              type="text"
              placeholder="98"
              value={sinaisVitais.saturacao || ''}
              onChange={(e) => handleChange('saturacao', e.target.value)}
              disabled={disabled}
              className={cn('px-3 py-2 rounded-lg text-sm', glass.glassSubtle, text.primary, 'placeholder:text-white/30')}
            />
          </div>
        </div>
      )}
    </div>
  );
}
