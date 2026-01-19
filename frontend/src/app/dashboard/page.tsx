'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Calendar, Target, MessageCircle, Users, Shield, BarChart3,
  ChevronRight, Bell, Check, Clock, Sparkles, Settings,
  TrendingUp, AlertCircle, FileText, Mic, CreditCard,
  ArrowUpRight, Activity
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles, getGreeting, formatDate } from '@/lib/utils';

export default function DashboardHome() {
  const router = useRouter();
  const { user, isDark, setActiveModule } = useAppStore();
  const [currentTime, setCurrentTime] = useState(new Date());

  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  // Update time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Mock data
  const stats = {
    consultas: 14,
    realizadas: 8,
    aguardando: 3,
    precisao: 94,
    validacoesPendentes: 8,
    mensagensNaoLidas: 5
  };

  const proximasConsultas = [
    { time: '14:00', name: 'Maria Silva', type: 'Retorno', status: 'arrived', doctor: 'Dra. Ana' },
    { time: '14:30', name: 'João Santos', type: '1ª consulta', status: 'coming', doctor: 'Dra. Ana' },
    { time: '15:00', name: 'Ana Costa', type: 'Exames', status: 'confirmed', doctor: 'Dr. Pedro' },
  ];

  const ultimasMensagens = [
    { name: 'Maria Silva', message: 'Cheguei na clínica', time: '2 min', unread: true },
    { name: 'João Santos', message: 'Vou atrasar 10 min', time: '15 min', unread: true },
    { name: 'Ana Costa', message: 'Ok, confirmado!', time: '1h', unread: false },
  ];

  const apps = [
    { icon: Calendar, label: 'Agenda', gradient: 'from-blue-500 to-blue-600', desc: 'Gerenciar consultas', path: '/dashboard/agenda' },
    { icon: Target, label: 'Card', gradient: 'from-emerald-500 to-green-600', desc: 'Fluxo de pacientes', badge: 3, path: '/dashboard/cards' },
    { icon: MessageCircle, label: 'Chat', gradient: 'from-violet-500 to-purple-600', desc: 'WhatsApp', badge: 5, path: '/dashboard/chat' },
    { icon: Users, label: 'Pacientes', gradient: 'from-orange-500 to-amber-600', desc: 'Cadastros', path: '/dashboard/pacientes' },
    { icon: Shield, label: 'Governança', gradient: 'from-pink-500 to-rose-600', desc: 'Validações', badge: 8, path: '/dashboard/governanca' },
    { icon: Mic, label: 'SOAP', gradient: 'from-cyan-500 to-teal-600', desc: 'Transcrição IA', path: '/dashboard/soap' },
    { icon: FileText, label: 'Prontuário', gradient: 'from-indigo-500 to-blue-600', desc: 'Documentos', path: '/dashboard/prontuario' },
    { icon: BarChart3, label: 'Relatórios', gradient: 'from-amber-500 to-orange-600', desc: 'Métricas', path: '/dashboard/relatorios' },
    { icon: CreditCard, label: 'Financeiro', gradient: 'from-green-500 to-emerald-600', desc: 'Pagamentos', path: '/dashboard/financeiro' },
    { icon: Settings, label: 'Configurar', gradient: 'from-neutral-500 to-neutral-600', desc: 'Sistema', path: '/dashboard/config' },
  ];

  const navigateTo = (path: string, label: string) => {
    setActiveModule(label);
    router.push(path);
  };

  return (
    <div className="p-6 pb-8 overflow-y-auto">
      <div className="max-w-7xl mx-auto">

        {/* Header */}
        <div className="flex items-start justify-between mb-8">
          <div>
            <p className={cn('text-sm capitalize', text.muted)}>{formatDate(currentTime)}</p>
            <h1 className={cn('text-4xl font-bold mt-1', text.primary)}>
              {getGreeting()},{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-purple-400">
                {user?.name.split(' ')[0]}
              </span>
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden sm:block">
              <p className={cn('text-lg font-semibold', text.primary)}>
                {currentTime.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
              </p>
              <p className={cn('text-xs', text.muted)}>{user?.clinicaNome}</p>
            </div>
          </div>
        </div>

        {/* Quick Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* Consultas */}
          <div className={cn(glass.glassStrong, 'rounded-2xl p-5')}>
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-400" />
              </div>
              <span className="text-xs font-semibold text-emerald-400 bg-emerald-500/20 px-2 py-0.5 rounded-full flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                +12%
              </span>
            </div>
            <p className={cn('text-3xl font-bold', text.primary)}>{stats.consultas}</p>
            <p className={cn('text-sm mt-1', text.muted)}>consultas hoje</p>
            <div className="flex gap-2 mt-3">
              <span className={cn('text-xs', text.secondary)}>✓ {stats.realizadas} realizadas</span>
              <span className={cn('text-xs', text.muted)}>· {stats.aguardando} aguardando</span>
            </div>
          </div>

          {/* Precisão */}
          <div className={cn(glass.glassStrong, 'rounded-2xl p-5')}>
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/20 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-emerald-400" />
              </div>
              <Activity className={cn('w-5 h-5', text.muted)} />
            </div>
            <p className={cn('text-3xl font-bold', text.primary)}>
              {stats.precisao}<span className={cn('text-lg', text.muted)}>%</span>
            </p>
            <p className={cn('text-sm mt-1', text.muted)}>precisão do sistema</p>
            <div className="mt-3 h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-green-400 rounded-full"
                style={{ width: `${stats.precisao}%` }}
              />
            </div>
          </div>

          {/* Governança */}
          <div
            onClick={() => navigateTo('/dashboard/governanca', 'Governança')}
            className={cn(glass.glassStrong, 'rounded-2xl p-5 cursor-pointer hover:bg-white/[0.12] transition-all')}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500/20 flex items-center justify-center">
                <Shield className="w-5 h-5 text-orange-400" />
              </div>
              <ChevronRight className={cn('w-5 h-5', text.muted)} />
            </div>
            <p className={cn('text-3xl font-bold', text.primary)}>{stats.validacoesPendentes}</p>
            <p className={cn('text-sm mt-1', text.muted)}>validações pendentes</p>
            <div className="mt-3 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-orange-500/20">
              <AlertCircle className="w-3 h-3 text-orange-400" />
              <span className="text-xs font-medium text-orange-400">Ação necessária</span>
            </div>
          </div>

          {/* Mensagens */}
          <div
            onClick={() => navigateTo('/dashboard/chat', 'Chat')}
            className={cn(glass.glassStrong, 'rounded-2xl p-5 cursor-pointer hover:bg-white/[0.12] transition-all')}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-violet-400" />
              </div>
              <ChevronRight className={cn('w-5 h-5', text.muted)} />
            </div>
            <p className={cn('text-3xl font-bold', text.primary)}>{stats.mensagensNaoLidas}</p>
            <p className={cn('text-sm mt-1', text.muted)}>mensagens não lidas</p>
            <div className="mt-3 inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/20">
              <span className="w-2 h-2 bg-violet-400 rounded-full animate-pulse" />
              <span className="text-xs font-medium text-violet-400">Novas mensagens</span>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-12 gap-6">

          {/* Left - Próximas + Mensagens */}
          <div className="col-span-12 lg:col-span-5 space-y-6">
            {/* Próximas Consultas */}
            <div className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
              <div className="p-5 border-b border-white/[0.08] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
                    <Clock className="w-5 h-5 text-blue-400" />
                  </div>
                  <div>
                    <h2 className={cn('text-lg font-semibold', text.primary)}>Próximas</h2>
                    <p className={cn('text-xs', text.muted)}>Consultas de hoje</p>
                  </div>
                </div>
                <button
                  onClick={() => navigateTo('/dashboard/agenda', 'Agenda')}
                  className={cn(glass.glass, 'rounded-lg px-3 py-1.5 text-xs font-medium hover:bg-white/20 transition-all flex items-center gap-1', text.secondary)}
                >
                  Ver agenda
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="p-3">
                {proximasConsultas.map((consulta, i) => (
                  <div
                    key={i}
                    className={cn(glass.glass, 'rounded-xl p-4 mb-2 last:mb-0 cursor-pointer hover:bg-white/20 transition-all')}
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-center w-14">
                        <p className={cn('text-2xl font-bold', text.primary)}>{consulta.time.split(':')[0]}</p>
                        <p className={cn('text-xs', text.muted)}>{consulta.time}</p>
                      </div>
                      <div className={cn(
                        'w-1 h-12 rounded-full',
                        consulta.status === 'arrived' ? 'bg-emerald-500' :
                        consulta.status === 'coming' ? 'bg-orange-500' : 'bg-white/20'
                      )} />
                      <div className="flex-1">
                        <p className={cn('text-base font-semibold', text.primary)}>{consulta.name}</p>
                        <p className={cn('text-sm', text.secondary)}>{consulta.type} · {consulta.doctor}</p>
                      </div>
                      <div className={cn(
                        'px-2.5 py-1 rounded-full',
                        consulta.status === 'arrived' ? 'bg-emerald-500/20' :
                        consulta.status === 'coming' ? 'bg-orange-500/20' : 'bg-white/10'
                      )}>
                        {consulta.status === 'arrived' && (
                          <span className="text-xs font-medium text-emerald-400 flex items-center gap-1">
                            <span className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
                            Chegou
                          </span>
                        )}
                        {consulta.status === 'coming' && (
                          <span className="text-xs font-medium text-orange-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            A caminho
                          </span>
                        )}
                        {consulta.status === 'confirmed' && (
                          <span className={cn('text-xs font-medium', text.muted)}>Confirmado</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Últimas Mensagens */}
            <div className={cn(glass.glassStrong, 'rounded-2xl overflow-hidden')}>
              <div className="p-5 border-b border-white/[0.08] flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                    <MessageCircle className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <h2 className={cn('text-lg font-semibold', text.primary)}>Mensagens</h2>
                    <p className={cn('text-xs', text.muted)}>WhatsApp recentes</p>
                  </div>
                </div>
                <div className="w-6 h-6 rounded-full bg-red-500 flex items-center justify-center">
                  <span className="text-[10px] font-bold text-white">{stats.mensagensNaoLidas}</span>
                </div>
              </div>

              <div className="p-3">
                {ultimasMensagens.map((msg, i) => (
                  <div
                    key={i}
                    className={cn(glass.glass, 'rounded-xl p-3 mb-2 last:mb-0 cursor-pointer hover:bg-white/20 transition-all')}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-violet-500 flex items-center justify-center flex-shrink-0">
                        <span className="text-sm font-bold text-white">{msg.name[0]}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className={cn('text-sm font-medium', text.primary)}>{msg.name}</span>
                          <span className={cn('text-[10px]', text.muted)}>{msg.time}</span>
                        </div>
                        <p className={cn('text-xs truncate', text.secondary)}>{msg.message}</p>
                      </div>
                      {msg.unread && (
                        <div className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right - Apps + Governança */}
          <div className="col-span-12 lg:col-span-7 space-y-6">
            {/* Apps Grid */}
            <div className={cn(glass.glassStrong, 'rounded-2xl p-6')}>
              <div className="flex items-center justify-between mb-6">
                <h2 className={cn('text-lg font-semibold', text.primary)}>Módulos</h2>
                <button className={cn(glass.glass, 'rounded-lg px-3 py-1.5 text-xs font-medium hover:bg-white/20 transition-all', text.secondary)}>
                  Personalizar
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
                {apps.map((app) => (
                  <button
                    key={app.label}
                    onClick={() => navigateTo(app.path, app.label)}
                    className={cn(glass.glass, 'rounded-2xl p-4 flex flex-col items-center gap-3 hover:bg-white/20 transition-all group')}
                  >
                    <div className="relative">
                      <div className={cn(
                        'w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform',
                        app.gradient
                      )}>
                        <app.icon className="w-7 h-7 text-white" />
                        <div className="absolute inset-0 rounded-2xl bg-gradient-to-b from-white/20 to-transparent" />
                      </div>
                      {app.badge && (
                        <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-[20px] bg-red-500 rounded-full text-[10px] font-bold text-white flex items-center justify-center px-1">
                          {app.badge}
                        </span>
                      )}
                    </div>
                    <div className="text-center">
                      <p className={cn('text-sm font-medium', text.primary)}>{app.label}</p>
                      <p className={cn('text-[10px]', text.muted)}>{app.desc}</p>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Governança Quick View */}
            <div className={cn(glass.glassStrong, 'rounded-2xl p-6')}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-violet-500/20 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-violet-400" />
                  </div>
                  <div>
                    <h2 className={cn('text-lg font-semibold', text.primary)}>Governança</h2>
                    <p className={cn('text-xs', text.muted)}>Dia 12 de 30 · Implantação</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={cn('text-2xl font-bold', text.primary)}>94%</p>
                  <p className="text-xs text-emerald-400">Meta: 90%</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative h-3 bg-white/10 rounded-full overflow-hidden mb-4">
                <div
                  className="absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-violet-500 to-purple-400"
                  style={{ width: '94%' }}
                >
                  <div className="h-full bg-gradient-to-b from-white/30 to-transparent" />
                </div>
                <div
                  className="absolute top-0 bottom-0 w-0.5 bg-white/50"
                  style={{ left: '90%' }}
                />
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-4 gap-3">
                {[
                  { label: 'Pendentes', value: '8', color: 'text-orange-400' },
                  { label: 'Aprovadas', value: '142', color: 'text-emerald-400' },
                  { label: 'Corrigidas', value: '6', color: 'text-yellow-400' },
                  { label: 'Rejeitadas', value: '2', color: 'text-red-400' },
                ].map((stat) => (
                  <div key={stat.label} className={cn(glass.glass, 'rounded-xl p-3 text-center')}>
                    <p className={cn('text-xl font-bold', stat.color)}>{stat.value}</p>
                    <p className={cn('text-[10px]', text.muted)}>{stat.label}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
