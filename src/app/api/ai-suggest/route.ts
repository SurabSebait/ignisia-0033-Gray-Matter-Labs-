import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import clientPromise from "@/lib/mongodb";

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

  if (!ragServerUrl) {
    // Fallback fake response for local/dummy state
    const response = `AI suggestion based on: ${prompt.slice(0, 240)}`;
    const citations = [
      "https://example.com/reference/1",
      "https://example.com/reference/2",
    ];

    return NextResponse.json({ response, citations });
  }

  try {
    const conversationHistory = ticket.messages || [];

    const apiRes = await fetch(ragServerUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ conversationHistory, prompt }),
    });

    if (!apiRes.ok) {
      throw new Error("AI service returned error");
    }

    const dataRes = await apiRes.json();
    return NextResponse.json({
      response: dataRes.response,
      citations: dataRes.citations || [],
    });
  } catch (err) {
    return NextResponse.json(
      { error: (err as Error).message || "AI call failed" },
      { status: 500 },
    );
  }
}
