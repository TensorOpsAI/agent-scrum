import { useState, useEffect, useCallback } from 'react';
import {
  Bot, Plus, Trash2, Power, PowerOff, ChevronDown, ChevronUp,
  Wrench, Pencil, Lock, Loader2,
} from 'lucide-react';
import { cn } from '../../lib/utils';
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

const CATEGORY_DOTS: Record<string, string> = {
  security:    'bg-red-500',
  code:        'bg-blue-500',
  testing:     'bg-emerald-500',
  docs:        'bg-amber-500',
  performance: 'bg-purple-500',
  devops:      'bg-orange-500',
  custom:      'bg-pink-500',
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
    <div className={cn(
      'surface-muted transition-opacity',
      !agent.is_active && 'opacity-60'
    )}>
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-sm text-foreground truncate">{agent.name}</h3>
              {agent.template && (
                <span className="text-[10px] font-mono text-muted-foreground/60 uppercase tracking-wider">
                  {agent.template}
                </span>
              )}
            </div>
            {agent.description && (
              <p className="text-xs text-muted-foreground mt-0.5 line-clamp-2 leading-relaxed">
                {agent.description}
              </p>
            )}
          </div>
          <div className="flex items-center gap-0.5 flex-shrink-0">
            <button
              onClick={() => onEdit(agent)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
              title="Edit"
            >
              <Pencil className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onToggleActive(agent.id, !agent.is_active)}
              className={cn(
                'p-1.5 rounded-md transition-colors',
                agent.is_active
                  ? 'text-emerald-400 hover:bg-emerald-500/10'
                  : 'text-muted-foreground hover:bg-accent'
              )}
              title={agent.is_active ? 'Deactivate' : 'Activate'}
            >
              {agent.is_active ? <Power className="w-3.5 h-3.5" /> : <PowerOff className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={() => onDelete(agent.id)}
              className="p-1.5 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
              title="Delete"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors mt-1"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          <span className="tabular-nums">{agent.tools.length}</span> tools
          {agent.skills.length > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="tabular-nums">{agent.skills.length}</span> skills
            </>
          )}
        </button>

        {expanded && (
          <div className="mt-3 pt-3 border-t border-border space-y-3 animate-fade-in">
            {agent.tools.length > 0 && (
              <div>
                <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Tools
                </h4>
                <div className="flex flex-wrap gap-1">
                  {agent.tools.map((toolId) => (
                    <span
                      key={toolId}
                      className="px-1.5 py-0.5 text-[10px] bg-secondary border border-border text-muted-foreground rounded"
                    >
                      {toolId.replace(/_/g, ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {agent.skills.length > 0 && (
              <div>
                <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
                  Skills
                </h4>
                <div className="space-y-1">
                  {agent.skills.map((skill) => (
                    <div key={skill.id} className="text-xs">
                      <span className="text-foreground">{skill.name}</span>
                      {skill.description && (
                        <span className="text-muted-foreground"> — {skill.description}</span>
                      )}
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
    <div className={cn('surface-muted p-3', tool.is_builtin && 'opacity-80')}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={cn('status-dot flex-shrink-0', CATEGORY_DOTS[tool.category] || CATEGORY_DOTS.custom)} />
          <span className="text-sm font-medium text-foreground truncate">{tool.name}</span>
          {tool.is_builtin && (
            <Lock className="w-3 h-3 text-muted-foreground/60 flex-shrink-0" aria-label="Built-in" />
          )}
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70 ml-1">
            {tool.category}
          </span>
        </div>
        <div className="flex items-center gap-0.5 flex-shrink-0">
          {!tool.is_builtin && (
            <>
              {onEdit && (
                <button
                  onClick={() => onEdit(tool)}
                  className="p-1 rounded-md text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
                  title="Edit"
                >
                  <Pencil className="w-3 h-3" />
                </button>
              )}
              {onDelete && (
                <button
                  onClick={() => onDelete(tool.id)}
                  className="p-1 rounded-md text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-colors"
                  title="Delete"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              )}
            </>
          )}
        </div>
      </div>

      {tool.description && (
        <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{tool.description}</p>
      )}

      {tool.capabilities.length > 0 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground transition-colors mt-2"
        >
          {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          <span className="tabular-nums">{tool.capabilities.length}</span> capabilities
        </button>
      )}

      {expanded && tool.capabilities.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1 animate-fade-in">
          {tool.capabilities.map((cap) => (
            <span key={cap} className="px-1.5 py-0.5 text-[10px] bg-secondary text-muted-foreground rounded font-mono">
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
      capabilities: formData.capabilities.split(',').map((c) => c.trim()).filter(Boolean),
    });
  };

  return (
    <div className="surface p-4 space-y-3 animate-fade-in">
      <h4 className="text-sm font-medium text-foreground">Create custom tool</h4>

      {error && (
        <div className="bg-destructive/10 border border-destructive/30 text-destructive-foreground px-3 py-1.5 rounded-md text-xs">
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] text-muted-foreground mb-1">Tool ID</label>
          <input
            type="text"
            value={formData.id}
            onChange={(e) => setFormData((prev) => ({ ...prev, id: e.target.value }))}
            placeholder="my_custom_tool"
            className="w-full h-8 px-2 bg-input border border-border rounded-md text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring font-mono"
          />
        </div>
        <div>
          <label className="block text-[11px] text-muted-foreground mb-1">Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
            placeholder="My Custom Tool"
            className="w-full h-8 px-2 bg-input border border-border rounded-md text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div>
        <label className="block text-[11px] text-muted-foreground mb-1">Description</label>
        <input
          type="text"
          value={formData.description}
          onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
          placeholder="What does this tool do?"
          className="w-full h-8 px-2 bg-input border border-border rounded-md text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-[11px] text-muted-foreground mb-1">Category</label>
          <select
            value={formData.category}
            onChange={(e) => setFormData((prev) => ({ ...prev, category: e.target.value }))}
            className="w-full h-8 px-2 bg-input border border-border rounded-md text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          >
            {categories.map((cat) => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
            <option value="custom">custom</option>
          </select>
        </div>
        <div>
          <label className="block text-[11px] text-muted-foreground mb-1">Capabilities (comma-separated)</label>
          <input
            type="text"
            value={formData.capabilities}
            onChange={(e) => setFormData((prev) => ({ ...prev, capabilities: e.target.value }))}
            placeholder="analyze, report, fix"
            className="w-full h-8 px-2 bg-input border border-border rounded-md text-sm text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <button onClick={onCancel} className="btn-ghost">Cancel</button>
        <button onClick={handleSubmit} className="btn-primary">Create tool</button>
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

  useEffect(() => { loadData(); }, [loadData]);

  const handleToggleActive = async (agentId: string, active: boolean) => {
    try {
      await agentManagementApi.toggleActivation(agentId, active);
      setAgents((prev) => prev.map((a) => (a.id === agentId ? { ...a, is_active: active } : a)));
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
      refreshStoreAgents();
    } catch (err) {
      console.error('Failed to delete agent:', err);
    }
  };

  const handleAgentCreated = (newAgent: DynamicAgent) => {
    setAgents((prev) => [newAgent, ...prev]);
    setShowCreateModal(false);
    refreshStoreAgents();
  };

  const handleAgentUpdated = (updatedAgent: DynamicAgent) => {
    setAgents((prev) => prev.map((a) => (a.id === updatedAgent.id ? updatedAgent : a)));
    setEditingAgent(null);
    refreshStoreAgents();
  };

  const handleCreateTool = async (request: CreateToolRequest) => {
    try {
      const newTool = await agentManagementApi.createTool(request);
      setTools((prev) => [...prev, newTool]);
      setShowCreateTool(false);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create tool');
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
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-5 h-5 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div>
      {/* Tabs row + add button */}
      <div className="flex items-center justify-between px-4 pt-3 border-b border-border">
        <div className="flex">
          <button
            onClick={() => setActiveTab('agents')}
            className={cn(
              'h-9 px-3 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5',
              activeTab === 'agents'
                ? 'text-foreground border-primary'
                : 'text-muted-foreground border-transparent hover:text-foreground'
            )}
          >
            <Bot className="w-3.5 h-3.5" />
            Agents
            <span className="text-[10px] tabular-nums opacity-70">({agents.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('tools')}
            className={cn(
              'h-9 px-3 text-sm font-medium transition-colors border-b-2 -mb-px flex items-center gap-1.5',
              activeTab === 'tools'
                ? 'text-foreground border-primary'
                : 'text-muted-foreground border-transparent hover:text-foreground'
            )}
          >
            <Wrench className="w-3.5 h-3.5" />
            Tools
            <span className="text-[10px] tabular-nums opacity-70">({tools.length})</span>
          </button>
        </div>

        {activeTab === 'agents' ? (
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-1.5 h-7 px-2.5 mb-1 rounded-md text-xs font-medium bg-primary hover:bg-primary/90 text-primary-foreground transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add agent
          </button>
        ) : (
          <button
            onClick={() => setShowCreateTool(true)}
            className="inline-flex items-center gap-1.5 h-7 px-2.5 mb-1 rounded-md text-xs font-medium bg-primary hover:bg-primary/90 text-primary-foreground transition-colors"
          >
            <Plus className="w-3 h-3" />
            Add tool
          </button>
        )}
      </div>

      <div className="p-4 space-y-4">
        {error && (
          <div className="flex items-start gap-2 px-3 py-2 rounded-md text-xs bg-destructive/10 border border-destructive/30 text-destructive-foreground">
            {error}
          </div>
        )}

        {activeTab === 'agents' ? (
          <div className="space-y-4">
            {/* Dynamic Agents */}
            <section>
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2">
                Dynamic agents <span className="opacity-60 tabular-nums">({agents.length})</span>
              </h3>
              {agents.length === 0 ? (
                <div className="surface-muted p-6 text-center">
                  <Bot className="w-7 h-7 text-muted-foreground/50 mx-auto mb-2" />
                  <p className="text-sm text-foreground">No dynamic agents yet</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Click "Add agent" to create one</p>
                </div>
              ) : (
                <div className="space-y-2">
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
            </section>

            {/* Templates */}
            <section>
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2">
                Available templates <span className="opacity-60 tabular-nums">({templates.length})</span>
              </h3>
              <div className="space-y-1.5">
                {templates.map((template) => (
                  <div key={template.id} className="surface-muted p-2.5">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm text-foreground truncate">{template.name}</span>
                      <span className="text-[10px] text-muted-foreground tabular-nums whitespace-nowrap">
                        {template.default_tools.length} tools
                      </span>
                    </div>
                    {template.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{template.description}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          </div>
        ) : (
          <div className="space-y-4">
            {showCreateTool && (
              <CreateToolForm
                categories={categories}
                onSubmit={handleCreateTool}
                onCancel={() => setShowCreateTool(false)}
              />
            )}

            {/* Custom Tools */}
            <section>
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2">
                Custom tools <span className="opacity-60 tabular-nums">({customTools.length})</span>
              </h3>
              {customTools.length === 0 ? (
                <div className="surface-muted p-6 text-center">
                  <Wrench className="w-7 h-7 text-muted-foreground/50 mx-auto mb-2" />
                  <p className="text-sm text-foreground">No custom tools yet</p>
                  <p className="text-xs text-muted-foreground mt-0.5">Click "Add tool" to create one</p>
                </div>
              ) : (
                <div className="space-y-1.5">
                  {customTools.map((tool) => (
                    <ToolCard key={tool.id} tool={tool} onDelete={handleDeleteTool} />
                  ))}
                </div>
              )}
            </section>

            {/* Built-in Tools */}
            <section>
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2">
                Built-in tools <span className="opacity-60 tabular-nums">({builtinTools.length})</span>
              </h3>
              <div className="space-y-1.5">
                {builtinTools.map((tool) => (
                  <ToolCard key={tool.id} tool={tool} />
                ))}
              </div>
            </section>
          </div>
        )}
      </div>

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
