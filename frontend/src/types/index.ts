// frontend/src/types/index.ts

export interface Placeholder {
  name: string;
  context: string;
  before?: string;
  after?: string;
  filled: boolean;
  value?: string;
  type?: string;
  description?: string;
  inferred_name?: string;           // NEW: Name inferred from context
  inference_confidence?: number;    // NEW: Confidence score (0-1)
  reasoning?: string;               // NEW: Why it was inferred this way
}

export interface UploadResponse {
  session_id: string;
  filename: string;
  placeholders: Placeholder[];
}

export interface ChatResponse {
  assistant_message: string;
  filled_values: Record<string, string>;
  placeholders: Placeholder[];
  next_question?: string;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface SessionData {
  session_id: string;
  filename: string;
  placeholders: Placeholder[];
  conversation: ConversationMessage[];
}