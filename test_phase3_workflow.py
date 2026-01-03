"""Test script for Phase 3: Composite Workflows functionality."""

import sys
import io
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from context_launcher.core.config import ConfigManager
from context_launcher.core.session import (
    Session, Workflow, WorkflowStep, LaunchConfiguration, SessionType
)
from context_launcher.core.workflow_executor import WorkflowExecutor, StepStatus
import uuid
from datetime import datetime


def test_workflow_creation_and_execution():
    """Test creating and executing a workflow."""
    print("=" * 60)
    print("Phase 3: Composite Workflows - Test")
    print("=" * 60)

    # Initialize config manager
    config_manager = ConfigManager()
    print(f"\n✓ Config manager initialized")
    print(f"  Data directory: {config_manager.data_dir}")
    print(f"  Workflows directory: {config_manager.workflows_dir}")

    # Create test sessions
    print("\n[1] Creating test sessions...")

    # Chrome session with Google
    chrome_session = Session(
        id=str(uuid.uuid4()),
        name="Test Browser Session",
        icon="🌐",
        description="Chrome with Google",
        tab_id="work",
        type=SessionType.SINGLE_APP,
        launch_config=LaunchConfiguration(
            app_type="browser",
            app_name="chrome",
            parameters={
                "tabs": [
                    {"type": "url", "url": "https://www.google.com"}
                ],
                "profile": ""
            }
        ),
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    # VS Code session (if available)
    vscode_session = Session(
        id=str(uuid.uuid4()),
        name="Test VS Code Session",
        icon="💻",
        description="Open VS Code workspace",
        tab_id="work",
        type=SessionType.SINGLE_APP,
        launch_config=LaunchConfiguration(
            app_type="editor",
            app_name="vscode",
            parameters={
                "workspace": str(Path(__file__).parent)
            }
        ),
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    # Save sessions
    config_manager.save_session(chrome_session.id, chrome_session.to_dict())
    config_manager.save_session(vscode_session.id, vscode_session.to_dict())

    print(f"  ✓ Created Chrome session: {chrome_session.id}")
    print(f"  ✓ Created VS Code session: {vscode_session.id}")

    # Create workflow
    print("\n[2] Creating test workflow...")

    workflow = Workflow(
        id=str(uuid.uuid4()),
        name="Test Workflow: Chrome + VS Code",
        icon="⚡",
        description="Launch Chrome first, then VS Code after 2 seconds",
        tab_id="work",
        type=SessionType.COMPOSITE_WORKFLOW,
        launch_sequence=[
            WorkflowStep(
                order=0,
                session_ref=chrome_session.id,
                delay_ms=2000,  # 2 second delay before next step
                continue_on_failure=True,
                description="Launch Chrome browser"
            ),
            WorkflowStep(
                order=1,
                session_ref=vscode_session.id,
                delay_ms=0,
                continue_on_failure=True,
                description="Launch VS Code"
            )
        ],
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    # Save workflow
    config_manager.save_workflow(workflow.id, workflow.to_dict())
    print(f"  ✓ Created workflow: {workflow.id}")
    print(f"  Name: {workflow.name}")
    print(f"  Steps: {len(workflow.launch_sequence)}")

    # Load and verify workflow
    print("\n[3] Loading and verifying workflow...")
    loaded_workflow = Workflow.from_dict(
        config_manager.load_workflow(workflow.id)
    )
    print(f"  ✓ Loaded workflow: {loaded_workflow.name}")
    print(f"  Steps:")
    for i, step in enumerate(loaded_workflow.launch_sequence):
        session = chrome_session if step.session_ref == chrome_session.id else vscode_session
        print(f"    {i + 1}. {step.description} (delay: {step.delay_ms}ms, "
              f"continue_on_failure: {step.continue_on_failure})")

    # Execute workflow
    print("\n[4] Executing workflow...")
    print("  This will launch Chrome and VS Code in sequence with a 2-second delay.")
    print("  Press Ctrl+C to skip execution test.\n")

    try:
        executor = WorkflowExecutor(config_manager)

        # Set up progress callback
        def progress_callback(step_result):
            status_icon = {
                StepStatus.SUCCESS: "✓",
                StepStatus.FAILED: "✗",
                StepStatus.SKIPPED: "⊘",
                StepStatus.RUNNING: "⏳"
            }.get(step_result.status, "?")

            print(f"  {status_icon} Step {step_result.step_index + 1}: "
                  f"{step_result.step.description} - {step_result.status.value} "
                  f"({step_result.elapsed_ms}ms)")

        executor.set_progress_callback(progress_callback)

        # Load sessions for workflow execution
        sessions = [chrome_session, vscode_session]

        # Execute
        result = executor.execute_workflow(loaded_workflow, sessions)

        print(f"\n[5] Workflow execution completed!")
        print(f"  Overall status: {result.status.value}")
        print(f"  Total time: {result.total_elapsed_ms}ms")
        print(f"  ✓ Successful steps: {result.successful_steps}")
        print(f"  ✗ Failed steps: {result.failed_steps}")
        print(f"  ⊘ Skipped steps: {result.skipped_steps}")

        # Show details of failed steps
        if result.failed_steps > 0:
            print("\n  Failed step details:")
            for step_result in result.step_results:
                if step_result.status == StepStatus.FAILED:
                    print(f"    - Step {step_result.step_index + 1}: {step_result.error_message}")

    except KeyboardInterrupt:
        print("\n  Workflow execution skipped by user.")

    # Test workflow persistence methods
    print("\n[6] Testing workflow persistence...")
    workflow_files = config_manager.list_workflows()
    print(f"  ✓ Found {len(workflow_files)} workflow(s)")

    for wf_file in workflow_files:
        wf_data = config_manager.load_workflow(wf_file.stem)
        print(f"    - {wf_data['name']} ({wf_file.stem})")

    # Cleanup option
    print("\n[7] Cleanup")
    print(f"  Test sessions and workflow saved to: {config_manager.data_dir}")
    print(f"  You can delete them manually or use the UI.")

    print("\n" + "=" * 60)
    print("Test completed successfully! ✓")
    print("=" * 60)


def test_workflow_error_handling():
    """Test workflow error handling with a failing step."""
    print("\n\n" + "=" * 60)
    print("Testing Workflow Error Handling")
    print("=" * 60)

    config_manager = ConfigManager()

    # Create a session that will fail (invalid executable)
    failing_session = Session(
        id=str(uuid.uuid4()),
        name="Test Failing Session",
        icon="❌",
        description="This session will fail",
        tab_id="work",
        type=SessionType.SINGLE_APP,
        launch_config=LaunchConfiguration(
            app_type="generic",
            app_name="generic",
            parameters={
                "executable_path": "C:\\NonExistent\\app.exe",
                "arguments": []
            }
        ),
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    # Create Chrome session (should succeed)
    chrome_session = Session(
        id=str(uuid.uuid4()),
        name="Chrome After Failure",
        icon="🌐",
        description="Chrome session",
        tab_id="work",
        type=SessionType.SINGLE_APP,
        launch_config=LaunchConfiguration(
            app_type="browser",
            app_name="chrome",
            parameters={
                "tabs": [{"type": "url", "url": "https://www.google.com"}],
                "profile": ""
            }
        ),
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    print("\n[1] Testing continue_on_failure=True...")

    workflow_continue = Workflow(
        id=str(uuid.uuid4()),
        name="Test Error Handling (Continue)",
        icon="⚡",
        description="Workflow with failing step but continue_on_failure=True",
        tab_id="work",
        type=SessionType.COMPOSITE_WORKFLOW,
        launch_sequence=[
            WorkflowStep(
                order=0,
                session_ref=failing_session.id,
                delay_ms=0,
                continue_on_failure=True,  # Continue despite failure
                description="This step will fail"
            ),
            WorkflowStep(
                order=1,
                session_ref=chrome_session.id,
                delay_ms=0,
                continue_on_failure=True,
                description="This step should execute anyway"
            )
        ],
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    executor = WorkflowExecutor(config_manager)
    sessions = [failing_session, chrome_session]

    result = executor.execute_workflow(workflow_continue, sessions)

    print(f"  Result: {result.status.value}")
    print(f"  Successful: {result.successful_steps}, Failed: {result.failed_steps}, "
          f"Skipped: {result.skipped_steps}")

    if result.failed_steps > 0 and result.successful_steps > 0:
        print("  ✓ Workflow continued after failure as expected")

    print("\n[2] Testing continue_on_failure=False...")

    workflow_stop = Workflow(
        id=str(uuid.uuid4()),
        name="Test Error Handling (Stop)",
        icon="⚡",
        description="Workflow with failing step and continue_on_failure=False",
        tab_id="work",
        type=SessionType.COMPOSITE_WORKFLOW,
        launch_sequence=[
            WorkflowStep(
                order=0,
                session_ref=failing_session.id,
                delay_ms=0,
                continue_on_failure=False,  # Stop on failure
                description="This step will fail and stop workflow"
            ),
            WorkflowStep(
                order=1,
                session_ref=chrome_session.id,
                delay_ms=0,
                continue_on_failure=True,
                description="This step should be skipped"
            )
        ],
        metadata={
            "category_id": "work",
            "tags": [],
            "favorite": False,
            "launch_count": 0,
            "last_launched": None
        }
    )

    result = executor.execute_workflow(workflow_stop, sessions)

    print(f"  Result: {result.status.value}")
    print(f"  Successful: {result.successful_steps}, Failed: {result.failed_steps}, "
          f"Skipped: {result.skipped_steps}")

    if result.skipped_steps > 0:
        print("  ✓ Workflow stopped after failure as expected")

    print("\n" + "=" * 60)
    print("Error handling test completed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_workflow_creation_and_execution()
        test_workflow_error_handling()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
