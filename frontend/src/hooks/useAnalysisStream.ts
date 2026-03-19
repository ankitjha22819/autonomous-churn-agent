
// useAnalysisStream - SSE Hook for Real-time Events


"use client";

import { useCallback, useRef } from "react";
import { getEventsUrl } from "@/lib/api";
import { useAnalysisStore } from "@/stores/analysisStore";
import type {
  AgentActivityData,
  ThinkingData,
  ToolUsageData,
  ReportReadyData,
  JobProgressData,
  JobCompleteData,
  JobErrorData,
} from "@/types/api";

interface UseAnalysisStreamReturn {
  connect: (jobId: string) => void;
  disconnect: () => void;
  isConnected: boolean;
}

export function useAnalysisStream(): UseAnalysisStreamReturn {
  const eventSourceRef = useRef<EventSource | null>(null);
  const isConnectedRef = useRef(false);

  const {
    setStatus,
    handleAgentActivity,
    handleThinking,
    handleToolUsage,
    handleReportReady,
    handleJobProgress,
    handleJobComplete,
    handleJobError,
  } = useAnalysisStore();

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      isConnectedRef.current = false;
    }
  }, []);

  const connect = useCallback(
    (jobId: string) => {
      // Disconnect any existing connection
      disconnect();

      const url = getEventsUrl(jobId);
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // ─
      // Connection Events
      // ─

      eventSource.onopen = () => {
        console.log("[SSE] Connected to", url);
        isConnectedRef.current = true;
        setStatus("streaming");
      };

      eventSource.onerror = (error) => {
        console.error("[SSE] Connection error:", error);
        
        // Only set error if we're not already done
        if (eventSource.readyState === EventSource.CLOSED) {
          isConnectedRef.current = false;
        }
      };

      // ─
      // Event Handlers (Discriminator Pattern)
      // ─

      eventSource.addEventListener("connected", (e) => {
        console.log("[SSE] Received connected event");
        const data = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] Job ID:", data.job_id);
      });

      eventSource.addEventListener("agent_activity", (e) => {
        const data: AgentActivityData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] agent_activity:", data.agent, data.status);
        handleAgentActivity(data);
      });

      eventSource.addEventListener("thinking", (e) => {
        const data: ThinkingData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] thinking:", data.agent);
        handleThinking(data);
      });

      eventSource.addEventListener("tool_usage", (e) => {
        const data: ToolUsageData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] tool_usage:", data.tool_name, data.status);
        handleToolUsage(data);
      });

      eventSource.addEventListener("report_ready", (e) => {
        const data: ReportReadyData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] report_ready:", data.summary);
        handleReportReady(data);
      });

      eventSource.addEventListener("job_progress", (e) => {
        const data: JobProgressData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] job_progress:", data.percentage + "%");
        handleJobProgress(data);
      });

      eventSource.addEventListener("job_complete", (e) => {
        const data: JobCompleteData = JSON.parse((e as MessageEvent).data);
        console.log("[SSE] job_complete:", data.message);
        handleJobComplete();
        disconnect();
      });

      eventSource.addEventListener("job_error", (e) => {
        const data: JobErrorData = JSON.parse((e as MessageEvent).data);
        console.error("[SSE] job_error:", data.detail);
        handleJobError(data);
        disconnect();
      });
    },
    [
      disconnect,
      setStatus,
      handleAgentActivity,
      handleThinking,
      handleToolUsage,
      handleReportReady,
      handleJobProgress,
      handleJobComplete,
      handleJobError,
    ]
  );

  return {
    connect,
    disconnect,
    isConnected: isConnectedRef.current,
  };
}