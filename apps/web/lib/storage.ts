/** Supabase Storage helper (server-only). Service-role key never reaches
 * the client — signed URLs are generated per-request and short-lived. */

const BUCKET = "documents";

export async function getSignedDocumentUrl(path: string, expiresIn = 3600): Promise<string> {
  const res = await fetch(
    `${process.env.SUPABASE_URL ?? deriveUrlFromDb()}/storage/v1/object/sign/${BUCKET}/${path}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
        apikey: process.env.SUPABASE_SERVICE_ROLE_KEY ?? "",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ expiresIn }),
      cache: "no-store",
    }
  );
  if (!res.ok) throw new Error(`signed url failed: ${res.status} ${await res.text()}`);
  const { signedURL } = (await res.json()) as { signedURL: string };
  return `${process.env.SUPABASE_URL ?? deriveUrlFromDb()}/storage/v1${signedURL}`;
}

function deriveUrlFromDb(): string {
  throw new Error("SUPABASE_URL is not set in the environment");
}
