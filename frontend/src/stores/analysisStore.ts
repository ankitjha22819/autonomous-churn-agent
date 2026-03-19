
// Analysis Store - Zustand State Management


import { create } from "zustand";
import type {
  ReportReadyData,
  AgentActivityData,
  ThinkingData,
  ToolUsageData,
  JobProgressData,
  JobErrorData,
} from "@/types/api";


// Types (matching component interfaces)


export type StreamStatus = "idle" | "streaming" | "done" | "error";
export type EventType = "thinking" | "tool_call" | "insight" | "action" | "final";

export interface FeedEvent {
  id: string;
  type: EventType;
  agent?: string;
  message: string;
  risk?: "high" | "medium" | "low";
  priority?: number;
}

export interface RiskSignal {
  label: string;
  active: boolean;
}

export interface FinalPayload {
  risk_score: number;
  previous_risk_score: number;
  days_to_renewal: number;
  signals: RiskSignal[];
  summary: string;
  actions: {
    priority: number;
    action: string;
    owner: string;
    effort: string;
    deadline: string;
    impact: string;
  }[];
  client: {
    contact_name: string;
    contact_title: string;
    company: string;
    csm_name: string;
    csm_title: string;
  };
  email_draft: string;
}


// Store Interface


interface AnalysisState {
  // Job state
  jobId: string | null;
  status: StreamStatus;
  progress: number;
  error: string | null;

  // Feed events
  feedEvents: FeedEvent[];

  // Final report
  finalPayload: FinalPayload | null;

  // Actions
  setJobId: (jobId: string) => void;
  setStatus: (status: StreamStatus) => void;
  setProgress: (progress: number) => void;
  setError: (error: string | null) => void;
  addFeedEvent: (event: FeedEvent) => void;
  setFinalPayload: (payload: FinalPayload) => void;
  reset: () => void;

  // Event handlers (called by SSE hook)
  handleAgentActivity: (data: AgentActivityData) => void;
  handleThinking: (data: ThinkingData) => void;
  handleToolUsage: (data: ToolUsageData) => void;
  handleReportReady: (data: ReportReadyData) => void;
  handleJobProgress: (data: JobProgressData) => void;
  handleJobComplete: () => void;
  handleJobError: (data: JobErrorData) => void;
}

// Event ID counter
let eventIdCounter = 0;
function generateEventId(): string {
  return `evt-${++eventIdCounter}-${Date.now()}`;
}


// Transform backend ReportReadyData to frontend FinalPayload


function transformReportToPayload(data: ReportReadyData): FinalPayload {
  // Extract signals from insights
  const signals: RiskSignal[] = data.insights.slice(0, 6).map((insight, idx) => ({
    label: insight,
    active: idx < Math.ceil(data.insights.length / 2), // First half are active
  }));

  // Pad to 6 signals if needed
  while (signals.length < 6) {
    signals.push({ label: "No additional signals detected", active: false });
  }

  // Transform recommended actions
  const actions = data.recommended_actions.slice(0, 4).map((action, idx) => ({
    priority: idx + 1,
    action: action,
    owner: idx < 2 ? "CSM" : "AE",
    effort: idx === 0 ? "Low" : idx === 1 ? "Medium" : "High",
    deadline: idx === 0 ? "Within 7 days" : idx === 1 ? "Within 5 days" : "Before renewal",
    impact: `Priority ${idx + 1} action based on risk analysis`,
  }));

  // Get top prediction for client info (or use defaults)
  const topPrediction = data.predictions[0];
  const clientCompany = topPrediction?.customer_id || "Customer";

  return {
    risk_score: Math.round(data.risk_score),
    previous_risk_score: Math.max(0, Math.round(data.risk_score) - 15), // Simulate previous
    days_to_renewal: 34, // Default, could be extracted from customer data
    signals,
    summary: data.summary,
    actions,
    client: {
      contact_name: "Contact Name",
      contact_title: "Head of Operations",
      company: clientCompany,
      csm_name: "Your CSM",
      csm_title: "Customer Success Manager",
    },
    email_draft: generateEmailDraft(data, clientCompany),
  };
}

function generateEmailDraft(data: ReportReadyData, company: string): string {
  return `Hi there,

I was reviewing ${company}'s account this week and wanted to reach out personally.

${data.summary}

I'd love to jump on a quick call to:
  → Review your current setup and usage patterns
  → Share some insights from our analysis
  → Ensure you're getting maximum value from our platform

Would later this week work for a 20-minute call?

Best regards,
Your Customer Success Team`;
}


// Store


export const useAnalysisStore = create<AnalysisState>((set, get) => ({
  // Initial state
  jobId: null,
  status: "idle",
  progress: 0,
  error: null,
  feedEvents: [],
  finalPayload: null,

  // Basic setters
  setJobId: (jobId) => set({ jobId }),
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  setError: (error) => set({ error, status: "error" }),

  addFeedEvent: (event) =>
    set((state) => ({
      feedEvents: [...state.feedEvents, event],
    })),

  setFinalPayload: (payload) => set({ finalPayload: payload }),

  reset: () => {
    eventIdCounter = 0;
    set({
      jobId: null,
      status: "idle",
      progress: 0,
      error: null,
      feedEvents: [],
      finalPayload: null,
    });
  },

  
  // SSE Event Handlers
  

  handleAgentActivity: (data) => {
    const { addFeedEvent } = get();

    // Map agent names to match frontend expectations
    const agentNameMap: Record<string, string> = {
      "Data Analyst": "Data Analyst",
      "Senior Customer Data Analyst": "Data Analyst",
      "Risk Assessor": "Data Analyst",
      "Churn Risk Assessment Specialist": "Data Analyst",
      "Strategy Expert": "Retention Strategist",
      "Customer Retention Strategy Expert": "Retention Strategist",
      "Report Compiler": "Playbook Writer",
      "Executive Report Compiler": "Playbook Writer",
    };

    const displayAgent = agentNameMap[data.agent] || data.agent;

    // Map status to event type
    const eventType: EventType = data.status === "thinking" ? "thinking" : "tool_call";

    addFeedEvent({
      id: generateEventId(),
      type: eventType,
      agent: displayAgent,
      message: data.message,
    });
  },

  handleThinking: (data) => {
    const { addFeedEvent } = get();

    const agentNameMap: Record<string, string> = {
      "Data Analyst": "Data Analyst",
      "Senior Customer Data Analyst": "Data Analyst",
      "Risk Assessor": "Data Analyst",
      "Churn Risk Assessment Specialist": "Data Analyst",
      "Strategy Expert": "Retention Strategist",
      "Customer Retention Strategy Expert": "Retention Strategist",
      "Report Compiler": "Playbook Writer",
      "Executive Report Compiler": "Playbook Writer",
    };

    const displayAgent = agentNameMap[data.agent] || data.agent;

    addFeedEvent({
      id: generateEventId(),
      type: "thinking",
      agent: displayAgent,
      message: data.thought,
    });
  },

  handleToolUsage: (data) => {
    const { addFeedEvent } = get();

    const agentNameMap: Record<string, string> = {
      "Data Analyst": "Data Analyst",
      "Senior Customer Data Analyst": "Data Analyst",
      "Risk Assessor": "Data Analyst",
      "Churn Risk Assessment Specialist": "Data Analyst",
      "Strategy Expert": "Retention Strategist",
      "Customer Retention Strategy Expert": "Retention Strategist",
      "Report Compiler": "Playbook Writer",
      "Executive Report Compiler": "Playbook Writer",
    };

    const displayAgent = agentNameMap[data.agent] || data.agent;

    // Tool name to friendly name mapping
    const toolNameMap: Record<string, string> = {
      "customer_data_fetcher": "Fetching customer data",
      "engagement_analyzer": "Analyzing engagement patterns",
      "churn_score_calculator": "Calculating churn risk score",
      "risk_segmenter": "Segmenting risk levels",
      "insight_generator": "Generating insights",
      "recommendation_generator": "Generating recommendations",
    };

    // Only show tool start events (not completion)
    if (data.status === "started") {
      addFeedEvent({
        id: generateEventId(),
        type: "tool_call",
        agent: displayAgent,
        message: toolNameMap[data.tool_name] || `Using ${data.tool_name}`,
      });
    }

    // Show tool result as insight if available
    if (data.status === "completed" && data.result) {
      const result = data.result as Record<string, unknown>;
      if (result.churn_score !== undefined) {
        const score = result.churn_score as number;
        const riskLevel = score >= 70 ? "high" : score >= 40 ? "medium" : "low";

        addFeedEvent({
          id: generateEventId(),
          type: "insight",
          agent: displayAgent,
          message: `Churn risk score: ${Math.round(score)} / 100`,
          risk: riskLevel,
        });
      }
    }
  },

  handleReportReady: (data) => {
    const { addFeedEvent, setFinalPayload } = get();

    // Add insights as feed events
    data.insights.slice(0, 4).forEach((insight, idx) => {
      const risk = idx < 2 ? "high" : idx < 3 ? "medium" : "low";
      addFeedEvent({
        id: generateEventId(),
        type: "insight",
        agent: "Data Analyst",
        message: insight,
        risk: risk as "high" | "medium" | "low",
      });
    });

    // Add actions as feed events
    data.recommended_actions.slice(0, 3).forEach((action, idx) => {
      addFeedEvent({
        id: generateEventId(),
        type: "action",
        agent: "Playbook Writer",
        message: action,
        priority: idx + 1,
      });
    });

    // Transform and set final payload
    const payload = transformReportToPayload(data);
    setFinalPayload(payload);
  },

  handleJobProgress: (data) => {
    set({ progress: data.percentage });
  },

  handleJobComplete: () => {
    set({ status: "done", progress: 100 });
  },

  handleJobError: (data) => {
    set({
      status: "error",
      error: data.detail,
    });
  },
}));


// Selectors


export const selectIsLoading = (state: AnalysisState) => state.status === "streaming";
export const selectIsComplete = (state: AnalysisState) => state.status === "done";
export const selectHasError = (state: AnalysisState) => state.status === "error";