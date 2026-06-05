import { initials } from "../api";

const SIZES = {
  sm: "h-6 w-6 text-[10px]",
  md: "h-8 w-8 text-xs",
  lg: "h-10 w-10 text-sm",
};

export default function Avatar({ name, color = "#94a3b8", size = "md", title }) {
  return (
    <span
      title={title || name || "Unassigned"}
      style={{ backgroundColor: name ? color : "#e2e8f0", color: name ? "#fff" : "#94a3b8" }}
      className={`inline-flex shrink-0 items-center justify-center rounded-full font-semibold ring-2 ring-white ${SIZES[size]}`}
    >
      {name ? initials(name) : "·"}
    </span>
  );
}
