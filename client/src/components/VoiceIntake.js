import React, { useState, useRef } from 'react';
import { Mic, Square, AlertTriangle, CheckCircle, Clock, MapPin, BellRing, Volume2, Loader2 } from 'lucide-react';
import VisitSummary from './VisitSummary';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const getOrCreateTriageSessionId = () => {
  let sessionId = localStorage.getItem('triage_session_id');
  if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('triage_session_id', sessionId);
  }
  return sessionId;
};

const URGENCY_STYLES = {
  urgent: { bg: 'bg-red-900/30', border: 'border-red-500/50', text: 'text-red-400', icon: AlertTriangle },
  moderate: { bg: 'bg-yellow-900/30', border: 'border-yellow-500/50', text: 'text-yellow-400', icon: Clock },
  routine: { bg: 'bg-green-900/30', border: 'border-green-500/50', text: 'text-green-400', icon: CheckCircle },
};

const HEADER_TEXT = {
  en: { title: "Voice Health Triage", desc: "Speak naturally, in whatever language mix feels comfortable. I'll ask a few follow-up questions if I need more detail." },
  pcm: { title: "Voice Health Check", desc: "Talk anyhow you like, mix your language as e dey come. I go ask small follow-up questions if I need more detail." },
  yo: { title: "Àyẹ̀wò Ìlera Ohùn", desc: "Sọ̀rọ̀ ní ti ẹ̀dá, ní èdè tí ó bá wù ọ́. Èmi yóò béèrè àwọn ìbéèrè díẹ̀ bí mo bá nílò àlàyé síwájú sí i." },
  ak: { title: "Nne Nhwehwɛmu", desc: "Kasa sɛnea ɛfata wo, fa wo kasa fra biara a wopɛ. Mɛbisa wo nsɛm kakra sɛ ehia me nkyerɛkyerɛmu pii." },
  am: { title: "የድምጽ ጤና ምርመራ", desc: "እንደወደዱት ቋንቋ ቀላቅለው በተፈጥሮ ይናገሩ። ተጨማሪ ዝርዝር ካስፈለገኝ ጥቂት ተከታይ ጥያቄዎችን እጠይቃለሁ።" },
};

const FOOTER_TEXT = {
  en: { disclaimer: "This is not a diagnosis. Please see a health worker for urgent concerns.", alertedBoth: "Your care team has been alerted via WhatsApp and Telegram.", alertedWhatsapp: "Your care team has been alerted via WhatsApp.", alertedTelegram: "Your care team has been alerted via Telegram." },
  pcm: { disclaimer: "This no be diagnosis. Abeg see health worker if e serious.", alertedBoth: "We don alert your care team for WhatsApp and Telegram.", alertedWhatsapp: "We don alert your care team for WhatsApp.", alertedTelegram: "We don alert your care team for Telegram." },
  yo: { disclaimer: "Èyí kì í ṣe àyẹ̀wò dókítà. Jọ̀wọ́ lọ bá òṣìṣẹ́ ìlera bí ọ̀rọ̀ bá pọ̀jù.", alertedBoth: "A ti kìlọ̀ fún ẹgbẹ́ ìtọ́jú rẹ nípasẹ̀ WhatsApp àti Telegram.", alertedWhatsapp: "A ti kìlọ̀ fún ẹgbẹ́ ìtọ́jú rẹ nípasẹ̀ WhatsApp.", alertedTelegram: "A ti kìlọ̀ fún ẹgbẹ́ ìtọ́jú rẹ nípasẹ̀ Telegram." },
  ak: { disclaimer: "Wei nyɛ oduruyɛfo nhwehwɛmu. Yɛsrɛ wo, kɔhwɛ ɔyaresafo sɛ ɛho hia ntɛm.", alertedBoth: "Yɛabɔ wo dɔfo kuo amanneɛ wɔ WhatsApp ne Telegram so.", alertedWhatsapp: "Yɛabɔ wo dɔfo kuo amanneɛ wɔ WhatsApp so.", alertedTelegram: "Yɛabɔ wo dɔfo kuo amanneɛ wɔ Telegram so." },
  am: { disclaimer: "ይህ ምርመራ አይደለም። አስቸኳይ ጉዳይ ካለ እባክዎ የጤና ባለሙያ ያማክሩ።", alertedBoth: "የእንክብካቤ ቡድንዎ በWhatsApp እና Telegram ተጠንቅቋል።", alertedWhatsapp: "የእንክብካቤ ቡድንዎ በWhatsApp ተጠንቅቋል።", alertedTelegram: "የእንክብካቤ ቡድንዎ በTelegram ተጠንቅቋል።" },
};

export default function VoiceIntake({ language = 'en' }) {
  const [conversation, setConversation] = useState([]);
  const [fields, setFields] = useState({});
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [engineUsed, setEngineUsed] = useState(null);
  const [playingIndex, setPlayingIndex] = useState(null);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const coordsRef = useRef({ lat: null, lng: null });
  const currentAudioRef = useRef(null);

  const captureLocationSilently = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (position) => {
        coordsRef.current = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
      },
      () => {
        coordsRef.current = { lat: null, lng: null };
      },
      { timeout: 8000, maximumAge: 300000 }
    );
  };

  const playText = async (text, index) => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
    }
    setPlayingIndex(index);
    try {
      const response = await fetch(`${API_BASE_URL}/api/voice/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language })
      });
      if (!response.ok) throw new Error('Speech generation failed');
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      currentAudioRef.current = audio;
      audio.onended = () => setPlayingIndex(null);
      audio.onerror = () => setPlayingIndex(null);
      await audio.play();
    } catch (err) {
      setPlayingIndex(null);
    }
  };

  const startRecording = async () => {
    try {
      captureLocationSilently();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach((track) => track.stop());
        await sendTurn(audioBlob);
      };
      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      alert('Unable to access the microphone. Please allow permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendTurn = async (audioBlob) => {
    setIsProcessing(true);
    const sessionId = getOrCreateTriageSessionId();
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');
    formData.append('language', language);
    formData.append('sessionId', sessionId);
    formData.append('existingFields', JSON.stringify(fields));
    if (coordsRef.current.lat !== null) {
      formData.append('lat', coordsRef.current.lat);
      formData.append('lng', coordsRef.current.lng);
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/intake/turn`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) throw new Error('Intake turn failed');
      const data = await response.json();

      setConversation((prev) => [
        ...prev,
        { sender: 'user', text: data.transcript },
      ]);
      setEngineUsed(data.transcription_engine);

      if (data.status === 'need_more_info') {
        setFields(data.fields);
        setConversation((prev) => [
          ...prev,
          { sender: 'bot', text: data.next_question },
        ]);
      } else if (data.status === 'complete') {
        setFields(data.fields);
        setResult({
          urgency: data.urgency,
          matched_signs: data.matched_signs,
          guidance: data.guidance,
          whatsapp_alert_sent: data.whatsapp_alert_sent,
          telegram_alert_sent: data.telegram_alert_sent,
          nearest_facility: data.nearest_facility,
        });
      }
    } catch (error) {
      setConversation((prev) => [
        ...prev,
        { sender: 'bot', text: "Sorry, I couldn't process that. Please try again." },
      ]);
    } finally {
      setIsProcessing(false);
    }
  };

  const startNewSession = () => {
    localStorage.setItem('triage_session_id', crypto.randomUUID());
    setConversation([]);
    setFields({});
    setResult(null);
  };

  return (
    <div className="flex flex-col h-full max-w-2xl mx-auto p-4 md:p-6">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-health-textPrimary">
          {(HEADER_TEXT[language] || HEADER_TEXT.en).title}
        </h2>
        <p className="text-sm text-health-textSecondary">
          {(HEADER_TEXT[language] || HEADER_TEXT.en).desc}
        </p>
        {engineUsed && (
          <p className="text-xs text-health-textSecondary/60 mt-1">
            Transcription engine: {engineUsed}
          </p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-4">
        {conversation.map((msg, i) => (
          <div key={i} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[85%] p-3 rounded-[18px] text-[15px] leading-relaxed shadow-sm flex items-start gap-2 ${
                msg.sender === 'user'
                  ? 'bg-health-userBubble text-health-textPrimary rounded-tr-[4px]'
                  : 'bg-health-aiBubble text-health-textPrimary rounded-tl-[4px]'
              }`}
            >
              <span className="flex-1">{msg.text}</span>
              {msg.sender === 'bot' && (
                <button
                  onClick={() => playText(msg.text, i)}
                  className="shrink-0 mt-0.5 text-health-textSecondary hover:text-health-accent transition"
                  aria-label="Listen"
                >
                  {playingIndex === i ? <Loader2 size={14} className="animate-spin" /> : <Volume2 size={14} />}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {result && (
        <div className={`rounded-xl border p-4 mb-4 ${URGENCY_STYLES[result.urgency]?.bg} ${URGENCY_STYLES[result.urgency]?.border}`}>
          <div className={`flex items-center gap-2 font-semibold mb-2 ${URGENCY_STYLES[result.urgency]?.text}`}>
            {React.createElement(URGENCY_STYLES[result.urgency]?.icon || CheckCircle, { size: 18 })}
            <span className="uppercase text-sm tracking-wide">{result.urgency}</span>
          </div>
          <div className="flex items-start gap-2 mb-2">
            <p className="text-sm text-health-textPrimary flex-1">{result.guidance}</p>
            <button
              onClick={() => playText(result.guidance, 'guidance')}
              className="shrink-0 mt-0.5 text-health-textSecondary hover:text-health-accent transition"
              aria-label="Listen"
            >
              {playingIndex === 'guidance' ? <Loader2 size={14} className="animate-spin" /> : <Volume2 size={14} />}
            </button>
          </div>
          {result.matched_signs?.length > 0 && (
            <ul className="text-xs text-health-textSecondary space-y-1 mb-2">
              {result.matched_signs.map((s, i) => (
                <li key={i}>- {s.explanation}</li>
              ))}
            </ul>
          )}

          {result.urgency === 'urgent' && (result.whatsapp_alert_sent || result.telegram_alert_sent) && (
            <div className="flex items-center gap-2 text-xs text-red-300 bg-red-950/40 rounded-lg p-2 mb-2">
              <BellRing size={14} />
              <span>
                {result.whatsapp_alert_sent && result.telegram_alert_sent
                  ? (FOOTER_TEXT[language] || FOOTER_TEXT.en).alertedBoth
                  : result.whatsapp_alert_sent
                  ? (FOOTER_TEXT[language] || FOOTER_TEXT.en).alertedWhatsapp
                  : (FOOTER_TEXT[language] || FOOTER_TEXT.en).alertedTelegram}
              </span>
            </div>
          )}

          {result.nearest_facility && (
            <a
              href={result.nearest_facility.maps_link}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-xs text-health-accentLight underline bg-health-bg/40 rounded-lg p-2 mb-2"
            >
              <MapPin size={14} />
              <span>Nearest facility: {result.nearest_facility.name}</span>
            </a>
          )}

          <VisitSummary fields={fields} result={result} language={language} />

          <button
            onClick={startNewSession}
            className="mt-2 text-xs underline text-health-accentLight"
          >
            Start a new session
          </button>
        </div>
      )}

      {!result && (
        <div className="flex justify-center">
          <button
            onClick={isRecording ? stopRecording : startRecording}
            disabled={isProcessing}
            className={`p-4 rounded-full transition-all ${
              isRecording
                ? 'bg-red-900/50 text-red-500 animate-pulse border border-red-500/50'
                : 'bg-health-bg border border-health-border text-health-textSecondary hover:text-health-accent'
            } disabled:opacity-50`}
          >
            {isRecording ? <Square size={20} fill="currentColor" /> : <Mic size={20} />}
          </button>
        </div>
      )}
      {isProcessing && (
        <p className="text-center text-xs text-health-textSecondary mt-2">Processing...</p>
      )}
      <p className="text-[10px] text-health-textSecondary/60 text-center mt-3">
        {(FOOTER_TEXT[language] || FOOTER_TEXT.en).disclaimer}
      </p>
    </div>
  );
}