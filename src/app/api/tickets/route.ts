import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import clientPromise from "@/lib/mongodb";
import { ObjectId } from "mongodb";
import { v4 as uuidv4 } from "uuid";

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const url = new URL(request.url);
  const queryUserId = url.searchParams.get("userId");

  const client = await clientPromise;
  const where: any = {};

  if (queryUserId) {
    where.user1_id = queryUserId;
  } else if (session.user.role === "user") {
    where.user1_id = session.user.id;
  }

  const tickets = await client
    .db("Ignisia")
    .collection("tickets")
    .find(where)
    .sort({ created_at: -1 })
    .toArray();

  return NextResponse.json(tickets);
}

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await request.json();
  const title = (data.title || "").toString().trim();
  const description = (data.description || "").toString().trim();

  if (!title || !description) {
    return NextResponse.json(
      { error: "Missing title or description" },
      { status: 400 },
    );
  }

  const client = await clientPromise;
  const conversationId = `conv_${uuidv4()}`;
  const now = new Date();

  // Call RAG backend with the initial description
  const ragServerUrl = process.env.RAG_MODEL_ENDPOINT || "";
  let ragAnswer = "";
  let ragSources: Array<{ doc_id?: string; page_num?: number }> = [];

  if (ragServerUrl) {
    try {
      const ragRes = await fetch(ragServerUrl, {
        method: "POST",
        headers: {
          accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question: description }),
      });

      if (ragRes.ok) {
        const ragData = await ragRes.json();
        ragAnswer = String(ragData.answer || "");
        ragSources = Array.isArray(ragData.sources) ? ragData.sources : [];
      }
    } catch (err) {
      console.error("RAG call failed during ticket creation:", err);
      // Continue without RAG data
    }
  }

  const userMessage = {
    message_id: uuidv4(),
    conversation_id: conversationId,
    sender_id: session.user.id,
    message_text: description,
    created_at: now,
  };

  const messages = [userMessage];

  // Add RAG response as AI message if available
  if (ragAnswer) {
    messages.push({
      message_id: uuidv4(),
      conversation_id: conversationId,
      sender_id: "support_ai",
      message_text: ragAnswer,
      created_at: new Date(),
    });
  }

  const ticket = {
    conversation_id: conversationId,
    user1_id: session.user.id,
    user2_id: null,
    title,
    description,
    status: "open",
    created_at: now,
    updated_at: now,
    issue: description,
    relevant_context: ragSources
      .filter((source) => typeof source.doc_id === "string")
      .map((source) => source.doc_id),
    resolution: ragAnswer,
    messages,
  };

  const result = await client
    .db("Ignisia")
    .collection("tickets")
    .insertOne(ticket);

  return NextResponse.json({ insertedId: result.insertedId, ...ticket });
}

export async function PATCH(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await request.json();
  const ticketId = data.ticketId;
  const status = data.status;

  if (!ticketId || !status) {
    return NextResponse.json(
      { error: "Missing ticketId or status" },
      { status: 400 },
    );
  }

  const client = await clientPromise;
  const result = await client
    .db("Ignisia")
    .collection("tickets")
    .updateOne(
      { _id: new ObjectId(ticketId) },
      { $set: { status: status, updated_at: new Date() } },
    );

  if (!result.modifiedCount) {
    return NextResponse.json({ error: "Ticket not updated" }, { status: 400 });
  }

  return NextResponse.json({ success: true });
}
