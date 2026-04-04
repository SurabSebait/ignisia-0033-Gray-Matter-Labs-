"use client";

import { useSession } from "next-auth/react";
import { useEffect, useState } from "react";
import FileUpload from "@/components/FileUpload";
import TicketList from "@/components/TicketList";
import ChatWindow from "@/components/ChatWindow";
import SignOutButton from "@/components/SignoutButton";

export default function DashboardHome() {
  const { data: session, status } = useSession();
  const [selectedTicket, setSelectedTicket] = useState<{ conversation_id: string; title: string; issue?: string; relevant_context?: string[]; resolution?: string } | null>(null);
  const [citations, setCitations] = useState<string[]>([]);
  const [newTicketTitle, setNewTicketTitle] = useState("");
  const [newTicketDesc, setNewTicketDesc] = useState("");
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    // clear message after success / error
    if (msg) {
      const timer = setTimeout(() => setMsg(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [msg]);

  if (status === "loading") {
    return <div className="p-8 text-gray-500">Checking session...</div>;
  }

  if (!session?.user) {
    return <div className="p-8 text-gray-500">Not logged in. Please go to /login.</div>;
  }

  const rawRole = (session.user.role || "user").toString();
  const role = (rawRole === "support personnel" || rawRole === "support") ? "support" : (rawRole === "admin" ? "admin" : "user");
  const userId = (session.user.id || "") as string;

  const handleCreateTicket = async () => {
    if (!newTicketTitle.trim() || !newTicketDesc.trim()) {
      setMsg("Title and description required.");
      return;
    }

    try {
      const res = await fetch("/api/tickets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTicketTitle, description: newTicketDesc })
      });

      if (!res.ok) throw new Error("Could not create ticket");
      setNewTicketTitle("");
      setNewTicketDesc("");
      setMsg("Ticket created successfully.");
    } catch (err) {
      setMsg((err as Error).message);
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-800">Dashboard</h1>

      </div>
      <p className="mt-2 text-gray-600">Logged in as: {session.user.email} ({role})</p>

      {role === "admin" && (
        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-800">Admin Upload</h2>
          <p className="text-sm text-gray-500">Upload validated file to GCS (.pdf, .xlsx only).</p>
          <FileUpload
            task="webcrawler"
            llm="gemini"
            userEmail={session.user.email || "admin"}
            accept=".pdf,.xlsx"
            onValidate={async (file) => {
              const allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"];
              const fileExt = file.name.split('.').pop()?.toLowerCase();
              const validExt = fileExt === "pdf" || fileExt === "xlsx";
              if (!validExt || !allowed.includes(file.type)) {
                alert("Only .pdf and .xlsx files are allowed.");
                return false;
              }
              return true;
            }}
          />
        </div>
      )}

      {role === "user" && (
        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-gray-800">Raise Ticket</h2>
            <input
              value={newTicketTitle}
              onChange={(e) => setNewTicketTitle(e.target.value)}
              className="mt-4 w-full rounded-md border p-2"
              placeholder="Ticket title"
            />
            <textarea
              value={newTicketDesc}
              onChange={(e) => setNewTicketDesc(e.target.value)}
              className="mt-3 h-24 w-full rounded-md border p-2"
              placeholder="Describe your issue"
            />
            <button onClick={handleCreateTicket} className="mt-3 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
              Create Ticket
            </button>
            {msg && <div className="mt-3 text-sm text-blue-600">{msg}</div>}
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-6">
            <h2 className="text-xl font-semibold text-gray-800">Your Tickets</h2>
            <TicketList role="user" userId={userId} onSelect={(t) => setSelectedTicket(t)} />
          </div>
        </div>
      )}

      {role === "user" && selectedTicket && (
        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6">
          <h2 className="text-xl font-semibold text-gray-800">Chat for Ticket: {selectedTicket.title}</h2>
          <ChatWindow
            conversationId={selectedTicket.conversation_id}
            currentUserId={userId}
            role={role}
            onCitationsUpdate={setCitations}
            ticket={selectedTicket}
          />

          <div className="mt-4 rounded-lg border border-gray-200 bg-gray-50 p-3">
            <h3 className="text-sm font-semibold text-gray-700">AI Citations</h3>
            {citations.length === 0 ? (
              <p className="text-sm text-gray-500">No citations yet for this conversation.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
                {citations.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {role === "support" && (
        <div className="mt-6 grid gap-4 lg:grid-cols-3">
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h2 className="text-lg font-semibold">Ticket List</h2>
            <TicketList role="support" onSelect={(t) => setSelectedTicket(t)} />
          </div>

          <div className="col-span-2 rounded-xl border border-gray-200 bg-white p-4">
            <h2 className="text-lg font-semibold">Chat</h2>
            <ChatWindow
              conversationId={selectedTicket?.conversation_id ?? null}
              currentUserId={userId}
              role={role}
              onCitationsUpdate={setCitations}
              ticket={selectedTicket}
            />
          </div>

          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <h2 className="text-lg font-semibold">AI Citations</h2>
            {citations.length === 0 ? (
              <p className="text-sm text-gray-500">No AI citations yet.</p>
            ) : (
              <ul className="list-disc space-y-1 pl-4 text-sm text-gray-700">
                {citations.map((c, i) => (
                  <li key={i}>{c}</li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {role === "admin" && (
        <div className="mt-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h2 className="text-xl font-semibold text-gray-800">Admin Ticket View</h2>
          <TicketList role="support" onSelect={(t) => setSelectedTicket(t)} />
        </div>
      )}

      {selectedTicket && role !== "user" && (
        <div className="mt-4 text-sm text-gray-700">Selected ticket: {selectedTicket.title}</div>
      )}
    </div>
  );
}
