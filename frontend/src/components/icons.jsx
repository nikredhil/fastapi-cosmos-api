// Shared line-style icons (stroke = currentColor, so color via text-* classes).

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
};

export function HomeIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M3 11l9-7 9 7" />
      <path d="M5.5 9.7V20h13V9.7" />
      <rect x="10" y="13" width="4" height="4" rx="0.6" />
    </svg>
  );
}

export function UserIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="8" r="3.4" />
      <path d="M5.5 19.5c0-3.6 2.9-6.5 6.5-6.5s6.5 2.9 6.5 6.5" />
    </svg>
  );
}

export function BillsIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M6 3h12v18l-2-1.3-2 1.3-2-1.3-2 1.3-2-1.3L6 21z" />
      <path d="M9 8h6M9 12h6" />
    </svg>
  );
}

export function KeyIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <circle cx="8" cy="8" r="3.6" />
      <path d="M10.6 10.6L19 19" />
      <path d="M16 16l1.7-1.7M18 18l1.7-1.7" />
    </svg>
  );
}

export function WalletIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <rect x="3" y="6" width="18" height="13" rx="2.5" />
      <path d="M3 10h18" />
      <circle cx="17" cy="14.5" r="1.1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ClockIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function CheckIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M8.5 12.3l2.4 2.4 4.6-5" />
    </svg>
  );
}

export function WaterIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M12 3s6 6.4 6 10.5a6 6 0 1 1-12 0C6 9.4 12 3 12 3z" />
    </svg>
  );
}

export function BoltIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M13 2 4.5 13H11l-1 9 8.5-12H12z" />
    </svg>
  );
}

export function WrenchIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

export function DocumentIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
      <path d="M14 3v5h5" />
      <path d="M9 13h6M9 17h6" />
    </svg>
  );
}

export function CameraIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
      <circle cx="12" cy="13" r="3.5" />
    </svg>
  );
}

export function ChatIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z" />
    </svg>
  );
}

export function GearIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
    </svg>
  );
}

// Friendly robot head — used for the assistant launcher.
export function RobotIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <rect x="4" y="8" width="16" height="11.5" rx="3" />
      <path d="M12 4.2V7" />
      <circle cx="12" cy="3.3" r="1" />
      <path d="M2.5 12.5v3M21.5 12.5v3" />
      <circle cx="9" cy="13" r="1.15" fill="currentColor" stroke="none" />
      <circle cx="15" cy="13" r="1.15" fill="currentColor" stroke="none" />
      <path d="M9.5 16.5h5" />
    </svg>
  );
}

// Stacked banknotes with a centre coin — used for "Rent & Bills".
export function CashIcon({ className = "" }) {
  return (
    <svg {...base} className={className}>
      <rect x="2.5" y="6" width="19" height="9.5" rx="1.6" />
      <circle cx="12" cy="10.75" r="2.4" />
      <path d="M5 19c2.2 1.1 4.4 1.1 7 0s4.8-1.1 7 0" />
    </svg>
  );
}

// Map a bill type to its icon component.
export const BILL_TYPE_ICONS = {
  rent: HomeIcon,
  water: WaterIcon,
  electricity: BoltIcon,
  maintenance: WrenchIcon,
  other: DocumentIcon,
};

export function BillTypeIcon({ type, className = "" }) {
  const Icon = BILL_TYPE_ICONS[type] || DocumentIcon;
  return <Icon className={className} />;
}


// Layout-grid "dashboard" glyph: two panels on top, a wide bar below.
export function DashboardIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      <rect x="3" y="3" width="7.5" height="11" rx="2" />
      <rect x="13.5" y="3" width="7.5" height="11" rx="2" />
      <rect x="3" y="17" width="18" height="4" rx="2" />
    </svg>
  );
}

// Group of three people — used for "Tenants".
export function TenantsIcon({ className = "" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"
      strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
      {/* side people */}
      <circle cx="5" cy="10" r="2.1" />
      <path d="M2.4 18.5c0-2 1.3-3.7 3.1-4.2" />
      <circle cx="19" cy="10" r="2.1" />
      <path d="M21.6 18.5c0-2-1.3-3.7-3.1-4.2" />
      {/* center person */}
      <circle cx="12" cy="8" r="3" />
      <path d="M7 19c0-2.8 2.2-5 5-5s5 2.2 5 5" />
    </svg>
  );
}

// High-rise building: rooftop box, a grid of windows, a door, on a ground line.
export function BuildingIcon({ className = "" }) {
  const cols = [7.6, 10.9, 14.2];
  const rows = [6.9, 9.4, 11.9, 14.4];
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round"
      strokeLinejoin="round" className={className} aria-hidden="true">
      {/* ground line, wider than the base */}
      <path d="M2.5 21h19" strokeWidth="1.8" />
      {/* body + rooftop box */}
      <path d="M6 21V5.5h12V21" strokeWidth="1.8" />
      <path d="M10 5.5V3h4v2.5" strokeWidth="1.8" />
      {/* door */}
      <path d="M10.25 21v-3.4h3.5V21" strokeWidth="1.6" />
      {/* windows */}
      {rows.map((y) =>
        cols.map((x) => (
          <rect key={`${x}-${y}`} x={x} y={y} width="2.2" height="1.9" rx="0.4"
            strokeWidth="1.3" />
        ))
      )}
    </svg>
  );
}
