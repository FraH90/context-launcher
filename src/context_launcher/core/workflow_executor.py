"""Workflow executor for launching multiple applications in sequence."""

import sys
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .session import Workflow, WorkflowStep, Session
from ..launchers import LaunchConfig, AppType, LauncherFactory, LaunchResult
from ..utils.logger import get_logger


class StepStatus(str, Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStepResult:
    """Result of executing a single workflow step."""
    step_index: int
    step: WorkflowStep
    status: StepStatus
    launch_result: Optional[LaunchResult] = None
    error_message: Optional[str] = None
    elapsed_ms: int = 0


@dataclass
class WorkflowExecutionResult:
    """Result of executing an entire workflow."""
    workflow_id: str
    workflow_name: str
    status: StepStatus  # Overall status
    step_results: List[WorkflowStepResult]
    total_elapsed_ms: int
    successful_steps: int
    failed_steps: int
    skipped_steps: int


class WorkflowExecutor:
    """Executes workflows by launching applications in sequence."""

    def __init__(self, config_manager):
        """Initialize workflow executor.

        Args:
            config_manager: ConfigManager instance for loading sessions
        """
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable[[WorkflowStepResult], None]):
        """Set callback for progress updates.

        Args:
            callback: Function called after each step with WorkflowStepResult
        """
        self._progress_callback = callback

    def execute_workflow(
        self,
        workflow: Workflow,
        sessions: List[Session]
    ) -> WorkflowExecutionResult:
        """Execute a workflow by launching all steps in sequence.

        Args:
            workflow: Workflow to execute
            sessions: List of available sessions (for resolving session_ref)

        Returns:
            WorkflowExecutionResult with execution details
        """
        self.logger.info(f"Starting workflow execution: {workflow.name}")

        start_time = time.time()
        step_results: List[WorkflowStepResult] = []

        # Sort steps by order
        sorted_steps = sorted(workflow.launch_sequence, key=lambda s: s.order)

        for index, step in enumerate(sorted_steps):
            step_result = self._execute_step(step, index, sessions)
            step_results.append(step_result)

            # Call progress callback
            if self._progress_callback:
                self._progress_callback(step_result)

            # Check if we should stop on failure
            if step_result.status == StepStatus.FAILED and not step.continue_on_failure:
                self.logger.warning(f"Step {index} failed and continue_on_failure=False. Stopping workflow.")

                # Mark remaining steps as skipped
                for remaining_index in range(index + 1, len(sorted_steps)):
                    skipped_result = WorkflowStepResult(
                        step_index=remaining_index,
                        step=sorted_steps[remaining_index],
                        status=StepStatus.SKIPPED,
                        error_message="Skipped due to previous failure"
                    )
                    step_results.append(skipped_result)

                    if self._progress_callback:
                        self._progress_callback(skipped_result)

                break

            # Apply delay before next step (except for last step)
            if index < len(sorted_steps) - 1 and step.delay_ms > 0:
                self.logger.info(f"Waiting {step.delay_ms}ms before next step")
                time.sleep(step.delay_ms / 1000.0)

        # Calculate summary
        total_elapsed_ms = int((time.time() - start_time) * 1000)
        successful = sum(1 for r in step_results if r.status == StepStatus.SUCCESS)
        failed = sum(1 for r in step_results if r.status == StepStatus.FAILED)
        skipped = sum(1 for r in step_results if r.status == StepStatus.SKIPPED)

        # Determine overall status
        if failed > 0 and successful == 0:
            overall_status = StepStatus.FAILED
        elif failed > 0:
            overall_status = StepStatus.FAILED  # Partial failure
        else:
            overall_status = StepStatus.SUCCESS

        result = WorkflowExecutionResult(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            status=overall_status,
            step_results=step_results,
            total_elapsed_ms=total_elapsed_ms,
            successful_steps=successful,
            failed_steps=failed,
            skipped_steps=skipped
        )

        self.logger.info(
            f"Workflow '{workflow.name}' completed: "
            f"{successful} success, {failed} failed, {skipped} skipped "
            f"({total_elapsed_ms}ms)"
        )

        return result

    def _execute_step(
        self,
        step: WorkflowStep,
        index: int,
        sessions: List[Session]
    ) -> WorkflowStepResult:
        """Execute a single workflow step.

        Args:
            step: WorkflowStep to execute
            index: Step index
            sessions: Available sessions

        Returns:
            WorkflowStepResult
        """
        self.logger.info(f"Executing step {index}: {step.description or 'Unnamed step'}")

        start_time = time.time()

        try:
            # Resolve launch configuration
            launch_config = None

            if step.session_ref:
                # Find referenced session
                session = next((s for s in sessions if s.id == step.session_ref), None)
                if not session:
                    raise ValueError(f"Session reference not found: {step.session_ref}")

                launch_config = LaunchConfig(
                    app_type=AppType(session.launch_config.app_type),
                    app_name=session.launch_config.app_name,
                    parameters=session.launch_config.parameters,
                    platform=sys.platform
                )
                step_name = session.name

            elif step.inline_config:
                launch_config = LaunchConfig(
                    app_type=AppType(step.inline_config.app_type),
                    app_name=step.inline_config.app_name,
                    parameters=step.inline_config.parameters,
                    platform=sys.platform
                )
                step_name = step.inline_config.app_name

            else:
                raise ValueError("Step has neither session_ref nor inline_config")

            # Create launcher and launch
            launcher = LauncherFactory.create_launcher(launch_config)
            launch_result = launcher.launch()

            elapsed_ms = int((time.time() - start_time) * 1000)

            if launch_result.success:
                self.logger.info(f"Step {index} succeeded: {step_name}")
                return WorkflowStepResult(
                    step_index=index,
                    step=step,
                    status=StepStatus.SUCCESS,
                    launch_result=launch_result,
                    elapsed_ms=elapsed_ms
                )
            else:
                self.logger.error(f"Step {index} failed: {launch_result.message}")
                return WorkflowStepResult(
                    step_index=index,
                    step=step,
                    status=StepStatus.FAILED,
                    launch_result=launch_result,
                    error_message=launch_result.message,
                    elapsed_ms=elapsed_ms
                )

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"Step {index} failed with exception: {e}", exc_info=True)

            return WorkflowStepResult(
                step_index=index,
                step=step,
                status=StepStatus.FAILED,
                error_message=str(e),
                elapsed_ms=elapsed_ms
            )
