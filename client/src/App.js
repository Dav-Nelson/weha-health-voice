import React, { useState, useRef, useEffect } from 'react';
import { Mic, Square, Send, MessageSquare, Settings, History, HelpCircle, Menu, X } from 'lucide-react';
import Header from './components/Header';
import ChatDisplay from './components/ChatDisplay';
import OnboardingModal from './OnboardingModal';
import HistoryPanel from './components/HistoryPanel';
import HelpModal from './components/HelpModal';
import SettingsPanel from './components/SettingsPanel';
import { startSilentTracking } from './utils/tracking';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const LANGUAGE_ISO_MAP = {
  'english': 'en', 'pidgin': 'pcm', 'swahili': 'sw', 'oromo': 'om', 'twi': 'tw', 'amharic': 'am'
};

// --- TRANSLATION DICTIONARY ---
const TRANSLATIONS = {
  en: {
    welcome1: "Welcome to HealthBridge Africa 🌍\nI'm your personal health companion, here to listen and help — in your language, at your pace.\nYou are safe here. Everything you share stays between us. 💛",
    welcome2: "Please tell me — what is bothering you today? Or what health question can I answer for you?",
    placeholder: "Type your health question or symptom...",
    recording: "Listening...",
    wait: "Wait for response...",
    disclaimer: "⚕️ This system is not a substitute for professional medical advice. Always consult a certified doctor.",
    secure: "Secure Clinical Consultation"
  },
  pcm: {
    welcome1: "Welcome to HealthBridge Africa 🌍\nI be your personal health companion. I dey here to listen and help you for your own language.\nYou dey safe here. Everything wey you tell me na secret. 💛",
    welcome2: "Abeg tell me — wetin dey do you today? Or which health question you want ask?",
    placeholder: "Type wetin dey do you...",
    recording: "I dey listen...",
    wait: "Abeg wait small...",
    disclaimer: "⚕️ This system no be doctor substitute. Make you always check certified doctor.",
    secure: "Safe Health Tok"
  },
  sw: {
    welcome1: "Karibu HealthBridge Africa 🌍\nMimi ni rafiki yako wa afya, hapa kusikiliza na kusaidia — kwa lugha yako.\nUko salama hapa. Kila kitu unachoshiriki kinabaki kati yetu. 💛",
    welcome2: "Tafadhali niambie — nini kinakusumbua leo? Au ninaweza kujibu swali gani la afya?",
    placeholder: "Andika swali lako la afya au dalili...",
    recording: "Inasikiliza...",
    wait: "Subiri majibu...",
    disclaimer: "⚕️ Mfumo huu sio mbadala wa ushauri wa kitaalamu wa matibabu. Daima shauriana na daktari.",
    secure: "Ushauri Salama wa Kliniki"
  },
  tw: {
    welcome1: "Akwaaba kɔ HealthBridge Africa 🌍\nMe yɛ wo apɔwmuden adamfo, me wɔ ha sɛ mɛtie wo na m'aboa wo — wɔ wo kasa mu.\nWo ho dwo wo wɔ ha. Biribiara a woka kyerɛ me no yɛ kokoam asɛm. 💛",
    welcome2: "Mesrɛ wo ka kyerɛ me — dɛn na ɛhaw wo nnɛ? Anaa apɔwmuden asɛm bɛn na wobisa?",
    placeholder: "Kyerɛw wo apɔwmuden asɛm...",
    recording: "Mretie...",
    wait: "Twɛn mmuae...",
    disclaimer: "⚕️ Eyi nsi aduruyɛ ho afutuo ananmu. Bere biara kɔbɔ oduruyɛfoɔ a ɔwɔ tumi krataa kɔkɔ.",
    secure: "Ayaresa Nkitahodie a Ɛyɛ Ahobammɔ"
  },
  om: {
    welcome1: "Baga nagaan gara HealthBridge Africa dhuftan 🌍\nAni hiriyyaa fayyaa keeti, dhaggeeffachuu fi si gargaaruuf asan jira.\nAsitti nageenyi kee eegamaadha. Wanti ati natti himtu hundi icciitidha. 💛",
    welcome2: "Mee natti himi — har'a maaltu si rakkisaa jira? Ykn gaaffii fayyaa akkamii qabda?",
    placeholder: "Gaaffii fayyaa kee barreessi...",
    recording: "Dhaggeeffachaa jira...",
    wait: "Deebii eegi...",
    disclaimer: "⚕️ Sirni kun gorsa yaala ogeessaa bakka hin bu'u. Yeroo mara ogeessa fayyaa mariisisi.",
    secure: "Marii Kiliinikaa Icciitii"
  },
  am: {
    welcome1: "ወደ HealthBridge Africa በደህና መጡ 🌍\nእኔ የእርስዎ የግል ጤና ጓደኛ ነኝ፣ እርስዎን ለማዳመጥ እና ለመርዳት እዚህ ነኝ።\nእዚህ ደህንነትዎ የተጠበቀ ነው። የሚያጋሩት ማንኛውም ነገር ሚስጥር ነው። 💛",
    welcome2: "እባክዎ ይንገሩኝ — ዛሬ ምን እየረበሸዎት ነው? ወይም ምን የጤና ጥያቄ መመለስ እችላለሁ?",
    placeholder: "የጤና ጥያቄዎን እዚህ ይጻፉ...",
    recording: "እያዳመጥኩ ነው...",
    wait: "ምላሽ ይጠብቁ...",
    disclaimer: "⚕️ ይህ ዘዴ የባለሙያ የህክምና ምክርን አይተካም። ሁልጊዜ የተረጋገጠ ዶክተር ያማክሩ።",
    secure: "ደህንነቱ የተጠበቀ የክሊኒክ ምክክር"
  }
};

const getOrCreateSessionId = () => {
  let sessionId = localStorage.getItem('chat_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('chat_session_id', sessionId);
  }
  return sessionId;
};

export default function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [language, setLanguage] = useState('English');
  const [showOnboarding, setShowOnboarding] = useState(true);
  const [showHelp, setShowHelp] = useState(false);
  const [activeTab, setActiveTab] = useState('consultation');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const hasWelcomedRef = useRef(false);

  const getCleanLanguageCode = () => {
    const currentLang = typeof language === 'string' ? language : language.name;
    return LANGUAGE_ISO_MAP[currentLang.toLowerCase()] || currentLang.toLowerCase();
  };

  const langCode = getCleanLanguageCode();
  const t = TRANSLATIONS[langCode] || TRANSLATIONS['en'];

  // Initial Welcome Flow
  useEffect(() => {
    if (!showOnboarding && !hasWelcomedRef.current) {
      hasWelcomedRef.current = true;
      startSilentTracking(language);

      const runWelcome = async () => {
        setIsTyping(true);
        await new Promise(r => setTimeout(r, 2000));
        setMessages([{ id: Date.now(), sender: 'bot', text: t.welcome1 }]);
        
        await new Promise(r => setTimeout(r, 1500));
        setMessages(prev => [...prev, { id: Date.now()+1, sender: 'bot', text: t.welcome2 }]);
        setIsTyping(false);
      };
      runWelcome();
    }
  }, [showOnboarding, language, t.welcome1, t.welcome2]);

  // Handle changing languages from the Settings Panel
  const handleLanguageChange = (newLang) => {
    setLanguage(newLang);
    setMessages([]); // Clear chat history visually
    localStorage.setItem('chat_session_id', crypto.randomUUID()); // Reset backend memory
    
    // Immediately greet in the new language
    const targetLangCode = LANGUAGE_ISO_MAP[newLang.toLowerCase()] || 'en';
    const newT = TRANSLATIONS[targetLangCode] || TRANSLATIONS['en'];

    setIsTyping(true);
    setTimeout(() => {
      setMessages([{ id: Date.now(), sender: 'bot', text: newT.welcome1 }]);
      setTimeout(() => {
        setMessages(prev => [...prev, { id: Date.now()+1, sender: 'bot', text: newT.welcome2 }]);
        setIsTyping(false);
      }, 1500);
    }, 1000);
  };

  const handleSendMessage = async (textToProcess) => {
    if (!textToProcess.trim()) return;

    setMessages(prev => [...prev, { id: Date.now(), sender: 'user', text: textToProcess }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const targetCode = getCleanLanguageCode();
      const sessionId = getOrCreateSessionId();
      let finalMessageToSend = textToProcess;

      // SMART AI TRIAGE: Inject instructions ONLY on the first message so the AI knows how to route it
      const isFirstUserMessage = !messages.some(m => m.sender === 'user');

      if (isFirstUserMessage) {
        finalMessageToSend = `[SYSTEM INSTRUCTIONS - STRICTLY ADHERE TO THESE]
You are HealthBridge Africa — a warm, culturally grounded AI health companion built for African communities.
Respond natively in ${language.name || language}.

Analyze the user's opening message: "${textToProcess}"

BEHAVIOUR RULES:
1. GENERAL QUESTION: If the user is asking a general health fact or question (e.g., "about cancer", "what is malaria"), simply answer the question clearly, warmly, and accurately. Do NOT ask triage questions.
2. SYMPTOM/COMPLAINT: If the user is describing a personal symptom or feeling sick (e.g., "my head hurts", "I am coughing"), express brief empathy, then act as a triage nurse and ask ONE follow-up question (like onset or severity) to understand better.
3. When you use any medical term, immediately explain it in plain language using a simple, relatable African analogy.
4. Never give a definitive diagnosis.
5. Always close medical guidance with: "⚕️ Remember: I'm here to support, not replace, a certified doctor."
[END OF SYSTEM INSTRUCTIONS]

User's message: "${textToProcess}"`;
      }

      const response = await fetch(`${API_BASE_URL}/api/voice/text-chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: finalMessageToSend, language: targetCode, sessionId: sessionId }),
      });

      if (!response.ok) throw new Error('API response failed');
      const data = await response.json();

      setMessages(prev => [...prev, { sender: 'bot', text: data.response, language: targetCode }]);
    } catch (error) {
      // --- SMART NETWORK ERROR HANDLING (TEXT) ---
      let errorMessage = "Sorry, I am having trouble connecting right now.";
      if (!navigator.onLine || error.message.includes('Failed to fetch')) {
        errorMessage = "🌐 It looks like your internet connection is unstable right now. Please check your data or WiFi and try again.";
      } else {
        errorMessage = "⚙️ Sorry, I am having technical issues. Please try again in a few minutes!";
      }
      setMessages(prev => [...prev, { sender: 'bot', text: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleTextSubmit = (e) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunksRef.current.push(e.data); };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        await processVoiceAudio(audioBlob);
      };
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) { alert("Unable to access the microphone. Please allow permissions."); }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const processVoiceAudio = async (audioBlob) => {
    setIsLoading(true);
    const targetCode = getCleanLanguageCode();
    const sessionId = getOrCreateSessionId();
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('language', targetCode);
    formData.append('sessionId', sessionId);

    try {
      const response = await fetch(`${API_BASE_URL}/api/voice/chat`, { method: 'POST', body: formData });
      if (!response.ok) throw new Error('Voice chat failed');
      const data = await response.json();
      
      const isFirstUserMessage = !messages.some(m => m.sender === 'user');

      // Pass transcribed audio to the text pipeline so the Smart Triage instructions get applied!
      if (isFirstUserMessage && data.transcribed) {
        setIsLoading(false); 
        handleSendMessage(data.transcribed);
        return;
      }

      if (data.transcribed) setMessages(prev => [...prev, { sender: 'user', text: data.transcribed }]);
      if (data.response) setMessages(prev => [...prev, { sender: 'bot', text: data.response, language: targetCode }]);
    } catch (error) {
      // --- SMART NETWORK ERROR HANDLING (VOICE) ---
      let errorMessage = "Sorry, I couldn't process your voice message.";
      if (!navigator.onLine || error.message.includes('Failed to fetch')) {
        errorMessage = "🌐 It looks like your internet connection is unstable right now. Please check your data or WiFi and try again.";
      } else {
        errorMessage = "⚙️ Sorry, I am having technical issues processing your voice. Please try again in a few minutes!";
      }
      setMessages(prev => [...prev, { sender: 'bot', text: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  const currentLangName = typeof language === 'string' ? language : language.name;

  return (
    <div className="min-h-screen w-full max-w-[100vw] overflow-x-hidden bg-health-bg text-health-textPrimary flex font-body antialiased overflow-hidden relative break-words">

      {showOnboarding && (
        <OnboardingModal onComplete={(selectedLanguage) => {
          if (selectedLanguage) setLanguage(selectedLanguage);
          setShowOnboarding(false);
        }} />
      )}

      {showHelp && <HelpModal onClose={() => setShowHelp(false)} language={currentLangName} />}

      <div className={`fixed inset-0 z-50 bg-black/60 backdrop-blur-sm transition-opacity duration-300 ${isMobileMenuOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'} md:hidden`} onClick={() => setIsMobileMenuOpen(false)}>
        <aside className={`w-72 bg-health-surface border-r border-health-border h-screen p-6 text-health-textSecondary flex flex-col justify-between transform transition-transform duration-300 ease-out ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full'}`} onClick={(e) => e.stopPropagation()}>
          <div className="flex flex-col gap-6 w-full">
            <div className="flex items-center justify-between">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-health-accent to-health-accentLight flex items-center justify-center text-health-bg font-brand font-bold text-lg">
                HB
              </div>
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 hover:bg-health-chat rounded-lg text-health-textSecondary">
                <X size={20} />
              </button>
            </div>
            <hr className="border-health-border" />
            <nav className="flex flex-col gap-2">
              <button onClick={() => { setActiveTab('consultation'); setIsMobileMenuOpen(false); }} className={`flex items-center gap-3 w-full p-3.5 rounded-xl font-medium transition ${activeTab === 'consultation' ? 'bg-health-chat text-health-accentLight' : 'hover:bg-health-chat hover:text-health-textPrimary'}`}>
                <MessageSquare size={20} /><span>Consultation Room</span>
              </button>
              <button onClick={() => { setActiveTab('history'); setIsMobileMenuOpen(false); }} className={`flex items-center gap-3 w-full p-3.5 rounded-xl font-medium transition ${activeTab === 'history' ? 'bg-health-chat text-health-accentLight' : 'hover:bg-health-chat hover:text-health-textPrimary'}`}>
                <History size={20} /><span>Medical History</span>
              </button>
            </nav>
          </div>
          <div className="flex flex-col gap-2 w-full">
            <button onClick={() => { setShowHelp(true); setIsMobileMenuOpen(false); }} className="flex items-center gap-3 w-full p-3.5 rounded-xl font-medium hover:bg-health-chat hover:text-health-textPrimary transition">
              <HelpCircle size={20} /><span>Help & FAQ</span>
            </button>
            <button onClick={() => { setActiveTab('settings'); setIsMobileMenuOpen(false); }} className={`flex items-center gap-3 w-full p-3.5 rounded-xl font-medium transition ${activeTab === 'settings' ? 'bg-health-chat text-health-accentLight' : 'hover:bg-health-chat hover:text-health-textPrimary'}`}>
              <Settings size={20} /><span>System Settings</span>
            </button>
          </div>
        </aside>
      </div>

      <aside className="hidden md:flex w-20 bg-health-surface h-screen flex-col items-center justify-between py-6 text-health-textSecondary border-r border-health-border flex-shrink-0 z-30">
        <div className="flex flex-col items-center gap-6 w-full">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-health-accent to-health-accentLight flex items-center justify-center text-health-bg shadow-md font-brand font-bold text-lg">
            HB
          </div>
          <hr className="w-8 border-health-border" />
          <button onClick={() => setActiveTab('consultation')} className={`p-3 rounded-xl transition relative group ${activeTab === 'consultation' ? 'bg-health-chat text-health-accentLight shadow-inner' : 'hover:text-health-textPrimary'}`}>
            <MessageSquare size={22} />
          </button>
          <button onClick={() => setActiveTab('history')} className={`p-3 rounded-xl transition relative group ${activeTab === 'history' ? 'bg-health-chat text-health-accentLight shadow-inner' : 'hover:text-health-textPrimary'}`}>
            <History size={22} />
          </button>
        </div>
        <div className="flex flex-col items-center gap-4 w-full">
          <button onClick={() => setShowHelp(true)} className="p-3 hover:bg-health-chat hover:text-health-textPrimary rounded-xl transition relative group">
            <HelpCircle size={22} />
          </button>
          <button onClick={() => setActiveTab('settings')} className={`p-3 rounded-xl transition relative group ${activeTab === 'settings' ? 'bg-health-chat text-health-accentLight shadow-inner' : 'hover:text-health-textPrimary'}`}>
            <Settings size={22} />
            <span className={`absolute left-0 w-1 h-4 bg-health-accent rounded-r-full top-[18px] transition-transform ${activeTab === 'settings' ? 'scale-100' : 'scale-0'}`}></span>
          </button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col h-screen overflow-hidden bg-health-chat relative">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none opacity-[0.04] z-0">
          <svg viewBox="0 0 100 100" className="w-[80vw] max-w-[500px] animate-spin-slow fill-health-accent">
            <path d="M50 0 C60 20, 80 40, 100 50 C80 60, 60 80, 50 100 C40 80, 20 60, 0 50 C20 40, 40 20, 50 0 Z" />
            <circle cx="50" cy="50" r="15" className="fill-health-bg" />
          </svg>
        </div>

        <div className="flex items-center bg-health-surface border-b border-health-border px-4 md:px-0 z-20">
          <button onClick={() => setIsMobileMenuOpen(true)} className="p-2 mr-1 text-health-textSecondary hover:bg-health-chat rounded-lg block md:hidden transition">
            <Menu size={24} />
          </button>
          <div className="flex-1">
            <Header language={currentLangName} />
          </div>
        </div>

        <main className="flex-grow flex flex-col w-full h-[calc(100vh-80px)] overflow-hidden z-10 relative">
          {activeTab === 'consultation' && (
            <div className="flex flex-col h-full">
              <div className="flex-1 overflow-y-auto px-4 md:px-6 py-4">
                <ChatDisplay 
                  messages={messages} 
                  isTyping={isTyping} 
                  isLoading={isLoading} 
                  language={currentLangName}
                  secureText={t.secure}
                />
              </div>

              <div className="bg-health-surface border-t border-health-border p-3 md:p-4 flex-shrink-0 z-20">
                <div className="max-w-4xl mx-auto">
                  <form onSubmit={handleTextSubmit} className="flex items-center gap-2 md:gap-3">
                    <button type="button" onClick={isRecording ? stopRecording : startRecording} className={`p-3.5 md:p-4 rounded-full flex-shrink-0 transition-all ${isRecording ? 'bg-red-900/50 text-red-500 animate-pulse border border-red-500/50' : 'bg-health-bg border border-health-border text-health-textSecondary hover:text-health-accent'}`}>
                      {isRecording ? <Square size={18} fill="currentColor"/> : <Mic size={18} />}
                    </button>

                    <div className="flex-1 bg-health-bg border border-health-border focus-within:border-health-accent rounded-3xl flex items-center px-4 py-2">
                      <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={isRecording ? t.recording : (isTyping ? t.wait : t.placeholder)}
                        disabled={isRecording || isLoading || isTyping}
                        className="flex-grow bg-transparent border-none focus:outline-none text-health-textPrimary placeholder-health-textSecondary disabled:opacity-50 py-1"
                      />
                    </div>

                    <button type="submit" disabled={!inputValue.trim() || isLoading || isRecording || isTyping} className={`p-3.5 md:p-4 rounded-full flex-shrink-0 transition-all ${inputValue.trim() && !isTyping && !isLoading ? 'bg-gradient-to-r from-health-accent to-health-accentLight text-health-bg shadow-[0_4px_15px_rgba(212,131,10,0.3)]' : 'bg-health-bg border border-health-border text-health-textSecondary cursor-not-allowed'}`}>
                      <Send size={18} />
                    </button>
                  </form>
                  <p className="text-[10px] md:text-[11px] text-health-textSecondary/60 text-center mt-2 font-medium px-2">
                    {t.disclaimer}
                  </p>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'history' && <HistoryPanel />}
          {activeTab === 'settings' && <SettingsPanel language={currentLangName} setLanguage={handleLanguageChange} />}
        </main>
      </div>
    </div>
  );
}