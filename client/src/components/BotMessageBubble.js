import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Copy, Check, Share2, ShieldCheck } from 'lucide-react';
import ResponsePlayer from './ResponsePlayer';

export default function BotMessageBubble({ text, language }) {
  const [feedback, setFeedback] = useState(null);
  const [isCopied, setIsCopied] = useState(false);

  const handleFeedback = (type) => setFeedback(type);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(text);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {}
  };

  const handleShare = async () => {
    if (navigator.share) {
      try { await navigator.share({ title: 'HealthBridge Africa', text }); } catch (err) {}
    } else {
      await handleCopy();
      alert('Response copied to clipboard to share!');
    }
  };

  return (
    <div className="max-w-[92%] md:max-w-[85%] rounded-[18px] rounded-tl-[4px] px-4 py-3 md:px-5 md:py-4 bg-health-aiBubble text-health-textPrimary self-start shadow-sm">

      <div className="flex items-center gap-1.5 mb-2 text-health-accentLight">
        <ShieldCheck size={14} />
        <span className="text-[10px] font-bold uppercase tracking-widest font-brand">HealthBridge</span>
      </div>

      <p className="leading-relaxed text-[15px] whitespace-pre-line">{text}</p>

      <div className="mt-3 flex flex-wrap items-center justify-between border-t border-health-border/50 pt-3 gap-2">
        <ResponsePlayer text={text} language={language} />

        <div className="flex items-center gap-1">
          <button onClick={handleCopy} title="Copy response" className="p-1.5 text-health-textSecondary hover:text-health-accent hover:bg-health-surface rounded-md transition-colors">
            {isCopied ? <Check size={16} className="text-health-accent" /> : <Copy size={16} />}
          </button>

          <button onClick={handleShare} title="Share response" className="p-1.5 text-health-textSecondary hover:text-health-accent hover:bg-health-surface rounded-md transition-colors">
            <Share2 size={16} />
          </button>

          <div className="w-px h-4 bg-health-border mx-1" />

          <button onClick={() => handleFeedback('up')} className={`p-1.5 rounded-md transition-colors ${feedback === 'up' ? 'text-health-bg bg-health-accent' : 'text-health-textSecondary hover:text-health-accent hover:bg-health-surface'}`}>
            <ThumbsUp size={16} className={feedback === 'up' ? 'fill-current' : ''} />
          </button>

          <button onClick={() => handleFeedback('down')} className={`p-1.5 rounded-md transition-colors ${feedback === 'down' ? 'text-health-bg bg-red-600' : 'text-health-textSecondary hover:text-red-500 hover:bg-health-surface'}`}>
            <ThumbsDown size={16} className={feedback === 'down' ? 'fill-current' : ''} />
          </button>
        </div>
      </div>
    </div>
  );
}