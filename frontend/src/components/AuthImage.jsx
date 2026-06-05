import { useEffect, useState } from "react";
import { getToken } from "../auth";

// Loads an image from an authenticated endpoint by fetching it with the bearer
// token and turning the response into an object URL (a plain <img src> can't
// send the Authorization header).
export default function AuthImage({ url, alt = "", className = "", fallback = null }) {
  const [src, setSrc] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    let objectUrl;
    if (!url) return;
    setFailed(false);
    setSrc(null);
    (async () => {
      try {
        const res = await fetch(url, { headers: { Authorization: `Bearer ${await getToken()}` } });
        if (!res.ok) throw new Error(String(res.status));
        const blob = await res.blob();
        objectUrl = URL.createObjectURL(blob);
        if (active) setSrc(objectUrl);
      } catch {
        if (active) setFailed(true);
      }
    })();
    return () => {
      active = false;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  if (failed) return fallback;
  if (!src) {
    return (
      <div className={`flex items-center justify-center bg-slate-100 ${className}`}>
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-500" />
      </div>
    );
  }
  return <img src={src} alt={alt} className={className} />;
}
