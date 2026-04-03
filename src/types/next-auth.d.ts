import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
  interface User {
    id?: string;
    role?: string;
    dbSecret?: string;
    permissions?: string[];
    workFromHome?: boolean;
  }

  interface Session {
    user: {
      id?: string;
      name?: string;
      email?: string;
      role?: string;
      permissions?: string[];
      dbSecret?: string;
      workFromHome?: boolean;
    }; // This ensures 'name', 'email' are still there
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: string;
    dbSecret?: string;
    permissions?: string[];
    workFromHome?: boolean;
  }
}
