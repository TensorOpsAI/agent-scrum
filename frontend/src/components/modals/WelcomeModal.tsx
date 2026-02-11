import { useState } from 'react';
import { Bot, Key, Layout, Rocket, ChevronRight, ChevronLeft, ExternalLink, Sparkles } from 'lucide-react';
import { clsx } from 'clsx';
import { settingsApi } from '../../api/client';

const ONBOARDING_KEY = 'agent_scrum_onboarding_done';

export function isOnboardingComplete(): boolean {
  return localStorage.getItem(ONBOARDING_KEY) === 'true';
}

export function markOnboardingComplete(): void {
  localStorage.setItem(ONBOARDING_KEY, 'true');
}

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
}

const steps = [
  {
    icon: Bot,
    title: 'Welcome to Agent Scrum',
    description:
      'Agent Scrum is an AI-powered project management tool where autonomous agents collaborate to break down, plan, and manage your work items.',
    details: [
      'Create boards for different workflows (Scrum, CISO, HR, etc.)',
      'AI agents automatically process and manage your items',
      'Watch agents collaborate in real-time via the chat panel',
    ],
  },
  {
    icon: Key,
    title: 'Set Up Your API Key',
    description:
      'To use live AI agents, you need a Gemini API key. Without it, the agents won\'t be able to process your items.',
    details: [
      'Go to Settings (gear icon in the top right)',
      'Paste your Gemini API key and click Save',
      'Or use Simulation Mode to try the app with mock responses',
    ],
    action: 'apiKey',
  },
  {
    icon: Layout,
    title: 'Create Your First Board',
    description:
      'Boards are workspaces tailored to specific workflows. Each board type comes with its own columns, agents, and automation rules.',
    details: [
      'Click "New Board" in the header to get started',
      'Choose a template: Scrum, CISO, HR, and more',
      'Each template has pre-configured agents and workflow stages',
    ],
  },
  {
    icon: Rocket,
    title: 'You\'re All Set!',
    description:
      'Submit work items and watch your AI agent team spring into action. Here are a few tips to get the most out of Agent Scrum:',
    details: [
      'Use the @ mention in chat to direct messages to specific agents',
      'Click on any agent card to see its role and current activity',
      'Open the Agent Manager to customize your team\'s composition',
    ],
  },
];

export function WelcomeModal({ isOpen, onClose, onOpenSettings }: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [apiKey, setApiKey] = useState('');
  const [apiKeySaved, setApiKeySaved] = useState(false);

  if (!isOpen) return null;

  const step = steps[currentStep];
  const isLastStep = currentStep === steps.length - 1;
  const Icon = step.icon;

  const handleNext = () => {
    if (isLastStep) {
      markOnboardingComplete();
      onClose();
    } else {
      setCurrentStep((s) => s + 1);
    }
  };

  const handleBack = () => {
    setCurrentStep((s) => Math.max(0, s - 1));
  };

  const handleSkip = () => {
    markOnboardingComplete();
    onClose();
  };

  const handleSaveApiKey = () => {
    if (!apiKey.trim()) return;
    settingsApi.saveApiKeyLocally(apiKey);
    setApiKeySaved(true);
    setApiKey('');
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70" />

      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Progress bar */}
        <div className="flex gap-1 px-6 pt-4">
          {steps.map((_, i) => (
            <div
              key={i}
              className={clsx(
                'h-1 flex-1 rounded-full transition-colors',
                i <= currentStep ? 'bg-blue-500' : 'bg-gray-700'
              )}
            />
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <Icon className="w-5 h-5 text-blue-400" />
            </div>
            <h2 className="text-xl font-bold text-white">{step.title}</h2>
          </div>

          <p className="text-gray-300 text-sm mb-4">{step.description}</p>

          <ul className="space-y-2 mb-6">
            {step.details.map((detail, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-400">
                <Sparkles className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                {detail}
              </li>
            ))}
          </ul>

          {/* API Key inline form on step 2 */}
          {step.action === 'apiKey' && (
            <div className="bg-gray-900 rounded-lg p-4 mb-2">
              {apiKeySaved ? (
                <div className="flex items-center gap-2 text-green-400 text-sm">
                  <Key className="w-4 h-4" />
                  API key saved! You can always change it in Settings later.
                </div>
              ) : (
                <>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Paste your Gemini API key..."
                      className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveApiKey(); }}
                    />
                    <button
                      onClick={handleSaveApiKey}
                      disabled={!apiKey.trim()}
                      className={clsx(
                        'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                        apiKey.trim()
                          ? 'bg-blue-600 hover:bg-blue-700 text-white'
                          : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                      )}
                    >
                      Save
                    </button>
                  </div>
                  <p className="text-xs text-gray-500">
                    Get your free key from{' '}
                    <a
                      href="https://aistudio.google.com/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:underline inline-flex items-center gap-1"
                    >
                      Google AI Studio <ExternalLink className="w-3 h-3" />
                    </a>
                    {' '}&middot;{' '}
                    <button
                      onClick={onOpenSettings}
                      className="text-blue-400 hover:underline"
                    >
                      or configure in Settings
                    </button>
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-700 bg-gray-850">
          <button
            onClick={handleSkip}
            className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
          >
            Skip walkthrough
          </button>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Back
              </button>
            )}
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-2 text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              {isLastStep ? 'Get Started' : 'Next'}
              {!isLastStep && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
