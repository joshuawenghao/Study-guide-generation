type PreviewIconProps = {
  iconKey?: string;
  className?: string;
};

export const PREVIEW_CALLOUT_ICON_KEYS = {
  default: "spark",
  success: "check-badge",
  warning: "alert",
} as const;

function joinClasses(...values: Array<string | undefined>): string {
  return values.filter(Boolean).join(" ");
}

const ICON_PATHS: Record<string, JSX.Element> = {
  spark: (
    <path d="M12 3 13.9 8.1 19 10 13.9 11.9 12 17 10.1 11.9 5 10 10.1 8.1Z" />
  ),
  target: (
    <>
      <circle cx="12" cy="12" r="8" />
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </>
  ),
  lightning: <path d="M13 2 5 14h5l-1 8 8-12h-5Z" />,
  book: (
    <>
      <path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v16H5.5C4.7 20 4 19.3 4 18.5Z" />
      <path d="M20 5.5C20 4.7 19.3 4 18.5 4H13v16h5.5c.8 0 1.5-.7 1.5-1.5Z" />
      <path d="M11 6h2" />
    </>
  ),
  books: (
    <>
      <path d="M4.5 6.5c0-.8.7-1.5 1.5-1.5h4.5v12H6c-.8 0-1.5.7-1.5 1.5Z" />
      <path d="M10.5 5H15c.8 0 1.5.7 1.5 1.5V18h-4.5c-.8 0-1.5.7-1.5 1.5Z" />
      <path d="M16.5 7H19c.8 0 1.5.7 1.5 1.5V19h-4" />
      <path d="M6.5 8h2.5M12.5 8H15M17.5 10h1.5" />
    </>
  ),
  compass: (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="m15.5 8.5-2.5 7-4 2 2.5-7Z" />
      <path d="M12 4v2M12 18v2M4 12h2M18 12h2" />
    </>
  ),
  gamepad: (
    <>
      <path d="M7 9h10a4 4 0 0 1 3.8 5.4l-1 3A2.5 2.5 0 0 1 17.4 19a2.5 2.5 0 0 1-1.8-.8L13.8 16h-3.6l-1.8 2.2a2.5 2.5 0 0 1-1.8.8 2.5 2.5 0 0 1-2.4-1.6l-1-3A4 4 0 0 1 7 9Z" />
      <path d="M8 12h3M9.5 10.5v3" />
      <circle cx="16.5" cy="12" r=".9" />
      <circle cx="18.7" cy="10.8" r=".9" />
    </>
  ),
  layers: (
    <>
      <path d="m12 4 8 4-8 4-8-4Z" />
      <path d="m4 12 8 4 8-4" />
      <path d="m4 16 8 4 8-4" />
    </>
  ),
  map: (
    <>
      <path d="M3 6.5 8 4l8 2.5L21 4v13.5L16 20l-8-2.5L3 20Z" />
      <path d="M8 4v13.5" />
      <path d="M16 6.5V20" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="m20 20-4.2-4.2" />
    </>
  ),
  glasses: (
    <>
      <circle cx="7.5" cy="13" r="3.5" />
      <circle cx="16.5" cy="13" r="3.5" />
      <path d="M11 13h2M3.5 11l1-4h5l1 4M13.5 11l1-4h5l1 4" />
    </>
  ),
  reader: (
    <>
      <circle cx="8.5" cy="6.5" r="2.2" />
      <path d="M6 20v-5.5a2.5 2.5 0 0 1 2.5-2.5h2" />
      <path d="M12.5 10 19 8.5v8l-6.5 1.5Z" />
      <path d="M12.5 10v8" />
      <path d="M15 11.5v3.5" />
    </>
  ),
  notes: (
    <>
      <rect x="5" y="4.5" width="12" height="15" rx="1.5" />
      <path d="M8 8h6M8 11h6M8 14h4" />
      <path d="m17 16 2.5 2.5" />
      <path d="m18.2 14.8 1.8 1.8-2.8 2.8-1.8-1.8Z" />
    </>
  ),
  "message-check": (
    <>
      <path d="M5 6.5h14v9H9l-4 3z" />
      <path d="m10 11 2 2 4-4" />
    </>
  ),
  pin: (
    <>
      <path d="M12 21v-6" />
      <path d="M8 10V4h8v6l2 2H6Z" />
    </>
  ),
  clipboard: (
    <>
      <path d="M9 4h6" />
      <rect x="6" y="5" width="12" height="15" rx="1.5" />
      <path d="M9 8h6" />
    </>
  ),
  "clipboard-notes": (
    <>
      <path d="M9 4h6" />
      <rect x="6" y="5" width="12" height="15" rx="1.5" />
      <path d="M9 8h6M9 11h6M9 14h4" />
      <path d="m15.5 15.5 2.8 2.8" />
    </>
  ),
  checklist: (
    <>
      <path d="m5 7 1.5 1.5L9 6" />
      <path d="M11 7h8" />
      <path d="m5 12 1.5 1.5L9 11" />
      <path d="M11 12h8" />
      <path d="m5 17 1.5 1.5L9 16" />
      <path d="M11 17h8" />
    </>
  ),
  pencil: (
    <>
      <path d="m4 20 4.5-1 9.7-9.7-3.5-3.5L5 15.5Z" />
      <path d="m13.8 6.2 3.5 3.5" />
      <path d="M4 20h4.5" />
    </>
  ),
  stairs: <path d="M4 18h4v-4h4v-4h4V6h4" />,
  gauge: (
    <>
      <path d="M5 16a7 7 0 1 1 14 0" />
      <path d="m12 12 4-3" />
      <path d="M12 16h.01" />
    </>
  ),
  key: (
    <>
      <circle cx="8" cy="12" r="3" />
      <path d="M11 12h9" />
      <path d="M17 12v3" />
      <path d="M14 12v2" />
    </>
  ),
  alert: (
    <>
      <path d="M12 4 20 19H4Z" />
      <path d="M12 9v4" />
      <path d="M12 16h.01" />
    </>
  ),
  "check-badge": (
    <>
      <circle cx="12" cy="12" r="8" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </>
  ),
};

export function hasPreviewIcon(iconKey?: string): boolean {
  return typeof iconKey === "string" && iconKey in ICON_PATHS;
}

export default function PreviewIcon({
  iconKey,
  className,
}: PreviewIconProps): JSX.Element | null {
  if (!iconKey || !hasPreviewIcon(iconKey)) {
    return null;
  }

  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={joinClasses("h-5 w-5 shrink-0", className)}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {ICON_PATHS[iconKey]}
    </svg>
  );
}
