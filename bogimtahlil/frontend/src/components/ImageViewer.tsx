import { ExternalLink, Maximize2, Minus, Plus, RotateCcw } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "./ui/button";

export function ImageViewer({ src, alt, width, height }: { src: string; alt: string; width: number; height: number }) {
  const [scale, setScale] = useState(1);
  const boxRef = useRef<HTMLDivElement>(null);
  const zoom = (d: number) => setScale((s) => Math.min(4, Math.max(1, +(s + d).toFixed(2))));
  const fullscreen = () => {
    const el = boxRef.current;
    if (el?.requestFullscreen) void el.requestFullscreen();
    else window.open(src, "_blank", "noopener");
  };
  return (
    <div className="space-y-3">
      <div ref={boxRef} className="checker relative h-[360px] overflow-auto rounded-lg md:h-[440px] [&:fullscreen]:h-screen">
        <div className="flex min-h-full min-w-full items-center justify-center" style={{ width: `${scale * 100}%`, height: `${scale * 100}%` }}>
          <img src={src} alt={alt} className="max-h-full max-w-full object-contain" draggable={false} />
        </div>
      </div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <Button size="icon" variant="outline" onClick={() => zoom(-0.5)} disabled={scale <= 1} aria-label="Kichiklashtirish"><Minus /></Button>
          <span className="w-14 text-center text-sm tabular-nums text-muted">{Math.round(scale * 100)}%</span>
          <Button size="icon" variant="outline" onClick={() => zoom(0.5)} disabled={scale >= 4} aria-label="Kattalashtirish"><Plus /></Button>
          <Button size="icon" variant="ghost" onClick={() => setScale(1)} aria-label="Asl holatga qaytarish"><RotateCcw /></Button>
        </div>
        <div className="flex items-center gap-1">
          <Button size="sm" variant="outline" onClick={fullscreen}><Maximize2 /> To‘liq ekran</Button>
          <Button size="sm" variant="ghost" asChild>
            <a href={src} target="_blank" rel="noopener"><ExternalLink /> Alohida ochish</a>
          </Button>
        </div>
      </div>
      <p className="text-xs text-muted">Tasvir o‘lchamlari: {width} × {height} piksel</p>
    </div>
  );
}
