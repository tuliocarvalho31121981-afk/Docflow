# Clinic OS - Frontend

Sistema operacional para clínicas com interface Liquid Glass.

## 🚀 Quick Start

```bash
# Instalar dependências
npm install

# Rodar em desenvolvimento
npm run dev

# Build para produção
npm run build

# Rodar produção
npm start
```

Acesse [http://localhost:3000](http://localhost:3000)

## 📁 Estrutura

```
src/
├── app/                    # Next.js App Router
│   ├── page.tsx           # Login
│   └── dashboard/         # Área logada
│       ├── layout.tsx     # Layout com Dock
│       ├── page.tsx       # Home
│       ├── kanban/        # Módulo Kanban
│       ├── governanca/    # Módulo Governança
│       ├── agenda/        # Módulo Agenda
│       ├── chat/          # Módulo Chat
│       └── pacientes/     # Módulo Pacientes
├── components/
│   ├── ui/               # Componentes base (Button, Input, etc)
│   ├── modules/          # Componentes de módulos
│   └── layout/           # Componentes de layout
├── lib/
│   ├── api.ts            # Cliente API
│   ├── store.ts          # Zustand store
│   └── utils.ts          # Utilitários
└── styles/
    └── globals.css       # Estilos globais + Tailwind
```

## 🎨 Design System

### Glass Effects
```tsx
import { getGlassStyles } from '@/lib/utils';

const { glass, glassStrong, glassSolid } = getGlassStyles(isDark);
```

### Text Styles
```tsx
import { getTextStyles } from '@/lib/utils';

const { primary, secondary, muted } = getTextStyles(isDark);
```

### Wallpapers
```tsx
import { WALLPAPERS, useAppStore } from '@/lib/store';

const { wallpaper, setWallpaper } = useAppStore();
```

## 🔌 Conectando ao Backend

1. Copie `.env.example` para `.env.local`
2. Configure a URL do backend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

3. A API está configurada em `src/lib/api.ts`

## 📱 Responsivo

- Desktop: Layout completo com módulos lado a lado
- Tablet: Layout adaptado
- Mobile: Interface estilo smartphone

## 🛠️ Tecnologias

- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Icons**: Lucide React
- **Drag & Drop**: dnd-kit (para Kanban)

## 📝 Próximos Passos

- [ ] Implementar Kanban completo
- [ ] Implementar Chat com WebSocket
- [ ] Implementar Agenda com calendário
- [ ] Implementar SOAP com gravação de áudio
- [ ] PWA para mobile
- [ ] Push notifications

## 🎯 Padrões

### Criar novo módulo

1. Criar pasta em `src/app/dashboard/[modulo]/`
2. Criar `page.tsx` com o conteúdo
3. Adicionar ao Dock em `src/app/dashboard/layout.tsx`
4. Adicionar rota na API em `src/lib/api.ts`

### Componentes

- Use `cn()` para merge de classes Tailwind
- Use `getGlassStyles()` para efeitos glass
- Use `getTextStyles()` para cores de texto
