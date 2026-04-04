import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import clientPromise from "@/lib/mongodb";
import { v4 as uuidv4 } from "uuid";

type ChatMessage = {
  message_id: string;
  conversation_id: string;
  message_text: string;
  sender_id: string;
  created_at: string | Date;
};

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await request.json();
  const conversationId = (data.conversation_id || "").toString();
  const prompt = (data.prompt || "").toString();

  if (!conversationId || !prompt) {
    return NextResponse.json(
      { error: "Missing conversation_id or prompt" },
      { status: 400 },
    );
  }

  const client = await clientPromise;
  const ticket = await client
    .db("Ignisia")
    .collection("tickets")
    .findOne({ conversation_id: conversationId });

  if (!ticket) {
    return NextResponse.json(
      { error: "Conversation not found" },
      { status: 404 },
    );
  }

  const ragServerUrl = process.env.RAG_MODEL_ENDPOINT || "";

  const ticketMessages = Array.isArray(ticket.messages)
    ? (ticket.messages as ChatMessage[])
    : [];
  const sortedMessages = [...ticketMessages].sort(
    (a, b) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
  );

  const conversationStringParts: string[] = sortedMessages.map((msg) => {
    const sender = msg.sender_id === session.user.id ? "user" : "assistant";
    return `${sender}: ${msg.message_text}`;
  });
  conversationStringParts.push(`user: ${prompt}`);

  const question = conversationStringParts.join("\n");

  let answer = "";
  let sources: Array<{ doc_id?: string; page_num?: number }> = [];

  if (!ragServerUrl) {
    answer = `AI response based on: ${prompt}`;
    sources = [];
  } else {
    try {
      const apiRes = await fetch(ragServerUrl, {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!apiRes.ok) {
        const errorText = await apiRes.text();
        console.error(`RAG backend error ${apiRes.status}:`, errorText);
        throw new Error(`RAG backend returned ${apiRes.status}: ${errorText}`);
      }

      const dataRes = await apiRes.json();
      answer = String(dataRes.answer || "");
      sources = Array.isArray(dataRes.sources) ? dataRes.sources : [];
    } catch (err) {
      console.error("AI suggest error:", err);
      return NextResponse.json(
        { error: (err as Error).message || "AI call failed" },
        { status: 500 },
      );
    }
  }

  const aiMessage = {
    message_id: uuidv4(),
    conversation_id: conversationId,
    message_text: answer,
    sender_id: "support_ai",
    created_at: new Date(),
  };

  const updateResult = await client
    .db("Ignisia")
    .collection("tickets")
    .updateOne(
      { conversation_id: conversationId },
      {
        $push: { messages: aiMessage },
        $set: {
          updated_at: new Date(),
          issue: prompt,
          relevant_context: (sources as any[])
            .filter((source) => typeof source.doc_id === "string")
            .map((source) => source.doc_id),
          resolution: answer,
        },
      },
    );

  if (!updateResult.acknowledged) {
    return NextResponse.json(
      { error: "Failed to store AI response" },
      { status: 500 },
    );
  }

  const citations = sources
    .filter(
      (source): source is { doc_id: string; page_num: number } =>
        typeof source.doc_id === "string" &&
        typeof source.page_num === "number",
    )
    .map((source) => `${source.doc_id} (page ${source.page_num})`);

  return NextResponse.json({ response: answer, citations });
}
