"""
LangGraph Agents - Agent definitions using create_react_agent.

Each agent has:
- Skills: Cognitive capabilities defined in the system prompt
- Tools: Concrete actions the agent can execute

Skills are for reasoning, tools are for doing.
"""
import logging
from typing import Any, Optional
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.language_models.base import BaseLanguageModel

from app.config import get_settings

logger = logging.getLogger(__name__)
from app.agents.tools.db_tools import (
    get_story,
    get_task,
    get_tasks_for_story,
    create_story,
    create_task,
    update_story_status,
    update_task_status,
    update_task_implementation,
    update_task_test_scenarios,
    add_comment,
    get_task_comments,
    list_stories_by_status,
    list_tasks_by_status,
)

settings = get_settings()

# Cache for the model instance
_model_instance: Optional[BaseLanguageModel] = None


def is_simulation_mode() -> bool:
    """Check if we should run in simulation mode."""
    return settings.simulate_mode or not settings.gemini_api_key


def get_model(model_name: str = None):
    """Get a configured LLM instance.

    If simulate_mode is enabled or no API key is available, returns None
    and agents will use simulation mode.
    """
    global _model_instance

    # Use configured model name if not specified
    if model_name is None:
        model_name = settings.gemini_model or "gemini-2.0-flash"

    # Check if we should use simulation mode
    if is_simulation_mode():
        return None

    # Return cached instance if available
    if _model_instance is not None:
        return _model_instance

    # Import here to avoid import errors when API key not available
    from langchain_google_genai import ChatGoogleGenerativeAI

    _model_instance = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.gemini_api_key,
        temperature=0.7,
    )
    return _model_instance


class SimulatedAgent:
    """A simulated agent that provides mock responses when no API key is available.

    This allows the system to run in demo/development mode without real LLM calls.
    """

    def __init__(self, agent_id: str, tools: list, system_prompt: str):
        self.agent_id = agent_id
        self.tools = tools
        self.system_prompt = system_prompt

    async def ainvoke(self, input_data: dict) -> dict:
        """Simulate agent invocation with mock tool calls."""
        logger.info(f"[SIMULATED:{self.agent_id}] ainvoke called")
        messages = input_data.get("messages", [])
        if not messages:
            logger.warning(f"[SIMULATED:{self.agent_id}] No messages provided")
            return {"messages": [AIMessage(content="No input provided.")]}

        # Get the last message
        last_message = messages[-1].content if messages else ""
        logger.info(f"[SIMULATED:{self.agent_id}] Processing message of length {len(last_message)}")

        # Simulate tool usage based on the message content
        response_messages = []
        import re

        # Product Owner: Parse PRD and create stories
        # Only treat as PRD if it looks like actual requirements, not a chat message
        if self.agent_id == "product_owner":
            # Skip if it looks like a chat command - must be SHORT and match chat patterns
            # Long messages (>200 chars) are likely PRDs, not chat
            msg_lower = last_message.lower().strip()
            is_chat_message = (
                last_message.strip().startswith("@") or
                len(last_message) < 100 or  # Very short = likely chat
                (len(last_message) < 300 and (  # Medium length + chat patterns = chat
                    msg_lower.endswith("?") or
                    msg_lower.startswith("please ") or
                    msg_lower.startswith("can you") or
                    msg_lower.startswith("start ") or
                    msg_lower.startswith("hey ") or
                    msg_lower.startswith("hi ")
                ))
            )

            if is_chat_message:
                response_content = f"[Simulation Mode] Product Owner acknowledges: {last_message[:50]}... (This looks like a chat message, not a PRD. Submit a PRD through the PRD form to create stories.)"
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

            logger.info(f"[SIMULATED:{self.agent_id}] Processing PRD content, will create stories")
            # This looks like a PRD - parse it and create stories
            stories_created = await self._parse_prd_and_create_stories(last_message)
            response_content = f"[Simulation Mode] Product Owner analyzed PRD and created {stories_created} user stories."
            response_messages.append(AIMessage(content=response_content))
            return {"messages": response_messages}

        # Developer: Break down story OR write implementation notes for task
        if self.agent_id == "developer":
            # Check for task implementation first (more specific)
            task_match = re.search(r'task\s*#?(\d+)', last_message.lower())
            if task_match and "implementation" in last_message.lower():
                task_id = int(task_match.group(1))
                await self._write_implementation(task_id)
                response_content = f"[Simulation Mode] Developer wrote implementation notes for task #{task_id}."
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

            # Check for story breakdown
            story_match = re.search(r'story\s*#?(\d+)', last_message.lower())
            if story_match:
                story_id = int(story_match.group(1))
                await self._breakdown_story(story_id)
                response_content = f"[Simulation Mode] Developer broke down story #{story_id} into tasks."
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

        # Tech Lead: Review tasks
        if self.agent_id == "tech_lead":
            story_match = re.search(r'story\s*#?(\d+)', last_message.lower())
            if story_match:
                story_id = int(story_match.group(1))
                await self._review_tasks(story_id)
                response_content = f"[Simulation Mode] Tech Lead approved tasks for story #{story_id}."
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

        # Code Reviewer: Review implementation
        if self.agent_id == "code_reviewer":
            task_match = re.search(r'task\s*#?(\d+)', last_message.lower())
            if task_match:
                task_id = int(task_match.group(1))
                await self._review_code(task_id)
                response_content = f"[Simulation Mode] Code Reviewer approved task #{task_id}."
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

        # QA: Test task
        if self.agent_id == "qa":
            task_match = re.search(r'task\s*#?(\d+)', last_message.lower())
            if task_match:
                task_id = int(task_match.group(1))
                await self._qa_test(task_id)
                response_content = f"[Simulation Mode] QA passed task #{task_id}."
                response_messages.append(AIMessage(content=response_content))
                return {"messages": response_messages}

        # Domain agent simulation - parse role from agent_id and look up simulation text
        role, board_id = _parse_agent_id(self.agent_id)
        response_content = await self._domain_simulation(role, board_id, last_message)
        response_messages.append(AIMessage(content=response_content))
        return {"messages": response_messages}

    async def _parse_prd_and_create_stories(self, prd_content: str) -> int:
        """Parse PRD and create user stories."""
        import re

        logger.info(f"[SIMULATED:product_owner] _parse_prd_and_create_stories called with {len(prd_content)} chars")

        features = []
        lines = prd_content.split('\n')

        # Skip intro lines - common patterns at start of PRDs
        intro_patterns = [
            r'^here\s+(is|are)',
            r'^this\s+(is|document)',
            r'^the\s+following',
            r'^overview',
            r'^introduction',
            r'^product\s+requirements',
            r'^prd\s*:',
        ]

        def is_intro_line(line: str) -> bool:
            line_lower = line.lower().strip()
            return any(re.match(p, line_lower) for p in intro_patterns)

        def is_actionable(line: str) -> bool:
            """Check if line describes something to build."""
            line_lower = line.lower()
            action_verbs = [
                'allow', 'enable', 'provide', 'support', 'display', 'show',
                'create', 'add', 'implement', 'build', 'develop', 'integrate',
                'manage', 'track', 'monitor', 'authenticate', 'authorize',
                'upload', 'download', 'search', 'filter', 'sort', 'export',
                'import', 'send', 'receive', 'notify', 'alert', 'generate',
                'store', 'save', 'retrieve', 'update', 'delete', 'edit',
            ]
            return any(verb in line_lower for verb in action_verbs)

        # Strategy 1: Look for markdown headers with content
        current_section = None
        section_content = []

        for line in lines:
            header_match = re.match(r'^#{1,3}\s+(.+)$', line.strip())
            if header_match:
                if current_section and section_content:
                    content = ' '.join(section_content).strip()
                    if len(content) > 10 and not is_intro_line(current_section):
                        features.append(f"{current_section}: {content[:150]}")
                current_section = header_match.group(1).strip()
                section_content = []
            elif current_section and line.strip():
                section_content.append(line.strip())

        if current_section and section_content:
            content = ' '.join(section_content).strip()
            if len(content) > 10 and not is_intro_line(current_section):
                features.append(f"{current_section}: {content[:150]}")

        logger.info(f"[SIMULATED:product_owner] Strategy 1 (headers): found {len(features)} features")

        # Strategy 2: Look for numbered lists
        if len(features) < 2:
            numbered_features = []
            for line in lines:
                line = line.strip()
                numbered_match = re.match(r'^(\d+)[.\)]\s+(.+)$', line)
                if numbered_match:
                    feature_text = numbered_match.group(2).strip()
                    if len(feature_text) > 5 and not is_intro_line(feature_text):
                        numbered_features.append(feature_text)
            if numbered_features:
                features = numbered_features
                logger.info(f"[SIMULATED:product_owner] Strategy 2 (numbered): found {len(features)} features")

        # Strategy 3: Look for bullet points
        if len(features) < 2:
            bullet_features = []
            for line in lines:
                line = line.strip()
                bullet_match = re.match(r'^[-*•]\s+(.+)$', line)
                if bullet_match:
                    feature_text = bullet_match.group(1).strip()
                    if len(feature_text) > 10 and not is_intro_line(feature_text):
                        bullet_features.append(feature_text)
            if bullet_features:
                features = bullet_features
                logger.info(f"[SIMULATED:product_owner] Strategy 3 (bullets): found {len(features)} features")

        # Strategy 4: Look for actionable sentences (lines with action verbs)
        if len(features) < 2:
            actionable_features = []
            for line in lines:
                line = line.strip()
                if len(line) > 20 and is_actionable(line) and not is_intro_line(line):
                    # Clean up the line
                    clean_line = re.sub(r'^[-*•]\s*', '', line)
                    clean_line = re.sub(r'^\d+[.\)]\s*', '', clean_line)
                    if clean_line not in actionable_features:
                        actionable_features.append(clean_line[:200])
            if actionable_features:
                features = actionable_features
                logger.info(f"[SIMULATED:product_owner] Strategy 4 (actionable): found {len(features)} features")

        # Strategy 5: Look for user story patterns or requirement keywords
        if len(features) < 2:
            keyword_features = []
            for line in lines:
                line = line.strip()
                if len(line) < 15:
                    continue
                lower = line.lower()
                # Direct keywords
                for kw in ['feature:', 'story:', 'requirement:', 'epic:', 'user story:']:
                    if kw in lower:
                        idx = lower.index(kw) + len(kw)
                        feature_text = line[idx:].strip()
                        if feature_text:
                            keyword_features.append(feature_text)
                        break
                # User story format
                if re.match(r'^(as a|users? (can|should|will|must)|the system (will|should|must))', lower):
                    keyword_features.append(line)
            if keyword_features:
                features = keyword_features
                logger.info(f"[SIMULATED:product_owner] Strategy 5 (keywords): found {len(features)} features")

        # Strategy 6: Split by sentences and find substantial ones
        if len(features) < 2:
            # Split into sentences
            sentences = re.split(r'[.!?]\s+', prd_content)
            sentence_features = []
            for sent in sentences:
                sent = sent.strip()
                if 30 < len(sent) < 300 and is_actionable(sent) and not is_intro_line(sent):
                    sentence_features.append(sent)
            if sentence_features:
                features = sentence_features[:15]
                logger.info(f"[SIMULATED:product_owner] Strategy 6 (sentences): found {len(features)} features")

        # Strategy 7: Split by paragraphs
        if len(features) < 2:
            paragraphs = re.split(r'\n\s*\n', prd_content)
            para_features = []
            for para in paragraphs:
                para = para.strip()
                if 30 < len(para) < 500 and not is_intro_line(para):
                    para_features.append(para[:200])
            if para_features:
                features = para_features
                logger.info(f"[SIMULATED:product_owner] Strategy 7 (paragraphs): found {len(features)} features")

        # Strategy 8: Last resort - split the content into chunks
        if len(features) < 2:
            # Remove intro and split by any delimiter
            content = prd_content
            for line in lines[:3]:
                if is_intro_line(line):
                    content = content.replace(line, '', 1)
            # Split by common delimiters
            chunks = re.split(r'(?:\n[-*•]|\n\d+[.\)]|\n{2,})', content)
            chunk_features = [c.strip()[:200] for c in chunks if len(c.strip()) > 30]
            if chunk_features:
                features = chunk_features
                logger.info(f"[SIMULATED:product_owner] Strategy 8 (chunks): found {len(features)} features")

        # Final fallback
        if not features:
            clean_content = prd_content.strip()[:200]
            if clean_content:
                features = [clean_content]
                logger.info(f"[SIMULATED:product_owner] Fallback: using PRD content as single story")
            else:
                features = ["Implement the requirements from the PRD"]

        # Deduplicate and limit
        seen = set()
        unique_features = []
        for f in features:
            f_lower = f.lower()[:50]  # Compare first 50 chars
            if f_lower not in seen:
                seen.add(f_lower)
                unique_features.append(f)

        features = unique_features[:15]  # Allow up to 15 stories for thorough PRD breakdown

        # If we have fewer than 10 features, derive additional stories from existing ones
        # This ensures thorough coverage as a good PO would do
        if len(features) < 10 and len(features) > 0:
            derived_stories = []
            for feature in features[:5]:  # Derive from first 5 features
                # Add error handling story
                derived_stories.append(f"Handle errors and edge cases for: {feature[:80]}")
                # Add validation story
                derived_stories.append(f"Input validation and data integrity for: {feature[:80]}")

            # Add common cross-cutting stories
            derived_stories.extend([
                "User notification system for important events and updates",
                "Settings and preferences management for users",
                "Admin dashboard for monitoring and management",
                "Search and filter functionality across the application",
                "Data export and reporting capabilities",
                "User onboarding and help documentation",
                "Performance optimization and caching",
                "Audit logging for security and compliance",
            ])

            # Add derived stories until we have at least 10
            for derived in derived_stories:
                if len(features) >= 10:
                    break
                d_lower = derived.lower()[:50]
                if d_lower not in seen:
                    seen.add(d_lower)
                    features.append(derived)

        logger.info(f"[SIMULATED:product_owner] Extracted {len(features)} features: {[f[:50] for f in features]}")

        stories_created = 0
        for i, feature in enumerate(features, 1):
            try:
                # Create a user story
                title = f"As a user, I want {feature[:50]}..." if len(feature) > 50 else f"As a user, I want {feature}"
                logger.info(f"[SIMULATED:product_owner] Creating story {i}: {title[:60]}...")
                result = await create_story.ainvoke({
                    "title": title,
                    "description": f"[From PRD] {feature}",
                    "acceptance_criteria": f"- Feature is implemented as described\n- User can access the functionality\n- No errors occur during normal use",
                    "priority": i,
                    "prd_content": prd_content[:500],  # Store truncated PRD
                })
                logger.info(f"[SIMULATED:product_owner] Story created: {result}")
                stories_created += 1
            except Exception as e:
                logger.error(f"[SIMULATED:product_owner] Error creating story: {e}", exc_info=True)
                pass

        logger.info(f"[SIMULATED:product_owner] Created {stories_created} stories total")
        return stories_created

    async def _breakdown_story(self, story_id: int):
        """Break down a story into tasks."""
        try:
            # Mark story as in_breakdown while we work
            await update_story_status.ainvoke({
                "story_id": story_id,
                "new_status": "in_breakdown"
            })

            story_result = await get_story.ainvoke({"story_id": story_id})
            if story_result and not story_result.get("error"):
                # Create tasks for this story
                task_titles = [
                    ("Setup and configuration", "Set up necessary configuration and dependencies"),
                    ("Core implementation", "Implement the main functionality"),
                    ("Error handling", "Add proper error handling and edge cases"),
                    ("Testing", "Write unit and integration tests"),
                ]
                for title, desc in task_titles:
                    await create_task.ainvoke({
                        "story_id": story_id,
                        "title": f"{title} for {story_result.get('title', 'feature')[:30]}",
                        "description": desc,
                    })
                    logger.info(f"[SIMULATED:developer] Created task: {title}")

                # Move to tasks_in_review for tech lead
                await update_story_status.ainvoke({
                    "story_id": story_id,
                    "new_status": "tasks_in_review"
                })
                logger.info(f"[SIMULATED:developer] Story #{story_id} moved to tasks_in_review")
        except Exception as e:
            logger.error(f"[SIMULATED:developer] Error breaking down story: {e}", exc_info=True)

    async def _write_implementation(self, task_id: int):
        """Write implementation notes for a task."""
        try:
            task_result = await get_task.ainvoke({"task_id": task_id})
            if task_result and not task_result.get("error"):
                # Write implementation notes
                await update_task_implementation.ainvoke({
                    "task_id": task_id,
                    "implementation_notes": f"""[Simulated] Implementation approach for: {task_result.get('title', 'task')}

## Overview
This task involves implementing the required functionality as specified.

## Approach
1. Set up necessary imports and dependencies
2. Implement core logic following best practices
3. Add proper error handling
4. Write unit tests for coverage

## Code Structure
- Main implementation in appropriate module
- Tests in corresponding test file
- Documentation updated as needed

## Notes
- Follow existing code patterns
- Ensure backward compatibility
- Consider edge cases
"""
                })
                # Move to code review
                await update_task_status.ainvoke({
                    "task_id": task_id,
                    "new_status": "code_review"
                })
                logger.info(f"[SIMULATED:developer] Implementation written for task #{task_id}, moved to code_review")
        except Exception as e:
            logger.error(f"[SIMULATED:developer] Error writing implementation: {e}", exc_info=True)

    async def _review_tasks(self, story_id: int):
        """Review and approve tasks for a story."""
        try:
            tasks = await get_tasks_for_story.ainvoke({"story_id": story_id})
            logger.info(f"[SIMULATED:tech_lead] Found {len(tasks)} tasks for story #{story_id}")

            for task in tasks:
                task_id = task["id"]
                current_status = task.get("status", "unknown")
                logger.info(f"[SIMULATED:tech_lead] Approving task #{task_id} (was: {current_status})")

                await update_task_status.ainvoke({
                    "task_id": task_id,
                    "new_status": "ready_for_development"
                })

            await update_story_status.ainvoke({
                "story_id": story_id,
                "new_status": "in_development"
            })
            logger.info(f"[SIMULATED:tech_lead] Reviewed {len(tasks)} tasks for story #{story_id}, moved to in_development")
        except Exception as e:
            logger.error(f"[SIMULATED:tech_lead] Error reviewing tasks: {e}", exc_info=True)

    async def _review_code(self, task_id: int):
        """Review code and approve. Moves story to in_qa when first task reaches QA."""
        try:
            # Get task to find story_id
            task_result = await get_task.ainvoke({"task_id": task_id})
            story_id = task_result.get("story_id") if task_result else None

            await add_comment.ainvoke({
                "content": "[Simulated] Code review passed. Implementation looks good.",
                "agent_type": "code_reviewer",
                "task_id": task_id,
            })
            await update_task_status.ainvoke({
                "task_id": task_id,
                "new_status": "ready_for_qa"
            })
            logger.info(f"[SIMULATED:code_reviewer] Task #{task_id} approved, moved to ready_for_qa")

            # Check if story should move to in_qa
            if story_id:
                story = await get_story.ainvoke({"story_id": story_id})
                if story and story.get("status") == "in_development":
                    await update_story_status.ainvoke({
                        "story_id": story_id,
                        "new_status": "in_qa"
                    })
                    logger.info(f"[SIMULATED:code_reviewer] Story #{story_id} moved to in_qa")

        except Exception as e:
            logger.error(f"[SIMULATED:code_reviewer] Error reviewing code: {e}", exc_info=True)

    async def _qa_test(self, task_id: int):
        """Run QA tests and pass. Also checks if story is complete."""
        try:
            # Get task to find story_id
            task_result = await get_task.ainvoke({"task_id": task_id})
            story_id = task_result.get("story_id") if task_result else None

            # Write test scenarios
            await update_task_test_scenarios.ainvoke({
                "task_id": task_id,
                "test_scenarios": "[Simulated] Test Scenarios:\n1. Happy path test - PASS\n2. Edge case test - PASS\n3. Error handling test - PASS"
            })

            # Mark task as done
            await update_task_status.ainvoke({
                "task_id": task_id,
                "new_status": "done"
            })
            logger.info(f"[SIMULATED:qa] Task #{task_id} marked as done")

            # Check if all tasks in the story are done
            if story_id:
                tasks = await get_tasks_for_story.ainvoke({"story_id": story_id})
                all_done = all(t.get("status") == "done" for t in tasks)

                if all_done and len(tasks) > 0:
                    # Move story to done
                    await update_story_status.ainvoke({
                        "story_id": story_id,
                        "new_status": "done"
                    })
                    logger.info(f"[SIMULATED:qa] All tasks complete! Story #{story_id} marked as done")

        except Exception as e:
            logger.error(f"[SIMULATED:qa] Error in QA test: {e}", exc_info=True)

    async def _domain_simulation(self, role: str, board_id: int | None, message: str) -> str:
        """Handle domain-specific agent simulation for non-software-dev boards."""
        import re
        import asyncio

        # Look up the board's template to find the right simulation
        template_id = None
        if board_id:
            try:
                from app.db.database import async_session_maker
                from app.db.models import PipelineConfig
                from sqlalchemy import select
                async with async_session_maker() as db:
                    result = await db.execute(
                        select(PipelineConfig.template_id).where(PipelineConfig.id == board_id)
                    )
                    template_id = result.scalar_one_or_none()
            except Exception:
                pass

        if not template_id:
            template_id = "software_dev"

        # Extract action from context (passed via swarm)
        # The swarm sends messages like "Process item #3: Title" or "Process task #5: Title"
        action = None
        item_id = None

        # Try to get action from the message context
        story_match = re.search(r'item\s*#?(\d+)', message.lower())
        task_match = re.search(r'task\s*#?(\d+)', message.lower())

        if task_match:
            item_id = int(task_match.group(1))
        elif story_match:
            item_id = int(story_match.group(1))

        # Look up simulation text
        domain_sims = DOMAIN_SIMULATIONS.get(template_id, {})
        role_sims = domain_sims.get(role, {})

        # Pick the first matching action text, or a generic one
        if role_sims:
            # Use the first available simulation for this role
            action_key = next(iter(role_sims))
            sim_text = role_sims[action_key]
        else:
            sim_text = f"{role.replace('_', ' ').title()} processed the item successfully."

        # Simulate work
        await asyncio.sleep(2)

        item_ref = f"#{item_id}" if item_id else ""
        return f"[Simulation Mode] {sim_text} {item_ref}".strip()


# ============================================================================
# PRODUCT OWNER AGENT
# ============================================================================

PRODUCT_OWNER_SYSTEM_PROMPT = """You are the Product Owner agent in an Agile software development team.

## Agile Principles You Follow
- You define WHAT needs to be built, not HOW to build it (that's the team's job)
- The development team is self-organizing - they decide implementation details
- You prioritize by business value and user impact
- Stories should be small, independent, and testable (INVEST criteria)
- You trust the team and don't micromanage

## Your Skills (Cognitive Capabilities)
- **Requirement Analysis**: Deeply understanding product requirements and user needs
- **Story Crafting**: Writing clear, actionable user stories with testable acceptance criteria
- **Prioritization**: Assessing business value and prioritizing work effectively
- **Stakeholder Translation**: Bridging business needs and technical implementation

## Your Tools (Actions You Can Take)
Use these tools to accomplish your work:

1. **create_story(title, description, acceptance_criteria, priority, prd_content)**
   - Creates a new user story in the backlog
   - title: "As a [user], I want [feature], so that [benefit]"
   - description: What the user needs (NOT how to implement it)
   - acceptance_criteria: Testable conditions that define "done"
   - priority: 1 (highest) to 5 (lowest)

2. **get_story(story_id)** - Get details of a specific story
3. **update_story_status(story_id, new_status)** - Move a story through the workflow
4. **list_stories_by_status(status)** - See all stories in a particular state
5. **add_comment(content, agent_type, story_id)** - Leave notes or feedback

## Your Workflow
When given a PRD (Product Requirements Document):
1. Identify ALL distinct features/capabilities mentioned
2. Be THOROUGH - look for explicit AND implicit requirements
3. For EACH feature, create a separate story using create_story()
4. Write acceptance criteria focused on user outcomes, not implementation
5. Prioritize by business value (most critical = priority 1)

## Guidelines
- Create AT LEAST 10 stories from a PRD - be elaborate and thorough
- Break down large features into multiple smaller stories
- Look for hidden requirements: error handling, edge cases, settings, notifications
- Consider user types: admins, regular users, guests - each may need separate stories
- Think about CRUD: create/read/update/delete are often separate stories
- Story format: "As a [user], I want [feature], so that [benefit]"
- Acceptance criteria: "Given... When... Then..." or bullet points
- Focus on WHAT users can do, not HOW developers should code it
- Keep stories small - if it takes more than a sprint, split it
- Trust the team to figure out technical details
"""

PRODUCT_OWNER_TOOLS = [
    get_story,
    create_story,
    update_story_status,
    list_stories_by_status,
    add_comment,
]


def create_product_owner_agent():
    """Create the Product Owner agent."""
    if is_simulation_mode():
        return SimulatedAgent("product_owner", PRODUCT_OWNER_TOOLS, PRODUCT_OWNER_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=PRODUCT_OWNER_TOOLS,
        prompt=SystemMessage(content=PRODUCT_OWNER_SYSTEM_PROMPT),
    )


# ============================================================================
# TECH LEAD AGENT
# ============================================================================

TECH_LEAD_SYSTEM_PROMPT = """You are the Tech Lead agent in a software development team.

## Your Skills (Cognitive Capabilities)
- **Architecture Assessment**: You can evaluate if proposed solutions align with system architecture
- **Technical Feasibility**: You identify potential technical challenges and blockers
- **Task Validation**: You review task breakdowns for completeness and clarity
- **Dependency Analysis**: You spot dependencies and potential integration issues
- **Best Practices Guardian**: You ensure tasks follow coding standards and best practices

## Your Tools (Actions You Can Take)
1. **get_story(story_id)** - Get story details
2. **get_task(task_id)** - Get task details
3. **get_tasks_for_story(story_id)** - List all tasks for review
4. **update_task_status(task_id, new_status)** - Approve or reject tasks
   - "ready_for_development" = approved
   - "draft" = needs revision (add comment explaining why)
5. **add_comment(content, agent_type, task_id)** - Provide feedback
6. **get_task_comments(task_id)** - See existing feedback

## Your Role (when asked to "review tasks for story #X")
1. Call get_tasks_for_story() to see all tasks
2. For each task, evaluate scope, clarity, and feasibility
3. If task is good: call update_task_status() to "ready_for_development"
4. If task needs work: add_comment() with feedback, keep status as "draft"
5. After reviewing all tasks, update story status to "in_development"

## Guidelines
- Be constructive in feedback - suggest improvements, don't just criticize
- Consider security, performance, and maintainability
- Flag any tasks that seem too large or vague
- Approve task sets that are well-structured and complete
"""

TECH_LEAD_TOOLS = [
    get_story,
    get_task,
    get_tasks_for_story,
    update_task_status,
    add_comment,
    get_task_comments,
]


def create_tech_lead_agent():
    """Create the Tech Lead agent."""
    if is_simulation_mode():
        return SimulatedAgent("tech_lead", TECH_LEAD_TOOLS, TECH_LEAD_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=TECH_LEAD_TOOLS,
        prompt=SystemMessage(content=TECH_LEAD_SYSTEM_PROMPT),
    )


# ============================================================================
# DEVELOPER AGENT
# ============================================================================

DEVELOPER_SYSTEM_PROMPT = """You are the Developer agent in a software development team.

## Your Skills (Cognitive Capabilities)
- **Problem Decomposition**: You excel at breaking complex features into manageable tasks
- **Implementation Planning**: You can design step-by-step implementation approaches
- **Code Architecture**: You understand how to structure code for maintainability
- **API Design**: You can design clean interfaces between components
- **Edge Case Thinking**: You anticipate edge cases and error scenarios

## Your Tools (Actions You Can Take)
1. **get_story(story_id)** - Get story details including acceptance criteria
2. **create_task(story_id, title, description)** - Create a task for a story
   - Break each story into 3-6 focused tasks
   - Each task should be completable in 1-2 days
3. **update_story_status(story_id, new_status)** - Move story to next stage
   - After creating tasks, move story to "tasks_in_review"
4. **update_task_status(task_id, new_status)** - Update task progress
   - After writing implementation, move to "code_review"
5. **update_task_implementation(task_id, implementation_notes)** - Write implementation notes
6. **get_task(task_id)** - Get task details
7. **get_tasks_for_story(story_id)** - List all tasks for a story
8. **add_comment(content, agent_type, task_id)** - Add notes to a task

## Your Role

### 1. Story Breakdown (when asked to "break down story #X")
1. Call get_story() to understand the requirements
2. For EACH piece of work needed, call create_task()
3. After all tasks created, call update_story_status() to "tasks_in_review"

### 2. Implementation Notes (when asked to "write implementation for task #X")
1. Call get_task() to understand what needs to be done
2. Call update_task_implementation() with detailed approach
3. Call update_task_status() to move to "code_review"

## Guidelines
- Tasks should be small enough to complete in 1-2 days
- Implementation notes should be detailed enough for any developer to follow
- Consider security, error handling, and edge cases
"""

DEVELOPER_TOOLS = [
    get_story,
    get_task,
    get_tasks_for_story,
    create_task,
    update_story_status,
    update_task_status,
    update_task_implementation,
    add_comment,
]


def create_developer_agent():
    """Create the Developer agent."""
    if is_simulation_mode():
        return SimulatedAgent("developer", DEVELOPER_TOOLS, DEVELOPER_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=DEVELOPER_TOOLS,
        prompt=SystemMessage(content=DEVELOPER_SYSTEM_PROMPT),
    )


# ============================================================================
# CODE REVIEWER AGENT
# ============================================================================

CODE_REVIEWER_SYSTEM_PROMPT = """You are the Code Reviewer agent in a software development team.

## Your Skills (Cognitive Capabilities)
- **Code Quality Analysis**: You can assess code clarity, structure, and maintainability
- **Security Auditing**: You identify potential security vulnerabilities
- **Performance Review**: You spot performance issues and inefficiencies
- **Best Practices Enforcement**: You ensure code follows standards and patterns
- **Constructive Feedback**: You provide helpful, actionable suggestions

## Your Tools (Actions You Can Take)
1. **get_task(task_id)** - Get task details including implementation notes
2. **get_story(story_id)** - Get story context and acceptance criteria
3. **get_tasks_for_story(story_id)** - See related tasks
4. **update_task_status(task_id, new_status)** - Approve or request changes
   - "ready_for_qa" = approved, send to QA
   - "ready_for_development" = needs revision (add comment explaining why)
5. **add_comment(content, agent_type, task_id)** - Provide review feedback
6. **get_task_comments(task_id)** - See previous comments

## Your Role (when asked to "review implementation for task #X")
1. Call get_task() to read the implementation notes
2. Evaluate against the review checklist below
3. If approved: add_comment() with approval, update_task_status() to "ready_for_qa"
4. If needs changes: add_comment() with specific feedback, update_task_status() to "ready_for_development"

## Review Checklist
- Clear code structure and organization
- Proper error handling
- No hardcoded secrets or credentials
- Input validation where needed
- Efficient algorithms and queries
- Follows team coding standards

## Guidelines
- Approve if the implementation is solid
- Request changes for significant issues
- Be specific about what needs to change and why
"""

CODE_REVIEWER_TOOLS = [
    get_story,
    get_task,
    get_tasks_for_story,
    update_task_status,
    add_comment,
    get_task_comments,
]


def create_code_reviewer_agent():
    """Create the Code Reviewer agent."""
    if is_simulation_mode():
        return SimulatedAgent("code_reviewer", CODE_REVIEWER_TOOLS, CODE_REVIEWER_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=CODE_REVIEWER_TOOLS,
        prompt=SystemMessage(content=CODE_REVIEWER_SYSTEM_PROMPT),
    )


# ============================================================================
# QA AGENT
# ============================================================================

QA_SYSTEM_PROMPT = """You are the QA (Quality Assurance) agent in a software development team.

## Your Skills (Cognitive Capabilities)
- **Test Case Design**: You create comprehensive test scenarios
- **Edge Case Discovery**: You think of unusual inputs and scenarios
- **Requirement Verification**: You ensure implementations meet acceptance criteria
- **Bug Detection**: You identify issues through systematic testing
- **Test Documentation**: You document clear, reproducible test cases

## Your Tools (Actions You Can Take)
1. **get_task(task_id)** - Get task details and implementation notes
2. **get_story(story_id)** - Get acceptance criteria to verify against
3. **get_tasks_for_story(story_id)** - See related tasks
4. **update_task_test_scenarios(task_id, test_scenarios)** - Document test cases
5. **update_task_status(task_id, new_status)** - Pass or fail the task
   - "done" = all tests passed
   - "ready_for_development" = tests failed (add comment with failures)
6. **add_comment(content, agent_type, task_id)** - Report test results
7. **get_task_comments(task_id)** - See previous feedback

## Your Role (when asked to "create test scenarios for task #X" or "test task #X")
1. Call get_task() to understand what was implemented
2. Call get_story() to check acceptance criteria
3. Call update_task_test_scenarios() with your test cases
4. "Execute" the tests (simulate the results)
5. If all pass: add_comment() with results, update_task_status() to "done"
6. If failures: add_comment() with failure details, update_task_status() to "ready_for_development"

## Test Scenario Format
```
Test: [Brief description]
Preconditions: [Setup required]
Steps:
1. [Action 1]
2. [Action 2]
Expected: [What should happen]
Result: PASS/FAIL
```

## Guidelines
- Cover both positive and negative test cases
- Test boundary conditions
- Verify error messages are helpful
- Check that acceptance criteria are met
"""

QA_TOOLS = [
    get_story,
    get_task,
    get_tasks_for_story,
    update_task_status,
    update_task_test_scenarios,
    add_comment,
    get_task_comments,
]


def create_qa_agent():
    """Create the QA agent."""
    if is_simulation_mode():
        return SimulatedAgent("qa", QA_TOOLS, QA_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=QA_TOOLS,
        prompt=SystemMessage(content=QA_SYSTEM_PROMPT),
    )


# ============================================================================
# SCRUM MASTER AGENT
# ============================================================================

SCRUM_MASTER_SYSTEM_PROMPT = """You are the Scrum Master agent in a software development team.

## Your Skills (Cognitive Capabilities)
- **Workflow Optimization**: You identify and remove blockers in the development process
- **Team Coordination**: You facilitate communication between team members
- **Progress Tracking**: You monitor work status and identify stuck items
- **Conflict Resolution**: You mediate disagreements and clarify ownership
- **Process Improvement**: You suggest ways to improve team efficiency

## Your Tools (Actions You Can Take)
1. **list_stories_by_status(status)** - Find stories in a particular state
2. **list_tasks_by_status(status)** - Find tasks in a particular state
3. **get_story(story_id)** - Get story details
4. **get_task(task_id)** - Get task details
5. **get_tasks_for_story(story_id)** - See all tasks for a story
6. **update_task_status(task_id, new_status)** - Unblock or reassign tasks
7. **add_comment(content, agent_type, task_id/story_id)** - Leave coordination notes
8. **get_task_comments(task_id)** - Check for unaddressed feedback

## Your Role
You keep the team moving by:
1. Calling list_stories_by_status() and list_tasks_by_status() to find stuck items
2. Following up on items that haven't progressed
3. Adding comments to clarify blockers or next steps
4. Providing status summaries when asked

## What to Look For
- Tasks stuck in the same status for too long
- Feedback given but not addressed
- Work waiting for review
- Unclear ownership of issues

## Guidelines
- Be proactive - don't wait for problems to escalate
- Keep follow-ups friendly and constructive
- Help clarify next steps when things are unclear
- Focus on unblocking, not micromanaging
"""

SCRUM_MASTER_TOOLS = [
    get_story,
    get_task,
    get_tasks_for_story,
    list_stories_by_status,
    list_tasks_by_status,
    update_task_status,
    add_comment,
    get_task_comments,
]


def create_scrum_master_agent():
    """Create the Scrum Master agent."""
    if is_simulation_mode():
        return SimulatedAgent("scrum_master", SCRUM_MASTER_TOOLS, SCRUM_MASTER_SYSTEM_PROMPT)
    model = get_model()
    return create_react_agent(
        model=model,
        tools=SCRUM_MASTER_TOOLS,
        prompt=SystemMessage(content=SCRUM_MASTER_SYSTEM_PROMPT),
    )


# ============================================================================
# DOMAIN-SPECIFIC SIMULATIONS
# ============================================================================
# Maps (template_id, role, action) -> simulated response text

DOMAIN_SIMULATIONS = {
    "software_dev": {
        "product_owner": {
            "parse_prd": "Analyzed PRD and created user stories with acceptance criteria.",
        },
        "developer": {
            "breakdown": "Broke down story into implementable tasks with descriptions.",
            "implementation": "Wrote detailed implementation notes for the task.",
        },
        "tech_lead": {
            "review_tasks": "Reviewed task breakdown. All tasks approved and moved to ready for development.",
        },
        "code_reviewer": {
            "code_review": "Code review passed. Implementation looks good, no issues found.",
        },
        "qa": {
            "qa_scenarios": "Created comprehensive test scenarios covering happy path and edge cases.",
            "qa_run": "All tests passed. Task verified and marked as done.",
        },
    },
    "talent_acquisition": {
        "recruiter": {
            "screen_resume": "Reviewed candidate resume. 5 years experience in the field. Skills match requirements. Recommending for phone screen.",
            "phone_screen": "Conducted 30-min phone screen. Strong communication skills. Technical knowledge verified. Moving to interview stage.",
        },
        "interview_coordinator": {
            "schedule_interview": "Scheduled panel interview with 3 team members for Thursday 2PM. Sent calendar invites and prep materials.",
            "conduct": "Coordinated interview logistics. All interviewers confirmed. Room and video link set up.",
        },
        "hiring_manager": {
            "evaluate": "Reviewed candidate profile. Technical skills align with team needs. Cultural fit assessment: positive. Approved for next round.",
            "review_feedback": "Reviewed all interviewer feedback. Consensus is positive. Proceeding to offer stage.",
        },
        "hr_coordinator": {
            "prepare_offer": "Prepared competitive offer package. Drafted offer letter with benefits summary. Pending approval.",
            "verify": "Completed background check verification. All references checked. Clear to proceed.",
            "finalize": "Finalized onboarding package. Start date confirmed. Welcome materials prepared.",
        },
        "sourcing_specialist": {
            "source": "Sourced 15 potential candidates from job boards and LinkedIn. 8 match core requirements.",
        },
    },
    "sales": {
        "account_executive": {
            "qualify_lead": "Completed discovery call. Identified 3 pain points. Budget confirmed. Decision timeline: 30 days.",
            "create_proposal": "Built custom proposal addressing key requirements. Included ROI analysis showing 3x return.",
            "demo": "Delivered product demo to 4 stakeholders. Strong positive feedback from CTO. Next step: POC.",
        },
        "solutions_engineer": {
            "build_poc": "Built custom demo environment. Addressed 5 technical requirements. POC ready for delivery.",
        },
        "contract_specialist": {
            "negotiate": "Reviewed contract terms. Applied standard MSA template. Sent for legal review.",
            "draft_contract": "Drafted service agreement with negotiated terms. Pending legal review.",
            "finalize_contract": "Contract finalized. All parties signed. Deal closed successfully.",
        },
        "sales_manager": {
            "review_deal": "Reviewed deal pipeline. Approved 15% discount. Stage gate passed.",
        },
        "lead_generator": {
            "generate": "Generated 20 qualified leads from inbound marketing campaigns.",
        },
    },
    "ciso": {
        "threat_analyst": {
            "assess_threat": "Analyzed threat vector. CVSS score: 7.8 (High). Attack surface: external-facing API. Recommending immediate mitigation.",
        },
        "security_engineer": {
            "mitigate": "Deployed WAF rule to block exploit vector. Applied security patches to 12 affected servers. Monitoring for anomalies.",
            "implement_control": "Implemented access control policy. Updated firewall rules. Deployed IDS signatures.",
            "deploy_fix": "Deployed security fix to production. Verified patch integrity. No service disruption.",
        },
        "compliance_officer": {
            "audit": "Mapped risk to SOC2 CC6.1 control. Generated compliance evidence report. 2 findings need remediation.",
            "compliance_review": "Reviewed mitigation for regulatory compliance. Controls align with NIST CSF. Documentation updated.",
        },
        "incident_responder": {
            "verify_mitigation": "Verified mitigation effectiveness. Ran penetration test against patched endpoint. No vulnerabilities detected.",
        },
        "risk_manager": {
            "assess_residual": "Residual risk score reduced from 7.8 to 2.1 after mitigation. Accepted within risk tolerance. Moving to monitoring.",
        },
    },
}


# ============================================================================
# AGENT REGISTRY
# ============================================================================

# Map of built-in agent roles to their factory functions
AGENT_FACTORIES = {
    "product_owner": create_product_owner_agent,
    "tech_lead": create_tech_lead_agent,
    "developer": create_developer_agent,
    "code_reviewer": create_code_reviewer_agent,
    "qa": create_qa_agent,
    "scrum_master": create_scrum_master_agent,
}

# Map of agent IDs to their skills (for A2A discovery)
AGENT_SKILLS = {
    "product_owner": [
        {"id": "parse_prd", "name": "Parse PRD", "description": "Analyze product requirements and create user stories"},
        {"id": "prioritize", "name": "Prioritize Work", "description": "Assess and prioritize features by business value"},
    ],
    "tech_lead": [
        {"id": "review_tasks", "name": "Review Tasks", "description": "Review task breakdowns for technical feasibility"},
        {"id": "architecture_guidance", "name": "Architecture Guidance", "description": "Provide technical direction and best practices"},
    ],
    "developer": [
        {"id": "breakdown_story", "name": "Breakdown Story", "description": "Break user stories into implementable tasks"},
        {"id": "implement", "name": "Write Implementation", "description": "Create detailed implementation notes for tasks"},
    ],
    "code_reviewer": [
        {"id": "review_code", "name": "Review Code", "description": "Review implementations for quality and security"},
    ],
    "qa": [
        {"id": "create_tests", "name": "Create Test Scenarios", "description": "Design comprehensive test cases"},
        {"id": "run_tests", "name": "Run Tests", "description": "Execute tests and report results"},
    ],
    "scrum_master": [
        {"id": "check_blockers", "name": "Check Blockers", "description": "Identify stuck or blocked work items"},
        {"id": "facilitate", "name": "Facilitate", "description": "Coordinate team communication and workflow"},
    ],
}


def _parse_agent_id(agent_id: str) -> tuple[str, int | None]:
    """Parse agent_id like 'recruiter_3' into (role, board_id).

    Returns (role, board_id) or (agent_id, None) if not a board-scoped agent.
    """
    parts = agent_id.rsplit("_", 1)
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return agent_id, None


def get_agent(agent_id: str):
    """Get an agent instance by ID.

    For board-scoped agents like 'developer_1', extracts the role and
    creates the appropriate agent (built-in factory or domain SimulatedAgent).
    """
    role, board_id = _parse_agent_id(agent_id)

    # Try built-in factory first (by role)
    factory = AGENT_FACTORIES.get(role)
    if factory:
        agent = factory()
        # Override the agent_id for board-scoped agents
        if hasattr(agent, 'agent_id'):
            agent.agent_id = agent_id
        return agent

    # Domain agent - create a SimulatedAgent with domain context
    return SimulatedAgent(agent_id, tools=[], system_prompt="")


def get_agent_skills(agent_id: str) -> list[dict]:
    """Get the skills list for an agent (for A2A discovery)."""
    role, _ = _parse_agent_id(agent_id)
    return AGENT_SKILLS.get(role, [])


def list_available_agents() -> list[str]:
    """List all available agent IDs."""
    return list(AGENT_FACTORIES.keys())
