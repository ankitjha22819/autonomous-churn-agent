
// API Types - Mirrors backend Pydantic schemas


// Enums
export type CustomerSegment = "enterprise" | "mid_market" | "smb" | "startup" | "individual";
export type SubscriptionTier = "free" | "basic" | "pro" | "enterprise";
export type RiskLevel = "low" | "medium" | "high" | "critical";
export type JobStatus = "pending" | "queued" | "running" | "completed" | "failed" | "cancelled";


// Customer Data


export interface CustomerRow {
  customer_id: string;
  company_name?: string | null;
  email?: string | null;
  segment?: CustomerSegment;
  subscription_tier?: SubscriptionTier;
  mrr: number;
  days_since_last_login: number;
  login_count_30d: number;
  feature_adoption_score: number;
  support_tickets_30d: number;
  nps_score?: number | null;
  contract_start_date?: string | null;
  contract_end_date?: string | null;
  months_as_customer: number;
  previous_churn_flag?: boolean;
  expansion_revenue_30d?: number;
  contraction_revenue_30d?: number;
  metadata?: Record<string, unknown>;
}


// Analysis Request/Response


export interface AnalysisConfig {
  include_recommendations?: boolean;
  include_insights?: boolean;
  include_individual_predictions?: boolean;
  high_risk_threshold?: number;
  critical_risk_threshold?: number;
  focus_segments?: CustomerSegment[] | null;
  focus_tiers?: SubscriptionTier[] | null;
  max_recommendations?: number;
  max_insights?: number;
}

export interface AnalysisRequest {
  customers?: CustomerRow[] | null;
  data_source_id?: string | null;
  config?: AnalysisConfig;
  requested_by?: string | null;
  callback_url?: string | null;
  tags?: string[];
}

export interface JobCreatedResponse {
  job_id: string;
  status: JobStatus;
  events_url: string;
  created_at: string;
  estimated_duration_seconds?: number | null;
}

export interface JobStatusResponse {
  job_id: string;
  status: JobStatus;
  progress?: number | null;
  current_step?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
}


// SSE Event Types (Discriminator Pattern)


export type AgentStatus = "thinking" | "executing" | "completed" | "error";
export type ToolStatus = "started" | "completed" | "error";

export interface AgentActivityData {
  agent: string;
  message: string;
  status: AgentStatus;
  progress?: number | null;
  metadata?: Record<string, unknown> | null;
}

export interface ThinkingData {
  agent: string;
  thought: string;
  step: number;
  total_steps?: number | null;
}

export interface ToolUsageData {
  agent: string;
  tool_name: string;
  tool_input?: Record<string, unknown>;
  status: ToolStatus;
  result?: unknown | null;
  error?: string | null;
  duration_ms?: number | null;
}

export interface ChurnPrediction {
  customer_id: string;
  risk_score: number;
  risk_level: RiskLevel;
  confidence: number;
  top_factors: string[];
}

export interface ReportReadyData {
  summary: string;
  risk_score: number;
  total_analyzed: number;
  high_risk_count: number;
  predictions: ChurnPrediction[];
  recommended_actions: string[];
  insights: string[];
  generated_at: string;
}

export interface JobProgressData {
  current_step: number;
  total_steps: number;
  step_name: string;
  percentage: number;
}

export interface JobCompleteData {
  status: "success" | "partial";
  message: string;
  duration_seconds?: number | null;
}

export interface JobErrorData {
  error_code: string;
  detail: string;
  recoverable: boolean;
  retry_after_seconds?: number | null;
}

// Union type for all SSE events
export type SSEEventType = 
  | "connected"
  | "agent_activity"
  | "thinking"
  | "tool_usage"
  | "report_ready"
  | "job_progress"
  | "job_complete"
  | "job_error";

export interface SSEEvent<T = unknown> {
  event: SSEEventType;
  data: T;
  id?: string;
}