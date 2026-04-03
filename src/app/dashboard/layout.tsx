import { getServerSession } from "next-auth";
import SignOutButton from "@/components/SignoutButton";
import Link from "next/link";
import { authOptions } from "@/app/api/auth/[...nextauth]/route";


export const dynamic = "force-dynamic";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
    const session = await getServerSession(authOptions);
    // console.log(">>> FULL SESSION USER:", JSON.stringify(session?.user));
    const perms = session?.user?.permissions || [];
    const isAdmin = session?.user?.role === "admin";

    return (
        <div className="flex min-h-screen bg-gray-100">
            {/* Sidebar */}
            <aside className="w-64 bg-slate-900 text-white flex flex-col">
                <div className="p-6 text-xl font-bold border-b border-slate-800">
                    Service Portal
                </div>

                <div className="p-4 border-t border-slate-800">
                    <div className="text-xs text-slate-400 mb-2">Logged in as:</div>
                    <div className="text-sm truncate mb-4">{session?.user?.email}</div>
                    <SignOutButton />
                </div>
            </aside>

            {/* Main Content Area */}
            <main className="flex-1 overflow-y-auto">
                {children}
            </main>
        </div>
    );
}