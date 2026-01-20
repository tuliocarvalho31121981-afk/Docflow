'use client';

import { ChevronLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { getGlassStyles, getTextStyles } from '../styles';
import { ColunaColapsavelProps } from '../types';

export function ColunaColapsavel({
  titulo,
  icon: Icon,
  expanded,
  onToggle,
  children,
  widthExpanded = 'w-80',
  widthCollapsed = 'w-14',
  iconColor = 'from-blue-500 to-purple-600'
}: ColunaColapsavelProps) {
  const glass = getGlassStyles();
  const text = getTextStyles();

  return (
    <div
      className={cn(
        'flex-shrink-0 flex flex-col h-full transition-all duration-300 ease-in-out overflow-hidden',
        glass.glass,
        'rounded-2xl',
        expanded ? widthExpanded : widthCollapsed
      )}
    >
      {expanded ? (
        // Modo Expandido - Mostra conteúdo completo
        <>
          <div className={cn('flex items-center justify-between p-4 border-b border-white/10', glass.glassSubtle)}>
            <div className="flex items-center gap-3">
              <div className={cn('w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center', iconColor)}>
                <Icon className="w-5 h-5 text-white" />
              </div>
              <h2 className={cn('font-bold', text.primary)}>{titulo}</h2>
            </div>
            <button
              onClick={onToggle}
              className={cn('p-2 rounded-lg transition-colors hover:bg-white/10', text.muted)}
              title="Minimizar"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto min-h-0">
            {children}
          </div>
        </>
      ) : (
        // Modo Colapsado - Mostra apenas ícone com tooltip
        <button
          onClick={onToggle}
          className="flex-1 flex flex-col items-center justify-center gap-2 hover:bg-white/5 transition-colors group relative"
          title={titulo}
        >
          <div className={cn('w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center', iconColor)}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          {/* Tooltip */}
          <div className={cn(
            'absolute left-full ml-2 px-3 py-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50',
            glass.glassStrong
          )}>
            <span className={cn('text-sm font-medium', text.primary)}>{titulo}</span>
          </div>
        </button>
      )}
    </div>
  );
}
