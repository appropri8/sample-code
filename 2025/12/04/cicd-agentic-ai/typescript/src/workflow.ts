/** Workflow implementation with versioning and state management */
import { Agent } from "./agent";

export interface WorkflowNode {
  name: string;
  agent: Agent;
  condition?: (state: Record<string, any>) => boolean;
}

export interface WorkflowConfig {
  name: string;
  nodes: Array<{ name: string; agent: any }>;
  edges: Array<[string, string]>;
  version: string;
}

export class Workflow {
  name: string;
  nodes: WorkflowNode[];
  edges: Array<[string, string]>;
  version: string;
  nodeMap: Map<string, WorkflowNode>;

  constructor(
    name: string,
    nodes: WorkflowNode[],
    edges: Array<[string, string]>,
    version: string
  ) {
    this.name = name;
    this.nodes = nodes;
    this.edges = edges;
    this.version = version;
    this.nodeMap = new Map();
    nodes.forEach(node => this.nodeMap.set(node.name, node));
  }

  async execute(initialState: Record<string, any>): Promise<Record<string, any>> {
    const currentState = { ...initialState };
    currentState.workflow_version = this.version;
    currentState.trace_id = currentState.trace_id || `trace_${Date.now()}`;

    if (this.nodes.length === 0) {
      return currentState;
    }

    let currentNode = this.nodes[0];
    const executionPath: string[] = [];

    while (currentNode) {
      executionPath.push(currentNode.name);

      if (currentNode.condition && !currentNode.condition(currentState)) {
        break;
      }

      try {
        const result = await currentNode.agent.run(currentState);
        Object.assign(currentState, result.result || {});
        currentState.last_node = currentNode.name;
        currentState.last_result = result;
      } catch (error: any) {
        currentState.error = error.message;
        break;
      }

      const nextNode = this.getNextNode(currentNode, currentState);
      if (!nextNode) {
        break;
      }
      currentNode = nextNode;
    }

    currentState.execution_path = executionPath;
    return currentState;
  }

  private getNextNode(
    currentNode: WorkflowNode,
    state: Record<string, any>
  ): WorkflowNode | null {
    for (const edge of this.edges) {
      if (edge[0] === currentNode.name) {
        const nextName = edge[1];
        const nextNode = this.nodeMap.get(nextName);
        if (nextNode) {
          return nextNode;
        }
      }
    }
    return null;
  }
}

