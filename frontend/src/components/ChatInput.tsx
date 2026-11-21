import React, { useRef, useEffect } from 'react';
import { Send, CornerDownLeft } from 'lucide-react';

interface ChatInputProps {
  inputMessage: string;
  setInputMessage: (val: string) => void;
  onSend: () => void;
  isLoading: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  inputMessage,
  setInputMessage,
  onSend,
  isLoading,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (!isLoading && inputMessage.trim()) {
        onSend();
      }
    }
  };

  // Adjust textarea height automatically
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [inputMessage]);

  return (
    <div className="p-4 bg-slate-900/80 border-t border-slate-800/80 backdrop-blur">
      <div className="max-w-4xl mx-auto relative flex items-end bg-slate-950 border border-slate-800 rounded-2xl shadow-lg focus-within:border-emerald-500/60 focus-within:ring-1 focus-within:ring-emerald-500/30 transition-all p-2">
        <textarea
          ref={textareaRef}
          data-testid="chat-input"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          rows={1}
          disabled={isLoading}
          className="flex-1 bg-transparent text-slate-100 placeholder-slate-500 text-sm px-3 py-2 resize-none outline-none max-h-40 min-h-[44px]"
        />

        <button
          data-testid="send-button"
          onClick={onSend}
          disabled={isLoading || !inputMessage.trim()}
          className="h-10 w-10 mb-0.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:hover:bg-emerald-600 text-white flex items-center justify-center transition-all shadow-md shadow-emerald-950 shrink-0"
          title="Send Message"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </button>
      </div>

      <div className="max-w-4xl mx-auto flex items-center justify-between mt-2 px-2 text-[11px] text-slate-500">
        <div className="flex items-center space-x-1">
          <CornerDownLeft className="w-3 h-3 text-slate-600" />
          <span>Press Enter to send</span>
        </div>
        <div>
          <span>LiteLLM Gateway • Deterministic Failover Pool</span>
        </div>
      </div>
    </div>
  );
};
