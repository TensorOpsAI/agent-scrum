import { useState } from 'react';
import { X, FileText, Loader2, Lightbulb, ArrowRight } from 'lucide-react';
import { clsx } from 'clsx';
import { prdApi } from '../../api/client';
import { usePipelineStore } from '../../store/pipelineStore';

// Quick-start examples per template
const EXAMPLE_INPUTS: Record<string, { title: string; content: string }> = {
  software_dev: {
    title: 'User Authentication System',
    content: `# Feature: User Authentication System

## Overview
Implement a secure user authentication system that allows users to sign up, log in, and manage their sessions.

## Requirements
- Users can sign up with email and password
- Users can log in with existing credentials
- Passwords must be hashed and stored securely
- Sessions expire after 24 hours of inactivity
- Users can reset their password via email

## Acceptance Criteria
- Sign-up form validates email format and password strength
- Login returns a JWT token
- Protected routes reject unauthenticated requests
- Password reset emails are sent within 30 seconds`,
  },
  publisher: {
    title: 'AI Regulation Update',
    content: `# Topic: New EU AI Act Enforcement Begins

## Key Developments
- EU AI Act enforcement starts with first compliance deadlines
- Major tech companies scrambling to meet transparency requirements
- New AI oversight board established with enforcement powers

## Angle
Focus on what this means for businesses using AI tools — practical compliance steps and potential penalties for non-compliance.

## Target Audience
Tech leaders and business decision-makers`,
  },
  talent_acquisition: {
    title: 'Senior Backend Engineer',
    content: `# Position: Senior Backend Engineer

## Department
Engineering — Platform Team

## Requirements
- 5+ years experience in backend development
- Strong Python and/or Go skills
- Experience with distributed systems and microservices
- Familiarity with cloud platforms (AWS/GCP)
- PostgreSQL and Redis experience

## Nice to Have
- Experience with Kubernetes
- Background in high-throughput data pipelines

## Compensation
$160K–$200K + equity, remote-friendly`,
  },
  sales: {
    title: 'Acme Corp Enterprise Deal',
    content: `# Account: Acme Corp

## Contact
Jane Chen, VP of Engineering
jane.chen@acme.com

## Opportunity
- Looking for an enterprise platform solution
- Current pain: manual processes slowing team velocity
- Budget: $80K–$150K annually
- Timeline: Decision by end of Q2
- 500+ seat deployment

## Next Steps
- Schedule discovery call
- Prepare custom demo environment`,
  },
  ciso: {
    title: 'API Authentication Bypass',
    content: `# Incident: API Authentication Bypass Vulnerability

## Severity
Critical (CVSS 9.1)

## Details
- Affected endpoint: /api/v2/admin/*
- Attack vector: Malformed JWT tokens bypass signature verification
- Discovered via: Bug bounty submission (report #4521)
- Affected versions: v2.3.0 through v2.5.2

## Impact
- Unauthorized access to admin endpoints
- Potential data exfiltration of user PII
- No evidence of exploitation in the wild (yet)

## Immediate Actions Needed
- Patch JWT validation library
- Rotate all existing admin tokens
- Audit access logs for anomalies`,
  },
};

interface PRDInputModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function PRDInputModal({ isOpen, onClose }: PRDInputModalProps) {
  const [content, setContent] = useState('');
  const [title, setTitle] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentBoardId = usePipelineStore((s) => s.currentBoardId);
  const currentBoard = usePipelineStore((s) => s.currentBoard);

  const inputNoun = currentBoard?.input_noun ?? 'PRD';
  const itemNoun = currentBoard?.item_noun ?? 'Story';
  const templateId = currentBoard?.template_id ?? 'software_dev';
  const inputPlaceholder = currentBoard?.input_placeholder ??
    `Paste your ${inputNoun} here...`;

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim() || !currentBoardId) return;

    setIsSubmitting(true);
    setError(null);

    try {
      await prdApi.submit(content, currentBoardId, title || undefined);
      setContent('');
      setTitle('');
      onClose();
    } catch (err) {
      setError(`Failed to submit ${inputNoun}. Please try again.`);
      console.error(`Error submitting ${inputNoun}:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTryExample = () => {
    const example = EXAMPLE_INPUTS[templateId] || EXAMPLE_INPUTS.software_dev;
    setTitle(example.title);
    setContent(example.content);
  };

  const hasContent = content.trim().length > 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-blue-500" />
            <h2 className="text-lg font-semibold text-white">Submit {inputNoun}</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            {/* Quick-start hint when empty */}
            {!hasContent && (
              <button
                type="button"
                onClick={handleTryExample}
                className="w-full flex items-center gap-3 px-4 py-3 bg-blue-600/10 hover:bg-blue-600/20 border border-blue-500/30 rounded-lg transition-colors text-left group"
              >
                <Lightbulb className="w-5 h-5 text-blue-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-blue-300">
                    First time? Try an example
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Load a sample {inputNoun.toLowerCase()} to see how it works — you can edit it or submit as-is.
                  </p>
                </div>
                <ArrowRight className="w-4 h-4 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              </button>
            )}

            <div>
              <label
                htmlFor="title"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Title <span className="text-gray-500 font-normal">(optional)</span>
              </label>
              <input
                type="text"
                id="title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder={`Give this ${inputNoun.toLowerCase()} a short name...`}
                className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            <div>
              <label
                htmlFor="content"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                {inputNoun} Content
              </label>
              <textarea
                id="content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder={inputPlaceholder}
                rows={12}
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-none"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-300 text-sm">
                {error}
              </div>
            )}
          </div>

          {/* What happens next */}
          {hasContent && (
            <div className="flex items-center gap-2 mt-4 px-1 text-xs text-gray-400">
              <ArrowRight className="w-3.5 h-3.5 text-blue-400 flex-shrink-0" />
              <span>
                After submitting, AI agents will analyze this and create {itemNoun.toLowerCase()}s on your board automatically.
              </span>
            </div>
          )}

          <div className="flex justify-end gap-3 mt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!content.trim() || !currentBoardId || isSubmitting}
              className={clsx(
                'flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-colors',
                content.trim() && currentBoardId && !isSubmitting
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              )}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                `Submit ${inputNoun}`
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
