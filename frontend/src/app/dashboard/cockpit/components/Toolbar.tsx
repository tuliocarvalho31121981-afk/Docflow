'use client';

import { Pill, FileText, TestTube, ArrowRight, CheckCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getGlassStyles, getTextStyles } from '../styles';
import { ToolbarProps } from '../types';

export function Toolbar({
  onReceita,
  onAtestado,
  onExames,
  onEncaminhamento,
  onFinalizar,
  disabled,
  finalizando
}: ToolbarProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  const tools = [
    { icon: Pill, label: 'Receita', onClick: onReceita, color: 'from-blue-500 to-cyan-600' },
    { icon: FileText, label: 'Atestado', onClick: onAtestado, color: 'from-green-500 to-emerald-600' },
    { icon: TestTube, label: 'Exames', onClick: onExames, color: 'from-purple-500 to-violet-600' },
    { icon: ArrowRight, label: 'Encaminhar', onClick: onEncaminhamento, color: 'from-orange-500 to-red-600' },
  ];

  return (
    <div className={cn('flex items-center justify-between p-4', glass.glass, 'rounded-2xl')}>
      <div className="flex items-center gap-2">
        {tools.map((tool) => (
          <button
            key={tool.label}
            onClick={tool.onClick}
            disabled={disabled}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-xl transition-all',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              glass.glassSubtle,
              'hover:bg-white/10'
            )}
          >
            <div className={cn('w-8 h-8 rounded-lg flex items-center justify-center bg-gradient-to-br', tool.color)}>
              <tool.icon className="w-4 h-4 text-white" />
            </div>
            <span className={cn('text-sm font-medium', text.primary)}>{tool.label}</span>
          </button>
        ))}
      </div>

      <button
        onClick={onFinalizar}
        disabled={disabled || finalizando}
        className={cn(
          'flex items-center gap-2 px-6 py-3 rounded-xl transition-all',
          'bg-gradient-to-r from-green-500 to-emerald-600',
          'hover:from-green-600 hover:to-emerald-700',
          'text-white font-medium shadow-lg',
          'disabled:opacity-50 disabled:cursor-not-allowed'
        )}
      >
        {finalizando ? (
          <RefreshCw className="w-5 h-5 animate-spin" />
        ) : (
          <CheckCircle className="w-5 h-5" />
        )}
        Finalizar Consulta
      </button>
    </div>
  );
}
