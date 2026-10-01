import type { CSSProperties } from "react";

export type IconName = "grid" | "pulse" | "clock" | "tools" | "book" | "shield" | "wifi" | "check" | "arrow" | "download" | "globe" | "close" | "play" | "info" | "trash" | "laptop";
const paths: Record<IconName, string> = {
  grid: "M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z",
  pulse: "M2 12h4l3-8 5 16 3-8h5",
  clock: "M12 8v5l3 2 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  tools: "m14 6 4 4 M4 20l8-8 M15 3a6 6 0 0 0-7 7L3 15a4 4 0 0 0 6 6l5-5a6 6 0 0 0 7-7l-4 4-6-6 4-4",
  book: "M12 5v16 M12 5C9 2 4 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-2-1-7-2-10 1",
  shield: "M12 3 3 7v5c0 5 9 10 9 10s9-5 9-10V7l-9-4 M8 12l3 3 5-6",
  wifi: "M2 8a16 16 0 0 1 20 0 M5 12a11 11 0 0 1 14 0 M8 16a6 6 0 0 1 8 0 M12 20h.01",
  check: "m5 12 4 4L19 6",
  arrow: "M5 12h14 m-5-5 5 5-5 5",
  download: "M12 3v12 m-5-5 5 5 5-5 M4 16v5h16v-5",
  globe: "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0 M3 12h18 M12 3c-5 5-5 13 0 18 5-5 5-13 0-18",
  close: "m6 6 12 12 M6 18 18 6",
  play: "m9 5 11 7-11 7V5",
  info: "M12 11v6 M12 7h.01 M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  trash: "M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7",
  laptop: "M4 3h16v13H4z M2 20h20l-2-4H4l-2 4",
};
export function Icon({ name, size = 20, style }: { name: IconName; size?: number; style?: CSSProperties }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={style}><path d={paths[name]} /></svg>;
}
