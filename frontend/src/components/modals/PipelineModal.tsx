import { useState, useEffect } from 'react';
import {
  X, Loader2, Bot, Users, Newspaper,
  ArrowRight, Sparkles,
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { usePipelineStore } from '../../store/pipelineStore';
import { useStoryStore } from '../../store/storyStore';
import type { PipelineTemplate } from '../../types';

interface PipelineModalProps {
  isOpen: boolean;
  onClose: () => void;
}

// Template metadata: descriptions and icons (the API doesn't return these)
const TEMPLATE_META: Record<string, {
  icon: React.ElementType;
  tagline: string;
  description: string;
  accent: string; // tailwind gradient pair
}> = {
  publisher: {
    icon: Newspaper,
    tagline: 'Equipo editorial de IA',
    description: 'Los curadores seleccionan briefs, los periodistas redactan artículos y un editor los revisa antes de publicar.',
    accent: 'from-pink-500/20 to-rose-500/10 text-pink-300',
  },
};

export function PipelineModal({ isOpen, onClose }: PipelineModalProps) {
  const { templates, fetchTemplates, createBoard, isLoading } = usePipelineStore();
  const { fetchStories } = useStoryStore();
  const [selectedTemplate, setSelectedTemplate] = useState<PipelineTemplate | null>(null);
  const [boardName, setBoardName] = useState('');

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
      setSelectedTemplate(null);
      setBoardName('');
    }
  }, [isOpen, fetchTemplates]);

  const handleSelect = (template: PipelineTemplate) => {
    setSelectedTemplate(template);
    setBoardName(template.name);
  };

  const handleCreate = async () => {
    if (!selectedTemplate) return;
    const board = await createBoard(selectedTemplate.template_id, boardName || undefined);
    fetchStories(board.id);
    onClose();
  };

  const pluralize = (noun: string) => {
    const lower = noun.toLowerCase();
    if (lower.endsWith('y') && !/[aeiou]y$/.test(lower)) return noun.slice(0, -1) + 'ies';
    if (lower.endsWith('s')) return noun;
    return noun + 's';
  };

  if (!isOpen) return null;

  // Selected-template detail view
  if (selectedTemplate) {
    const meta = TEMPLATE_META[selectedTemplate.template_id] ?? {
      icon: Bot,
      tagline: 'Flujo de trabajo con IA',
      description: '',
      accent: 'from-blue-500/20 to-indigo-500/10 text-blue-300',
    };
    const Icon = meta.icon;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
        <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

        <div className="relative surface shadow-2xl w-full max-w-xl mx-4 max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between px-5 h-14 border-b border-border shrink-0">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setSelectedTemplate(null)}
                className="text-muted-foreground hover:text-foreground text-sm"
              >
                ← Atrás
              </button>
              <span className="text-muted-foreground/40">/</span>
              <h2 className="text-sm font-medium text-foreground">Configurar tablero</h2>
            </div>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="p-6 overflow-y-auto flex-1 space-y-5">
            {/* Template summary */}
            <div className={cn(
              'rounded-lg border border-border/60 bg-gradient-to-br p-4 flex items-start gap-3',
              meta.accent
            )}>
              <div className="w-10 h-10 rounded-md bg-card/60 ring-1 ring-white/5 flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="font-medium text-foreground">{selectedTemplate.name}</div>
                <p className="text-xs leading-relaxed mt-0.5 opacity-90">
                  {meta.description}
                </p>
              </div>
            </div>

            {/* Pipeline preview */}
            <div>
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2 block">
                Flujo
              </label>
              <div className="flex items-center gap-1.5 flex-wrap">
                {selectedTemplate.columns.map((col, i) => (
                  <div key={col.key} className="flex items-center gap-1.5">
                    <span className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-xs text-foreground bg-secondary/60 border border-border">
                      <span className={cn('status-dot', col.color)} />
                      {col.label}
                    </span>
                    {i < selectedTemplate.columns.length - 1 && (
                      <ArrowRight className="w-3 h-3 text-muted-foreground/40 flex-shrink-0" />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Board name */}
            <div>
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2 block">
                Nombre del tablero
              </label>
              <input
                type="text"
                value={boardName}
                onChange={(e) => setBoardName(e.target.value)}
                placeholder={selectedTemplate.name}
                className="w-full h-10 px-3 bg-input border border-border rounded-md text-foreground placeholder-muted-foreground/60 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                autoFocus
                onKeyDown={(e) => { if (e.key === 'Enter') handleCreate(); }}
              />
            </div>
          </div>

          {/* Footer */}
          <div className="px-5 h-14 flex items-center justify-end gap-2 border-t border-border shrink-0">
            <button
              onClick={() => setSelectedTemplate(null)}
              className="btn-ghost"
            >
              Cancelar
            </button>
            <button
              onClick={handleCreate}
              disabled={isLoading}
              className="btn-primary"
            >
              {isLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
              Crear tablero
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Template grid
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative surface shadow-2xl w-full max-w-3xl mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-border shrink-0">
          <div>
            <h2 className="text-sm font-medium text-foreground">Nuevo tablero</h2>
            <p className="text-[11px] text-muted-foreground -mt-0.5">Elige un flujo de trabajo para empezar</p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Template grid */}
        <div className="p-4 overflow-y-auto flex-1">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {templates.map((template) => {
              const meta = TEMPLATE_META[template.template_id] ?? {
                icon: Bot,
                tagline: 'Flujo de trabajo con IA',
                description: '',
                accent: 'from-zinc-500/20 to-zinc-500/10 text-zinc-300',
              };
              const Icon = meta.icon;

              return (
                <button
                  key={template.template_id}
                  onClick={() => handleSelect(template)}
                  className={cn(
                    'group text-left rounded-lg border border-border bg-card/40 p-4 transition-all',
                    'hover:border-border/100 hover:bg-card hover:-translate-y-px hover:shadow-lg hover:shadow-black/30'
                  )}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className={cn(
                      'w-9 h-9 rounded-md bg-gradient-to-br border border-border/40 flex items-center justify-center',
                      meta.accent
                    )}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="inline-flex items-center gap-1 text-[10px] uppercase tracking-wider text-muted-foreground">
                      {template.agent_automation ? (
                        <><Bot className="w-3 h-3" /> Automático</>
                      ) : (
                        <><Users className="w-3 h-3" /> Manual</>
                      )}
                    </span>
                  </div>

                  <h3 className="font-medium text-foreground text-sm mb-1 leading-snug">
                    {template.name}
                  </h3>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-3 line-clamp-2 min-h-[2lh]">
                    {meta.description}
                  </p>

                  {/* Compact pipeline preview as dots */}
                  <div className="flex items-center gap-1 mt-2">
                    {template.columns.map((col) => (
                      <span
                        key={col.key}
                        className={cn('status-dot', col.color)}
                        title={col.label}
                      />
                    ))}
                    <span className="text-[10px] text-muted-foreground/60 ml-1.5">
                      {template.columns.length} etapas · {pluralize(template.item_noun)}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
