import { NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";

export async function middleware(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.NEXTAUTH_SECRET });
  const { pathname } = req.nextUrl;
  const clientIp =
    req.headers.get("x-forwarded-for")?.split(",")[0] || "127.0.0.1";
  const OFFICE_IP = process.env.OFFICE_STATIC_IP;
  // const isLocalhost = clientIp === '::1' || clientIp === '127.0.0.1'; // use during testing only
  const isWFHUser = token?.workFromHome === true;

  // Helper: Determine if this user SHOULD be restricted by IP
  // Admins bypass IP checks. If no token, we can't check role yet.
  const isRestrictedUser = token && token.role !== "admin";
  const isOffNetwork = clientIp !== OFFICE_IP && !isWFHUser;

  // If a restricted user is off-network, we must let them see the login page
  // to show the error message. We only redirect them to dashboard if they are
  // ON the office network.

  if (token && pathname === "/login") {
    if (isRestrictedUser && isOffNetwork) {
      console.log(">>> Off-network user at login: Staying here to show error.");
      return NextResponse.next();
    }
    console.log(">>> On-network/Admin at login: Redirecting to dashboard.");
    return NextResponse.redirect(new URL("/dashboard", req.url));
  }

  // Allow the login page to load for everyone
  if (pathname === "/login") {
    if (token) {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }

    return NextResponse.next();
  }

  if (pathname.startsWith("/dashboard")) {
    if (!token) {
      return NextResponse.redirect(new URL("/login", req.url));
    }

    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|favicon.ico).*)"],
};
