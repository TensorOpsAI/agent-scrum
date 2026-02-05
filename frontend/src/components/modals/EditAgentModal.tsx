import { useState } from 'react';
import { X, Bot, Plus, Trash2 } from 'lucide-react';
import { clsx } from 'clsx';
import {
  agentManagementApi,
  type DynamicAgent,
  type AgentTool,
  type UpdateAgentRequest,
} from '../../api/client';

interface EditAgentModalProps {
  agent: DynamicAgent;
  tools: AgentTool[];
  onClose: () => void;
  onUpdated: (agent: DynamicAgent) => void;
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

export function EditAgentModal({ agent, tools, onClose, onUpdated }: EditAgentModalProps) {
  const [formData, setFormData] = useState({
    name: agent.name,
    description: agent.description || '',
    tools: [...agent.tools],
    skills: [...agent.skills],
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

  const handleToolToggle = (toolId: string) => {
    setFormData((prev) => ({
      ...prev,
      tools: prev.tools.includes(toolId)
        ? prev.tools.filter((t) => t !== toolId)
        : [...prev.tools, toolId],
    }));
  };

  const handleAddSkill = () => {
    if (!newSkill.id || !newSkill.name) return;

    setFormData((prev) => ({
      ...prev,
      skills: [
        ...prev.skills,
        {
          id: newSkill.id,
          name: newSkill.name,
          description: newSkill.description,
          tags: newSkill.tags
            .split(',')
            .map((t) => t.trim())
            .filter(Boolean),
          examples: newSkill.examples
            .split('\n')
            .map((e) => e.trim())
            .filter(Boolean),
        },
      ],
    }));
    setNewSkill({ id: '', name: '', description: '', tags: '', examples: '' });
  };

  const handleRemoveSkill = (skillId: string) => {
    setFormData((prev) => ({
      ...prev,
      skills: prev.skills.filter((s) => s.id !== skillId),
    }));
  };

  const handleSubmit = async () => {
    if (!formData.name) {
      setError('Agent name is required');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const request: UpdateAgentRequest = {
        name: formData.name,
        description: formData.description || undefined,
        tools: formData.tools,
        skills: formData.skills,
      };

      const updatedAgent = await agentManagementApi.updateAgent(agent.id, request);
      onUpdated(updatedAgent);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update agent';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Group tools by category
  const toolsByCategory = tools.reduce(
    (acc, tool) => {
      if (!acc[tool.category]) {
        acc[tool.category] = [];
      }
      acc[tool.category].push(tool);
      return acc;
    },
    {} as Record<string, AgentTool[]>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-white">Edit Agent: {agent.id}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="bg-red-500/20 text-red-400 px-4 py-2 rounded-lg text-sm">{error}</div>
          )}

          {/* Basic Info */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-gray-300">Basic Information</h3>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                placeholder="e.g., Security Analyst"
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="What does this agent do?"
                rows={2}
                className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Tools */}
          <div className="space-y-3">
            <h3 className="text-sm font-medium text-gray-300">
              Tools ({formData.tools.length} selected)
            </h3>
            {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
              <div
                key={category}
                className={clsx('p-3 rounded-lg border', CATEGORY_COLORS[category] || CATEGORY_COLORS.custom)}
              >
                <div className="text-xs font-medium text-gray-300 mb-2 capitalize">{category}</div>
                <div className="flex flex-wrap gap-2">
                  {categoryTools.map((tool) => (
                    <button
                      key={tool.id}
                      onClick={() => handleToolToggle(tool.id)}
                      className={clsx(
                        'px-2 py-1 text-xs rounded border transition-colors',
                        formData.tools.includes(tool.id)
                          ? 'border-blue-500 bg-blue-500/20 text-blue-300'
                          : 'border-gray-600 bg-gray-800 text-gray-400 hover:border-gray-500'
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
            <h3 className="text-sm font-medium text-gray-300">Skills ({formData.skills.length})</h3>
            {formData.skills.map((skill) => (
              <div
                key={skill.id}
                className="flex items-start justify-between p-2 bg-gray-800 rounded"
              >
                <div>
                  <div className="text-sm text-white">{skill.name}</div>
                  <div className="text-xs text-gray-400">{skill.description}</div>
                </div>
                <button
                  onClick={() => handleRemoveSkill(skill.id)}
                  className="p-1 text-red-400 hover:bg-red-500/20 rounded"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))}

            {/* Add new skill */}
            <div className="p-3 bg-gray-800/50 rounded border border-gray-700">
              <div className="text-xs text-gray-400 mb-2">Add Custom Skill</div>
              <div className="grid grid-cols-2 gap-2 mb-2">
                <input
                  type="text"
                  value={newSkill.id}
                  onChange={(e) => setNewSkill((prev) => ({ ...prev, id: e.target.value }))}
                  placeholder="Skill ID"
                  className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                />
                <input
                  type="text"
                  value={newSkill.name}
                  onChange={(e) => setNewSkill((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="Skill Name"
                  className="px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white"
                />
              </div>
              <input
                type="text"
                value={newSkill.description}
                onChange={(e) => setNewSkill((prev) => ({ ...prev, description: e.target.value }))}
                placeholder="Description"
                className="w-full px-2 py-1 bg-gray-800 border border-gray-700 rounded text-xs text-white mb-2"
              />
              <button
                onClick={handleAddSkill}
                disabled={!newSkill.id || !newSkill.name}
                className="flex items-center gap-1 px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Plus className="w-3 h-3" />
                Add Skill
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !formData.name}
            className="px-4 py-2 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
