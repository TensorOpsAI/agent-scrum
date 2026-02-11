import { useState, useEffect } from 'react';
import { X, Key, Loader2, CheckCircle, AlertCircle, ExternalLink, Trash2, Play, Square, Pause, XCircle } from 'lucide-react';
import { clsx } from 'clsx';
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
  const [isSwarmActionLoading, setIsSwarmActionLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const activeConfig = usePipelineStore((s) => s.activeConfig);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    setIsLoading(true);
    try {
      const data = await settingsApi.get();
      // Merge with local API key state
      const localApiKey = settingsApi.getLocalApiKey();
      data.has_api_key = !!localApiKey;
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
      // Update has_api_key in local settings state
      if (settings) {
        setSettings({ ...settings, has_api_key: true, simulate_mode: false });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save API key' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearApiKey = () => {
    if (!confirm('Are you sure you want to clear the API key? The system will switch to simulation mode.')) {
      return;
    }

    setIsSaving(true);
    setMessage(null);

    try {
      const result = settingsApi.clearApiKeyLocally();
      setMessage({ type: 'success', text: result.message });
      if (settings) {
        setSettings({ ...settings, has_api_key: false, simulate_mode: true });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to clear API key' });
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
          text: result.simulate_mode ? 'Simulation mode enabled' : 'Simulation mode disabled',
        });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to toggle simulation mode' });
    }
  };

  const handleReset = async () => {
    if (!confirm('Are you sure you want to reset all data? All boards, stories, tasks, and comments will be deleted. Your settings will be preserved.')) {
      return;
    }

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
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to reset data' });
    } finally {
      setIsResetting(false);
    }
  };

  const handleSwarmAction = async (action: 'start' | 'stop' | 'pause' | 'resume') => {
    setIsSwarmActionLoading(true);
    setMessage(null);

    try {
      let result;
      switch (action) {
        case 'start':
          result = await settingsApi.startSwarm();
          break;
        case 'stop':
          result = await settingsApi.stopSwarm();
          break;
        case 'pause':
          result = await settingsApi.pauseSwarm();
          break;
        case 'resume':
          result = await settingsApi.resumeSwarm();
          break;
      }
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        loadSettings();
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Failed to ${action} swarm` });
    } finally {
      setIsSwarmActionLoading(false);
    }
  };

  if (!isOpen) return null;

  const automationEnabled = activeConfig?.agent_automation === true;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700 shrink-0">
          <div className="flex items-center gap-3">
            <Key className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-white">Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-6 overflow-y-auto flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : (
            <div className="space-y-5">
              {/* Message - show at top */}
              {message && (
                <div
                  className={clsx(
                    'p-3 rounded-lg text-sm',
                    message.type === 'success'
                      ? 'bg-green-900/50 border border-green-700 text-green-300'
                      : 'bg-red-900/50 border border-red-700 text-red-300'
                  )}
                >
                  {message.text}
                </div>
              )}

              {/* Status Bar - compact */}
              <div className="flex flex-wrap gap-3 text-sm">
                <div className={clsx(
                  'px-3 py-1.5 rounded-full flex items-center gap-1.5',
                  settings?.has_api_key ? 'bg-green-900/30 text-green-400' : 'bg-yellow-900/30 text-yellow-400'
                )}>
                  {settings?.has_api_key ? <CheckCircle className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
                  {settings?.has_api_key ? 'API Key Set' : 'No API Key'}
                </div>
                <div className={clsx(
                  'px-3 py-1.5 rounded-full',
                  settings?.simulate_mode ? 'bg-yellow-900/30 text-yellow-400' : 'bg-green-900/30 text-green-400'
                )}>
                  {settings?.simulate_mode ? 'Simulation Mode' : 'Live Mode'}
                </div>
                {automationEnabled && (
                  <div className={clsx(
                    'px-3 py-1.5 rounded-full',
                    settings?.swarm_status === 'running' ? 'bg-green-900/30 text-green-400' :
                    settings?.swarm_status === 'paused' ? 'bg-yellow-900/30 text-yellow-400' :
                    'bg-red-900/30 text-red-400'
                  )}>
                    Swarm: {settings?.swarm_status || 'stopped'}
                  </div>
                )}
              </div>

              {/* API Key Section */}
              <div className="bg-gray-900 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-300">Gemini API Key</h3>
                  {settings?.has_api_key && (
                    <button
                      onClick={handleClearApiKey}
                      disabled={isSaving}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-lg bg-orange-600 hover:bg-orange-700 text-white transition-colors disabled:opacity-50"
                    >
                      <XCircle className="w-4 h-4" />
                      Clear API Key
                    </button>
                  )}
                </div>
                <div className="flex gap-2">
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={settings?.has_api_key ? "Enter new key to replace..." : "Enter your Gemini API key..."}
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    onClick={handleSaveApiKey}
                    disabled={!apiKey.trim() || isSaving}
                    className={clsx(
                      'px-4 py-2 rounded-lg font-medium transition-colors text-sm',
                      apiKey.trim() && !isSaving
                        ? 'bg-blue-600 hover:bg-blue-700 text-white'
                        : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    )}
                  >
                    {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
                  </button>
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  Get your API key from{' '}
                  <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer"
                    className="text-blue-400 hover:underline inline-flex items-center gap-1">
                    Google AI Studio <ExternalLink className="w-3 h-3" />
                  </a>
                </p>
              </div>

              {/* Swarm Controls - only show when automation is enabled */}
              {automationEnabled && (
                <div className="bg-gray-900 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-3">Agent Swarm</h3>
                  <div className="flex gap-2">
                    {settings?.swarm_status === 'stopped' ? (
                      <button
                        onClick={() => handleSwarmAction('start')}
                        disabled={isSwarmActionLoading}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                      >
                        {isSwarmActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                        Start Swarm
                      </button>
                    ) : (
                      <>
                        {settings?.swarm_status === 'paused' ? (
                          <button
                            onClick={() => handleSwarmAction('resume')}
                            disabled={isSwarmActionLoading}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-green-600 hover:bg-green-700 text-white disabled:opacity-50"
                          >
                            {isSwarmActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            Resume
                          </button>
                        ) : (
                          <button
                            onClick={() => handleSwarmAction('pause')}
                            disabled={isSwarmActionLoading}
                            className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-yellow-600 hover:bg-yellow-700 text-white disabled:opacity-50"
                          >
                            {isSwarmActionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Pause className="w-4 h-4" />}
                            Pause
                          </button>
                        )}
                        <button
                          onClick={() => handleSwarmAction('stop')}
                          disabled={isSwarmActionLoading}
                          className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                        >
                          <Square className="w-4 h-4" />
                          Stop
                        </button>
                      </>
                    )}
                  </div>
                </div>
              )}

              {/* Simulation Mode - only show when automation is enabled */}
              {automationEnabled && (
                <div className="bg-gray-900 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-gray-300">Simulation Mode</h3>
                      <p className="text-xs text-gray-500 mt-0.5">Use mock responses instead of Gemini API</p>
                    </div>
                    <button
                      onClick={handleToggleSimulateMode}
                      className={clsx(
                        'relative inline-flex h-6 w-11 items-center rounded-full transition-colors',
                        settings?.simulate_mode ? 'bg-blue-600' : 'bg-gray-600'
                      )}
                    >
                      <span className={clsx(
                        'inline-block h-4 w-4 transform rounded-full bg-white transition-transform',
                        settings?.simulate_mode ? 'translate-x-6' : 'translate-x-1'
                      )} />
                    </button>
                  </div>
                </div>
              )}

              {/* Reset Data */}
              <div className="bg-red-900/20 border border-red-800/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-red-400">Reset All Data</h3>
                    <p className="text-xs text-gray-500 mt-0.5">Delete all boards and stories. Settings will be preserved.</p>
                  </div>
                  <button
                    onClick={handleReset}
                    disabled={isResetting}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg font-medium bg-red-600 hover:bg-red-700 text-white disabled:opacity-50"
                  >
                    {isResetting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    Reset
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-700 bg-gray-850 shrink-0">
          <p className="text-xs text-gray-500 text-center">
            API key is stored in your browser only and never sent to the server for storage.
          </p>
        </div>
      </div>
    </div>
  );
}
