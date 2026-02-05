import { useState, useEffect, useCallback } from 'react';
import { Bot, Plus, Settings2, Trash2, Power, PowerOff, ChevronDown, ChevronUp, Wrench, Pencil, Lock } from 'lucide-react';
import { clsx } from 'clsx';
import {
  agentManagementApi,
  type DynamicAgent,
  type AgentTemplate,
  type AgentTool,
  type CreateToolRequest,
} from '../../api/client';
import { useStoryStore } from '../../store/storyStore';
import { CreateAgentModal } from '../modals/CreateAgentModal';
import { EditAgentModal } from '../modals/EditAgentModal';

const CATEGORY_COLORS: Record<string, string> = {
  security: 'bg-red-500/20 text-red-400',
  code: 'bg-blue-500/20 text-blue-400',
  testing: 'bg-green-500/20 text-green-400',
  docs: 'bg-yellow-500/20 text-yellow-400',
  performance: 'bg-purple-500/20 text-purple-400',
  devops: 'bg-orange-500/20 text-orange-400',
  custom: 'bg-pink-500/20 text-pink-400',
};

interface AgentCardProps {
  agent: DynamicAgent;
  onToggleActive: (agentId: string, active: boolean) => void;
  onDelete: (agentId: string) => void;
  onEdit: (agent: DynamicAgent) => void;
}

function AgentCard({ agent, onToggleActive, onDelete, onEdit }: AgentCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={clsx(
      'bg-gray-800 rounded-lg border',
      agent.is_active ? 'border-gray-700' : 'border-gray-700/50 opacity-60'
    )}>
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2">
            <Bot className={clsx(
              'w-5 h-5',
              agent.is_active ? 'text-blue-400' : 'text-gray-500'
            )} />
            <h3 className="font-medium text-white">{agent.name}</h3>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onEdit(agent)}
              className="p-1.5 rounded text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 transition-colors"
              title="Edit"
            >
              <Pencil className="w-4 h-4" />
            </button>
            <button
              onClick={() => onToggleActive(agent.id, !agent.is_active)}
              className={clsx(
                'p-1.5 rounded transition-colors',
                agent.is_active
                  ? 'text-green-400 hover:bg-green-500/20'
                  : 'text-gray-500 hover:bg-gray-700'
              )}
              title={agent.is_active ? 'Deactivate' : 'Activate'}
            >
              {agent.is_active ? <Power className="w-4 h-4" /> : <PowerOff className="w-4 h-4" />}
            </button>
            <button
              onClick={() => onDelete(agent.id)}
              className="p-1.5 rounded text-red-400 hover:bg-red-500/20 transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-sm text-gray-400 mb-3">{agent.description || 'No description'}</p>

        {agent.template && (
          <span className="inline-block px-2 py-0.5 text-xs bg-purple-500/20 text-purple-400 rounded mb-2">
            Template: {agent.template}
          </span>
        )}

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {agent.tools.length} tools, {agent.skills.length} skills
        </button>

        {expanded && (
          <div className="mt-3 pt-3 border-t border-gray-700 space-y-3">
            {agent.tools.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-gray-400 mb-1">Tools</h4>
                <div className="flex flex-wrap gap-1">
                  {agent.tools.map((toolId) => (
                    <span
                      key={toolId}
                      className="px-2 py-0.5 text-xs bg-gray-700 text-gray-300 rounded"
                    >
                      {toolId.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {agent.skills.length > 0 && (
              <div>
                <h4 className="text-xs font-medium text-gray-400 mb-1">Skills</h4>
                <div className="space-y-1">
                  {agent.skills.map((skill) => (
                    <div key={skill.id} className="text-xs">
                      <span className="text-gray-300">{skill.name}</span>
                      <span className="text-gray-500 ml-1">- {skill.description}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

interface ToolCardProps {
  tool: AgentTool;
  onEdit?: (tool: AgentTool) => void;
  onDelete?: (toolId: string) => void;
}

function ToolCard({ tool, onEdit, onDelete }: ToolCardProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className={clsx(
      'bg-gray-800 rounded-lg border p-3',
      tool.is_builtin ? 'border-gray-700/50' : 'border-gray-700'
    )}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Wrench className={clsx(
            'w-4 h-4',
            tool.is_builtin ? 'text-gray-500' : 'text-blue-400'
          )} />
          <span className="text-sm text-white">{tool.name}</span>
          {tool.is_builtin && (
            <span title="Built-in tool">
              <Lock className="w-3 h-3 text-gray-500" />
            </span>
          )}
        </div>
        <div className="flex items-center gap-1">
          <span className={clsx(
            'px-1.5 py-0.5 text-xs rounded',
            CATEGORY_COLORS[tool.category] || CATEGORY_COLORS.custom
          )}>
            {tool.category}
          </span>
          {!tool.is_builtin && (
            <>
              {onEdit && (
                <button
                  onClick={() => onEdit(tool)}
                  className="p-1 rounded text-gray-400 hover:text-blue-400 hover:bg-blue-500/20 transition-colors"
                  title="Edit"
                >
                  <Pencil className="w-3 h-3" />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => onDelete(tool.id)}
                  className="p-1 rounded text-red-400 hover:bg-red-500/20 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      <p className="text-xs text-gray-400 mt-1">{tool.description}</p>

      {tool.capabilities.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-300 transition-colors mt-2"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          {tool.capabilities.length} capabilities
        </button>
      )}

      {expanded && tool.capabilities.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {tool.capabilities.map((cap) => (
            <span
              key={cap}
              className="px-1.5 py-0.5 text-xs bg-gray-700/50 text-gray-400 rounded"
            >
              {cap}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

interface CreateToolFormProps {
  categories: string[];
  onSubmit: (tool: CreateToolRequest) => void;
  onCancel: () => void;
}

function CreateToolForm({ categories, onSubmit, onCancel }: CreateToolFormProps) {
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    description: '',
    category: categories[0] || 'custom',
    capabilities: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = () => {
    if (!formData.id || !formData.name) {
      setError('Tool ID and name are required');
      return;
    }
    if (!/^[a-z][a-z0-9_]*$/.test(formData.id)) {
      setError('Tool ID must start with a letter and contain only lowercase letters, numbers, and underscores');
      return;
    }

    onSubmit({
      id: formData.id,
      name: formData.name,
      description: formData.description || undefined,
      category: formData.category,
      capabilities: formData.capabilities
        .split(',')
        .map((c) => c.trim())
        .filter(Boolean),
    });
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 space-y-3">
      <h4 className="text-sm font-medium text-white">Create Custom Tool</h4>

      {error && (
        <div className="bg-red-500/20 text-red-400 px-3 py-1.5 rounded text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Tool ID</label>
          <input
            type="text"
            value={formData.id}
            onChange={(e) => setFormData((prev) => ({ ...prev, id: e.target.value }))}
            placeholder="e.g., my_custom_tool"
            className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
            placeholder="e.g., My Custom Tool"
            className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs text-gray-400 mb-1">Description</label>
        <input
          type="text"
          value={formData.description}
          onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
          placeholder="What does this tool do?"
          className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Category</label>
          <select
            value={formData.category}
            onChange={(e) => setFormData((prev) => ({ ...prev, category: e.target.value }))}
            className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
            <option value="custom">custom</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Capabilities (comma-separated)</label>
          <input
            type="text"
            value={formData.capabilities}
            onChange={(e) => setFormData((prev) => ({ ...prev, capabilities: e.target.value }))}
            placeholder="e.g., analyze, report, fix"
            className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-2">
        <button
          onClick={onCancel}
          className="px-3 py-1.5 text-sm text-gray-400 hover:text-white transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white rounded transition-colors"
        >
          Create Tool
        </button>
      </div>
    </div>
  );
}

export function AgentManager() {
  const { fetchAgents: refreshStoreAgents } = useStoryStore();
  const [agents, setAgents] = useState<DynamicAgent[]>([]);
  const [templates, setTemplates] = useState<AgentTemplate[]>([]);
  const [tools, setTools] = useState<AgentTool[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateTool, setShowCreateTool] = useState(false);
  const [editingAgent, setEditingAgent] = useState<DynamicAgent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'agents' | 'tools'>('agents');

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const [agentsData, templatesData, toolsData, categoriesData] = await Promise.all([
        agentManagementApi.listAgents(),
        agentManagementApi.getTemplates(),
        agentManagementApi.getTools(),
        agentManagementApi.getToolCategories(),
      ]);
      setAgents(agentsData);
      setTemplates(templatesData);
      setTools(toolsData);
      setCategories(categoriesData);
    } catch (err) {
      console.error('Failed to load agent data:', err);
      setError('Failed to load agent data');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleToggleActive = async (agentId: string, active: boolean) => {
    try {
      await agentManagementApi.toggleActivation(agentId, active);
      setAgents((prev) =>
        prev.map((a) => (a.id === agentId ? { ...a, is_active: active } : a))
      );
      // Refresh the store's agent list so AgentPanel updates
      refreshStoreAgents();
    } catch (err) {
      console.error('Failed to toggle agent activation:', err);
    }
  };

  const handleDeleteAgent = async (agentId: string) => {
    if (!confirm(`Delete agent "${agentId}"? This cannot be undone.`)) return;

    try {
      await agentManagementApi.deleteAgent(agentId);
      setAgents((prev) => prev.filter((a) => a.id !== agentId));
      // Refresh the store's agent list so AgentPanel updates
      refreshStoreAgents();
    } catch (err) {
      console.error('Failed to delete agent:', err);
    }
  };

  const handleAgentCreated = (newAgent: DynamicAgent) => {
    setAgents((prev) => [newAgent, ...prev]);
    setShowCreateModal(false);
    // Refresh the store's agent list so AgentPanel updates
    refreshStoreAgents();
  };

  const handleAgentUpdated = (updatedAgent: DynamicAgent) => {
    setAgents((prev) =>
      prev.map((a) => (a.id === updatedAgent.id ? updatedAgent : a))
    );
    setEditingAgent(null);
    // Refresh the store's agent list so AgentPanel updates
    refreshStoreAgents();
  };

  const handleCreateTool = async (request: CreateToolRequest) => {
    try {
      const newTool = await agentManagementApi.createTool(request);
      setTools((prev) => [...prev, newTool]);
      setShowCreateTool(false);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create tool';
      setError(errorMessage);
    }
  };

  const handleDeleteTool = async (toolId: string) => {
    if (!confirm(`Delete tool "${toolId}"? This cannot be undone.`)) return;

    try {
      await agentManagementApi.deleteTool(toolId);
      setTools((prev) => prev.filter((t) => t.id !== toolId));
    } catch (err) {
      console.error('Failed to delete tool:', err);
    }
  };

  const builtinTools = tools.filter((t) => t.is_builtin);
  const customTools = tools.filter((t) => !t.is_builtin);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Settings2 className="w-5 h-5 text-blue-500" />
          <h2 className="font-semibold text-white">Agent Manager</h2>
        </div>
        <div className="flex items-center gap-2">
          {activeTab === 'agents' ? (
            <button
              onClick={() => setShowCreateModal(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Agent
            </button>
          ) : (
            <button
              onClick={() => setShowCreateTool(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Tool
            </button>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-700">
        <button
          onClick={() => setActiveTab('agents')}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
            activeTab === 'agents'
              ? 'text-blue-400 border-blue-400'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          )}
        >
          <Bot className="w-4 h-4 inline-block mr-1.5" />
          Agents ({agents.length})
        </button>
        <button
          onClick={() => setActiveTab('tools')}
          className={clsx(
            'px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px',
            activeTab === 'tools'
              ? 'text-blue-400 border-blue-400'
              : 'text-gray-400 border-transparent hover:text-gray-300'
          )}
        >
          <Wrench className="w-4 h-4 inline-block mr-1.5" />
          Tools ({tools.length})
        </button>
      </div>

      {error && (
        <div className="bg-red-500/20 text-red-400 px-4 py-2 rounded-lg text-sm">
          {error}
        </div>
      )}

      {activeTab === 'agents' ? (
        <div className="space-y-4">
          {/* Dynamic Agents */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Dynamic Agents ({agents.length})
            </h3>
            {agents.length === 0 ? (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <Bot className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">No dynamic agents yet</p>
                <p className="text-gray-500 text-xs">Click "Add Agent" to create one</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {agents.map((agent) => (
                  <AgentCard
                    key={agent.id}
                    agent={agent}
                    onToggleActive={handleToggleActive}
                    onDelete={handleDeleteAgent}
                    onEdit={setEditingAgent}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Templates */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Available Templates ({templates.length})
            </h3>
            <div className="grid gap-2">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white">{template.name}</span>
                    <span className="text-xs text-gray-500">
                      {template.default_tools.length} tools
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{template.description}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Create Tool Form */}
          {showCreateTool && (
            <CreateToolForm
              categories={categories}
              onSubmit={handleCreateTool}
              onCancel={() => setShowCreateTool(false)}
            />
          )}

          {/* Custom Tools */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Custom Tools ({customTools.length})
            </h3>
            {customTools.length === 0 ? (
              <div className="bg-gray-800 rounded-lg p-6 text-center">
                <Wrench className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">No custom tools yet</p>
                <p className="text-gray-500 text-xs">Click "Add Tool" to create one</p>
              </div>
            ) : (
              <div className="grid gap-2">
                {customTools.map((tool) => (
                  <ToolCard
                    key={tool.id}
                    tool={tool}
                    onDelete={handleDeleteTool}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Built-in Tools */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-2">
              Built-in Tools ({builtinTools.length})
            </h3>
            <div className="grid gap-2">
              {builtinTools.map((tool) => (
                <ToolCard key={tool.id} tool={tool} />
              ))}
            </div>
          </div>
        </div>
      )}

      {showCreateModal && (
        <CreateAgentModal
          templates={templates}
          tools={tools}
          onClose={() => setShowCreateModal(false)}
          onCreated={handleAgentCreated}
        />
      )}

      {editingAgent && (
        <EditAgentModal
          agent={editingAgent}
          tools={tools}
          onClose={() => setEditingAgent(null)}
          onUpdated={handleAgentUpdated}
        />
      )}
    </div>
  );
}
