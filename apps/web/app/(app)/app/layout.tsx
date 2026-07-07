import { Sidebar } from "@/components/sidebar";
import { requireOrg } from "@/lib/auth";
import { getPendingExtractionCount } from "@/lib/data";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { orgId } = await requireOrg();
  const pendingCount = await getPendingExtractionCount(orgId);
  return (
    <div className="flex min-h-screen">
      <Sidebar pendingCount={pendingCount} />
      <main className="min-w-0 flex-1">{children}</main>
    </div>
  );
}
