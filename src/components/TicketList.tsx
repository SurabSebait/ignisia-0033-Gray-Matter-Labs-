"use client";

import { useEffect, useState } from "react";

type Ticket = {
  _id: string;
  conversation_id: string;
  title: string;
  status: string;
  user1_id: string;
  user2_id?: string;
  created_at: string;
  issue?: string;
  relevant_context?: string[];
  resolution?: string;
};

type TicketListProps = {
  role: "admin" | "user" | "support";
  userId?: string;
  onSelect?: (ticket: Ticket) => void;
};

export default function TicketList({ role, userId, onSelect }: TicketListProps) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = async () => {
    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (role === "user" && userId) {
      params.set("userId", userId);
    }

    try {
      const res = await fetch(`/api/tickets?${params.toString()}`);
      if (!res.ok) {
        throw new Error("Failed to load tickets");
      }

      const data = await res.json();
      setTickets(Array.isArray(data) ? data : []);
    } catch (err) {
      setError((err as Error).message || "Unable to fetch tickets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
  }, [role, userId]);

  if (loading) {
    return <div className="p-4 text-sm text-gray-500">Loading tickets...</div>;
  }

  if (error) {
    return <div className="p-4 text-sm text-red-600">{error}</div>;
  }

  if (tickets.length === 0) {
    return <div className="p-4 text-sm text-gray-500">No tickets found.</div>;
  }

  return (
    <div className="space-y-2">
      {tickets.map((ticket) => (
        <button
          key={ticket._id}
          onClick={() => onSelect?.(ticket)}
          className="w-full text-left rounded-lg border border-gray-200 bg-white p-3 hover:border-blue-500 hover:shadow-sm"
        >
          <div className="flex justify-between text-sm font-medium text-gray-700">
            <span>{ticket.title}</span>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs text-blue-700">{ticket.status}</span>
          </div>
          <div className="mt-1 text-xs text-gray-500">{new Date(ticket.created_at).toLocaleString()}</div>
        </button>
      ))}
    </div>
  );
}
