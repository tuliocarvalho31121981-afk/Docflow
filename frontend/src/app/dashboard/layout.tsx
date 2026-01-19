'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Calendar, Target, MessageCircle, Users, Shield, BarChart3,
  Search, Settings, Bell, Moon, Sun
} from 'lucide-react';
import { useAppStore, WALLPAPERS } from '@/lib/store';
import { cn, getGlassStyles, getTextStyles } from '@/lib/utils';
import { api, clearExpiredTokens } from '@/lib/api';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const router = useRouter();
  const {
    user,
    isDark,
    wallpaper,
    showSettings,
    setShowSettings,
    setWallpaper,
    toggleTheme,
    activeModule,
    setActiveModule
  } = useAppStore();

  const glass = getGlassStyles(isDark);
  const text = getTextStyles(isDark);

  // Recuperar token do localStorage/sessionStorage e configurar no api
  useEffect(() => {
    // Limpar tokens expirados antes de recuperar
    clearExpiredTokens();

    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token');
    if (token) {
      api.setToken(token);
    }
  }, []);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!user) {
      router.push('/');
    }
  }, [user, router]);

  if (!user) return null;

  const apps = [
    { icon: Calendar, label: 'Agenda', path: '/dashboard/agenda', color: 'from-blue-500 to-blue-600' },
    { icon: Target, label: 'Card', path: '/dashboard/cards', color: 'from-emerald-500 to-green-600', badge: 3 },
    { icon: MessageCircle, label: 'Chat', path: '/dashboard/chat', color: 'from-violet-500 to-purple-600', badge: 5 },
    { icon: Users, label: 'Pacientes', path: '/dashboard/pacientes', color: 'from-orange-500 to-amber-600' },
    { icon: Shield, label: 'Governança', path: '/dashboard/governanca', color: 'from-pink-500 to-rose-600', badge: 8 },
    { icon: BarChart3, label: 'Relatórios', path: '/dashboard/relatorios', color: 'from-cyan-500 to-teal-600' },
  ];

  const handleNavigate = (path: string, label: string) => {
    setActiveModule(label);
    router.push(path);
  };

  return (
    <div
      className="min-h-screen w-full relative overflow-hidden"
      style={{ background: WALLPAPERS[wallpaper] }}
    >
      {/* Noise texture */}
      <div className="absolute inset-0 opacity-[0.02] pointer-events-none noise" />

      {/* Main Content */}
      <main className="relative z-10 min-h-screen pb-24">
        {children}
      </main>

      {/* Bottom Dock */}
      <div className="fixed bottom-0 left-0 right-0 p-4 z-50">
        <div className={cn(glass.glassSolid, 'rounded-2xl mx-auto max-w-2xl')}>
          <div className="flex items-center justify-between px-4 py-2.5">
            {/* Apps */}
            <div className="flex items-center gap-1">
              {/* Home button */}
              <button
                onClick={() => handleNavigate('/dashboard', 'Home')}
                className={cn(
                  'relative p-1.5 rounded-xl transition-all hover:bg-white/10',
                  activeModule === 'Home' && 'bg-white/10'
                )}
                title="Home"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neutral-600 to-neutral-700 flex items-center justify-center shadow-lg">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                  </svg>
                </div>
              </button>

              {apps.map((app) => (
                <button
                  key={app.label}
                  onClick={() => handleNavigate(app.path, app.label)}
                  className={cn(
                    'relative p-1.5 rounded-xl transition-all hover:bg-white/10',
                    activeModule === app.label && 'bg-white/10'
                  )}
                  title={app.label}
                >
                  <div className={cn(
                    'w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center shadow-lg',
                    app.color
                  )}>
                    <app.icon className="w-5 h-5 text-white" />
                  </div>
                  {app.badge && (
                    <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center">
                      {app.badge}
                    </span>
                  )}
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className={cn('w-px h-10 mx-3', isDark ? 'bg-white/20' : 'bg-black/10')} />

            {/* Search */}
            <button className={cn(glass.glass, 'rounded-xl px-4 py-2 flex items-center gap-2 hover:bg-white/20 transition-all')}>
              <Search className={cn('w-4 h-4', text.muted)} />
              <span className={cn('text-sm hidden sm:inline', text.muted)}>Buscar...</span>
              <div className={cn(glass.glass, 'rounded px-1.5 py-0.5 hidden sm:block')}>
                <span className={cn('text-[10px]', text.muted)}>⌘K</span>
              </div>
            </button>

            {/* Divider */}
            <div className={cn('w-px h-10 mx-3', isDark ? 'bg-white/20' : 'bg-black/10')} />

            {/* Right - Settings */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className={cn(glass.glass, 'rounded-xl p-2 hover:bg-white/20 transition-all')}
              >
                <Settings className={cn('w-5 h-5', text.secondary)} />
              </button>
              <button className={cn('relative', glass.glass, 'rounded-xl p-2 hover:bg-white/20 transition-all')}>
                <Bell className={cn('w-5 h-5', text.secondary)} />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </button>
              <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg">
                <span className="text-sm font-bold text-white">{user.name[0]}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowSettings(false)}
          />

          {/* Panel */}
          <div className={cn(
            glass.glassSolid,
            'fixed bottom-24 right-4 w-72 rounded-2xl p-4 z-50 animate-slide-in'
          )}>
            <div className="flex items-center justify-between mb-4">
              <span className={cn('text-sm font-semibold', text.primary)}>Personalizar</span>
              <button
                onClick={toggleTheme}
                className={cn(glass.glass, 'rounded-full p-2 hover:bg-white/20 transition-all')}
              >
                {isDark ? <Moon className="w-4 h-4 text-white" /> : <Sun className="w-4 h-4" />}
              </button>
            </div>

            <p className={cn('text-xs mb-2', text.muted)}>Papel de parede</p>
            <div className="grid grid-cols-3 gap-2">
              {(Object.keys(WALLPAPERS) as Array<keyof typeof WALLPAPERS>).map((key) => (
                <button
                  key={key}
                  onClick={() => setWallpaper(key)}
                  className={cn(
                    'aspect-video rounded-xl transition-all',
                    wallpaper === key ? 'ring-2 ring-white scale-105' : 'opacity-60 hover:opacity-100'
                  )}
                  style={{ background: WALLPAPERS[key] }}
                />
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/10">
              <p className={cn('text-xs', text.muted)}>
                {user.clinicaNome}
              </p>
              <p className={cn('text-xs', text.muted)}>
                {user.email}
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
