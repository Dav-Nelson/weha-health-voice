import React, { useState } from 'react';

const LANGUAGES = [
  { id: 'en', code: 'ng', name: 'English', native: 'English', tagline: "Let's talk about your health" },
  { id: 'yo', code: 'ng', name: 'Yoruba', native: 'Yorùbá', tagline: "Jẹ́ ká sọ̀rọ̀ nípa ìlera rẹ" },
  { id: 'ak', code: 'gh', name: 'Akan', native: 'Akan', tagline: "Mma yɛnkasa fa wo apɔwmuden ho" },
  { id: 'pi', code: 'ng', name: 'Pidgin', native: 'Naija', tagline: "Make we tok about your health" },
  { id: 'am', code: 'et', name: 'Amharic', native: 'አማርኛ', tagline: "ስለ ጤናዎ እናውራ" },
];

export default function OnboardingModal({ onComplete }) {
  const [selectedLanguage, setSelectedLanguage] = useState(null);

  const handleContinue = () => {
    if (selectedLanguage) {
      onComplete(selectedLanguage);
    }
  };

  return (
    <div className="fixed inset-0 z-50 w-full h-full bg-health-bg font-body flex flex-col items-center justify-center p-4 overflow-hidden">

      <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.04]">
        <svg viewBox="0 0 100 100" className="w-[120vw] h-[120vw] max-w-[800px] max-h-[800px] animate-spin-slow fill-health-accent">
          <path d="M50 0 C60 20, 80 40, 100 50 C80 60, 60 80, 50 100 C40 80, 20 60, 0 50 C20 40, 40 20, 50 0 Z" />
          <circle cx="50" cy="50" r="15" className="fill-health-bg" />
        </svg>
      </div>

      <div className="relative z-10 w-full max-w-md flex flex-col h-[90vh] max-h-[800px]">

        <div className="text-center mb-6 pt-8">
          <h1 className="font-brand font-extrabold text-4xl text-health-textPrimary tracking-wide mb-2">
            Weha <span className="text-health-accentLight">Health</span>
          </h1>
          <div className="h-[2px] w-3/4 mx-auto bg-gradient-to-r from-health-accent via-health-accentLight to-health-aiBubble mb-4 rounded-full"></div>
          <p className="text-health-textSecondary text-lg font-light">
            Choose your language to begin
          </p>
        </div>

        <div className="flex-1 overflow-y-auto hide-scrollbar space-y-3 pb-4 px-2">
          {LANGUAGES.map((lang) => {
            const isSelected = selectedLanguage?.id === lang.id;
            return (
              <button
                key={lang.id}
                onClick={() => setSelectedLanguage(lang)}
                className={`w-full text-left p-4 rounded-xl border transition-all duration-300 flex items-center gap-4 group
                  ${isSelected
                    ? 'bg-health-surface border-health-accent shadow-[0_0_15px_rgba(212,131,10,0.15)]'
                    : 'bg-health-surface/60 border-health-border hover:border-health-textSecondary hover:bg-health-surface'
                  }`}
              >
                <div className="shrink-0 flex items-center justify-center w-8 h-8 rounded-full overflow-hidden bg-health-chat border border-health-border">
                  {lang.name === 'English' ? (
                    <span className="text-lg leading-none">🌍</span>
                  ) : (
                    <img
                      src={`https://flagcdn.com/w40/${lang.code}.png`}
                      alt={`${lang.name} flag`}
                      className="w-full h-full object-cover"
                    />
                  )}
                </div>

                <div className="flex-1">
                  <div className="flex items-baseline gap-2">
                    <span className="text-health-textPrimary font-bold text-lg">{lang.name}</span>
                    <span className="text-health-textSecondary text-sm">{lang.native}</span>
                  </div>
                  <p className="text-health-textSecondary font-light text-sm italic mt-0.5">
                    "{lang.tagline}"
                  </p>
                </div>

                <div className={`shrink-0 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all duration-300
                  ${isSelected ? 'border-health-accent bg-health-accent text-health-bg' : 'border-health-border border-dashed text-transparent'}
                `}>
                  <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 20 20">
                    <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
                  </svg>
                </div>
              </button>
            );
          })}
        </div>

        <div className="pt-4 pb-2 mt-auto text-center flex flex-col gap-4">
          <button
            onClick={handleContinue}
            disabled={!selectedLanguage}
            className={`w-full py-4 rounded-full font-bold text-lg transition-all duration-300 flex items-center justify-center gap-2
              ${selectedLanguage
                ? 'bg-health-accent text-health-bg hover:bg-health-accentLight hover:scale-[1.02] shadow-[0_4px_20px_rgba(212,131,10,0.3)] cursor-pointer'
                : 'bg-health-surface border border-health-border text-health-textSecondary/50 cursor-not-allowed'
              }`}
          >
            Continue
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </button>

          <p className="text-health-textSecondary text-xs opacity-70 px-4">
            ⚕️ This system is not a substitute for professional medical advice. Always consult a certified doctor.
          </p>
        </div>

      </div>

      <style dangerouslySetInnerHTML={{__html: `
        .hide-scrollbar::-webkit-scrollbar { display: none; }
        .hide-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
      `}} />
    </div>
  );
}