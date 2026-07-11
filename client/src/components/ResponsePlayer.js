import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Volume2, Pause, Play, Loader2, AlertCircle } from 'lucide-react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

export default function ResponsePlayer({ text, language }) {
  const [playState, setPlayState] = useState('idle'); 
  const [speed, setSpeed] = useState(1);
  const [errorToast, setErrorToast] = useState('');
  const audioRef = useRef(null);
  const hasAutoPlayedRef = useRef(false);

  const handleSpeedChange = () => {
    const nextSpeed = speed === 1 ? 1.5 : speed === 1.5 ? 2 : 1;
    setSpeed(nextSpeed);
    if (audioRef.current) {
      audioRef.current.playbackRate = nextSpeed;
    }
  };

  const toggleAudio = useCallback(async () => {
    if (playState === 'playing' && audioRef.current) {
      audioRef.current.pause();
      setPlayState('paused');
      return;
    }

    if (playState === 'paused' && audioRef.current) {
      audioRef.current.play();
      setPlayState('playing');
      return;
    }

    if (window.hbCurrentAudio) {
      window.hbCurrentAudio.pause();
      window.dispatchEvent(new Event('hb-stop-audio'));
    }

    setPlayState('loading');
    setErrorToast(''); 

    try {
      const targetLang = language ? language.toLowerCase() : 'english';

      const response = await fetch(`${API_BASE_URL}/api/voice/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: targetLang }),
      });

      if (!response.ok) throw new Error('API_ERROR');

      const contentType = response.headers.get('content-type') || '';
      let audioUrl = '';

      if (contentType.includes('application/json')) {
        const data = await response.json();
        const rawBase64 = data.audio || data.audioContent || data.data;
        if (!rawBase64) throw new Error('DATA_ERROR');
        audioUrl = `data:audio/mp3;base64,${rawBase64}`;
      } else {
        const audioBlob = await response.blob();
        if (audioBlob.size === 0) throw new Error('DATA_ERROR');
        audioUrl = URL.createObjectURL(audioBlob);
      }

      const audio = new Audio(audioUrl);
      audio.playbackRate = speed;
      audioRef.current = audio;
      window.hbCurrentAudio = audio; 

      audio.onended = () => {
        setPlayState('idle');
        audioRef.current = null;
        if (!contentType.includes('application/json')) URL.revokeObjectURL(audioUrl);
      };

      audio.onerror = () => {
        setPlayState('idle');
        audioRef.current = null;
      };

      setPlayState('playing');
      const playPromise = audio.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => { setPlayState('idle'); audioRef.current = null; });
      }
    } catch (error) {
      setPlayState('idle');
      if (!navigator.onLine || error.message.includes('Failed to fetch')) {
        setErrorToast("🌐 Your internet connection seems unstable. Please check your network and try again.");
      } else {
        setErrorToast("⚙️ Sorry, I am having technical trouble with my voice right now. Please try again in a few minutes!");
      }
    }
  }, [text, language, playState, speed]);

  useEffect(() => {
    if (errorToast) {
      const timer = setTimeout(() => {
        setErrorToast('');
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [errorToast]);

  useEffect(() => {
    const stopListener = () => {
      if (audioRef.current && window.hbCurrentAudio !== audioRef.current) {
        setPlayState('idle');
        audioRef.current = null;
      }
    };
    window.addEventListener('hb-stop-audio', stopListener);
    return () => window.removeEventListener('hb-stop-audio', stopListener);
  }, []);

  useEffect(() => {
    if (localStorage.getItem('hb_autoplay') === 'true' && text && !hasAutoPlayedRef.current) {
      hasAutoPlayedRef.current = true;
      const timer = setTimeout(() => toggleAudio(), 600);
      return () => clearTimeout(timer);
    }
  }, [text, toggleAudio]);

  return (
    <>
      {errorToast && createPortal(
        <div className="fixed top-6 left-1/2 transform -translate-x-1/2 z-[9999] bg-health-surface border border-health-accent/50 shadow-2xl rounded-2xl px-4 py-3 flex items-center gap-3 text-sm font-medium text-health-textPrimary max-w-[90vw] md:max-w-md transition-all duration-300 ease-in-out">
          <AlertCircle className="text-health-accent shrink-0" size={20} />
          <p>{errorToast}</p>
        </div>,
        document.body
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={toggleAudio}
          disabled={playState === 'loading'}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-colors ${
            playState === 'playing' || playState === 'paused'
              ? 'bg-health-accent/20 text-health-accentLight border border-health-accent'
              : 'bg-health-surface text-health-textSecondary border border-health-border hover:bg-health-chat hover:text-health-textPrimary'
          }`}
        >
          {playState === 'loading' ? (
            <Loader2 size={14} className="animate-spin" />
          ) : playState === 'playing' ? (
            <Pause size={14} />
          ) : playState === 'paused' ? (
            <Play size={14} />
          ) : (
            <Volume2 size={14} />
          )}
          
          {playState === 'loading' 
            ? 'Loading...' 
            : playState === 'playing' 
            ? 'Pause' 
            : playState === 'paused' 
            ? 'Resume' 
            : 'Listen'}
        </button>

        <button
          onClick={handleSpeedChange}
          className="flex items-center justify-center px-2 py-1.5 rounded-lg text-xs font-bold bg-health-surface text-health-textSecondary border border-health-border hover:bg-health-chat hover:text-health-textPrimary transition-colors"
          title="Change playback speed"
        >
          {speed}x
        </button>
      </div>
    </>
  );
}