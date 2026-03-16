"use client";

import { useState, useRef } from "react";
import ExcelUpload from "../components/ExcelUpload";
import AgentActivity, { FeedEvent, StreamStatus } from "../components/AgentActivity";
import RetentionPlaybook, { FinalPayload } from "../components/RetentionPlaybook";

type JsonRow = Record<string, string | number | boolean | null>;

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------
const MOCK_EVENTS: Omit<FeedEvent, "id">[] = [
  { type: "thinking",  agent: "Data Analyst",         message: "Reviewing account timeline and CRM history…" },
  { type: "tool_call", agent: "Data Analyst",         message: "Fetching product usage data" },
  { type: "thinking",  agent: "Data Analyst",         message: "Checking login frequency over last 90 days…" },
  { type: "insight",   agent: "Data Analyst",         message: "3 of 5 power users inactive for 14+ days", risk: "high" },
  { type: "tool_call", agent: "Data Analyst",         message: "Querying support ticket volume" },
  { type: "insight",   agent: "Data Analyst",         message: "Support tickets are 3× account baseline this quarter", risk: "high" },
  { type: "insight",   agent: "Data Analyst",         message: "Churn risk score: 82 / 100 — 4 of 6 signals active", risk: "high" },
  { type: "thinking",  agent: "Retention Strategist", message: "Reviewing last 12 months of CSM activity…" },
  { type: "insight",   agent: "Retention Strategist", message: "47 days since last CSM contact — 2.3× above threshold", risk: "medium" },
  { type: "tool_call", agent: "Retention Strategist", message: "Querying retention playbook knowledge base" },
  { type: "insight",   agent: "Retention Strategist", message: "EBR + re-activation saved 3 comparable accounts in Q3", risk: "low" },
  { type: "thinking",  agent: "Playbook Writer",      message: "Drafting retention playbook and outreach email…" },
  { type: "action",    agent: "Playbook Writer",      message: "Schedule executive business review within 7 days", priority: 1 },
  { type: "action",    agent: "Playbook Writer",      message: "Re-activate 3 dormant power users with onboarding session", priority: 2 },
  { type: "action",    agent: "Playbook Writer",      message: "Send personalised outreach email today", priority: 3 },
];

const MOCK_FINAL: FinalPayload = {
  risk_score: 82,
  previous_risk_score: 54,
  days_to_renewal: 34,

  signals: [
    { label: "Power user drop-off (3 of 5 inactive 14+ days)",   active: true  },
    { label: "Support ticket spike (3× account baseline)",        active: true  },
    { label: "No CSM contact in 47 days (threshold: 21)",         active: true  },
    { label: "Feature adoption regression (–41% last 30 days)",   active: true  },
    { label: "Executive sponsor change (unconfirmed)",             active: false },
    { label: "NPS detractor response in last survey",             active: false },
  ],

  summary:
    "This account shows 4 of 6 high-risk indicators. Power user engagement has dropped 68% over 14 days with no CSM touchpoint in 47 days, ahead of a 34-day renewal window. Immediate intervention is recommended.",

  actions: [
    {
      priority: 1,
      action:   "Schedule executive business review",
      owner:    "CSM",
      effort:   "Low",
      deadline: "Within 7 days",
      impact:   "EBR reduced churn in 3 comparable Q3 accounts; avg. score drop of 24 pts post-meeting.",
    },
    {
      priority: 2,
      action:   "Re-activate 3 dormant power users",
      owner:    "CSM",
      effort:   "Medium",
      deadline: "Within 5 days",
      impact:   "Restoring active seat usage is the #1 predictor of renewal confidence in this tier.",
    },
    {
      priority: 3,
      action:   "Send personalised outreach email",
      owner:    "AE",
      effort:   "Low",
      deadline: "Today",
      impact:   "Opens a direct line ahead of the EBR and signals proactive partnership.",
    },
    {
      priority: 4,
      action:   "Evaluate tier downgrade as retention offer",
      owner:    "AE",
      effort:   "High",
      deadline: "Before renewal",
      impact:   "Last-resort lever — preserves ARR at a lower rate vs. full churn.",
    },
  ],

  client: {
    contact_name:  "Jorge Mendez",
    contact_title: "Head of Operations",
    company:       "Acme Corp",
    csm_name:      "Sarah Chen",
    csm_title:     "Customer Success Manager",
  },

  email_draft: `Hi Jorge,\n\nI was reviewing your team's setup this week and wanted to reach out personally.\n\nI noticed a few of your power users haven't been active recently — and with your Q4 reporting cycle coming up, I want to make sure Acme is set up to get the most out of the platform.\n\nI'd love to jump on a 20-minute call to:\n  → Walk through the new workflow automation features\n  → Get feedback on what's working\n  → Ensure a smooth renewal\n\nWould Thursday or Friday work?\n\nBest,\nSarah Chen\nCustomer Success Manager`,
};

const EVENT_DELAYS = [400, 900, 1500, 2200, 2900, 3700, 4400, 5200, 6000, 6800, 7500, 8300, 9100, 9800, 10400];
const FINAL_DELAY  = 11200;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function ChurnAgentUI() {
  const [status, setStatus]             = useState<StreamStatus>("idle");
  const [feedEvents, setFeedEvents]     = useState<FeedEvent[]>([]);
  const [finalPayload, setFinalPayload] = useState<FinalPayload | null>(null);
  const feedRef = useRef<HTMLDivElement | null>(null);

  const handleSubmit = (_rows: JsonRow[], _file: File) => {
    setStatus("streaming");
    setFeedEvents([]);
    setFinalPayload(null);

    MOCK_EVENTS.forEach((evt, idx) => {
      setTimeout(() => {
        setFeedEvents((prev) => [...prev, { ...evt, id: `${idx}-${Date.now()}` }]);
        setTimeout(() => {
          if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
        }, 50);
      }, EVENT_DELAYS[idx] ?? idx * 700);
    });

    setTimeout(() => {
      setFinalPayload(MOCK_FINAL);
      setStatus("done");
    }, FINAL_DELAY);
  };

  const handleReset = () => {
    setStatus("idle");
    setFeedEvents([]);
    setFinalPayload(null);
  };

  return (
    <div className="min-h-screen bg-[#0a1628] p-6">
      <div className="max-w-6xl mx-auto space-y-4">

        {/* Header */}
        <div className="relative flex items-center w-full justify-center">
          <div className="text-center">
            <h1 className="text-3xl font-semibold text-[#fffffa]">Autonomous Churn Agent</h1>
            <p className="text-md text-slate-500 mt-0.5">
              Upload customer data · run AI analysis · get retention playbook
            </p>
          </div>
          {status !== "idle" && (
            <button
              onClick={handleReset}
              className="absolute right-0 text-sm text-[#fffffa] hover:text-[#fffffa] border border-slate-200 hover:border-slate-300 px-3 py-1.5 rounded-lg transition-colors"
            >
              Start over
            </button>
          )}
        </div>

        {/* Sections 1 + 2 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ExcelUpload
            onSubmit={handleSubmit}
            onReset={handleReset}
            isLoading={status === "streaming"}
          />
          <AgentActivity
            status={status}
            feedEvents={feedEvents}
            feedRef={feedRef}
          />
        </div>

        {/* Section 3 */}
        {finalPayload && (
          <RetentionPlaybook finalPayload={finalPayload} />
        )}

      </div>
    </div>
  );
}