"""
Omnix V5 - Planning Subsystem

This package provides the command understanding and planning layer
for Omnix.

Main flow:

    Command
        ↓
    Intent Classification
        ↓
    Target Resolution
        ↓
    Execution Context
        ↓
    Task Planning
        ↓
    Task Plan

The planning subsystem does not directly execute tasks.

Execution is handled by higher-level systems such as:

    - Agent subsystem
    - Skills subsystem
    - System automation
    - Vision
    - Legacy compatibility adapters
"""

# ============================================================================
# COMMAND SCHEMA
# ============================================================================

from .command_schema import (
    Command,
    CommandStatus,
    CommandType,
    create_command,
)

# ============================================================================
# INTENT CLASSIFICATION
# ============================================================================

from .intent_classifier import (
    IntentResult,
    IntentRule,
    IntentClassifier,
    get_intent_classifier,
    reset_intent_classifier,
    classify_intent,
)

# ============================================================================
# TARGET RESOLUTION
# ============================================================================

from .target_resolver import (
    ResolvedTarget,
    TargetResolver,
    get_target_resolver,
    reset_target_resolver,
)

# ============================================================================
# EXECUTION CONTEXT
# ============================================================================

from .execution_context import (
    ExecutionContext,
    ExecutionState,
    create_execution_context,
)

# ============================================================================
# TASK PLANNING
# ============================================================================

from .task_planner import (
    TaskPlan,
    TaskPlanner,
    get_task_planner,
    reset_task_planner,
)

# ============================================================================
# COMMAND PROCESSING
# ============================================================================

from .command_processor import (
    CommandProcessingResult,
    CommandProcessor,
    get_command_processor,
    reset_command_processor,
    process_command,
)

# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # ------------------------------------------------------------------
    # Command Schema
    # ------------------------------------------------------------------
    "Command",
    "CommandStatus",
    "CommandType",
    "create_command",
    # ------------------------------------------------------------------
    # Intent Classification
    # ------------------------------------------------------------------
    "IntentResult",
    "IntentRule",
    "IntentClassifier",
    "get_intent_classifier",
    "reset_intent_classifier",
    "classify_intent",
    # ------------------------------------------------------------------
    # Target Resolution
    # ------------------------------------------------------------------
    "ResolvedTarget",
    "TargetResolver",
    "get_target_resolver",
    "reset_target_resolver",
    # ------------------------------------------------------------------
    # Execution Context
    # ------------------------------------------------------------------
    "ExecutionContext",
    "ExecutionState",
    "create_execution_context",
    # ------------------------------------------------------------------
    # Task Planning
    # ------------------------------------------------------------------
    "TaskPlan",
    "TaskPlanner",
    "get_task_planner",
    "reset_task_planner",
    # ------------------------------------------------------------------
    # Command Processing
    # ------------------------------------------------------------------
    "CommandProcessingResult",
    "CommandProcessor",
    "get_command_processor",
    "reset_command_processor",
    "process_command",
]
