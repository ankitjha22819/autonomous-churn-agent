"use client";

import { RefObject } from "react";
import type { StreamStatus, FeedEvent } from "../stores/analysisStore";

interface AgentActivityProps {
  status: StreamStatus;
  feedEvents: FeedEvent[];
  feedRef: RefObject<HTMLDivElement | null>;
}

const AGENT_COLOR: Record<string, string> = {
  "Data Analyst":         "text-blue-500",
  "Retention Strategist": "text-teal-500",
  "Playbook Writer":      "text-violet-500",
};

function EventRow({ event }: { event: FeedEvent }) {
  const initials = (event.agent ?? "").split(" ").map((w) => w[0]).join("");
  const color = AGENT_COLOR[event.agent ?? ""] ?? "text-slate-400";

  if (event.type === "thinking") return (
    <div className="flex items-start gap-3 py-1.5">
      <span className={`text-xs font-mono font-medium mt-0.5 w-6 flex-shrink-0 ${color}`}>{initials}</span>
      <span className="text-sm text-slate-400 italic">{event.message}</span>
    </div>
  );

  if (event.type === "tool_call") return (
    <div className="flex items-center gap-3 py-1.5">
      <span className={`text-xs font-mono font-medium w-6 flex-shrink-0 ${color}`}>{initials}</span>
      <span className="text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200 font-mono flex-shrink-0">tool</span>
      <span className="text-sm text-slate-500">{event.message}</span>
    </div>
  );

  if (event.type === "insight") {
    const borderColors = {
      high:   "border-red-300 bg-red-50",
      medium: "border-amber-300 bg-amber-50",
      low:    "border-emerald-300 bg-emerald-50",
    };
    const textColors = {
      high:   "text-red-700",
      medium: "text-amber-700",
      low:    "text-emerald-700",
    };
    const risk = event.risk ?? "low";
    return (
      <div className="flex items-start gap-3 py-1.5">
        <span className={`text-xs font-mono font-medium mt-0.5 w-6 flex-shrink-0 ${color}`}>{initials}</span>
        <div className={`flex-1 px-3 py-2 rounded-lg border-l-2 ${borderColors[risk]}`}>
          <span className={`text-sm font-medium ${textColors[risk]}`}>{event.message}</span>
        </div>
      </div>
    );
  }

  if (event.type === "action") return (
    <div className="flex items-start gap-3 py-1.5">
      <span className={`text-xs font-mono font-medium mt-0.5 w-6 flex-shrink-0 ${color}`}>{initials}</span>
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-slate-500 w-4">{event.priority}.</span>
        <span className="text-sm text-slate-700">{event.message}</span>
      </div>
    </div>
  );

  return null;
}

export default function AgentActivity({ status, feedEvents, feedRef }: AgentActivityProps) {
  return (
    <div className="bg-[#fffffa] shadow-2xl min-h-[400px] rounded-xl border-2 border-slate-500 p-5 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center font-medium">
            2
          </span>
          <h2 className="text-lg font-semibold text-slate-700">Agent activity</h2>
        </div>

        {status === "streaming" && (
          <span className="flex items-center gap-1.5 text-xs text-blue-600">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            Live
          </span>
        )}
        {status === "done" && (
          <span className="flex items-center gap-1.5 text-xs text-emerald-600">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            Complete
          </span>
        )}
      </div>

      {/* Feed */}
      <div ref={feedRef} className="flex-1 overflow-y-auto min-h-[260px] max-h-[320px]">
        {status === "idle" && (
          <div className="flex flex-col items-center justify-center h-full gap-2 py-10">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-slate-300">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.2" />
              <path d="M12 8v4l3 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
            <p className="text-sm text-slate-400">Waiting for analysis to start</p>
          </div>
        )}

        {status === "streaming" && feedEvents.length === 0 && (
          <div className="flex items-center gap-2 py-4">
            <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
            <span className="text-sm text-slate-500">Starting agents…</span>
          </div>
        )}

        {feedEvents.length > 0 && (
          <div className="divide-y divide-slate-50">
            {feedEvents.map((evt) => (
              <EventRow key={evt.id} event={evt} />
            ))}
            {status === "done" && (
              <div className="flex items-center gap-2 py-3">
                <div className="h-px flex-1 bg-slate-200" />
                <span className="text-xs text-emerald-600 font-medium">Analysis complete</span>
                <div className="h-px flex-1 bg-slate-200" />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-4">
        {[
          { color: "text-blue-500",   label: "DA = Data Analyst" },
          { color: "text-teal-500",   label: "RS = Strategist" },
          { color: "text-violet-500", label: "PW = Playbook Writer" },
        ].map(({ color, label }) => (
          <span key={label} className={`text-xs ${color}`}>{label}</span>
        ))}
      </div>
    </div>
  );
}