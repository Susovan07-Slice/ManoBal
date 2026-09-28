"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { HeartPulse, Shield, Brain, TrendingUp, Moon, Briefcase, Users, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import Image from "next/image";

const SLIDE_MS = 5000;

interface SlideData {
  id: number;
  headlineBefore: string;
  headlineBold: string;
  headlineAfter: string;
  tagline: string;
  chips: React.ElementType[];
}

const SLIDES: SlideData[] = [
  {
    id: 1,
    headlineBefore: "Your Mind. ",
    headlineBold: "Your Strength.",
    headlineAfter: "",
    tagline: "ManoBal, your daily wellness check-in. Two minutes for yourself.",
    chips: [HeartPulse, Shield, Brain]
  },
  {
    id: 2,
    headlineBefore: "Check in daily. ",
    headlineBold: "Know where you stand.",
    headlineAfter: "",
    tagline: "One short assessment. A clear wellbeing score. Trends you can follow.",
    chips: [TrendingUp, Moon, Briefcase]
  },
  {
    id: 3,
    headlineBefore: "Help is ",
    headlineBold: "one tap away.",
    headlineAfter: "",
    tagline: "Voluntary. Non-punitive. Ask for welfare support whenever you need it.",
    chips: [HeartPulse, Users, ShieldCheck]
  }
];

export function StoryOnboarding() {
  const router = useRouter();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [progress, setProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  const progressRef = useRef<number>(0);
  const lastTimeRef = useRef<number>(0);
  const rafRef = useRef<number>(null);
  
  const finishOnboarding = useCallback(() => {
    try {
      localStorage.setItem("manobal_onboarding_seen", "1");
    } catch (e) {
      // ignore
    }
    router.replace("/login");
  }, [router]);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(mediaQuery.matches);
    const handler = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  const goToNext = useCallback(() => {
    if (currentSlide < SLIDES.length - 1) {
      setCurrentSlide((prev) => prev + 1);
      progressRef.current = 0;
      setProgress(0);
    }
  }, [currentSlide]);

  const goToPrev = useCallback(() => {
    if (currentSlide > 0) {
      setCurrentSlide((prev) => prev - 1);
      progressRef.current = 0;
      setProgress(0);
    } else {
      progressRef.current = 0;
      setProgress(0);
    }
  }, [currentSlide]);

  const animate = useCallback((time: number) => {
    if (lastTimeRef.current === 0) lastTimeRef.current = time;
    const deltaTime = time - lastTimeRef.current;
    lastTimeRef.current = time;

    if (!isPaused) {
      progressRef.current += deltaTime;
      
      if (progressRef.current >= SLIDE_MS) {
        if (currentSlide < SLIDES.length - 1) {
          goToNext();
        } else {
          progressRef.current = SLIDE_MS; // Stop at 100% on last slide
          setProgress(100);
        }
      } else {
        setProgress((progressRef.current / SLIDE_MS) * 100);
      }
    }
    rafRef.current = requestAnimationFrame(animate);
  }, [currentSlide, isPaused, goToNext]);

  useEffect(() => {
    lastTimeRef.current = performance.now();
    rafRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [animate]);

  // Touch handling for swipes
  const touchStartRef = useRef<number | null>(null);
  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartRef.current = e.touches[0].clientX;
    setIsPaused(true);
  };
  const handleTouchMove = (e: React.TouchEvent) => {
    if (!touchStartRef.current) return;
    const diff = touchStartRef.current - e.touches[0].clientX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) goToNext();
      else goToPrev();
      touchStartRef.current = null; // Consume swipe
    }
  };
  const handleTouchEnd = (e: React.TouchEvent) => {
    touchStartRef.current = null;
    setIsPaused(false);
    
    // Tap detection is handled by onClick, but we need to ensure pause state resets
  };

  const handlePointerDown = () => setIsPaused(true);
  const handlePointerUp = () => setIsPaused(false);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") goToNext();
      if (e.key === "ArrowLeft") goToPrev();
      if (e.key === "Escape") finishOnboarding();
      if (e.key === " ") {
        setIsPaused(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === " ") {
        setIsPaused(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [goToNext, goToPrev, finishOnboarding]);

  const handleAreaClick = (e: React.MouseEvent) => {
    const width = window.innerWidth;
    const clickX = e.clientX;
    if (clickX > width * 0.35) {
      goToNext();
    } else {
      goToPrev();
    }
  };

  const slide = SLIDES[currentSlide];

  return (
    <div className="max-w-md mx-auto min-h-[100dvh] relative bg-[#f1f5f9] md:py-8 flex items-center justify-center overflow-hidden select-none">
      <div 
        className="absolute inset-0 md:relative md:w-full md:h-[844px] md:rounded-[40px] overflow-hidden flex flex-col shadow-[0_20px_60px_rgba(31,110,140,0.15)]"
        style={{ background: "linear-gradient(135deg, #9FD3E8 0%, #86C5DF 100%)" }}
        role="region"
        aria-roledescription="carousel"
        aria-live="polite"
      >
        {/* Soft radial highlights */}
        <div className="absolute top-[-20%] left-[-20%] w-[80%] h-[50%] bg-white/40 blur-[80px] rounded-full pointer-events-none" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[60%] h-[40%] bg-brand-500/10 blur-[80px] rounded-full pointer-events-none" />

        {/* Top Progress & Header */}
        <div className="absolute top-0 left-0 right-0 z-50 px-4 pt-[calc(1rem+env(safe-area-inset-top,0px))] flex flex-col gap-3 pointer-events-none">
          <div className="flex gap-[6px] h-1 w-full">
            {SLIDES.map((s, i) => {
              const isCompleted = i < currentSlide;
              const isCurrent = i === currentSlide;
              return (
                <div key={s.id} className="flex-1 bg-white/45 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-ink transition-none"
                    style={{ 
                      width: isCompleted ? "100%" : isCurrent ? `${progress}%` : "0%"
                    }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between items-center px-1">
            <span className="text-[13px] text-ink font-semibold tracking-wider">
              {currentSlide + 1} - {SLIDES.length}
            </span>
            <button 
              onClick={(e) => { e.stopPropagation(); finishOnboarding(); }}
              className="text-ink-2 font-semibold text-[14px] px-2 py-1 flex items-center justify-center min-w-[44px] min-h-[44px] hover:text-ink active:opacity-70 transition-colors cursor-pointer z-50 pointer-events-auto"
              aria-label="Skip onboarding"
            >
              Skip
            </button>
          </div>
        </div>

        {/* Main Tappable Area */}
        <div 
          className="absolute inset-0 z-20"
          onClick={handleAreaClick}
          onPointerDown={handlePointerDown}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
        >
          {/* Text Content (Fixed position below top bar) */}
          <div className="absolute top-[calc(5.5rem+env(safe-area-inset-top,0px))] left-0 right-0 z-30 px-6 pointer-events-none">
            {SLIDES.map((s, i) => (
              <div 
                key={s.id} 
                className={`absolute left-6 right-6 transition-all duration-250 ease-out ${
                  i === currentSlide 
                    ? "opacity-100 translate-y-0" 
                    : "opacity-0 translate-y-3"
                }`}
                style={{ transitionDuration: reducedMotion ? '0ms' : '250ms' }}
              >
                <h1 className="text-[34px] leading-[1.15] text-ink tracking-tight mb-3">
                  <span className="font-medium">{s.headlineBefore}</span>
                  <span className="font-bold">{s.headlineBold}</span>
                  <span className="font-medium">{s.headlineAfter}</span>
                </h1>
                <p className="text-[15px] leading-[22px] text-ink-2 font-medium">
                  {s.tagline}
                </p>
              </div>
            ))}
          </div>

          {/* Hero Visuals (Fixed to occupy middle and bottom) */}
          <div className="absolute top-[35%] bottom-[120px] left-0 right-0 z-20 flex items-center justify-center pointer-events-none">
            {SLIDES.map((s, i) => {
              const isActive = i === currentSlide;
              
              // Decorative Chips
              const chips = s.chips.map((Icon, idx) => {
                const pos = [
                  { top: "10%", left: "8%", delay: "0s", dur: "4s" },
                  { top: "50%", left: "4%", delay: "1.5s", dur: "5s" },
                  { top: "25%", right: "8%", delay: "0.7s", dur: "4.5s" }
                ][idx];
                
                return (
                  <div
                    key={idx}
                    className="absolute w-16 h-16 rounded-full bg-white/45 backdrop-blur-md shadow-[0_8px_32px_rgba(31,110,140,0.12)] flex items-center justify-center border border-white/60"
                    style={{
                      top: pos.top,
                      left: pos.left,
                      right: pos.right,
                      animation: isActive && !reducedMotion ? `float ${pos.dur} ease-in-out infinite alternate ${pos.delay}` : 'none'
                    }}
                  >
                    <Icon className="w-7 h-7 text-ink opacity-80" />
                  </div>
                );
              });

              return (
                <div 
                  key={s.id} 
                  className={`absolute inset-0 flex items-center justify-center transition-all duration-350 ${
                    isActive ? "opacity-100 translate-x-0 scale-100" : i < currentSlide ? "opacity-0 -translate-x-8 scale-95" : "opacity-0 translate-x-8 scale-95"
                  }`}
                  style={{ 
                    transitionTimingFunction: "cubic-bezier(.32,.72,0,1)",
                    transitionDuration: reducedMotion ? '0ms' : '350ms'
                  }}
                >
                  {chips}

                  {/* Slide 1 Hero */}
                  {i === 0 && (
                    <div className="relative w-48 h-48 flex items-center justify-center">
                      <div className="absolute inset-0 rounded-full border border-white/40 scale-150" />
                      <div className="absolute inset-0 rounded-full border border-white/50 scale-125" />
                      <div className={`w-full h-full bg-white/90 rounded-full shadow-[0_0_40px_rgba(255,255,255,0.8)] flex items-center justify-center border-4 border-white ${isActive && !reducedMotion ? 'animate-pulse' : ''}`}>
                        <div className="w-24 h-24 relative opacity-90">
                          <Image src="/logo.png" alt="ManoBal Logo" fill className="object-contain" priority onError={(e) => (e.currentTarget.style.display='none')} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Slide 2 Hero */}
                  {i === 1 && (
                    <div className="w-64 bg-white/70 backdrop-blur-xl rounded-[32px] p-6 shadow-[0_20px_40px_rgba(31,110,140,0.15)] border border-white flex flex-col items-center">
                      <span className="text-[11px] font-bold text-ink-3 uppercase tracking-wider mb-4 block">Continuous Risk</span>
                      <div className="relative w-36 h-36 mb-2">
                        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                          <circle cx="50" cy="50" r="45" fill="none" stroke="#E0F2F9" strokeWidth="8" />
                          <circle cx="50" cy="50" r="45" fill="none" stroke="#2FBF8F" strokeWidth="8" strokeDasharray="283" strokeDashoffset={isActive ? 283 * 0.7 : 283} className="transition-all duration-1000 ease-out delay-300" strokeLinecap="round" />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <span className="text-3xl font-semibold text-ink tabular-nums leading-none">30.7</span>
                          <span className="text-[10px] text-ink-3 font-medium mt-1">/100</span>
                        </div>
                      </div>
                      <div className="px-4 py-1.5 bg-[#DFF6EC] text-[#2FBF8F] rounded-full text-[12px] font-bold uppercase tracking-wider mb-4 border border-[#2FBF8F]/20">
                        Low Risk
                      </div>
                      <div className="w-full h-12 relative flex items-end justify-between px-2">
                        {[40, 35, 45, 30, 25, 30, 20].map((val, idx) => (
                          <div key={idx} className="w-1.5 bg-brand-500/40 rounded-t-full transition-all duration-700 ease-out" style={{ height: isActive ? `${val}%` : '0%', transitionDelay: `${idx * 100}ms` }} />
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Slide 3 Hero */}
                  {i === 2 && (
                    <div className="absolute inset-0 w-full h-full flex flex-col justify-end items-center">
                      {/* Decorative bottom sheet mock */}
                      <div className="absolute bottom-[-140px] left-8 right-8 h-64 bg-white/70 backdrop-blur-xl rounded-t-[32px] border-t border-white/80 shadow-[0_-10px_40px_rgba(31,110,140,0.1)] p-5 flex flex-col gap-3">
                        <div className="w-10 h-1 bg-ink-3/30 rounded-full mx-auto mb-2" />
                        <div className="h-10 rounded-2xl border border-white/60 bg-white/50" />
                        <div className="h-10 rounded-2xl border border-white/60 bg-white/50" />
                        <div className="h-10 rounded-2xl border border-white/60 bg-white/50" />
                      </div>
                      {/* Floating pill */}
                      <div className="absolute top-[10%] left-1/2 -translate-x-1/2 bg-gradient-to-r from-brand-500 to-[#1E8FC0] rounded-full px-6 py-4 flex items-center gap-3 shadow-[0_16px_40px_rgba(31,110,140,0.3)] border border-white/20">
                        <HeartPulse className="w-6 h-6 text-white" />
                        <span className="text-white font-bold whitespace-nowrap text-[15px]">Welfare Support</span>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Bottom Area (Gradient + Button) */}
        <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-[#86C5DF] to-transparent z-30 pointer-events-none" />
        
        <div className="absolute bottom-[calc(1.5rem+env(safe-area-inset-bottom,0px))] left-6 right-6 z-40">
          <button 
            onClick={(e) => { e.stopPropagation(); currentSlide === 2 ? finishOnboarding() : goToNext(); }}
            className="w-full h-[60px] bg-white text-ink rounded-full font-bold uppercase tracking-widest text-[14px] shadow-[0_16px_40px_rgba(31,110,140,0.22)] active:scale-[.97] transition-transform pointer-events-auto flex items-center justify-center cursor-pointer select-none"
          >
            {currentSlide === 2 ? "GET STARTED" : "CONTINUE"}
          </button>
        </div>
      </div>
      
      {/* CSS Animations */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes float {
          0% { transform: translateY(0px); }
          100% { transform: translateY(-12px); }
        }
      `}} />
    </div>
  );
}
