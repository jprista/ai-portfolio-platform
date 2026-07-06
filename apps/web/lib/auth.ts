import { auth, currentUser } from "@clerk/nextjs/server";
import { sql } from "./db";

/** Resolves the signed-in Clerk user to an organization.
 *  Dev bootstrap: first login with the seeded e-mail claims the admin row;
 *  any other user is attached to the demo org as professional. */
export async function requireOrg(): Promise<{ orgId: string; userId: string }> {
  const { userId } = await auth();
  if (!userId) throw new Error("unauthenticated");

  const found = await sql`
    select id, org_id from core.app_users where auth_external_id = ${userId}
  `;
  if (found.length) return { orgId: found[0].org_id, userId };

  const user = await currentUser();
  const email = user?.emailAddresses?.[0]?.emailAddress ?? "";
  const name = user?.fullName || email || "Profissional";

  const claimed = await sql`
    update core.app_users set auth_external_id = ${userId}, name = ${name}
    where auth_external_id = 'pending-first-login' and email = ${email}
    returning org_id
  `;
  if (claimed.length) return { orgId: claimed[0].org_id, userId };

  const org = await sql`select id from core.organizations where slug = 'demo'`;
  const inserted = await sql`
    insert into core.app_users (org_id, auth_external_id, name, email, role)
    values (${org[0].id}, ${userId}, ${name}, ${email}, 'professional')
    returning org_id
  `;
  return { orgId: inserted[0].org_id, userId };
}
