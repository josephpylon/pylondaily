// Cloudflare Pages Function: /api/daily
// Counts how everyone did on each day's Daily Drive, so the game can say "you beat X% of players today".
// Setup (Cloudflare dashboard): Workers & Pages > KV > create a namespace, then in this Pages project
// Settings > Functions > KV namespace bindings, bind it with the variable name HM_STATS.
//
// GET  /api/daily?date=YYYY-MM-DD                  -> {"counts":{"<score>":n,...}}
// POST /api/daily?date=YYYY-MM-DD  {"s":score,"id":device}  -> same, after counting this result once
// score: a touchdown in n plays = 200 - n, otherwise the yards reached (0-99). Higher is better.

const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status,
  headers: { "content-type": "application/json", "cache-control": "no-store" },
});

export async function onRequest({ request, env }) {
  if (!env.HM_STATS) return json({ error: "HM_STATS binding missing" }, 500);
  const url = new URL(request.url);
  const date = url.searchParams.get("date") || "";
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) return json({ error: "bad date" }, 400);
  const key = "d:" + date;

  if (request.method === "POST") {
    const b = await request.json().catch(() => null);
    const s = b && Number.isInteger(b.s) && b.s >= 0 && b.s <= 200 ? b.s : null;
    const id = b && typeof b.id === "string" && /^[a-z0-9]{8,40}$/.test(b.id) ? b.id : null;
    if (s === null || !id) return json({ error: "bad result" }, 400);
    const seenKey = "p:" + date + ":" + id;
    // one result per device per day
    if (!(await env.HM_STATS.get(seenKey))) {
      const cur = JSON.parse((await env.HM_STATS.get(key)) || "{}");
      cur[s] = (cur[s] || 0) + 1;
      await env.HM_STATS.put(key, JSON.stringify(cur), { expirationTtl: 60 * 60 * 24 * 60 });
      await env.HM_STATS.put(seenKey, String(s), { expirationTtl: 60 * 60 * 24 * 3 });
    }
  } else if (request.method !== "GET") {
    return json({ error: "method" }, 405);
  }
  const counts = JSON.parse((await env.HM_STATS.get(key)) || "{}");
  return json({ counts });
}
