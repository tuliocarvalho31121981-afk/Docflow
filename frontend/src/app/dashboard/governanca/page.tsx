'use client';

import React from 'react';
import { Shield, Check, X, Edit, AlertCircle } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

export default function GovernancaPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  const validacoes = [
    { id: 1, type: 'whatsapp', title: '"quero remarcar"', confidence: 87, action: 'REMARCAR', priority: 'alta' },
    { id: 2, type: 'fase', title: 'Maria Silva: Fase 0→1', evidence: '2/2', priority: 'normal' },
    { id: 3, type: 'whatsapp', title: '"cheguei"', confidence: 95, action: 'CHECK-IN', priority: 'normal' },
    { id: 4, type: 'fase', title: 'João Santos: Fase 1→2', evidence: '3/3', priority: 'normal' },
  ];

  return (
    <div className="p-6 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center shadow-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className={cn('text-2xl font-bold', text.primary)}>Governança</h1>
              <p className={cn('text-sm', text.muted)}>Dia 12 de 30 · Implantação</p>
            </div>
          </div>
          <div className="text-right">
            <p className={cn('text-3xl font-bold', text.primary)}>94%</p>
            <p className="text-sm text-emerald-400">Meta: 90%</p>
          </div>
        </div>

        {/* Progress */}
        <div className={cn(glass.glassStrong, 'rounded-2xl p-5 mb-6')}>
          <div className="flex items-center justify-between mb-3">
            <span className={cn('text-sm font-medium', text.secondary)}>Progresso da Implantação</span>
            <span className={cn('text-sm', text.muted)}>18 dias restantes</span>
          </div>
          <div className="relative h-3 bg-white/10 rounded-full overflow-hidden">
            <div 
              className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-400"
              style={{ width: '94%' }}
            >
              <div className="h-full bg-gradient-to-b from-white/30 to-transparent" />
            </div>
            <div className="absolute top-0 bottom-0 w-0.5 bg-white/50" style={{ left: '90%' }} />
          </div>
          <div className="flex justify-between mt-2">
            <span className={cn('text-xs', text.muted)}>0%</span>
            <span className="text-xs text-emerald-400">Meta 90%</span>
            <span className={cn('text-xs', text.muted)}>100%</span>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Pendentes', value: '8', color: 'text-orange-400', bg: 'bg-orange-500/20' },
            { label: 'Aprovadas', value: '142', color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
            { label: 'Corrigidas', value: '6', color: 'text-yellow-400', bg: 'bg-yellow-500/20' },
            { label: 'Rejeitadas', value: '2', color: 'text-red-400', bg: 'bg-red-500/20' },
          ].map((stat) => (
            <div key={stat.label} className={cn(glass.glassStrong, 'rounded-xl p-4 text-center')}>
              <p className={cn('text-2xl font-bold', stat.color)}>{stat.value}</p>
              <p className={cn('text-xs', text.muted)}>{stat.label}</p>
            </div>
          ))}
        </div>

        {/* Pending Validations */}
        <div className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
          <div className="p-4 border-b border-white/10 flex items-center justify-between">
            <h2 className={cn('text-lg font-semibold', text.primary)}>Validações Pendentes</h2>
            <button className="bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-medium px-4 py-2 rounded-xl transition-all">
              Aprovar Todos
            </button>
          </div>

          <div className="divide-y divide-white/10">
            {validacoes.map((v) => (
              <div key={v.id} className="p-4 hover:bg-white/5 transition-all">
                <div className="flex items-start gap-4">
                  <div className={cn(
                    'w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0',
                    v.type === 'whatsapp' ? 'bg-violet-500/20' : 'bg-blue-500/20'
                  )}>
                    {v.type === 'whatsapp' ? (
                      <span className="text-violet-400 text-lg">💬</span>
                    ) : (
                      <span className="text-blue-400 text-lg">🔄</span>
                    )}
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn('text-sm font-medium', text.primary)}>{v.title}</span>
                      {v.priority === 'alta' && (
                        <span className="text-[10px] font-bold text-orange-400 bg-orange-500/20 px-2 py-0.5 rounded-full">
                          ALTA
                        </span>
                      )}
                    </div>
                    {v.confidence && (
                      <p className={cn('text-xs', text.muted)}>
                        Interpretação: {v.action} ({v.confidence}% confiança)
                      </p>
                    )}
                    {v.evidence && (
                      <p className={cn('text-xs', text.muted)}>
                        Evidências: {v.evidence} completas
                      </p>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <button className="w-10 h-10 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 flex items-center justify-center transition-all">
                      <Check className="w-5 h-5 text-emerald-400" />
                    </button>
                    <button className="w-10 h-10 rounded-xl bg-yellow-500/20 hover:bg-yellow-500/30 flex items-center justify-center transition-all">
                      <Edit className="w-5 h-5 text-yellow-400" />
                    </button>
                    <button className="w-10 h-10 rounded-xl bg-red-500/20 hover:bg-red-500/30 flex items-center justify-center transition-all">
                      <X className="w-5 h-5 text-red-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
