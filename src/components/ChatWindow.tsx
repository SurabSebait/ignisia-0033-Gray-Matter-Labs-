"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";

type Message = {
  message_id: string;
  conversation_id: string;
  message_text: string;
  sender_id: string;
  created_at: string;
};

type Ticket = {
  _id: string;
  conversation_id: string;
  title: string;
  issue?: string;
  relevant_context?: string[];
  resolution?: string;
  // other fields...
};

type ChatWindowProps = {
  conversationId: string | null;
  currentUserId: string;
  role: "admin" | "user" | "support";
  onCitationsUpdate?: (citations: string[]) => void;
  ticket?: Ticket | null;
};

export default function ChatWindow({ conversationId, currentUserId, role, onCitationsUpdate, ticket }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiLoading, setAiLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
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

    const userMessage = input.trim();
    setError(null);
    setIsSending(true);
    setAiLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, message_text: userMessage, sender_id: currentUserId }),
      });
      if (!res.ok) throw new Error("Failed to send message");

      setInput("");

      const aiRes = await fetch("/api/ai-suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ conversation_id: conversationId, prompt: userMessage }),
      });

      if (!aiRes.ok) {
        const errData = await aiRes.json().catch(() => null);
        throw new Error(errData?.error || "AI request failed");
      }

      const aiData = await aiRes.json();
      setAiResponse(aiData.response || "");
      onCitationsUpdate?.(Array.isArray(aiData.citations) ? aiData.citations : []);

      await fetchChat();
    } catch (err) {
      setError((err as Error).message || "Unable to send message");
    } finally {
      setIsSending(false);
      setAiLoading(false);
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
              <div className="text-sm leading-relaxed">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 ml-4">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 ml-4">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    table: ({ children }) => <table className="border-collapse border border-gray-300 mb-2">{children}</table>,
                    thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-gray-200">{children}</tr>,
                    th: ({ children }) => <th className="border border-gray-300 px-2 py-1 text-left font-semibold">{children}</th>,
                    td: ({ children }) => <td className="border border-gray-300 px-2 py-1">{children}</td>,
                    code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                    pre: ({ children }) => <pre className="bg-gray-100 p-2 rounded mb-2 overflow-x-auto text-xs">{children}</pre>,
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2">{children}</blockquote>,
                  }}
                >
                  {message.message_text}
                </ReactMarkdown>
              </div>
            </div>
          ))
        )}
      </div>

      {ticket && ticket.issue && ticket.relevant_context && ticket.resolution && (
        <div className="mt-4 rounded-lg border border-green-200 bg-green-50 p-4">
          <h3 className="text-lg font-semibold text-green-800 mb-3">AI Resolution Summary</h3>
          <div className="space-y-3">
            <div>
              <h4 className="font-medium text-green-700">Issue:</h4>
              <p className="text-sm text-green-900 mt-1">{ticket.issue}</p>
            </div>
            {ticket.relevant_context.length > 0 && (
              <div>
                <h4 className="font-medium text-green-700">Relevant Context:</h4>
                <ul className="list-disc list-inside text-sm text-green-900 mt-1">
                  {ticket.relevant_context.map((context, index) => (
                    <li key={index}>{context}</li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h4 className="font-medium text-green-700">Resolution:</h4>
              <div className="text-sm text-green-900 mt-1 leading-relaxed">
                <ReactMarkdown
                  components={{
                    p: ({ children }) => <p className="mb-2">{children}</p>,
                    ul: ({ children }) => <ul className="list-disc list-inside mb-2 ml-4">{children}</ul>,
                    ol: ({ children }) => <ol className="list-decimal list-inside mb-2 ml-4">{children}</ol>,
                    li: ({ children }) => <li className="mb-1">{children}</li>,
                    table: ({ children }) => <table className="border-collapse border border-gray-300 mb-2">{children}</table>,
                    thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                    tbody: ({ children }) => <tbody>{children}</tbody>,
                    tr: ({ children }) => <tr className="border-b border-gray-200">{children}</tr>,
                    th: ({ children }) => <th className="border border-gray-300 px-2 py-1 text-left font-semibold">{children}</th>,
                    td: ({ children }) => <td className="border border-gray-300 px-2 py-1">{children}</td>,
                    code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                    pre: ({ children }) => <pre className="bg-gray-100 p-2 rounded mb-2 overflow-x-auto text-xs">{children}</pre>,
                    h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                    h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                    h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                    blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2">{children}</blockquote>,
                  }}
                >
                  {ticket.resolution}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-2">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isSending || aiLoading}
            className="flex-1 rounded-lg border border-gray-300 px-3 py-2 disabled:cursor-not-allowed disabled:opacity-50"
            placeholder="Type a message..."
          />
          <button
            onClick={sendMessage}
            disabled={isSending || aiLoading || !input.trim()}
            className="rounded-lg bg-blue-600 px-3 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSending ? "Sending..." : "Send"}
          </button>
        </div>

        {aiLoading && (
          <div className="text-sm text-gray-500 animate-pulse">AI is generating response from RAG backend...</div>
        )}
      </div>

      {(role === "support" || role === "admin") && (
        <button onClick={askAiSuggestion} className="rounded-lg border border-blue-600 bg-white px-3 py-2 text-blue-600 hover:bg-blue-50">Ask AI for suggestion</button>
      )}

      {aiResponse && (
        <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-2 text-sm text-indigo-900">
          <div className="leading-relaxed">
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2">{children}</p>,
                ul: ({ children }) => <ul className="list-disc list-inside mb-2 ml-4">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2 ml-4">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                table: ({ children }) => <table className="border-collapse border border-gray-300 mb-2">{children}</table>,
                thead: ({ children }) => <thead className="bg-gray-100">{children}</thead>,
                tbody: ({ children }) => <tbody>{children}</tbody>,
                tr: ({ children }) => <tr className="border-b border-gray-200">{children}</tr>,
                th: ({ children }) => <th className="border border-gray-300 px-2 py-1 text-left font-semibold">{children}</th>,
                td: ({ children }) => <td className="border border-gray-300 px-2 py-1">{children}</td>,
                code: ({ children }) => <code className="bg-gray-100 px-1 py-0.5 rounded text-xs font-mono">{children}</code>,
                pre: ({ children }) => <pre className="bg-gray-100 p-2 rounded mb-2 overflow-x-auto text-xs">{children}</pre>,
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-1">{children}</h3>,
                blockquote: ({ children }) => <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-2">{children}</blockquote>,
              }}
            >
              {aiResponse}
            </ReactMarkdown>
          </div>
        </div>
      )}
    </div>
  );
}
