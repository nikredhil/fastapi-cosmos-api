import { useEffect, useRef, useState } from "react";
import { Button, Modal } from "./ui";
import { CameraIcon } from "./icons";

// Reusable webcam capture modal. Calls onCapture(file) with a JPEG File, then
// the caller closes it. Works on desktop and mobile via getUserMedia.
export default function CameraCapture({ title = "Take a photo", onCapture, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const [error, setError] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setError("This browser can't access the camera. Choose a file instead.");
        return;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (videoRef.current) videoRef.current.srcObject = stream;
        setReady(true);
      } catch {
        setError("Couldn't access the camera. Check the browser permission, or choose a file.");
      }
    })();
    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  function capture() {
    const video = videoRef.current;
    if (!video || !video.videoWidth) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onCapture(new File([blob], `capture-${Date.now()}.jpg`, { type: "image/jpeg" }));
      },
      "image/jpeg",
      0.92
    );
  }

  return (
    <Modal title={title} onClose={onClose}>
      {error ? (
        <div className="space-y-4">
          <p className="text-sm text-red-600">{error}</p>
          <div className="flex justify-end">
            <Button variant="secondary" onClick={onClose}>Close</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <video ref={videoRef} autoPlay playsInline className="w-full rounded-xl bg-black" />
          <div className="flex justify-between gap-2">
            <Button variant="secondary" onClick={onClose}>Cancel</Button>
            <Button onClick={capture} disabled={!ready}>
              <CameraIcon className="h-4 w-4" /> Capture
            </Button>
          </div>
        </div>
      )}
    </Modal>
  );
}
