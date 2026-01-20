// Estilos Liquid Glass para o Cockpit do Médico

export function getGlassStyles() {
  return {
    glass: 'bg-white/10 backdrop-blur-xl border border-white/20 shadow-xl',
    glassStrong: 'bg-white/15 backdrop-blur-2xl border border-white/25 shadow-2xl',
    glassSubtle: 'bg-white/5 backdrop-blur-lg border border-white/10',
    glassDark: 'bg-black/20 backdrop-blur-xl border border-white/10',
  };
}

export function getTextStyles() {
  return {
    primary: 'text-white',
    secondary: 'text-white/80',
    muted: 'text-white/60',
    accent: 'text-amber-400',
  };
}
