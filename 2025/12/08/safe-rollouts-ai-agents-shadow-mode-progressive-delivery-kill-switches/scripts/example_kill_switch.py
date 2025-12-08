"""Example: Using kill switches for instant rollback."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.kill_switch import KillSwitch
from src.agent_factory import create_agent


def main():
    """Run kill switch example."""
    print("=== Kill Switch Example ===\n")
    
    # Create kill switch
    kill_switch = KillSwitch("kill_switches.json")
    
    # Check if version is killed
    agent_name = "support-agent"
    version = "v1.3.3"
    
    is_killed = kill_switch.is_killed(agent_name, version)
    print(f"Version {version} killed: {is_killed}")
    
    # Simulate processing a request
    print("\n=== Processing Request ===")
    if kill_switch.is_killed(agent_name, version):
        print(f"Version {version} is killed. Using previous version.")
        actual_version = "v1.3.2"
    else:
        print(f"Version {version} is active. Using it.")
        actual_version = version
    
    agent = create_agent(agent_name, actual_version)
    response = agent.process("Search for user john@example.com")
    print(f"Response from {actual_version}: {response['response']}")
    
    # Kill the version
    print("\n=== Killing Version ===")
    kill_switch.kill_version(
        agent_name=agent_name,
        version=version,
        reason="High error rate detected"
    )
    print(f"Killed version {version}")
    
    # Check again
    is_killed = kill_switch.is_killed(agent_name, version)
    print(f"Version {version} killed: {is_killed}")
    
    # Process another request
    print("\n=== Processing Request After Kill ===")
    if kill_switch.is_killed(agent_name, version):
        print(f"Version {version} is killed. Using previous version.")
        actual_version = "v1.3.2"
    else:
        actual_version = version
    
    agent = create_agent(agent_name, actual_version)
    response = agent.process("Search for user jane@example.com")
    print(f"Response from {actual_version}: {response['response']}")
    
    # Unkill the version
    print("\n=== Unkilling Version ===")
    kill_switch.unkill_version(agent_name, version)
    print(f"Unkilled version {version}")
    
    is_killed = kill_switch.is_killed(agent_name, version)
    print(f"Version {version} killed: {is_killed}")
    
    print("\n=== Kill switch example complete ===")


if __name__ == "__main__":
    main()
