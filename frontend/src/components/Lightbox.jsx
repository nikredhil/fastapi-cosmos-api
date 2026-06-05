import { useEffect } from "react";
import AuthImage from "./AuthImage";

// Full-screen overlay that shows an authenticated image at full size.
// Click the backdrop or press Escape to close.
export default function Lightbox({ url, alt = "", onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-slate-900/80 p-4"
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <button
        onClick={onClose}
        title="Close"
        className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-2xl leading-none text-white transition hover:bg-white/20"
      >
        ×
      </button>
      <AuthImage
        url={url}
        alt={alt}
        className="max-h-[90vh] max-w-[90vw] rounded-lg object-contain shadow-2xl"
      />
    </div>
  );
}
