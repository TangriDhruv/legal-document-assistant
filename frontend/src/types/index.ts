export interface Placeholder {
  name: string;
  context: string;
  filled: boolean;
  value?: string;
  type?: string;
  description?: string;
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