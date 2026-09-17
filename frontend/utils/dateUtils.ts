/**
 * Date and time formatting utility for Contract RAG Platform.
 * Converts ISO timestamps and date strings into dynamic, local relative dates
 * (e.g., "Just now", "5m ago", "Today, 2:45 PM", "Yesterday, 9:15 AM", "Sep 15, 2026 - 2:08 PM").
 */

export function formatFormattedDate(dateStr?: string, timestampStr?: string): string {
  const raw = timestampStr || dateStr;
  if (!raw) return "";

  let d = new Date(raw);

  // If raw string starts with "Today," or has custom formatting, attempt parsing fallback
  if (isNaN(d.getTime())) {
    if (raw.startsWith("Today, ")) {
      const timePart = raw.replace("Today, ", "").trim();
      const todayStr = new Date().toDateString();
      d = new Date(`${todayStr} ${timePart}`);
    } else if (raw.includes(" - ")) {
      const parts = raw.split(" - ");
      d = new Date(parts.join(" "));
    }
  }

  // If still unparseable, return the raw date string as fallback
  if (isNaN(d.getTime())) {
    return raw;
  }

  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  // Less than 1 minute
  if (diffSeconds >= 0 && diffSeconds < 60) {
    return "Just now";
  }

  // Less than 1 hour
  if (diffSeconds >= 60 && diffSeconds < 3600) {
    const mins = Math.floor(diffSeconds / 60);
    return `${mins}m ago`;
  }

  // Check for Today / Yesterday relative to local timezone
  const isToday =
    d.getDate() === now.getDate() &&
    d.getMonth() === now.getMonth() &&
    d.getFullYear() === now.getFullYear();

  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const isYesterday =
    d.getDate() === yesterday.getDate() &&
    d.getMonth() === yesterday.getMonth() &&
    d.getFullYear() === yesterday.getFullYear();

  const timeStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: true });

  if (isToday) {
    return `Today, ${timeStr}`;
  }
  if (isYesterday) {
    return `Yesterday, ${timeStr}`;
  }

  const dateFormatted = d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
  return `${dateFormatted} - ${timeStr}`;
}
