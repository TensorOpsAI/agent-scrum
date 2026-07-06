import { useState, useEffect } from 'react';
import { X, Bot, Plus, Trash2 } from 'lucide-react';
import { clsx } from 'clsx';
import {
  agentManagementApi,
  type DynamicAgent,
  type AgentTemplate,
  type AgentTool,
  type AgentSkill,
  type CreateAgentRequest,
} from '../../api/client';

interface CreateAgentModalProps {
  templates: AgentTemplate[];
  tools: AgentTool[];
  onClose: () => void;
  onCreated: (agent: DynamicAgent) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  security: 'border-red-500/50 bg-red-500/10',
  code: 'border-blue-500/50 bg-blue-500/10',
  testing: 'border-green-500/50 bg-green-500/10',
  docs: 'border-yellow-500/50 bg-yellow-500/10',
  performance: 'border-purple-500/50 bg-purple-500/10',
  devops: 'border-orange-500/50 bg-orange-500/10',
  custom: 'border-pink-500/50 bg-pink-500/10',
};

export function CreateAgentModal({ templates, tools, onClose, onCreated }: CreateAgentModalProps) {
  const [step, setStep] = useState<'template' | 'customize'>('template');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    tools: [] as string[],
    skills: [] as AgentSkill[],
  });
  const [newSkill, setNewSkill] = useState({
    id: '',
    name: '',
    description: '',
    tags: '',
    examples: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Apply template defaults when selected
  useEffect(() => {
    if (selectedTemplate) {
      const template = templates.find(t => t.id === selectedTemplate);
      if (template) {
        setFormData(prev => ({
          ...prev,
          name: template.name,
          description: template.description,
          tools: template.default_tools,
          skills: template.skills,
        }));
      }
    }
  }, [selectedTemplate, templates]);

  const handleToolToggle = (toolId: string) => {
    setFormData(prev => ({
      ...prev,
      tools: prev.tools.includes(toolId)
        ? prev.tools.filter(t => t !== toolId)
        : [...prev.tools, toolId],
    }));
  };

  const handleAddSkill = () => {
    if (!newSkill.id || !newSkill.name) return;

    setFormData(prev => ({
      ...prev,
      skills: [...prev.skills, {
        id: newSkill.id,
        name: newSkill.name,
        description: newSkill.description,
        tags: newSkill.tags.split(',').map(t => t.trim()).filter(Boolean),
        examples: newSkill.examples.split('\n').map(e => e.trim()).filter(Boolean),
      }],
    }));
    setNewSkill({ id: '', name: '', description: '', tags: '', examples: '' });
  };

  const handleRemoveSkill = (skillId: string) => {
    setFormData(prev => ({
      ...prev,
      skills: prev.skills.filter(s => s.id !== skillId),
    }));
  };

  const handleSubmit = async () => {
    if (!formData.id || !formData.name) {
      setError('El ID y el nombre del agente son obligatorios');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const request: CreateAgentRequest = {
        id: formData.id,
        name: formData.name,
        description: formData.description || undefined,
        template: selectedTemplate || undefined,
        tools: formData.tools,
        skills: formData.skills,
      };

      const newAgent = await agentManagementApi.createAgent(request);
      onCreated(newAgent);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'No se pudo crear el agente';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Group tools by category
  const toolsByCategory = tools.reduce((acc, tool) => {
    if (!acc[tool.category]) {
      acc[tool.category] = [];
    }
    acc[tool.category].push(tool);
    return acc;
  }, {} as Record<string, AgentTool[]>);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <h2 className="text-lg font-semibold text-gray-900">Crear nuevo agente</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-50 text-red-600 border border-red-200 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}

          {step === 'template' ? (
            <>
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-3">
                  Elige una plantilla (opcional)
                </h3>
                <div className="grid gap-2">
                  <button
                    onClick={() => {
                      setSelectedTemplate(null);
                      setStep('customize');
                    }}
                    className={clsx(
                      'text-left p-3 rounded-lg border transition-colors',
                      'border-gray-200 hover:border-primary/50 hover:bg-gray-50'
                    )}
                  >
                    <div className="font-medium text-gray-900">Agente personalizado</div>
                    <p className="text-xs text-gray-500 mt-1">
                      Empieza desde cero con tu propia configuración
                    </p>
                  </button>
                  {templates.map((template) => (
                    <button
                      key={template.id}
                      onClick={() => {
                        setSelectedTemplate(template.id);
                        setStep('customize');
                      }}
                      className={clsx(
                        'text-left p-3 rounded-lg border transition-colors',
                        selectedTemplate === template.id
                          ? 'border-primary bg-primary/10'
                          : 'border-gray-200 hover:border-primary/50 hover:bg-gray-50'
                      )}
                    >
                      <div className="font-medium text-gray-900">{template.name}</div>
                      <p className="text-xs text-gray-500 mt-1">{template.description}</p>
                      <div className="flex gap-1 mt-2">
                        {template.default_tools.slice(0, 3).map((tool) => (
                          <span
                            key={tool}
                            className="px-1.5 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                          >
                            {tool.replace('_', ' ')}
                          </span>
                        ))}
                        {template.default_tools.length > 3 && (
                          <span className="text-xs text-gray-400">
                            +{template.default_tools.length - 3} más
                          </span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <>
              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-gray-700">Información básica</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">ID del agente</label>
                    <input
                      type="text"
                      value={formData.id}
                      onChange={(e) => setFormData(prev => ({ ...prev, id: e.target.value }))}
                      placeholder="ej., security_analyst_1"
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Nombre</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="ej., Analista de Seguridad"
                      className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Descripción</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="¿Qué hace este agente?"
                    rows={2}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:border-primary"
                  />
                </div>
              </div>

              {/* Tools */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-700">
                  Herramientas ({formData.tools.length} seleccionadas)
                </h3>
                {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
                  <div key={category} className={clsx('p-3 rounded-lg border', CATEGORY_COLORS[category] || CATEGORY_COLORS.custom)}>
                    <div className="text-xs font-medium text-gray-600 mb-2 capitalize">{category}</div>
                    <div className="flex flex-wrap gap-2">
                      {categoryTools.map((tool) => (
                        <button
                          key={tool.id}
                          onClick={() => handleToolToggle(tool.id)}
                          className={clsx(
                            'px-2 py-1 text-xs rounded border transition-colors',
                            formData.tools.includes(tool.id)
                              ? 'border-primary bg-primary/10 text-primary'
                              : 'border-gray-300 bg-white text-gray-500 hover:border-gray-400'
                          )}
                          title={tool.description}
                        >
                          {tool.name}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Skills */}
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-gray-700">
                  Habilidades ({formData.skills.length})
                </h3>
                {formData.skills.map((skill) => (
                  <div
                    key={skill.id}
                    className="flex items-start justify-between p-2 bg-gray-50 rounded"
                  >
                    <div>
                      <div className="text-sm text-gray-900">{skill.name}</div>
                      <div className="text-xs text-gray-500">{skill.description}</div>
                    </div>
                    <button
                      onClick={() => handleRemoveSkill(skill.id)}
                      className="p-1 text-red-500 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))}

                {/* Add new skill */}
                <div className="p-3 bg-gray-50 rounded border border-gray-200">
                  <div className="text-xs text-gray-500 mb-2">Añadir habilidad personalizada</div>
                  <div className="grid grid-cols-2 gap-2 mb-2">
                    <input
                      type="text"
                      value={newSkill.id}
                      onChange={(e) => setNewSkill(prev => ({ ...prev, id: e.target.value }))}
                      placeholder="ID de habilidad"
                      className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-900"
                    />
                    <input
                      type="text"
                      value={newSkill.name}
                      onChange={(e) => setNewSkill(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Nombre de la habilidad"
                      className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-900"
                    />
                  </div>
                  <input
                    type="text"
                    value={newSkill.description}
                    onChange={(e) => setNewSkill(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Descripción"
                    className="w-full px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-900 mb-2"
                  />
                  <button
                    onClick={handleAddSkill}
                    disabled={!newSkill.id || !newSkill.name}
                    className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 text-gray-900 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Plus className="w-3 h-3" />
                    Añadir habilidad
                  </button>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-200">
          {step === 'customize' ? (
            <>
              <button
                onClick={() => setStep('template')}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Atrás
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || !formData.id || !formData.name}
                className="px-4 py-2 text-sm bg-primary hover:bg-primary/90 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Creando...' : 'Crear agente'}
              </button>
            </>
          ) : (
            <div className="ml-auto">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm text-gray-500 hover:text-gray-900 transition-colors"
              >
                Cancelar
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
