'use client';
import { Users } from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';

export default function PacientesPage() {
  const { isDark } = useAppStore();
  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  return (
    <div className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg">
          <Users className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className={cn('text-2xl font-bold', text.primary)}>Pacientes</h1>
          <p className={cn('text-sm', text.muted)}>Cadastros e histórico</p>
        </div>
      </div>
      <div className={cn(glass.glassStrong, 'rounded-2xl p-8 text-center')}>
        <p className={cn('text-lg', text.secondary)}>Módulo em construção...</p>
      </div>
    </div>
  );
}
