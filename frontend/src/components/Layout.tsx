import { Outlet } from 'react-router-dom';
import {
  Plus, Settings, Users, AlertCircle, X, Sparkles, Key, TrendingUp,
  Play, Square, Pause, Loader2,
} from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';
import { cn } from '../lib/utils';
import { PRDInputModal } from './modals/PRDInputModal';
import { SettingsModal } from './modals/SettingsModal';
import { PipelineModal } from './modals/PipelineModal';
import { TrendingNewsModal } from './modals/TrendingNewsModal';
import { WelcomeModal, isOnboardingComplete } from './modals/WelcomeModal';
import { AgentPanel } from './agents/AgentPanel';
import { AgentManager } from './agents/AgentManager';
import { ChatPanel } from './chat/ChatPanel';
import { StoryDetail } from './story/StoryDetail';
import { useStoryStore } from '../store/storyStore';
import { usePipelineStore } from '../store/pipelineStore';
import { useUIStore } from '../store/uiStore';
import { storyApi, simulateApi, settingsApi } from '../api/client';

export function Layout() {
  const isPRDModalOpen = useUIStore((s) => s.isPRDModalOpen);
  const openPRDModal = useUIStore((s) => s.openPRDModal);
  const closePRDModal = useUIStore((s) => s.closePRDModal);
  const [isSettingsModalOpen, setIsSettingsModalOpen] = useState(false);
  const [isPipelineModalOpen, setIsPipelineModalOpen] = useState(false);
  const [isTrendingModalOpen, setIsTrendingModalOpen] = useState(false);
  const [isAgentManagerOpen, setIsAgentManagerOpen] = useState(false);
  const [isWelcomeOpen, setIsWelcomeOpen] = useState(!isOnboardingComplete());
  const [hasApiKey, setHasApiKey] = useState(!!settingsApi.getLocalApiKey());
  const [swarmStatus, setSwarmStatus] = useState<'running' | 'stopped' | 'paused'>('stopped');
  const [isSwarmLoading, setIsSwarmLoading] = useState(false);
  const [addError, setAddError] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [isSimulating, setIsSimulating] = useState(false);
  const { selectedStoryId, setSelectedStory, fetchStories } = useStoryStore();
  const {
    boards,
    currentBoardId,
    currentBoard,
    fetchBoards,
    setCurrentBoard,
    deleteBoard,
  } = usePipelineStore();

  useEffect(() => { fetchBoards(); }, [fetchBoards]);

  useEffect(() => {
    if (currentBoardId != null) fetchStories(currentBoardId);
  }, [currentBoardId, fetchStories]);

  useEffect(() => {
    if (!isSettingsModalOpen && !isWelcomeOpen) {
      setHasApiKey(!!settingsApi.getLocalApiKey());
    }
  }, [isSettingsModalOpen, isWelcomeOpen]);

  const fetchSwarmStatus = useCallback(async () => {
    try {
      const res = await settingsApi.getSwarmStatus();
      setSwarmStatus(res.status);
    } catch { /* backend may not be ready */ }
  }, []);

  useEffect(() => { fetchSwarmStatus(); }, [fetchSwarmStatus, currentBoardId]);

  const handleSwarmAction = useCallback(async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    setIsSwarmLoading(true);
    try {
      let result;
      switch (action) {
        case 'start':  result = await settingsApi.startSwarm(); break;
        case 'stop':   result = await settingsApi.stopSwarm(); break;
        case 'pause':  result = await settingsApi.pauseSwarm(); break;
        case 'resume': result = await settingsApi.resumeSwarm(); break;
      }
      if (result.success) await fetchSwarmStatus();
    } catch (error) {
      console.error(`Failed to ${action} swarm:`, error);
    } finally {
      setIsSwarmLoading(false);
    }
  }, [fetchSwarmStatus]);

  useEffect(() => {
    if (addError) {
      const timer = setTimeout(() => setAddError(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [addError]);

  const automationEnabled = currentBoard?.agent_automation === true;
  const itemNoun = currentBoard?.item_noun ?? 'Artículo';
  const inputNoun = currentBoard?.input_noun ?? 'Brief';
  const isExternalSource = currentBoard?.item_source === 'external';

  const handleAddItem = async () => {
    if (!currentBoardId) return;
    setIsAdding(true);
    setAddError(null);
    try {
      await storyApi.create({
        board_id: currentBoardId,
        title: `New ${itemNoun}`,
        description: '',
        priority: 0,
      });
      fetchStories(currentBoardId);
    } catch (error) {
      console.error('Error creating item:', error);
      setAddError('No se pudo crear el elemento. ¿Está el backend en ejecución?');
    } finally {
      setIsAdding(false);
    }
  };

  const handleDeleteBoard = async (boardId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const board = boards.find((b) => b.id === boardId);
    if (!board) return;
    if (!confirm(`¿Eliminar el tablero "${board.name}"? Se eliminarán permanentemente todos sus elementos.`)) return;
    await deleteBoard(boardId);
    const newCurrentId = usePipelineStore.getState().currentBoardId;
    if (newCurrentId) fetchStories(newCurrentId);
  };

  const handleSimulate = async () => {
    if (!currentBoardId) return;
    setIsSimulating(true);
    setAddError(null);
    try {
      await simulateApi.generate(currentBoardId);
      fetchStories(currentBoardId);
    } catch (error) {
      console.error('Error simulating items:', error);
      setAddError('No se pudieron generar los elementos.');
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="px-5 h-14 flex items-center justify-between gap-4">
          {/* Brand + Boards */}
          <div className="flex items-center gap-4 min-w-0">
            <div className="flex items-center gap-2 flex-shrink-0">
              <img src="/el-pais-logo.svg" alt="El País" className="h-5 w-auto" />
            </div>

            <div className="h-6 w-px bg-border" />

            {/* Board tabs */}
            <div className="flex items-center gap-0.5 overflow-x-auto">
              {boards.map((board) => (
                <button
                  key={board.id}
                  onClick={() => setCurrentBoard(board.id)}
                  className={cn(
                    'group relative flex items-center gap-1.5 h-8 px-3 rounded-md text-sm whitespace-nowrap transition-colors',
                    board.id === currentBoardId
                      ? 'text-foreground bg-accent'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                  )}
                >
                  <span>{board.name}</span>
                  {boards.length > 1 && (
                    <span
                      role="button"
                      onClick={(e) => handleDeleteBoard(board.id, e)}
                      className={cn(
                        'inline-flex items-center justify-center w-4 h-4 rounded-sm transition-colors',
                        board.id === currentBoardId
                          ? 'hover:bg-secondary'
                          : 'opacity-0 group-hover:opacity-100 hover:bg-secondary'
                      )}
                    >
                      <X className="w-3 h-3" />
                    </span>
                  )}
                </button>
              ))}
              <button
                onClick={() => setIsPipelineModalOpen(true)}
                className="flex items-center gap-1 h-8 px-2.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 rounded-md transition-colors whitespace-nowrap"
                title="Nuevo tablero"
              >
                <Plus className="w-3.5 h-3.5" />
                Nuevo
              </button>
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 relative flex-shrink-0">
            {automationEnabled && (
              <button
                onClick={() => setIsTrendingModalOpen(true)}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium bg-secondary hover:bg-accent text-foreground transition-colors"
              >
                <TrendingUp className="w-3.5 h-3.5" />
                Tendencias
              </button>
            )}

            {/* Swarm */}
            {automationEnabled && (
              <div className="flex items-center gap-1.5">
                {swarmStatus === 'stopped' ? (
                  <button
                    onClick={() => handleSwarmAction('start')}
                    disabled={isSwarmLoading}
                    className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50"
                  >
                    {isSwarmLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                    Iniciar automatización
                  </button>
                ) : (
                  <>
                    <div className={cn(
                      'inline-flex items-center gap-1.5 h-8 px-2.5 rounded-md text-xs font-medium border',
                      swarmStatus === 'running'
                        ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                        : 'border-amber-500/30 bg-amber-500/10 text-amber-300'
                    )}>
                      <span className={cn(
                        'status-dot',
                        swarmStatus === 'running' ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                      )} />
                      {swarmStatus === 'running' ? 'En ejecución' : 'Pausado'}
                    </div>
                    {swarmStatus === 'paused' ? (
                      <button onClick={() => handleSwarmAction('resume')} disabled={isSwarmLoading}
                        className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white disabled:opacity-50 transition-colors"
                        title="Reanudar">
                        {isSwarmLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                      </button>
                    ) : (
                      <button onClick={() => handleSwarmAction('pause')} disabled={isSwarmLoading}
                        className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-secondary hover:bg-accent text-foreground disabled:opacity-50 transition-colors"
                        title="Pausar">
                        {isSwarmLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Pause className="w-3.5 h-3.5" />}
                      </button>
                    )}
                    <button onClick={() => handleSwarmAction('stop')} disabled={isSwarmLoading}
                      className="inline-flex items-center justify-center w-8 h-8 rounded-md bg-secondary hover:bg-destructive/80 text-foreground hover:text-white disabled:opacity-50 transition-colors"
                      title="Detener">
                      <Square className="w-3.5 h-3.5" />
                    </button>
                  </>
                )}
              </div>
            )}

            <div className="h-6 w-px bg-border mx-1" />

            {automationEnabled && (
              <button
                onClick={() => setIsAgentManagerOpen(true)}
                className="inline-flex items-center justify-center w-8 h-8 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                title="Gestionar agentes"
              >
                <Users className="w-4 h-4" />
              </button>
            )}

            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="inline-flex items-center justify-center w-8 h-8 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
              title="Configuración"
            >
              <Settings className="w-4 h-4" />
            </button>

            {automationEnabled && (isExternalSource || currentBoard?.template_id === 'publisher') && (
              <button
                onClick={handleSimulate}
                disabled={isSimulating}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground transition-colors"
              >
                <Sparkles className="w-3.5 h-3.5" />
                {isSimulating ? 'Generando…' : currentBoard?.template_id === 'publisher' ? `Generar ${itemNoun}s` : `Simular ${itemNoun}s`}
              </button>
            )}

            {automationEnabled && currentBoard?.template_id !== 'publisher' ? (
              <button
                onClick={() => openPRDModal()}
                className={cn(
                  'inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium transition-colors',
                  isExternalSource
                    ? 'bg-secondary hover:bg-accent text-foreground'
                    : 'bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm shadow-primary/30'
                )}
              >
                <Plus className="w-3.5 h-3.5" />
                Enviar {inputNoun}
              </button>
            ) : !automationEnabled ? (
              <button
                onClick={handleAddItem}
                disabled={isAdding}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium bg-primary hover:bg-primary/90 disabled:opacity-50 text-primary-foreground transition-colors"
              >
                <Plus className="w-3.5 h-3.5" />
                {isAdding ? 'Añadiendo…' : `Añadir ${itemNoun}`}
              </button>
            ) : null}

            {addError && (
              <div className="absolute top-full right-0 mt-2 flex items-center gap-2 px-3 py-2 bg-destructive/10 border border-destructive/30 text-destructive-foreground text-sm rounded-md whitespace-nowrap animate-fade-in">
                <AlertCircle className="w-4 h-4 flex-shrink-0 text-destructive" />
                {addError}
              </div>
            )}
          </div>
        </div>
      </header>

      {/* API Key banner */}
      {!hasApiKey && (
        <div className="flex-shrink-0 border-b border-primary/20 bg-primary/5">
          <div className="px-5 py-2.5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-primary/90 text-sm">
              <Key className="w-3.5 h-3.5 flex-shrink-0" />
              <span>
                <span className="font-medium text-primary">No hay clave API configurada.</span>
                <span className="text-primary/70"> Los agentes no podrán procesar elementos sin una clave API.</span>
              </span>
            </div>
            <button
              onClick={() => setIsSettingsModalOpen(true)}
              className="inline-flex items-center gap-1.5 h-7 px-2.5 text-xs font-medium border border-primary/30 hover:bg-primary/10 text-primary rounded-md transition-colors"
            >
              <Settings className="w-3 h-3" />
              Abrir configuración
            </button>
          </div>
        </div>
      )}

      {/* Body */}
      <div className="flex-1 flex min-h-0">
        <main className="flex-1 py-4 overflow-x-auto overflow-y-hidden">
          <Outlet />
        </main>

        {automationEnabled && (
          <aside className="w-96 flex-shrink-0 flex flex-col border-l border-border bg-card/30">
            <div className="flex-shrink-0 border-b border-border">
              <AgentPanel />
            </div>
            <div className="flex-1 min-h-0 overflow-hidden">
              <ChatPanel />
            </div>
          </aside>
        )}
      </div>

      {/* Modals */}
      <PRDInputModal isOpen={isPRDModalOpen} onClose={closePRDModal} />
      <SettingsModal isOpen={isSettingsModalOpen} onClose={() => setIsSettingsModalOpen(false)} />
      <PipelineModal isOpen={isPipelineModalOpen} onClose={() => setIsPipelineModalOpen(false)} />
      <TrendingNewsModal isOpen={isTrendingModalOpen} onClose={() => setIsTrendingModalOpen(false)} />

      {selectedStoryId && (
        <StoryDetail storyId={selectedStoryId} onClose={() => setSelectedStory(null)} />
      )}

      <WelcomeModal
        isOpen={isWelcomeOpen}
        onClose={() => setIsWelcomeOpen(false)}
        onOpenSettings={() => {
          setIsWelcomeOpen(false);
          setIsSettingsModalOpen(true);
        }}
      />

      {isAgentManagerOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-fade-in">
          <div className="surface shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-border">
              <h2 className="text-base font-semibold text-foreground">Gestor de agentes</h2>
              <button
                onClick={() => setIsAgentManagerOpen(false)}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="overflow-y-auto max-h-[calc(80vh-56px)]">
              <AgentManager />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
