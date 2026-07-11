import React from 'react';

const SUPPORTED_LANGUAGES = [
  'English',
  'Pidgin',
  'Swahili',
  'Twi',
  'Oromo',
  'Amharic',
];

const getFlag = (lang) => {
  const lowerLang = lang?.toLowerCase() || '';

  if (lowerLang.includes('english')) return null;
  if (lowerLang.includes('pidgin')) return '🇳🇬';
  if (lowerLang.includes('swahili')) return '🇰🇪';
  if (lowerLang.includes('twi')) return '🇬🇭';
  if (lowerLang.includes('oromo') || lowerLang.includes('amharic')) return '🇪🇹';

  return '🌍';
};

export default function Header({ language, onLanguageChange }) {
  const currentFlag = getFlag(language);

  return (
    <header className="flex items-center justify-between py-3 px-2 md:px-4 w-full bg-transparent">
      <div className="flex items-center gap-3">
        <div className="relative shrink-0">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-health-accent to-health-aiBubble p-[2px]">
            <div className="w-full h-full rounded-full bg-health-bg flex items-center justify-center overflow-hidden">
              <span className="text-xl">👩🏾‍⚕️</span>
            </div>
          </div>

          <div className="absolute bottom-0 right-0 w-3 h-3 rounded-full border-2 border-health-surface bg-green-500"></div>
        </div>

        <div>
          <h2 className="font-brand font-extrabold text-health-textPrimary text-lg leading-none tracking-wide">
            HealthBridge <span className="text-emerald-400">Africa</span>
          </h2>

          <p className="text-health-textSecondary text-[11px] font-medium mt-1 uppercase tracking-wider">
            Online · Health Companion
          </p>
        </div>
      </div>

      <div className="flex items-center gap-2 bg-health-chat border border-health-border px-3 py-1.5 rounded-full shadow-sm shrink-0">
        {currentFlag && (
          <span className="text-lg leading-none">{currentFlag}</span>
        )}

        <select
          value={language || 'English'}
          onChange={(e) => onLanguageChange?.(e.target.value)}
          className="bg-health-chat text-health-textPrimary text-sm font-medium rounded-md px-1 py-0.5 cursor-pointer focus:outline-none border-none"
        >
          {SUPPORTED_LANGUAGES.map((lang) => (
            <option
              key={lang}
              value={lang}
              style={{
                backgroundColor: '#352014',
                color: '#FDF6E3',
              }}
            >
              {lang}
            </option>
          ))}
        </select>
      </div>
    </header>
  );
}