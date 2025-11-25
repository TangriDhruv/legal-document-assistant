import { useState, useCallback } from "react";
import type { Placeholder, ChatResponse, ConversationMessage } from "../types";

const API_BASE = (import.meta as any).env?.VITE_API_URL || "http://localhost:8000";

export function useDocumentSession() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string>("");
  const [placeholders, setPlaceholders] = useState<Placeholder[]>([]);
  const [conversation, setConversation] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadDocument = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Upload failed");
      }

      const data = await response.json();
      setSessionId(data.session_id);
      setFilename(data.filename);
      setPlaceholders(data.placeholders);
      
      // Generate a more helpful initial message with placeholder details
      const placeholderNames = data.placeholders
        .slice(0, 5)
        .map((p: any) => p.name)
        .join(", ");
      const morePlaceholders = data.placeholders.length > 5 
        ? ` and ${data.placeholders.length - 5} more` 
        : "";
      
      const initialMessage = `I've successfully loaded your document "${file.name}". 
      
I found ${data.placeholders.length} fields that need to be filled:
${placeholderNames}${morePlaceholders}

You can:
- Tell me all the information at once (e.g., "The company is XYZ Corp, founded in 2020, located in NYC")
- Fill fields one by one (e.g., "The investor name is John Smith")
- Ask me to summarize what we've filled so far

What information would you like to provide?`;
      
      setConversation([
        {
          role: "assistant",
          content: initialMessage,
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!sessionId) return;

      setLoading(true);
      setError(null);

      setConversation((prev) => [
        ...prev,
        { role: "user", content: message },
      ]);

      try {
        const response = await fetch(`${API_BASE}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message,
            session_id: sessionId,
            placeholders,
          }),
        });

        if (!response.ok) {
          throw new Error("Chat failed");
        }

        const data: ChatResponse = await response.json();
        setPlaceholders(data.placeholders);
        setConversation((prev) => [
          ...prev,
          { role: "assistant", content: data.assistant_message },
        ]);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Chat failed");
        setConversation((prev) =>
          prev.slice(0, -1)
        );
      } finally {
        setLoading(false);
      }
    },
    [sessionId, placeholders]
  );

  const downloadDocument = useCallback(async () => {
    if (!sessionId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/download`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          placeholders,
        }),
      });

      if (!response.ok) {
        throw new Error("Download failed");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `completed_${filename}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Download failed");
    } finally {
      setLoading(false);
    }
  }, [sessionId, placeholders, filename]);

  const resetSession = useCallback(() => {
    setSessionId(null);
    setFilename("");
    setPlaceholders([]);
    setConversation([]);
    setError(null);
  }, []);

  return {
    sessionId,
    filename,
    placeholders,
    conversation,
    loading,
    error,
    uploadDocument,
    sendMessage,
    downloadDocument,
    resetSession,
  };
}