"use client";

import { useRef, useEffect } from "react";
import ExcelUpload from "@/components/ExcelUpload";
import AgentActivity from "@/components/AgentActivity";
import RetentionPlaybook from "@/components/RetentionPlaybook";
import { useAnalysisStore } from "@/stores/analysisStore";
import { useAnalysisStream } from "@/hooks/useAnalysisStream";
import { createAnalysisJob } from "@/lib/api";
import { transformExcelToCustomers, validateCustomers } from "@/lib/transforms";
import type { StreamStatus, FeedEvent, FinalPayload } from "@/stores/analysisStore";

type JsonRow = Record<string, string | number | boolean | null>;


// Page Component


export default function ChurnAgentUI() {
  const feedRef = useRef<HTMLDivElement | null>(null);
  const { connect, disconnect } = useAnalysisStream();

  // Zustand store state
  const status = useAnalysisStore((state) => state.status);
  const feedEvents = useAnalysisStore((state) => state.feedEvents);
  const finalPayload = useAnalysisStore((state) => state.finalPayload);
  const error = useAnalysisStore((state) => state.error);
  const reset = useAnalysisStore((state) => state.reset);
  const setStatus = useAnalysisStore((state) => state.setStatus);
  const setError = useAnalysisStore((state) => state.setError);
  const setJobId = useAnalysisStore((state) => state.setJobId);

  // Auto-scroll feed
  useEffect(() => {
    if (feedRef.current && feedEvents.length > 0) {
      setTimeout(() => {
        if (feedRef.current) {
          feedRef.current.scrollTop = feedRef.current.scrollHeight;
        }
      }, 50);
    }
  }, [feedEvents]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  
  // Submit Handler
  

  const handleSubmit = async (rows: JsonRow[], _file: File) => {
    try {
      // Reset state
      reset();
      setStatus("streaming");

      // Transform Excel data to API format
      const customers = transformExcelToCustomers(rows);
      
      // Validate
      const validation = validateCustomers(customers);
      if (!validation.isValid) {
        setError(validation.errors.join(", "));
        return;
      }

      // Log warnings
      if (validation.warnings.length > 0) {
        console.warn("[Validation]", validation.warnings);
      }

      console.log("[Submit] Creating job with", customers.length, "customers");

      // Create analysis job
      const job = await createAnalysisJob({
        customers,
        config: {
          include_recommendations: true,
          include_insights: true,
          include_individual_predictions: true,
          high_risk_threshold: 70,
          critical_risk_threshold: 85,
        },
      });

      console.log("[Submit] Job created:", job.job_id);
      setJobId(job.job_id);

      // Connect to SSE stream
      connect(job.job_id);
    } catch (err) {
      console.error("[Submit] Error:", err);
      setError(err instanceof Error ? err.message : "Failed to create analysis job");
    }
  };

  
  // Reset Handler
  

  const handleReset = () => {
    disconnect();
    reset();
  };

  
  // Render
  

  return (
    <div className="min-h-screen bg-[#0a1628] p-6">
      <div className="max-w-6xl mx-auto space-y-4">

        {/* Header */}
        <div className="relative flex items-center w-full justify-center">
          <div className="text-center">
            <h1 className="text-3xl font-semibold text-[#fffffa]">
              Autonomous Churn Agent
            </h1>
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

        {/* Error Banner */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              className="text-red-400 flex-shrink-0 mt-0.5"
            >
              <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="1.5" />
              <path
                d="M10 6v4M10 13v1"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
            <div className="flex-1">
              <p className="text-sm font-medium text-red-400">Analysis Error</p>
              <p className="text-sm text-red-300/80 mt-0.5">{error}</p>
            </div>
            <button
              onClick={handleReset}
              className="text-sm text-red-400 hover:text-red-300 underline"
            >
              Try again
            </button>
          </div>
        )}

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

        {/* Section 3 - Retention Playbook */}
        {finalPayload && <RetentionPlaybook finalPayload={finalPayload} />}

      </div>
    </div>
  );
}