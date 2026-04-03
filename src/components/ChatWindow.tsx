"use client";

import { useEffect, useMemo, useState } from "react";

type Message = {
  message_id: string;
  conversation_id: string;
  message_text: string;
  sender_id: string;
  created_at: string;
};

type ChatWindowProps = {
  conversationId: string | null;
  currentUserId: string;
  role: "admin" | "user" | "support";
  onCitationsUpdate?: (citations: string[]) => void;
};

export default function ChatWindow({ conversationId, currentUserId, role, onCitationsUpdate }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [input, setInput] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [error, setError] = useState<string | null>(null);

  const filteredMessages = useMemo(() => messages.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()), [messages]);

  const fetchChat = async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`/api/chat?conversation_id=${encodeURIComponent(conversationId)}`);
      if (!res.ok) throw new Error("Failed to load conversation");
      const data = await res.json();
      setMessages(Array.isArray(data.messages) ? data.messages : []);
    } catch (err) {
      setError((err as Error).message || "Unable to load chat");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChat();
  }, [conversationId]);

  const sendMessage = async () => {
    if (!conversationId || !input.trim()) return;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, message_text: input.trim(), sender_id: currentUserId })
      });
      if (!res.ok) throw new Error("Failed to send message");

      setInput("");
      setAiResponse("");
      await fetchChat();
    } catch (err) {
      setError((err as Error).message || "Unable to send message");
    }
  };

  const askAiSuggestion = async () => {
    if (!conversationId) return;

    try {
      const res = await fetch("/api/ai-suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, prompt: input })
      });

      if (!res.ok) throw new Error("AI request failed");

      const { response, citations } = await res.json();
      setAiResponse(response);
      setInput(response);
      onCitationsUpdate?.(Array.isArray(citations) ? citations : []);
    } catch (err) {
      setError((err as Error).message || "AI call error");
    }
  };

  if (!conversationId) {
    return <div className="p-4 text-sm text-gray-500">Select a ticket to view chat.</div>;
  }

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="h-64 overflow-y-auto rounded-lg border border-gray-200 bg-white p-3">
        {loading ? (
          <div className="text-sm text-gray-500">Loading...</div>
        ) : error ? (
          <div className="text-sm text-red-600">{error}</div>
        ) : filteredMessages.length === 0 ? (
          <div className="text-sm text-gray-500">No messages yet.</div>
        ) : (
          filteredMessages.map((message) => (
            <div key={message.message_id} className={`mb-3 rounded-lg p-2 ${message.sender_id === currentUserId ? "bg-blue-50 text-blue-800" : "bg-gray-100 text-gray-800"}`}>
              <div className="text-xs text-gray-500">{message.sender_id === currentUserId ? "You" : "Other"} • {new Date(message.created_at).toLocaleTimeString()}</div>
              <div>{message.message_text}</div>
            </div>
          ))
        )}
      </div>

      <div className="flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="flex-1 rounded-lg border border-gray-300 px-3 py-2"
          placeholder="Type a message..."
        />
        <button onClick={sendMessage} className="rounded-lg bg-blue-600 px-3 text-white hover:bg-blue-700">Send</button>
      </div>

      {(role === "support" || role === "admin") && (
        <button onClick={askAiSuggestion} className="rounded-lg border border-blue-600 bg-white px-3 py-2 text-blue-600 hover:bg-blue-50">Ask AI for suggestion</button>
      )}

      {aiResponse && (
        <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-2 text-sm text-indigo-900">AI draft: {aiResponse}</div>
      )}
    </div>
  );
}
