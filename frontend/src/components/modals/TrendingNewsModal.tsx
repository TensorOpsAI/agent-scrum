import { useState } from 'react';
import { X, TrendingUp, Loader2, CheckCircle2, Plus, Newspaper } from 'lucide-react';
import { cn } from '../../lib/utils';
import { storyApi } from '../../api/client';
import { useStoryStore } from '../../store/storyStore';
import { usePipelineStore } from '../../store/pipelineStore';
import { TRENDING_NEWS } from '../../fixtures/trendingNews';

interface TrendingNewsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type ItemState = 'idle' | 'translating' | 'added';

export function TrendingNewsModal({ isOpen, onClose }: TrendingNewsModalProps) {
  const currentBoardId = usePipelineStore((s) => s.currentBoardId);
  const { fetchStories } = useStoryStore();
  const [states, setStates] = useState<Record<string, ItemState>>({});

  if (!isOpen) return null;

  const handleAdd = async (item: (typeof TRENDING_NEWS)[number]) => {
    if (!currentBoardId || states[item.id]) return;
    setStates((prev) => ({ ...prev, [item.id]: 'translating' }));

    // Simulated agent step: translate + adapt tone to El País's style before landing on the board.
    await new Promise((resolve) => setTimeout(resolve, 900));

    try {
      await storyApi.create({
        board_id: currentBoardId,
        title: item.esTitle,
        description: `${item.esTeaser}\n\nFuente original: ${item.source} — "${item.originalTitle}"`,
        priority: 1,
      });
      await fetchStories(currentBoardId);
      setStates((prev) => ({ ...prev, [item.id]: 'added' }));
    } catch (error) {
      console.error('Error creating story from trending item:', error);
      setStates((prev) => ({ ...prev, [item.id]: 'idle' }));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative surface shadow-2xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-border shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <TrendingUp className="w-4 h-4 text-primary flex-shrink-0" />
            <div>
              <h2 className="text-sm font-medium text-foreground">Tendencias</h2>
              <p className="text-[11px] text-muted-foreground -mt-0.5">
                Noticias en tendencia ahora mismo — añade una al tablero
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* List */}
        <div className="p-4 overflow-y-auto flex-1 space-y-2.5">
          {TRENDING_NEWS.map((item) => {
            const state = states[item.id] ?? 'idle';
            return (
              <div key={item.id} className="surface-muted p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <span className="inline-flex items-center gap-1 text-[10px] font-medium uppercase tracking-wider text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                        <TrendingUp className="w-2.5 h-2.5" />
                        {item.category}
                      </span>
                      <span className="text-[10px] text-muted-foreground/70">{item.source}</span>
                    </div>
                    <h3 className="text-sm font-medium text-foreground leading-snug">
                      {item.originalTitle}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                      {item.originalTeaser}
                    </p>
                  </div>

                  <button
                    onClick={() => handleAdd(item)}
                    disabled={state !== 'idle'}
                    className={cn(
                      'inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-xs font-medium transition-colors flex-shrink-0 whitespace-nowrap',
                      state === 'added'
                        ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/30'
                        : state === 'translating'
                        ? 'bg-secondary text-muted-foreground cursor-wait'
                        : 'bg-primary hover:bg-primary/90 text-primary-foreground'
                    )}
                  >
                    {state === 'added' ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        Añadido
                      </>
                    ) : state === 'translating' ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        Traduciendo…
                      </>
                    ) : (
                      <>
                        <Plus className="w-3.5 h-3.5" />
                        Añadir al tablero
                      </>
                    )}
                  </button>
                </div>

                {state === 'added' && (
                  <div className="mt-3 pt-3 border-t border-border/60 flex items-start gap-2 animate-fade-in">
                    <Newspaper className="w-3.5 h-3.5 text-primary flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-foreground/90 leading-relaxed">
                      <span className="font-medium">{item.esTitle}</span>
                      <br />
                      <span className="text-muted-foreground">{item.esTeaser}</span>
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
