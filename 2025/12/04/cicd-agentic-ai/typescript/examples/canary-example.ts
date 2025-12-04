/** Example: Canary deployment */
import { Agent, AgentRole } from "../src/agent";
import { Workflow, WorkflowNode } from "../src/workflow";
import { CanaryDeployment } from "../src/deployment/canary";

function createBaselineWorkflow(): Workflow {
  const planner = new Agent(
    AgentRole.PLANNER,
    { model: "gpt-4", temperature: 0.7 },
    ["search_kb", "create_ticket"],
    "1.2.0"
  );

  const worker = new Agent(
    AgentRole.WORKER,
    { model: "gpt-4", temperature: 0.7 },
    ["search_kb", "create_ticket"],
    "1.2.0"
  );

  const nodes = [
    new WorkflowNode("planner", planner),
    new WorkflowNode("worker", worker)
  ];

  const edges: Array<[string, string]> = [["planner", "worker"]];

  return new Workflow("support", nodes, edges, "1.2.0");
}

function createCandidateWorkflow(): Workflow {
  const planner = new Agent(
    AgentRole.PLANNER,
    { model: "gpt-4", temperature: 0.5 },
    ["search_kb", "create_ticket", "escalate"],
    "1.3.0"
  );

  const worker = new Agent(
    AgentRole.WORKER,
    { model: "gpt-4", temperature: 0.5 },
    ["search_kb", "create_ticket", "escalate"],
    "1.3.0"
  );

  const nodes = [
    new WorkflowNode("planner", planner),
    new WorkflowNode("worker", worker)
  ];

  const edges: Array<[string, string]> = [["planner", "worker"]];

  return new Workflow("support", nodes, edges, "1.3.0");
}

async function main() {
  const baseline = createBaselineWorkflow();
  const candidate = createCandidateWorkflow();

  const canary = new CanaryDeployment(
    baseline,
    candidate,
    0.1, // 10% for demo
    {
      error_rate_threshold: 0.05,
      latency_threshold_ms: 10000,
      cost_threshold_multiplier: 2.0
    }
  );

  console.log("Simulating 100 requests...");
  for (let i = 0; i < 100; i++) {
    const testInput = {
      input: `Request ${i}: User needs help`,
      trace_id: `trace_${i}`
    };

    await canary.route(testInput);

    if (i % 20 === 0) {
      const metrics = canary.getMetrics();
      console.log(`\nAfter ${i} requests:`);
      console.log(`Canary requests: ${metrics.canary.requests}`);
      console.log(`Baseline requests: ${metrics.baseline.requests}`);
      console.log(`Rolled back: ${metrics.rolled_back}`);
    }
  }

  const metrics = canary.getMetrics();
  console.log("\n=== Final Metrics ===");
  console.log(`Canary:`, metrics.canary);
  console.log(`Baseline:`, metrics.baseline);
  console.log(`Rolled back: ${metrics.rolled_back}`);
}

main().catch(console.error);

