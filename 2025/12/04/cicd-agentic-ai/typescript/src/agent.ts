/** Agent implementation with versioning and tool management */

export enum AgentRole {
  PLANNER = "planner",
  WORKER = "worker",
  CRITIC = "critic",
  ROUTER = "router"
}

export interface ModelConfig {
  model: string;
  temperature: number;
  maxTokens?: number;
}

export interface AgentResult {
  success: boolean;
  result?: any;
  tools_called: string[];
  latency_ms: number;
  agent_version: string;
  error?: string;
}

export class Agent {
  role: AgentRole;
  modelConfig: ModelConfig;
  tools: string[];
  version: string;
  toolRegistry: Map<string, Function>;
  toolsCalled: string[];

  constructor(
    role: AgentRole,
    modelConfig: ModelConfig,
    tools: string[],
    version: string,
    toolRegistry?: Map<string, Function>
  ) {
    this.role = role;
    this.modelConfig = modelConfig;
    this.tools = tools;
    this.version = version;
    this.toolRegistry = toolRegistry || new Map();
    this.toolsCalled = [];
  }

  async run(inputData: Record<string, any>): Promise<AgentResult> {
    const startTime = Date.now();

    try {
      const result = await this.execute(inputData);
      const latencyMs = Date.now() - startTime;

      return {
        success: true,
        result,
        tools_called: this.toolsCalled,
        latency_ms: latencyMs,
        agent_version: this.version
      };
    } catch (error: any) {
      const latencyMs = Date.now() - startTime;
      return {
        success: false,
        error: error.message,
        tools_called: this.toolsCalled,
        latency_ms: latencyMs,
        agent_version: this.version
      };
    }
  }

  private async execute(inputData: Record<string, any>): Promise<any> {
    switch (this.role) {
      case AgentRole.PLANNER:
        return this.plan(inputData);
      case AgentRole.WORKER:
        return this.work(inputData);
      case AgentRole.CRITIC:
        return this.critique(inputData);
      default:
        return { status: "unknown_role" };
    }
  }

  private plan(inputData: Record<string, any>): any {
    const plan: any = {
      steps: [],
      tools_needed: []
    };

    const input = inputData.input || "";
    if (input.toLowerCase().includes("reset password")) {
      plan.steps = ["search_kb", "create_ticket"];
      plan.tools_needed = ["search_kb", "create_ticket"];
    }

    for (const tool of plan.tools_needed) {
      if (this.tools.includes(tool)) {
        this.toolsCalled.push(tool);
      }
    }

    return { plan };
  }

  private async work(inputData: Record<string, any>): Promise<any> {
    const toolsToCall = inputData.tools || [];
    const results: Record<string, any> = {};

    for (const tool of toolsToCall) {
      if (this.tools.includes(tool) && this.toolRegistry.has(tool)) {
        try {
          const toolFn = this.toolRegistry.get(tool)!;
          const result = await toolFn(inputData);
          results[tool] = result;
          this.toolsCalled.push(tool);
        } catch (error: any) {
          results[tool] = { error: error.message };
        }
      }
    }

    return { results };
  }

  private critique(inputData: Record<string, any>): any {
    return {
      critique: "Work looks good",
      suggestions: []
    };
  }
}

