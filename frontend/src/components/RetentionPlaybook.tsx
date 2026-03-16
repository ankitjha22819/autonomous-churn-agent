"use client";

import { useState } from "react";

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

interface RetentionPlaybookProps {
  finalPayload: FinalPayload;
}

function RiskBadge({ score }: { score: number }) {
  const level = score >= 70 ? "high" : score >= 40 ? "medium" : "low";
  const styles = {
    high: "bg-red-50 text-red-600 border-red-200",
    medium: "bg-amber-50 text-amber-600 border-amber-200",
    low: "bg-emerald-50 text-emerald-600 border-emerald-200",
  };
  const label = { high: "High risk", medium: "At risk", low: "Healthy" };
  return (
    <span
      className={`text-xs font-medium px-2.5 py-1 rounded-full border ${styles[level]}`}
    >
      {label[level]}
    </span>
  );
}

function Avatar({ name }: { name: string }) {
  const initials = name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  return (
    <span className="w-5 h-5 rounded-full bg-slate-200 text-slate-600 text-[10px] font-semibold flex items-center justify-center flex-shrink-0">
      {initials}
    </span>
  );
}

const EFFORT_COLORS: Record<string, string> = {
  Low: "bg-emerald-50 text-emerald-600 border-emerald-200",
  Medium: "bg-amber-50 text-amber-600 border-amber-200",
  High: "bg-slate-100 text-slate-500 border-slate-200",
};

const PRIORITY_COLORS: Record<number, string> = {
  1: "bg-red-100 text-red-600",
  2: "bg-amber-100 text-amber-600",
};

export default function RetentionPlaybook({
  finalPayload,
}: RetentionPlaybookProps) {
  const [emailCopied, setEmailCopied] = useState(false);

  const copyEmail = () => {
    navigator.clipboard.writeText(finalPayload.email_draft);
    setEmailCopied(true);
    setTimeout(() => setEmailCopied(false), 1800);
  };

  const riskColor = (s: number) =>
    s >= 70 ? "text-red-600" : s >= 40 ? "text-amber-600" : "text-emerald-600";
  const riskBarColor = (s: number) =>
    s >= 70 ? "bg-red-500" : s >= 40 ? "bg-amber-500" : "bg-emerald-500";

  const scoreDelta = finalPayload.risk_score - finalPayload.previous_risk_score;
  const activeCount = finalPayload.signals.filter((s) => s.active).length;
  const { client } = finalPayload;

  return (
    <div className="bg-[#fffffa] shadow-2xl min-h-[600px] rounded-xl border-2 border-slate-500 p-5">
      {/* Header */}
      <div className="flex items-center gap-2 mb-5">
        <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center font-medium">
          3
        </span>
        <h2 className="text-lg font-semibold text-slate-700">
          Retention playbook
        </h2>
        <RiskBadge score={finalPayload.risk_score} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* ── Col 1: Risk score ── */}
        <div className="space-y-3">
          <p className="text-md font-medium text-slate-500 uppercase tracking-wide">
            Churn risk score
          </p>

          <div className="flex items-end gap-3">
            <span
              className={`text-4xl font-bold ${riskColor(finalPayload.risk_score)}`}
            >
              {finalPayload.risk_score}
            </span>
            <span className="text-slate-400 text-sm mb-1">/ 100</span>
            {scoreDelta !== 0 && (
              <span
                className={`text-xs font-medium mb-1.5 ${scoreDelta > 0 ? "text-red-500" : "text-emerald-500"}`}
              >
                {scoreDelta > 0 ? `▲ +${scoreDelta}` : `▼ ${scoreDelta}`} vs
                last month
              </span>
            )}
          </div>

          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-1000 ${riskBarColor(finalPayload.risk_score)}`}
              style={{ width: `${finalPayload.risk_score}%` }}
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-500 bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <circle
                cx="6"
                cy="6"
                r="4.5"
                stroke="currentColor"
                strokeWidth="1.2"
              />
              <path
                d="M6 3.5V6l1.5 1.5"
                stroke="currentColor"
                strokeWidth="1.2"
                strokeLinecap="round"
              />
            </svg>
            <span>
              Renewal in{" "}
              <span
                className={`font-semibold ${finalPayload.days_to_renewal <= 30 ? "text-red-600" : "text-slate-700"}`}
              >
                {finalPayload.days_to_renewal} days
              </span>
            </span>
          </div>

          <p className="text-sm text-slate-600 leading-relaxed">
            {finalPayload.summary}
          </p>

          <div>
            <p className="text-xs font-medium text-slate-400 uppercase tracking-wide mb-1.5">
              Risk signals — {activeCount} of {finalPayload.signals.length}{" "}
              active
            </p>
            <div className="space-y-1.5">
              {finalPayload.signals.map((signal) => (
                <div key={signal.label} className="flex items-center gap-2">
                  <span
                    className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${signal.active ? "bg-red-400" : "bg-slate-200"}`}
                  />
                  <span
                    className={`text-xs ${signal.active ? "text-slate-700" : "text-slate-400"}`}
                  >
                    {signal.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Col 2: Recommended actions ── */}
        <div className="space-y-3">
          <p className="text-md font-medium text-slate-500 uppercase tracking-wide">
            Recommended actions
          </p>
          <div className="space-y-2">
            {finalPayload.actions.map((action) => (
              <div
                key={action.priority}
                className="flex items-start gap-3 p-2.5 rounded-lg border border-slate-100 hover:bg-slate-50 transition-colors"
              >
                <span
                  className={`w-5 h-5 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5 ${
                    PRIORITY_COLORS[action.priority] ??
                    "bg-slate-100 text-slate-500"
                  }`}
                >
                  {action.priority}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700">{action.action}</p>
                  <p className="text-xs text-slate-400 mt-0.5 leading-snug">
                    {action.impact}
                  </p>
                  <div className="flex items-center gap-2 mt-1 flex-wrap">
                    <span className="text-xs text-slate-400">
                      {action.owner}
                    </span>
                    <span
                      className={`text-xs px-1.5 py-0.5 rounded border ${EFFORT_COLORS[action.effort] ?? EFFORT_COLORS.High}`}
                    >
                      {action.effort}
                    </span>
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <svg
                        width="10"
                        height="10"
                        viewBox="0 0 10 10"
                        fill="none"
                      >
                        <rect
                          x="1"
                          y="2"
                          width="8"
                          height="7"
                          rx="1"
                          stroke="currentColor"
                          strokeWidth="1"
                        />
                        <path
                          d="M3 1v2M7 1v2M1 5h8"
                          stroke="currentColor"
                          strokeWidth="1"
                          strokeLinecap="round"
                        />
                      </svg>
                      {action.deadline}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Col 3: Email draft ── */}
        <div className="space-y-3">
          {/* Section label + copy button */}
          <div className="flex items-center justify-between">
            <p className="text-md font-medium text-slate-500 uppercase tracking-wide">
              Outreach email draft
            </p>
            <button
              onClick={copyEmail}
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-700 border border-slate-200 hover:border-slate-300 px-2 py-1 rounded transition-colors"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                {emailCopied ? (
                  <path
                    d="M2 6l2.5 2.5L10 3"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                ) : (
                  <>
                    <rect
                      x="3.5"
                      y="1"
                      width="7.5"
                      height="7.5"
                      rx="1"
                      stroke="currentColor"
                      strokeWidth="1.1"
                    />
                    <path
                      d="M1 4H3V11H9V9"
                      stroke="currentColor"
                      strokeWidth="1.1"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </>
                )}
              </svg>
              {emailCopied ? "Copied" : "Copy"}
            </button>
          </div>

          {/* From / To metadata */}
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-slate-400 uppercase w-6 flex-shrink-0">
                From
              </span>

              <span className="text-xs text-slate-700 font-medium">
                {client.csm_name}
              </span>
              <span className="text-xs text-slate-400">{client.csm_title}</span>
            </div>
            <div className="h-px bg-slate-200" />
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-medium text-slate-400 uppercase w-6 flex-shrink-0">
                To
              </span>

              <span className="text-xs text-slate-700 font-medium">
                {client.contact_name}
              </span>
              <span className="text-xs text-slate-400">
                {client.contact_title}
              </span>
              <span className="ml-auto text-[10px] font-semibold text-slate-500 bg-slate-200 px-1.5 py-0.5 rounded">
                {client.company}
              </span>
            </div>
          </div>

          <textarea
            readOnly
            value={finalPayload.email_draft}
            className="w-full h-44 text-xs font-mono text-slate-600 bg-slate-50 border border-slate-200 rounded-lg p-3 resize-none leading-relaxed focus:outline-none focus:ring-1 focus:ring-slate-300"
          />
          <button className="w-full py-2 rounded-lg border border-slate-200 text-sm text-slate-600 hover:bg-slate-50 hover:border-slate-300 transition-colors">
            Send via Gmail
          </button>
        </div>
      </div>
    </div>
  );
}
