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
    title: 'Bienvenido a la redacción con IA',
    description:
      'Un equipo de agentes de IA colabora para investigar, redactar, editar y publicar artículos de forma autónoma.',
    details: [
      'El tablero organiza el flujo editorial de principio a fin',
      'Los agentes de IA procesan y gestionan los artículos automáticamente',
      'Observa a los agentes colaborar en tiempo real en el panel de chat',
    ],
  },
  {
    icon: Key,
    title: 'Configura tu clave API',
    description:
      'Para usar agentes de IA en directo, necesitas una clave API. Sin ella, los agentes no podrán procesar tus artículos.',
    details: [
      'Ve a Configuración (icono de engranaje arriba a la derecha)',
      'Pega tu clave API y haz clic en Guardar',
      'O usa el Modo Simulación para probar la app con respuestas de ejemplo',
    ],
    action: 'apiKey',
  },
  {
    icon: Layout,
    title: 'Crea tu primer tablero',
    description:
      'El tablero editorial trae sus propias columnas, agentes y reglas de automatización ya configuradas.',
    details: [
      'Haz clic en "Nuevo tablero" en la cabecera para empezar',
      'Elige la plantilla de Redacción',
      'Incluye agentes preconfigurados para cada etapa del flujo editorial',
    ],
  },
  {
    icon: Rocket,
    title: '¡Todo listo!',
    description:
      'Envía un brief de noticias y observa a tu equipo de agentes de IA ponerse en marcha. Algunos consejos para sacarle el máximo partido:',
    details: [
      'Usa @ en el chat para dirigir mensajes a agentes concretos',
      'Haz clic en cualquier tarjeta de agente para ver su rol y actividad actual',
      'Abre el Gestor de agentes para personalizar la composición de tu equipo',
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

      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden">
        {/* Progress bar */}
        <div className="flex gap-1 px-6 pt-4">
          {steps.map((_, i) => (
            <div
              key={i}
              className={clsx(
                'h-1 flex-1 rounded-full transition-colors',
                i <= currentStep ? 'bg-primary' : 'bg-gray-200'
              )}
            />
          ))}
        </div>

        {/* Content */}
        <div className="px-6 py-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Icon className="w-5 h-5 text-primary" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">{step.title}</h2>
          </div>

          <p className="text-gray-600 text-sm mb-4">{step.description}</p>

          <ul className="space-y-2 mb-6">
            {step.details.map((detail, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-500">
                <Sparkles className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                {detail}
              </li>
            ))}
          </ul>

          {/* API Key inline form on step 2 */}
          {step.action === 'apiKey' && (
            <div className="bg-gray-50 rounded-lg p-4 mb-2">
              {apiKeySaved ? (
                <div className="flex items-center gap-2 text-emerald-600 text-sm">
                  <Key className="w-4 h-4" />
                  ¡Clave API guardada! Puedes cambiarla más tarde en Configuración.
                </div>
              ) : (
                <>
                  <div className="flex gap-2 mb-2">
                    <input
                      type="password"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="Paste your API key..."
                      className="flex-1 px-3 py-2 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                      onKeyDown={(e) => { if (e.key === 'Enter') handleSaveApiKey(); }}
                    />
                    <button
                      onClick={handleSaveApiKey}
                      disabled={!apiKey.trim()}
                      className={clsx(
                        'px-4 py-2 rounded-lg font-medium text-sm transition-colors',
                        apiKey.trim()
                          ? 'bg-primary hover:bg-primary/90 text-white'
                          : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      )}
                    >
                      Guardar
                    </button>
                  </div>
                  <p className="text-xs text-gray-500">
                    Consigue tu clave gratuita en{' '}
                    <a
                      href="https://aistudio.google.com/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline inline-flex items-center gap-1"
                    >
                      Google AI Studio <ExternalLink className="w-3 h-3" />
                    </a>
                    {' '}&middot;{' '}
                    <button
                      onClick={onOpenSettings}
                      className="text-primary hover:underline"
                    >
                      o configúrala en Configuración
                    </button>
                  </p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200 bg-gray-50">
          <button
            onClick={handleSkip}
            className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
          >
            Saltar introducción
          </button>

          <div className="flex items-center gap-2">
            {currentStep > 0 && (
              <button
                onClick={handleBack}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
                Atrás
              </button>
            )}
            <button
              onClick={handleNext}
              className="flex items-center gap-1 px-4 py-2 text-sm font-medium bg-primary hover:bg-primary/90 text-white rounded-lg transition-colors"
            >
              {isLastStep ? 'Empezar' : 'Siguiente'}
              {!isLastStep && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
