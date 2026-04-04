import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";
import clientPromise from "@/lib/mongodb";
import { v4 as uuidv4 } from "uuid";

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const url = new URL(request.url);
  const conversationId = url.searchParams.get("conversation_id");

  if (!conversationId) {
    return NextResponse.json(
      { error: "Missing conversation_id" },
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

  // Check if user has access to this ticket
  const userRole = (session.user.role || "user").toString();
  if (
    userRole !== "admin" &&
    userRole !== "support" &&
    userRole !== "support personnel"
  ) {
    if (
      ticket.user1_id !== session.user.id &&
      ticket.user2_id !== session.user.id
    ) {
      return NextResponse.json({ error: "Access denied" }, { status: 403 });
    }
  }

  return NextResponse.json({ messages: ticket.messages || [] });
}

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const data = await request.json();
  const conversationId = (data.conversation_id || "").toString();
  const messageText = (data.message_text || "").toString();
  const senderId = (data.sender_id || session.user.id || "").toString();

  if (!conversationId || !messageText) {
    return NextResponse.json(
      { error: "Missing conversation_id or message_text" },
      { status: 400 },
    );
  }

  const client = await clientPromise;

  // Find the ticket to check access
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

  // Check if user has access to this ticket
  const userRole = (session.user.role || "user").toString();
  if (
    userRole !== "admin" &&
    userRole !== "support" &&
    userRole !== "support personnel"
  ) {
    if (
      ticket.user1_id !== session.user.id &&
      ticket.user2_id !== session.user.id
    ) {
      return NextResponse.json({ error: "Access denied" }, { status: 403 });
    }
  }

  const message = {
    message_id: uuidv4(),
    conversation_id: conversationId,
    message_text: messageText,
    sender_id: senderId,
    created_at: new Date(),
  };

  const updateResult = await client
    .db("Ignisia")
    .collection("tickets")
    .updateOne(
      { conversation_id: conversationId },
      { $push: { messages: message }, $set: { updated_at: new Date() } },
    );

  if (!updateResult.acknowledged) {
    return NextResponse.json(
      { error: "Failed to update conversation" },
      { status: 500 },
    );
  }

  return NextResponse.json({ success: true });
}
