import React from 'react';

const STRESS_LEVELS = [
  { label: 'Very Calm', emoji: '😌', maxScore: 14 },
  { label: 'Calm', emoji: '🙂', maxScore: 28 },
  { label: 'Slightly Stressed', emoji: '😐', maxScore: 42 },
  { label: 'Moderate', emoji: '😕', maxScore: 57 },
  { label: 'Stressed', emoji: '😟', maxScore: 71 },
  { label: 'Highly Stressed', emoji: '😰', maxScore: 85 },
  { label: 'Extremely Stressed', emoji: '😫', maxScore: 100 },
];

export function getStressLevelIndex(score: number): number {
  for (let i = 0; i < STRESS_LEVELS.length; i++) {
    if (score <= STRESS_LEVELS[i].maxScore) return i;
  }
  return STRESS_LEVELS.length - 1;
}

export function StressEmojiScale({ score }: { score: number }) {
  const activeIndex = getStressLevelIndex(score);
  const activeLevel = STRESS_LEVELS[activeIndex];

  return (
    <div className="w-full bg-white/60 backdrop-blur-sm rounded-[20px] p-4 border border-sky-200/50 shadow-[0_4px_20px_rgba(31,110,140,0.03)] mt-6 flex flex-col gap-3 transition-all duration-300">
      <span className="text-[10px] font-bold text-ink-3 uppercase tracking-wider text-center block">
        Stress Level
      </span>
      
      <div className="flex justify-between items-center relative px-2 py-1">
        {/* Subtle connecting line behind emojis */}
        <div className="absolute left-[8%] right-[8%] h-[2px] bg-sky-200/40 top-1/2 -translate-y-1/2 z-0 rounded-full" />
        
        {STRESS_LEVELS.map((level, idx) => {
          const isActive = idx === activeIndex;
          return (
            <div
              key={idx}
              className="relative z-10 flex flex-col items-center transition-all duration-300"
            >
              <div
                className={`w-[34px] h-[34px] flex items-center justify-center rounded-full transition-all duration-300 ${
                  isActive 
                    ? 'bg-white shadow-[0_6px_16px_rgba(31,110,140,0.18)] ring-2 ring-brand-500 scale-125 z-20' 
                    : 'bg-sky-50 opacity-60 grayscale-[0.6] scale-90 border border-sky-200 hover:scale-100 hover:grayscale-0 hover:opacity-100'
                }`}
              >
                <span className="text-[18px] leading-none select-none" style={{ transform: isActive ? 'translateY(0px)' : 'translateY(1px)' }}>
                  {level.emoji}
                </span>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="text-center mt-2 flex items-center justify-center animate-fade-up">
        <span className="text-[12px] font-bold text-ink bg-white px-3 py-1.5 rounded-full border border-sky-200 shadow-sm">
          {activeLevel.label}
        </span>
      </div>
    </div>
  );
}
