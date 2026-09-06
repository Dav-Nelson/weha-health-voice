import React, { useState } from 'react';
import { Settings, Globe, Trash2, ShieldCheck } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const SUPPORTED_LANGUAGES = ['English', 'Pidgin', 'Yoruba', 'Akan', 'Amharic'];

const TRANSLATIONS = {
  English: { title: "System Preferences", desc: "Personalise your Weha Health experience", prefLang: "Preferred Language", prefLangDesc: "Sets the default language for your consultation. You can also change this anytime from the header.", clear: "Clear Consultation History", clearDesc: "Permanently removes your session and all conversation data from both this device and our servers.", clearing: "Clearing...", cleared: "✓ Session cleared — refresh to start fresh", btnClear: "Clear my session", privacy: "Weha Health does not collect your name, email, or any personal identity. Your conversations are stored securely and linked only to your device session. Clearing your session permanently deletes all conversation data from our servers." },
  Pidgin: { title: "System Settings", desc: "Set your Weha Health anyhow you like am", prefLang: "Language wey you prefer", prefLangDesc: "Choose the language wey you want make we use. You fit change am anytime for top.", clear: "Clear Wetin We Don Tok", clearDesc: "E go delete everything wey we don tok from your phone and our server. Next time na fresh start.", clearing: "E dey clear...", cleared: "✓ E don clear — refresh make we start fresh", btnClear: "Clear my session", privacy: "Weha Health no dey collect your name or email. Everything wey we tok na secret and e dey tied to only this your device. If you clear your session, everything go wipe patapata." },
  Yoruba: { title: "Ètò Ìṣàkóso", desc: "Ṣe Weha Health bí ó ṣe wù ọ́", prefLang: "Èdè tí O Fẹ́", prefLangDesc: "Ṣíṣe èdè àkọ́kọ́ fún ìjíròrò rẹ. O lè yí èyí padà nígbàkigbà láti orí ojú-ìwé.", clear: "Pa Ìtàn Ìjíròrò Rẹ Rẹ́", clearDesc: "Yóò yọ ìjókòó rẹ àti gbogbo dátà ìjíròrò kúrò pátápátá láti orí ẹ̀rọ yìí àti láti orí sáfà wa.", clearing: "Ń pa á rẹ́...", cleared: "✓ A ti pa ìjókòó rẹ́ — tún ojú-ìwé ṣe", btnClear: "Pa ìjókòó mi rẹ́", privacy: "Weha Health kì í gba orúkọ rẹ, email rẹ, tàbí ìdánimọ̀ rẹ. Ìjíròrò rẹ ni a ń fi pamọ́ ní ààbò. Bí o bá pa ìjókòó rẹ rẹ́, gbogbo dátà náà á parẹ́ pátápátá." },
  Akan: { title: "Nhyehyɛe", desc: "Yɛ Weha Health sɛnea wopɛ", prefLang: "Kasa a wopɛ", prefLangDesc: "Kyerɛ kasa a wopɛ sɛ yɛde di dwuma. Wobɛtumi asesa no bere biara firi soro hɔ.", clear: "Pepa Yɛn Nkitahodie", clearDesc: "Pepa wo nkitahodie ne nsɛm nyinaa firi afiri yi ne yɛn mfidie so koraa.", clearing: "Ɛrepepa...", cleared: "✓ Yɛapepa — kɔ so bio", btnClear: "Pepa me nkitahodie", privacy: "Weha Health nnye wo din anaa email. Yɛakora wo nsɛm no so yie. Sɛ wopepa wo nkitahodie a, nsɛm no nyinaa yera koraa." },
  Amharic: { title: "የስርዓት ምርጫዎች", desc: "የWeha Health ተሞክሮዎን ያብጁ", prefLang: "የተመረጠ ቋንቋ", prefLangDesc: "ለምክክርዎ ነባሪ ቋንቋ ያዘጋጃል። ይህንን በማንኛውም ጊዜ መቀየር ይችላሉ።", clear: "የምክክር ታሪክን ያጽዱ", clearDesc: "የእርስዎን ክፍለ ጊዜ እና ሁሉንም የውይይት ውሂብ ከዚህ መሣሪያ እና አገልጋዮቻችን በቋሚነት ያስወግዳል።", clearing: "እያጸዳ ነው...", cleared: "✓ ክፍለ ጊዜ ጸድቷል — ያድሱ", btnClear: "ክፍለ ጊዜዬን ያጽዱ", privacy: "Weha Health ስምዎን ወይም ኢሜይልዎን አይሰበስብም። ውይይቶችዎ ደህንነታቸው በተጠበቀ ሁኔታ ይቀመጣሉ። ክፍለ ጊዜዎን ማጽዳት ሁሉንም ውሂብ በቋሚነት ይሰርዛል።" }
};

export default function SettingsPanel({ language, setLanguage }) {
  const [cleared, setCleared] = useState(false);
  const [isClearing, setIsClearing] = useState(false);

  const t = TRANSLATIONS[language] || TRANSLATIONS['English'];

  const handleClearHistory = async () => {
    const sessionId = localStorage.getItem('chat_session_id');
    setIsClearing(true);
    if (sessionId) {
      try {
        await fetch(`${API_BASE_URL}/api/voice/history/${sessionId}`, { method: 'DELETE' });
      } catch (err) {
        console.error('Failed to delete server history:', err);
      }
    }
    localStorage.removeItem('chat_session_id');
    setIsClearing(false);
    setCleared(true);
    setTimeout(() => setCleared(false), 3000);
  };

  return (
    <div className="flex-grow bg-health-surface rounded-2xl shadow-sm border border-health-border overflow-y-auto">
      <div className="p-5 border-b border-health-border">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-health-chat border border-health-border flex items-center justify-center flex-shrink-0">
            <Settings size={18} className="text-health-accent" />
          </div>
          <div>
            <h2 className="text-lg font-brand font-bold text-health-textPrimary leading-tight">{t.title}</h2>
            <p className="text-xs text-health-textSecondary">{t.desc}</p>
          </div>
        </div>
      </div>

      <div className="p-5 flex flex-col gap-6">

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 mb-1">
            <Globe size={15} className="text-health-accentLight" />
            <span className="text-sm font-bold text-health-textPrimary">{t.prefLang}</span>
          </div>
          <p className="text-xs text-health-textSecondary mb-2">{t.prefLangDesc}</p>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full p-3 rounded-xl border border-health-border text-sm text-health-textPrimary bg-health-chat focus:border-health-accent outline-none appearance-none"
          >
            {SUPPORTED_LANGUAGES.map((lang) => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2 mb-1">
            <Trash2 size={15} className="text-red-500" />
            <span className="text-sm font-bold text-health-textPrimary">{t.clear}</span>
          </div>
          <p className="text-xs text-health-textSecondary mb-2">{t.clearDesc}</p>
          <button
            onClick={handleClearHistory}
            disabled={isClearing}
            className="w-full p-3 rounded-xl border border-red-900/50 text-sm font-bold text-red-500 bg-red-900/10 hover:bg-red-900/30 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isClearing ? t.clearing : cleared ? t.cleared : t.btnClear}
          </button>
        </div>

        <div className="flex items-start gap-3 p-4 bg-health-chat/50 rounded-xl border border-health-border">
          <ShieldCheck size={18} className="text-health-accent flex-shrink-0 mt-0.5" />
          <p className="text-xs text-health-textSecondary leading-relaxed">{t.privacy}</p>
        </div>

      </div>
    </div>
  );
}