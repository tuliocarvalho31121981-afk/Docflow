'use client';

import React from 'react';
import { Target } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

export default function KanbanPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  return (
    <div className="p-6 h-full">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 flex items-center justify-center shadow-lg">
            <Target className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={cn('text-2xl font-bold', text.primary)}>Kanban</h1>
            <p className={cn('text-sm', text.muted)}>Fluxo de pacientes</p>
          </div>
        </div>

        <div className={cn(glass.glassStrong, 'rounded-2xl p-8 text-center')}>
          <p className={cn('text-lg', text.secondary)}>
            Módulo em construção...
          </p>
          <p className={cn('text-sm mt-2', text.muted)}>
            Aqui ficará o quadro Kanban com as fases: Agendado → Pré-Consulta → Dia → Pós
          </p>
        </div>
      </div>
    </div>
  );
}
