import type { components } from "../../integrations/schema";
export interface ExecutionEvent {
  kind: string;
  description: string;
  line?: number;
  indices: number[];
}
export interface ExecutionContext {
  algorithm: string;
  language_version?: string;
  code: string;
  current_line?: number;
  phase: "before" | "after" | "unknown";
  run_id: string;
  step?: number;
  variables: Record<string, unknown>;
  arrays: Record<string, unknown[]>;
  recent_events: ExecutionEvent[];
}
export interface Source {
  id: string;
  title: string;
  path: string;
  section: string;
  text: string;
}
export interface TutorReply {
  evidence?: components["schemas"]["EvidenceReport"];
  teaching_decision?: components["schemas"]["TeachingDecision"] | null;
  code_examples?: components["schemas"]["CodeExample"][];

  answer: string;
  sources: Source[];
  context_status: string;
  warnings: string[];
  provider: string;
  model: string;
  latency_ms: number;
  fallback_used: boolean;
  prompt_version: string;
  knowledge_version: string;
}
export interface Message {
  role: "user" | "assistant";
  content: string;
  step?: number;
  reply?: TutorReply;
}
