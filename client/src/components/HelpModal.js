import React, { useState } from 'react';
import { X, HelpCircle, ChevronDown, ChevronUp } from 'lucide-react';

const TRANSLATIONS = {
  English: {
    title: "Help & FAQ",
    desc: "Common questions about Weha Health",
    footer: "Weha Health is not a medical service. Always consult a qualified healthcare provider.",
    faqs: [
      { q: "Is Weha Health a replacement for a doctor?", a: "No, Weha Health is a health information and triage tool, not a medical service. It helps you understand symptoms, know when to seek care, and get reliable health information in your language. Always consult a qualified healthcare provider for diagnosis and treatment." },
      { q: "What languages are supported?", a: "Weha Health supports English, Nigerian Pidgin, Yoruba, Akan, and Amharic. You can switch languages anytime using the dropdown at the top of the screen. The AI will respond in whichever language you select." },
      { q: "Is my conversation private?", a: "Your conversations are stored securely and linked only to your device session. No name, email, or personal identity is collected or required. Clearing your browser data will start a fresh session." },
      { q: "How accurate is the information?", a: "Responses are grounded in verified sources including WHO guidelines and country-level health data. The AI does not guess or fabricate answers. If it does not have reliable information on a topic, it will say so and recommend consulting a healthcare professional." },
      { q: "How do I use the voice feature?", a: "Tap the microphone button and speak your health question in your chosen language, then tap stop. Weha Health will transcribe what you said and respond in text. Tap Listen on any response to hear it read back to you." },
      { q: "What should I do in a medical emergency?", a: "If you or someone nearby is experiencing a medical emergency like difficulty breathing, chest pain, heavy bleeding, or loss of consciousness, do not use Weha Health. Go to the nearest hospital immediately or call your local emergency services." }
    ]
  },
  Pidgin: {
    title: "Help & FAQ",
    desc: "Question wey people dey always ask about Weha Health",
    footer: "Weha Health no be doctor clinic. Make you always check qualified doctor.",
    faqs: [
      { q: "Weha Health fit replace doctor?", a: "No, Weha Health na tool to help you understand your health, e no be hospital. Always check qualified doctor for proper treatment." },
      { q: "Which languages dey available?", a: "We get English, Pidgin, Yoruba, Akan, and Amharic. You fit change am anytime for top of the screen." },
      { q: "My conversation dey private?", a: "Yes, everything wey you tok dey secure and e only tie to your device. We no dey collect your name or email." },
      { q: "How sure the information be?", a: "The answers dey come from verified sources like WHO and country health data. AI no dey guess. If e no know, e go tell you make you see doctor." },
      { q: "How I fit use the voice feature?", a: "Press the mic button, talk wetin dey do you, then press stop. E go write wetin you talk and answer you. You fit press Listen make e read am for you." },
      { q: "Wetin make I do for medical emergency?", a: "If person no fit breathe well, get chest pain, dey bleed, or faint, no use Weha Health. Go nearest hospital straight or call emergency number." }
    ]
  },
  Yoruba: {
    title: "Ìrànlọ́wọ́ àti Ìbéèrè",
    desc: "Àwọn ìbéèrè tí a máa ń béèrè nípa Weha Health",
    footer: "Weha Health kì í ṣe iṣẹ́ ìṣègùn gidi. Jọ̀wọ́ máa lọ bá dókítà tó gbẹ́kẹ̀lé nígbà gbogbo.",
    faqs: [
      { q: "Ṣé Weha Health lè rọ́pò dókítà?", a: "Rárá, Weha Health jẹ́ irinṣẹ́ ìsọfúnni nípa ìlera, kì í ṣe iṣẹ́ ìṣègùn gidi. Ó ń ràn ọ́ lọ́wọ́ láti mọ àwọn àmì àìsàn àti ìgbà tó yẹ kó o lọ wo dókítà. Jọ̀wọ́ máa bá dókítà tó gbẹ́kẹ̀lé sọ̀rọ̀ fún àyẹ̀wò àti ìtọ́jú." },
      { q: "Èdè wo ni ó wà?", a: "Weha Health ń sọ èdè Gẹ̀ẹ́sì, Pidgin, Yorùbá, Akan, àti Amharic. O lè yí èdè padà nígbàkigbà pẹ̀lú àṣàyàn tó wà lókè ojú-ìwé." },
      { q: "Ṣé ìjíròrò mi jẹ́ àṣírí?", a: "Bẹ́ẹ̀ni, ìjíròrò rẹ ni a ń fi pamọ́ ní ààbò, a kò sì gba orúkọ tàbí email rẹ." },
      { q: "Bawo ni ìsọfúnni náà ṣe dájú tó?", a: "Àwọn ìdáhùn wa láti orísun tó dájú bíi WHO. AI náà kì í fojú-ẹ̀gbọ́n dá àwọn nǹkan mọ̀." },
      { q: "Báwo ni mo ṣe lè lo ohun ìró?", a: "Tẹ ìka rẹ sórí máìkì, sọ̀rọ̀, lẹ́yìn náà tẹ 'stop'. O lè tẹ Listen láti gbọ́ ìdáhùn náà." },
      { q: "Kín ni kí n ṣe bí ìṣẹ̀lẹ̀ àjàkálẹ̀ bá ṣẹlẹ̀?", a: "Bí ẹnikẹ́ni kò bá lè mí dáadáa tàbí ẹ̀jẹ̀ pọ̀ jáde, lọ sí ilé ìwòsàn tó súnmọ́ ọ lẹ́sẹ̀kẹsẹ̀." }
    ]
  },
  Akan: {
    title: "Mmoa & Nsɛmbisa",
    desc: "Nsɛm a nkurɔfoɔ taa bisa fa Weha Health ho",
    footer: "Weha Health nyɛ ayaresabea. Bere biara kɔhunu oduruyɛfoɔ a ɔwɔ tumi krataa.",
    faqs: [
      { q: "Weha Health bɛtumi asi oduruyɛfoɔ ananmu?", a: "Dabi, ɛyɛ afutuo nko ara, ɛnyɛ ayaresabea. Kɔhunu oduruyɛfoɔ bere biara ma nhwehwɛmu ne ayaresa." },
      { q: "Kasa bɛn na yɛde di dwuma?", a: "English, Pidgin, Yoruba, Akan, ne Amharic. Wobɛtumi asesa no bere biara wɔ soro hɔ." },
      { q: "Me nsɛm yɛ kokoam?", a: "Aane, wo nsɛm no yɛ kokoam, yɛnkora wo din anaa email so." },
      { q: "Nsɛm no yɛ nokware?", a: "Nsɛm no firi mmeaeɛ a wɔagye atom te sɛ WHO. AI no ntwen nkyerɛ nsɛm." },
      { q: "Mɛyɛ sɛn ade nne afiri no awura mu?", a: "Mia mic no so, kasa, na mia stop. Wobɛtumi atie mmuaeɛ no bio." },
      { q: "Sɛ asiane ba a mɛyɛ dɛn?", a: "Sɛ obi ntumi ngye ahome anaa ɔrepira a, kɔ ayaresabea a ɛbɛn wo ntɛm ara." }
    ]
  },
  Amharic: {
    title: "እገዛ እና ጥያቄዎች",
    desc: "ስለ Weha Health የተለመዱ ጥያቄዎች",
    footer: "Weha Health የህክምና አገልግሎት አይደለም። ሁልጊዜ ብቁ ዶክተር ያማክሩ።",
    faqs: [
      { q: "Weha Health የዶክተር ምትክ ነው?", a: "አይደለም፣ ይህ የጤና መረጃ መሳሪያ እንጂ የህክምና አገልግሎት አይደለም። ሁልጊዜ ብቁ ዶክተር ያማክሩ።" },
      { q: "ምን ቋንቋዎች ይደገፋሉ?", a: "እንግሊዝኛ፣ ፒጂን፣ ዮሩባ፣ አካን እና አማርኛ። በማንኛውም ጊዜ ከላይ ካለው ዝርዝር መቀየር ይችላሉ።" },
      { q: "ውይይቴ ሚስጥራዊ ነው?", a: "አዎ፣ ውይይቶችዎ ደህንነታቸው የተጠበቀ ነው። ስምዎን ወይም ኢሜይልዎን አንሰበስብም።" },
      { q: "መረጃው ምን ያህል ትክክል ነው?", a: "ምላሾቹ እንደ WHO ካሉ የተረጋገጡ ምንጮች የተገኙ ናቸው። AI አይገምትም፤ እርግጠኛ ካልሆነ ዶክተር እንዲያማክሩ ይመክራል።" },
      { q: "የድምጽ ባህሪውን እንዴት እጠቀማለሁ?", a: "ማይክሮፎኑን ይጫኑ፣ ይናገሩ፣ ከዚያ ያቁሙ። ምላሹን ለማዳመጥ Listen ይጫኑ።" },
      { q: "በድንገተኛ አደጋ ጊዜ ምን ላድርግ?", a: "የመተንፈስ ችግር ወይም ከባድ የደም መፍሰስ ካለ፣ Weha Health አይጠቀሙ፤ ወዲያውኑ ወደ ሆስፒታል ይሂዱ ወይም የአደጋ ጊዜ ስልክ ይደውሉ።" }
    ]
  }
};

function FAQItem({ question, answer }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-health-border rounded-xl overflow-hidden shrink-0">
      <button onClick={() => setIsOpen(!isOpen)} className="w-full flex items-center justify-between p-4 text-left bg-health-surface hover:bg-health-chat transition-colors">
        <span className="text-sm font-bold text-health-textPrimary pr-4 leading-snug">{question}</span>
        <span className="flex-shrink-0">
          {isOpen ? <ChevronUp size={16} className="text-health-accentLight" /> : <ChevronDown size={16} className="text-health-textSecondary" />}
        </span>
      </button>
      {isOpen && (
        <div className="px-4 pb-4 bg-health-chat border-t border-health-border/50">
          <p className="text-sm text-health-textSecondary leading-relaxed pt-3">{answer}</p>
        </div>
      )}
    </div>
  );
}

export default function HelpModal({ onClose, language }) {
  const t = TRANSLATIONS[language] || TRANSLATIONS['English'];

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
      <div className="bg-health-surface rounded-2xl shadow-2xl w-full max-w-lg border border-health-border flex flex-col max-h-[85vh]">

        <div className="flex items-center justify-between p-5 border-b border-health-border flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-health-chat border border-health-border flex items-center justify-center flex-shrink-0">
              <HelpCircle size={18} className="text-health-accent" />
            </div>
            <div>
              <h2 className="text-lg font-brand font-bold text-health-textPrimary leading-tight">{t.title}</h2>
              <p className="text-xs text-health-textSecondary">{t.desc}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-health-chat rounded-lg text-health-textSecondary hover:text-health-textPrimary transition-colors flex-shrink-0 ml-2">
            <X size={18} />
          </button>
        </div>

        <div className="overflow-y-auto p-5 flex flex-col gap-3 hide-scrollbar">
          {t.faqs.map((faq, index) => (
            <FAQItem key={index} question={faq.q} answer={faq.a} />
          ))}
        </div>

        <div className="p-4 border-t border-health-border flex-shrink-0">
          <p className="text-[11px] text-health-textSecondary/70 text-center">{t.footer}</p>
        </div>
      </div>
    </div>
  );
}