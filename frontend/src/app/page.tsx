'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Shield, ArrowRight, Eye, EyeOff, Sparkles,
  CheckCircle2, Lock, Mail, Building2
} from 'lucide-react';
import { useAppStore } from '@/lib/store';
import { api } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAppStore((state) => state.setUser);

  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    clinicaId: '1',
    email: '',
    password: '',
    remember: false,
  });

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      // Login real no backend
      const response = await api.login(
        formData.email,
        formData.password,
        formData.clinicaId
      );

      // Limpar tokens antigos antes de salvar o novo
      localStorage.removeItem('auth_token');
      localStorage.removeItem('refresh_token');
      sessionStorage.removeItem('auth_token');
      sessionStorage.removeItem('refresh_token');

      // Configurar token no api client
      api.setToken(response.access_token);

      // Armazenar token no localStorage se "Lembrar-me" estiver marcado
      if (formData.remember && response.access_token) {
        localStorage.setItem('auth_token', response.access_token);
        if (response.refresh_token) {
          localStorage.setItem('refresh_token', response.refresh_token);
        }
      } else {
        // Se não marcar "Lembrar-me", salvar apenas em sessionStorage
        sessionStorage.setItem('auth_token', response.access_token);
        if (response.refresh_token) {
          sessionStorage.setItem('refresh_token', response.refresh_token);
        }
      }

      // Configurar usuário no store
      setUser({
        id: response.user.id,
        name: response.user.nome,
        email: response.user.email,
        clinicaId: response.user.clinica_id,
        clinicaNome: response.user.clinica_nome,
        role: response.user.perfil?.nome || response.user.tipo || 'user',
      });

      router.push('/dashboard');
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Email ou senha incorretos';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full relative overflow-hidden">
      {/* Animated Background */}
      <div
        className="absolute inset-0"
        style={{
          background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0f0f1a 100%)'
        }}
      />

      {/* Gradient Orbs */}
      <div className="absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full opacity-30 blur-[120px]"
        style={{ background: 'radial-gradient(circle, #6366f1 0%, transparent 70%)' }}
      />
      <div className="absolute bottom-[-20%] right-[-10%] w-[600px] h-[600px] rounded-full opacity-30 blur-[120px]"
        style={{ background: 'radial-gradient(circle, #8b5cf6 0%, transparent 70%)' }}
      />
      <div className="absolute top-[50%] left-[50%] translate-x-[-50%] translate-y-[-50%] w-[800px] h-[800px] rounded-full opacity-20 blur-[100px]"
        style={{ background: 'radial-gradient(circle, #3b82f6 0%, transparent 70%)' }}
      />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)`,
          backgroundSize: '50px 50px'
        }}
      />

      {/* Content */}
      <div className="relative z-10 min-h-screen flex">

        {/* Left Side - Branding */}
        <div className="hidden lg:flex flex-1 flex-col justify-between p-12">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Clinic OS</h1>
              <p className="text-xs text-white/40">Sistema Inteligente</p>
            </div>
          </div>

          <div className="max-w-lg">
            <h2 className="text-5xl font-bold text-white leading-tight mb-6">
              A recepção da sua clínica,{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-violet-400 to-purple-400">
                reinventada.
              </span>
            </h2>
            <p className="text-lg text-white/60 leading-relaxed mb-8">
              Automação inteligente com supervisão humana.
              Seu sistema aprende, você governa.
            </p>

            <div className="space-y-4">
              {[
                { icon: Sparkles, text: 'IA que aprende com suas correções' },
                { icon: Shield, text: 'Governança com 94%+ de precisão' },
                { icon: CheckCircle2, text: 'Humano no controle, sempre' },
              ].map((feature, i) => (
                <div key={i} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-white/5 border border-white/10 flex items-center justify-center">
                    <feature.icon className="w-4 h-4 text-violet-400" />
                  </div>
                  <span className="text-white/70">{feature.text}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-6 text-sm text-white/30">
            <span>© 2025 Clinic OS</span>
            <span>·</span>
            <a href="#" className="hover:text-white/50 transition-colors">Termos</a>
            <span>·</span>
            <a href="#" className="hover:text-white/50 transition-colors">Privacidade</a>
          </div>
        </div>

        {/* Right Side - Login Form */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-md">

            {/* Mobile Logo */}
            <div className="lg:hidden flex items-center justify-center gap-3 mb-12">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/25">
                <Shield className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Clinic OS</h1>
                <p className="text-xs text-white/40">Sistema Inteligente</p>
              </div>
            </div>

            {/* Login Card */}
            <div className="backdrop-blur-2xl bg-white/[0.03] border border-white/10 rounded-3xl p-8 shadow-2xl">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-white mb-2">Bem-vindo de volta</h3>
                <p className="text-white/50">Entre para acessar sua clínica</p>
              </div>

              {error && (
                <div className="mb-6 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm text-center">
                  {error}
                </div>
              )}

              <form onSubmit={handleLogin} className="space-y-5">
                {/* Clinic Select */}
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Clínica
                  </label>
                  <div className="relative">
                    <Building2 className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                    <select
                      value={formData.clinicaId}
                      onChange={(e) => setFormData({ ...formData, clinicaId: e.target.value })}
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3.5 text-white appearance-none outline-none focus:border-violet-500/50 focus:bg-white/[0.07] transition-all"
                    >
                      <option value="1">Clínica São Paulo</option>
                      <option value="2">Clínica Centro</option>
                    </select>
                  </div>
                </div>

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Email
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                    <input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="seu@email.com"
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-4 py-3.5 text-white placeholder-white/30 outline-none focus:border-violet-500/50 focus:bg-white/[0.07] transition-all"
                    />
                  </div>
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-white/70 mb-2">
                    Senha
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/30" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      placeholder="••••••••"
                      className="w-full bg-white/5 border border-white/10 rounded-xl pl-12 pr-12 py-3.5 text-white placeholder-white/30 outline-none focus:border-violet-500/50 focus:bg-white/[0.07] transition-all"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-4 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/50 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                {/* Remember & Forgot */}
                <div className="flex items-center justify-between">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.remember}
                      onChange={(e) => setFormData({ ...formData, remember: e.target.checked })}
                      className="w-4 h-4 rounded border-white/20 bg-white/5 text-violet-500 focus:ring-violet-500/50"
                    />
                    <span className="text-sm text-white/50">Lembrar-me</span>
                  </label>
                  <a href="#" className="text-sm text-violet-400 hover:text-violet-300 transition-colors">
                    Esqueceu a senha?
                  </a>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white font-semibold py-3.5 rounded-xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-violet-500/25 disabled:opacity-50"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  ) : (
                    <>
                      Entrar
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>
            </div>

            <p className="text-center text-white/30 text-sm mt-6">
              Precisa de ajuda?{' '}
              <a href="#" className="text-violet-400 hover:text-violet-300 transition-colors">
                Fale conosco
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
