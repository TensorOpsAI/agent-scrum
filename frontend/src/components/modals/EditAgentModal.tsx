import { useState } from 'react';
import { X, Bot, Plus, Trash2, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';
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

const CATEGORY_DOTS: Record<string, string> = {
  security:    'bg-red-500',
  code:        'bg-blue-500',
  testing:     'bg-emerald-500',
  docs:        'bg-amber-500',
  performance: 'bg-purple-500',
  devops:      'bg-orange-500',
  custom:      'bg-pink-500',
};

export function EditAgentModal({ agent, tools, onClose, onUpdated }: EditAgentModalProps) {
  const [formData, setFormData] = useState({
    name: agent.name,
    description: agent.description || '',
    tools: [...agent.tools],
    skills: [...agent.skills],
  });
  const [newSkill, setNewSkill] = useState({
    id: '', name: '', description: '', tags: '', examples: '',
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
          tags: newSkill.tags.split(',').map((t) => t.trim()).filter(Boolean),
          examples: newSkill.examples.split('\n').map((e) => e.trim()).filter(Boolean),
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
      setError(err instanceof Error ? err.message : 'Failed to update agent');
    } finally {
      setIsSubmitting(false);
    }
  };

  const toolsByCategory = tools.reduce(
    (acc, tool) => {
      if (!acc[tool.category]) acc[tool.category] = [];
      acc[tool.category].push(tool);
      return acc;
    },
    {} as Record<string, AgentTool[]>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center animate-fade-in">
      <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

      <div className="relative surface shadow-2xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 h-14 border-b border-border shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            <Bot className="w-4 h-4 text-primary flex-shrink-0" />
            <h2 className="text-sm font-medium text-foreground truncate">
              Edit <span className="text-foreground">{agent.name}</span>
            </h2>
            <span className="text-[10px] font-mono text-muted-foreground/60 ml-1">{agent.id}</span>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {error && (
            <div className="flex items-start gap-2 px-3 py-2 rounded-md text-xs bg-destructive/10 border border-destructive/30 text-destructive-foreground animate-fade-in">
              {error}
            </div>
          )}

          {/* Basic Info */}
          <section>
            <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em] mb-2.5">
              Basic information
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Name</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData((prev) => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Security Analyst"
                  className="w-full h-9 px-3 bg-input border border-border rounded-md text-foreground placeholder-muted-foreground/60 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              <div>
                <label className="block text-xs text-muted-foreground mb-1">Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData((prev) => ({ ...prev, description: e.target.value }))}
                  placeholder="What does this agent do?"
                  rows={2}
                  className="w-full px-3 py-2 bg-input border border-border rounded-md text-foreground placeholder-muted-foreground/60 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none"
                />
              </div>
            </div>
          </section>

          {/* Tools */}
          <section>
            <div className="flex items-center justify-between mb-2.5">
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em]">
                Tools
              </h3>
              <span className="text-[11px] text-muted-foreground">
                <span className="text-primary font-medium tabular-nums">{formData.tools.length}</span> selected
              </span>
            </div>
            <div className="space-y-3">
              {Object.entries(toolsByCategory).map(([category, categoryTools]) => (
                <div key={category} className="surface-muted p-3">
                  <div className="flex items-center gap-1.5 mb-2">
                    <span className={cn('status-dot', CATEGORY_DOTS[category] || CATEGORY_DOTS.custom)} />
                    <span className="text-[11px] font-medium text-muted-foreground capitalize tracking-wide">
                      {category}
                    </span>
                    <span className="text-[10px] text-muted-foreground/60 ml-1 tabular-nums">
                      {categoryTools.filter(t => formData.tools.includes(t.id)).length}/{categoryTools.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {categoryTools.map((tool) => {
                      const isSelected = formData.tools.includes(tool.id);
                      return (
                        <button
                          key={tool.id}
                          onClick={() => handleToolToggle(tool.id)}
                          className={cn(
                            'inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded-md border transition-colors',
                            isSelected
                              ? 'border-primary/60 bg-primary/15 text-primary-foreground shadow-sm shadow-primary/20'
                              : 'border-border bg-card/40 text-muted-foreground hover:border-border/100 hover:text-foreground hover:bg-accent/40'
                          )}
                          title={tool.description}
                        >
                          {isSelected && <span className="w-1 h-1 rounded-full bg-primary" />}
                          {tool.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Skills */}
          <section>
            <div className="flex items-center justify-between mb-2.5">
              <h3 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-[0.1em]">
                Skills
              </h3>
              <span className="text-[11px] text-muted-foreground tabular-nums">{formData.skills.length}</span>
            </div>
            <div className="space-y-2">
              {formData.skills.map((skill) => (
                <div
                  key={skill.id}
                  className="flex items-start justify-between gap-2 p-2.5 surface-muted"
                >
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-foreground">{skill.name}</div>
                    {skill.description && (
                      <div className="text-xs text-muted-foreground mt-0.5">{skill.description}</div>
                    )}
                  </div>
                  <button
                    onClick={() => handleRemoveSkill(skill.id)}
                    className="p-1 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-md transition-colors flex-shrink-0"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              ))}

              {/* Add new skill */}
              <div className="surface-muted p-3 space-y-2">
                <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                  Add custom skill
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={newSkill.id}
                    onChange={(e) => setNewSkill((prev) => ({ ...prev, id: e.target.value }))}
                    placeholder="skill_id"
                    className="h-8 px-2 bg-input border border-border rounded-md text-xs text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring font-mono"
                  />
                  <input
                    type="text"
                    value={newSkill.name}
                    onChange={(e) => setNewSkill((prev) => ({ ...prev, name: e.target.value }))}
                    placeholder="Skill name"
                    className="h-8 px-2 bg-input border border-border rounded-md text-xs text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring"
                  />
                </div>
                <input
                  type="text"
                  value={newSkill.description}
                  onChange={(e) => setNewSkill((prev) => ({ ...prev, description: e.target.value }))}
                  placeholder="Description"
                  className="w-full h-8 px-2 bg-input border border-border rounded-md text-xs text-foreground placeholder-muted-foreground/60 focus:outline-none focus:ring-1 focus:ring-ring"
                />
                <button
                  onClick={handleAddSkill}
                  disabled={!newSkill.id || !newSkill.name}
                  className="inline-flex items-center gap-1 h-7 px-2.5 text-[11px] rounded-md bg-secondary hover:bg-accent text-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Plus className="w-3 h-3" />
                  Add skill
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-5 h-14 border-t border-border shrink-0">
          <button onClick={onClose} className="btn-ghost">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !formData.name}
            className="btn-primary"
          >
            {isSubmitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
            Save changes
          </button>
        </div>
      </div>
    </div>
  );
}
