"use client";

import React, { useState, useEffect, useRef } from "react";
import YouTube from "react-youtube";

const transcript: { text: string; start: number; duration: number }[] = [
  { text: "This is me at 19 years old. I was broke,", start: 0.16, duration: 4.08 },
  { text: "struggling in school, but with a dream", start: 2.56, duration: 4.319 },
  { text: "that one day I'll make it big. Today, I", start: 4.24, duration: 4.56 },
  { text: "can travel wherever I want \nto, dine at", start: 6.879, duration: 3.521 },
  { text: "the finest restaurants, and have the", start: 8.8, duration: 2.799 },
  { text: "freedom to do the things that I'm", start: 10.4, duration: 2.96 },
  { text: "passionate about. This is the story of", start: 11.599, duration: 3.441 },
  { text: "how I went from broke to becoming a", start: 13.36, duration: 3.759 },
  { text: "millionaire in 24 months. It was the", start: 15.04, duration: 4.159 },
  { text: "first quarter of 2019, the second year", start: 17.119, duration: 4.0 },
  { text: "of my school. I was studying information", start: 19.199, duration: 3.92 },
  { text: "technology and struggled with most of my", start: 21.119, duration: 4.4 },
  { text: "modules. Because of my low GPA and lack", start: 23.119, duration: 4.32 },
  { text: "of interest in studying, I knew that I", start: 25.519, duration: 3.6 },
  { text: "couldn't make it to university. That's", start: 27.439, duration: 3.68 },
  { text: "when I had an epiphany. I needed to make", start: 29.119, duration: 4.081 },
  { text: "a change or remain unsuccessful for the", start: 31.119, duration: 3.921 },
];

const normalizeTranscript = (transcript: { text: string; start: number; duration: number }[]) => {
  return transcript.map((line, idx) => {
    const next = transcript[idx + 1];
    return {
      ...line,
      end: next ? next.start : line.start + line.duration // last line keeps duration
    };
  });
};

const normalizedTranscript: { text: string; start: number; end: number }[] = normalizeTranscript(transcript);

export default function Home() {
  const [player, setPlayer] = useState<YT.Player | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  useEffect(() => {
    let animationFrame: number;

    const tick = () => {
      if (player) {
        const time = player.getCurrentTime();
        setCurrentTime(time);

        // Find active transcript line
        const idx = normalizedTranscript.findIndex(
          (line) => time >= line.start && time < line.end
        );
        if (idx !== -1) setActiveIndex(idx);
      }
      animationFrame = requestAnimationFrame(tick);
    };

    tick();
    return () => cancelAnimationFrame(animationFrame);
  }, [player]);

  // Compute visible lines
  let visibleLines: typeof normalizedTranscript = [];
  if (activeIndex !== null) {
    visibleLines = normalizedTranscript.slice(
      activeIndex - (activeIndex % 3),
      activeIndex + (3 - activeIndex % 3)
    );
  }

  return (
    <div className="gap-4 p-4">
      {/* Video */}
      <div>
        <YouTube
          videoId={"oLIkRpKLH1Y"}
          opts={{ width: "100%", height: "390" }}
          onReady={(e) => setPlayer(e.target)}
        />
      </div>

      {/* Transcript */}
      <div className="max-h-[390px] overflow-y-auto border rounded-lg p-4 bg-gray-50">
        <p className={"p-1 transition-colors text-center"}>
            {visibleLines.map((line, idx) => {
              const isActive = activeIndex !== null && idx === activeIndex % 3;
            return (
              <span key={idx} >
                {" "}
                <span className={`${isActive ? "bg-yellow-200 font-semibold" : ""}`}>{line.text}</span>
              </span>
            )
        })}
        </p>
      </div>
    </div>
  );
}
