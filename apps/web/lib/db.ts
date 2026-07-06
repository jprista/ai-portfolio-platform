import postgres from "postgres";

declare global {
  // eslint-disable-next-line no-var
  var __sql: ReturnType<typeof postgres> | undefined;
}

export const sql =
  globalThis.__sql ??
  postgres(process.env.DATABASE_URL!, { ssl: "require", prepare: false, max: 4 });

if (process.env.NODE_ENV !== "production") globalThis.__sql = sql;
