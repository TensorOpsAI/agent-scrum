import { useState, useEffect } from 'react';
import { X, Key, Loader2, CheckCircle2, AlertCircle, ExternalLink, Trash2, XCircle } from 'lucide-react';
import { cn } from '../../lib/utils';
import { settingsApi, type AppSettings } from '../../api/client';
import { usePipelineStore } from '../../store/pipelineStore';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [apiKey, setApiKey] = useState('');
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const activeConfig = usePipelineStore((s) => s.activeConfig);

  useEffect(() => {
    if (isOpen) loadSettings();
  }, [isOpen, activeConfig?.id]);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const data = await settingsApi.get();
      data.has_api_key = !!settingsApi.getLocalApiKey();
      setSettings(data);
    } catch (error) {
      console.error('Error loading settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveApiKey = () => {
    if (!apiKey.trim()) return;
    setIsSaving(true);
    setMessage(null);
    try {
      const result = settingsApi.saveApiKeyLocally(apiKey);
      setMessage({ type: 'success', text: result.message });
      setApiKey('');
      if (settings) setSettings({ ...settings, has_api_key: true, simulate_mode: false });
    } catch {
      setMessage({ type: 'error', text: 'No se pudo guardar la clave API' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearApiKey = () => {
    if (!confirm('¿Borrar la clave API? El sistema pasará al modo simulación.')) return;
    setIsSaving(true);
    setMessage(null);
    try {
      const result = settingsApi.clearApiKeyLocally();
      setMessage({ type: 'success', text: result.message });
      if (settings) setSettings({ ...settings, has_api_key: false, simulate_mode: true });
    } catch {
      setMessage({ type: 'error', text: 'No se pudo borrar la clave API' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleToggleSimulateMode = async () => {
    if (!settings) return;
    try {
      const result = await settingsApi.setSimulateMode(!settings.simulate_mode);
      if (result.success) {
        setSettings({ ...settings, simulate_mode: result.simulate_mode });
        setMessage({
          type: 'success',
          text: result.simulate_mode ? 'Modo simulación activado' : 'Modo simulación desactivado',
        });
      }
    } catch {
      setMessage({ type: 'error', text: 'No se pudo cambiar el modo simulación' });
    }
  };

  const handleReset = async () => {
    if (!confirm('¿Restablecer todos los datos? Se eliminarán todos los tableros, artículos, tareas y comentarios. La configuración se conservará.')) return;
    setIsResetting(true);
    setMessage(null);
    try {
      const result = await settingsApi.resetAllData();
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        setTimeout(() => window.location.reload(), 500);
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch {
      setMessage({ type: 'error', text: 'No se pudieron restablecer los datos' });
    } finally {
      setIsResetting(false);
    }
  };

  if (!isOpen) return null;

  const automationEnabled = activeConfig?.agent_automation === true;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative surface shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-border shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Key className="w-4 h-4 text-primary flex-shrink-0" />
            <h2 className="text-sm font-medium text-foreground">Configuración</h2>
            {activeConfig && (
              <>
                <span className="text-muted-foreground/40">·</span>
                <span className="text-xs text-muted-foreground truncate">
                  {activeConfig.name}
                </span>
              </>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-5 h-5 animate-spin text-primary" />
            </div>
          ) : (
            <div className="space-y-4">
              {message && (
                <div
                  className={cn(
                    'flex items-start gap-2 px-3 py-2 rounded-md text-xs animate-fade-in',
                    message.type === 'success'
                      ? 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-200'
                      : 'bg-destructive/10 border border-destructive/30 text-destructive-foreground'
                  )}
                >
                  {message.type === 'success' ? <CheckCircle2 className="w-3.5 h-3.5 mt-0.5 text-emerald-400" /> : <AlertCircle className="w-3.5 h-3.5 mt-0.5 text-destructive" />}
                  <span>{message.text}</span>
                </div>
              )}

              {/* Status pills */}
              <div className="flex flex-wrap gap-1.5">
                <span className={cn(
                  'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border',
                  settings?.has_api_key
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                )}>
                  <span className={cn('status-dot', settings?.has_api_key ? 'bg-emerald-400' : 'bg-amber-400')} />
                  {settings?.has_api_key ? 'Clave API configurada' : 'Sin clave API'}
                </span>
                <span className={cn(
                  'inline-flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border',
                  settings?.simulate_mode
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                )}>
                  <span className={cn('status-dot', settings?.simulate_mode ? 'bg-amber-400' : 'bg-emerald-400')} />
                  {settings?.simulate_mode ? 'Modo simulación' : 'Modo en vivo'}
                </span>
              </div>

              {/* API Key */}
              <div className="surface-muted p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">Clave API</h3>
                  {settings?.has_api_key && (
                    <button
                      onClick={handleClearApiKey}
                      disabled={isSaving}
                      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border border-border hover:border-destructive/50 hover:bg-destructive/10 hover:text-destructive-foreground text-muted-foreground transition-colors disabled:opacity-50"
                    >
                      <XCircle className="w-3 h-3" />
                      Borrar
                    </button>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={settings?.has_api_key ? 'Introduce una nueva clave para sustituirla…' : 'Pega tu clave API'}
                    className="flex-1 h-9 px-3 bg-input border border-border rounded-md text-foreground placeholder-muted-foreground/60 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                  <button
                    onClick={handleSaveApiKey}
                    disabled={!apiKey.trim() || isSaving}
                    className="btn-primary"
                  >
                    {isSaving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Guardar'}
                  </button>
                </div>
                <p className="mt-2 text-[11px] text-muted-foreground">
                  Consigue tu clave API en{' '}
                  <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer"
                    className="text-primary hover:underline inline-flex items-center gap-0.5">
                    Google AI Studio<ExternalLink className="w-2.5 h-2.5" />
                  </a>
                </p>
              </div>

              {/* Simulation Mode */}
              {automationEnabled && (
                <div className="surface-muted p-4 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="text-sm font-medium text-foreground">Modo simulación</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">Usa respuestas simuladas en lugar de llamadas de IA en vivo</p>
                  </div>
                  <button
                    onClick={handleToggleSimulateMode}
                    role="switch"
                    aria-checked={settings?.simulate_mode}
                    className={cn(
                      'relative inline-flex h-5 w-9 items-center rounded-full transition-colors flex-shrink-0',
                      settings?.simulate_mode ? 'bg-primary' : 'bg-secondary border border-border'
                    )}
                  >
                    <span className={cn(
                      'inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform',
                      settings?.simulate_mode ? 'translate-x-5' : 'translate-x-0.5'
                    )} />
                  </button>
                </div>
              )}

              {/* Danger zone */}
              <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="text-sm font-medium text-destructive-foreground">Restablecer todos los datos</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">Elimina todos los tableros y artículos. La configuración se conserva.</p>
                </div>
                <button
                  onClick={handleReset}
                  disabled={isResetting}
                  className="inline-flex items-center gap-1.5 h-8 px-3 rounded-md text-sm font-medium bg-destructive hover:bg-destructive/90 text-destructive-foreground disabled:opacity-50 transition-colors flex-shrink-0"
                >
                  {isResetting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
                  Restablecer
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-2.5 border-t border-border bg-card/40 shrink-0">
          <p className="text-[10px] text-muted-foreground text-center">
            🔒 La clave API se guarda solo en esta pestaña del navegador y se envía con tus solicitudes para que el backend pueda procesarlas. Nunca se almacena en el servidor.
          </p>
        </div>
      </div>
    </div>
  );
}
