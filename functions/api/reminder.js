// Cloudflare Pages Function: /api/reminder?t=HH:MM&d=YYYYMMDD
// Returns a repeating daily calendar event (an .ics file) for the Daily Drive reminder.
// A real web address works on iPhones, where a file made inside the page can't be opened,
// including from the home-screen app. Nothing is stored: the time and date only shape the file.
export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const t = url.searchParams.get("t") || "09:00";
  const d = url.searchParams.get("d") || "";
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(t) || !/^20\d{6}$/.test(d)) {
    return new Response("bad time or date", { status: 400 });
  }
  const [h, m] = t.split(":").map(Number);
  const end = h * 60 + m + 10;
  const z = (v) => String(v).padStart(2, "0");
  const endT = end >= 1440 ? "235900" : `${z(Math.floor(end / 60))}${z(end % 60)}00`;
  const now = new Date().toISOString().replace(/[-:]/g, "").slice(0, 15) + "Z";
  const ics = [
    "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Pylon Daily//Reminder//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
    "BEGIN:VEVENT",
    `UID:pylon-daily-reminder-${d}-${h}${z(m)}@pylondaily.com`, `DTSTAMP:${now}`,
    `DTSTART:${d}T${z(h)}${z(m)}00`, `DTEND:${d}T${endT}`, "RRULE:FREQ=DAILY",
    "SUMMARY:🏈 Pylon Daily: today's drive is up",
    "DESCRIPTION:Keep your streak going: https://pylondaily.com", "URL:https://pylondaily.com",
    "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Pylon Daily", "TRIGGER:PT0M", "END:VALARM",
    "END:VEVENT", "END:VCALENDAR", "",
  ].join("\r\n");
  return new Response(ics, {
    headers: {
      "content-type": "text/calendar; charset=utf-8",
      "content-disposition": 'inline; filename="pylon-daily-reminder.ics"',
      "cache-control": "no-store",
    },
  });
}
