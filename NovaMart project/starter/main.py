import sys
import os

from mcp.server.fastmcp import FastMCP

# Make the project root and src/ importable.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from agent_orchestrator import (
    build_inventory_agent,
    build_refund_agent,
    build_policy_agent,
    build_communication_agent,
    build_orchestrator_agent,
)

# Build the NovaMart multi-agent graph once when the runtime starts.
inventory_agent = build_inventory_agent()
refund_agent = build_refund_agent()
policy_agent = build_policy_agent()
communication_agent = build_communication_agent()

orchestrator = build_orchestrator_agent(
    inventory_agent,
    refund_agent,
    policy_agent,
    communication_agent,
)

mcp = FastMCP(
    name="NovaMart Customer Support",
    host="0.0.0.0",
    port=8000,
    streamable_http_path="/mcp",
    stateless_http=True,
)


@mcp.tool()
def customer_support(
    customer_id: str,
    session_id: str,
    message: str,
) -> str:
    """
    Process a NovaMart customer-support request using the multi-agent
    orchestrator.

    Args:
        customer_id: NovaMart customer ID, for example CUST-001.
        session_id: Session identifier used for workflow state and memory.
        message: The customer's support question or request.
    """
    prompt = (
        f"[Session ID: {session_id}] "
        f"[Customer ID: {customer_id}] "
        f"{message}"
    )

    response = orchestrator(prompt)

    # The communication agent stores the final customer-facing response
    # in workflow state. Prefer that response when available.
    try:
        from agent_orchestrator import _read_workflow_state, _strip_xml_tags

        final_state = _read_workflow_state(session_id) or {}
        communication_result = final_state.get("communication_agent", "")

        if communication_result:
            return _strip_xml_tags(str(communication_result))

    except Exception:
        pass

    return str(response)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
