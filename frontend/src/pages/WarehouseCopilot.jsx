import React, { useState, useRef, useEffect } from 'react';
import { Bot, Send, Sparkles, RefreshCw, ChevronDown, ChevronUp, Lightbulb, BarChart2, Package, ShoppingCart, AlertTriangle } from 'lucide-react';
import { askCopilot, fetchCopilotQuestions } from '../services/api';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Toast from '../components/common/Toast';

const INTENT_ICONS = {
  ORDER_RISK:      { icon: ShoppingCart, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  STOCKOUT_RISK:   { icon: Package, color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' },
  REORDER:         { icon: RefreshCw, color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/30' },
  ALLOCATION:      { icon: BarChart2, color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/30' },
  BOTTLENECK:      { icon: AlertTriangle, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
  TRACEABILITY:    { icon: Sparkles, color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
  EXCEPTIONS:      { icon: AlertTriangle, color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/30' },
  DISPATCH:        { icon: Sparkles, color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/30' },
  INVENTORY_RISK:  { icon: Package, color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/30' },
  GENERAL_STATUS:  { icon: Bot, color: 'text-sky-400', bg: 'bg-sky-500/10', border: 'border-sky-500/30' },
};

function ConfidenceDots({ confidence }) {
  const pct = Math.round(confidence * 100);
  const filled = Math.round(confidence * 5);
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <div key={i} className={`w-1.5 h-1.5 rounded-full ${i < filled ? 'bg-sky-400' : 'bg-slate-700'}`} />
      ))}
      <span className="text-[10px] text-slate-500 ml-1">{pct}% confidence</span>
    </div>
  );
}

function DataCount({ data }) {
  if (!data) return null;
  const count = Array.isArray(data) ? data.length : typeof data === 'object' ? Object.keys(data).length : 0;
  if (count === 0) return null;
  return (
    <span className="text-[10px] bg-slate-800 border border-slate-700 text-slate-400 px-2 py-0.5 rounded-full">
      {count} data point{count !== 1 ? 's' : ''} retrieved
    </span>
  );
}

function CopilotMessage({ msg }) {
  const [showData, setShowData] = useState(false);
  const cfg = INTENT_ICONS[msg.intent] || INTENT_ICONS.GENERAL_STATUS;
  const Icon = cfg.icon;
  const hasData = msg.data && (Array.isArray(msg.data) ? msg.data.length > 0 : Object.keys(msg.data).length > 0);
  const hasRecs = msg.recommendations && msg.recommendations.length > 0;

  return (
    <div className="flex gap-3">
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-xl border flex items-center justify-center ${cfg.bg} ${cfg.border}`}>
        <Icon className={`w-4 h-4 ${cfg.color}`} />
      </div>

      <div className="flex-1 space-y-2">
        {/* Intent badge + confidence */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.color} ${cfg.border}`}>
            {msg.intent.replace(/_/g, ' ')}
          </span>
          <ConfidenceDots confidence={msg.confidence} />
          <DataCount data={msg.data} />
        </div>

        {/* Answer */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 rounded-tl-sm">
          <div className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
            {msg.answer}
          </div>

          {/* Recommendations */}
          {hasRecs && (
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <p className="text-[10px] uppercase text-slate-500 tracking-wide font-semibold mb-2 flex items-center gap-1">
                <Lightbulb className="w-3 h-3" /> Recommended Actions
              </p>
              <ul className="space-y-1">
                {msg.recommendations.map((rec, i) => (
                  <li key={i} className="text-xs text-sky-300 flex items-start gap-1.5">
                    <span className="text-sky-500 mt-0.5">→</span> {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Toggle raw data */}
          {hasData && (
            <div className="mt-3 pt-3 border-t border-slate-700/50">
              <button onClick={() => setShowData(!showData)}
                className="text-[10px] text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-all">
                {showData ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {showData ? 'Hide' : 'Show'} raw data
              </button>
              {showData && (
                <pre className="mt-2 text-[10px] text-slate-400 bg-slate-950 rounded-xl p-3 overflow-x-auto max-h-48 border border-slate-800">
                  {JSON.stringify(msg.data, null, 2)}
                </pre>
              )}
            </div>
          )}
        </div>

        <p className="text-[10px] text-slate-600">{msg.timestamp}</p>
      </div>
    </div>
  );
}

function UserMessage({ text }) {
  return (
    <div className="flex gap-3 flex-row-reverse">
      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
        U
      </div>
      <div className="bg-sky-500/10 border border-sky-500/20 rounded-2xl rounded-tr-sm px-4 py-3 max-w-lg">
        <p className="text-sm text-slate-100">{text}</p>
      </div>
    </div>
  );
}

const QUICK_QUESTIONS = [
  "What should the warehouse manager do right now?",
  "Which orders are at risk today?",
  "Which products should I reorder?",
  "What are today's warehouse bottlenecks?",
  "Which products may stock out soon?",
  "Are there any active exceptions?",
  "How many orders are in transit?",
  "Show me inventory risks.",
];

export default function WarehouseCopilot() {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestedQs, setSuggestedQs] = useState(QUICK_QUESTIONS);
  const [toast, setToast] = useState({ message: '', type: 'info' });
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Auto scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const handleAsk = async (q) => {
    const text = (q || question).trim();
    if (!text || loading) return;

    setQuestion('');
    setMessages(prev => [...prev, { type: 'user', text, timestamp: new Date().toLocaleTimeString() }]);
    setLoading(true);

    try {
      const res = await askCopilot(text);
      const data = res.data || res;
      setMessages(prev => [
        ...prev,
        {
          type: 'copilot',
          answer: data.answer,
          intent: data.intent,
          confidence: data.confidence,
          data: data.data,
          recommendations: data.recommendations,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      if (data.suggested_questions?.length > 0) {
        setSuggestedQs(data.suggested_questions);
      }
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          type: 'copilot',
          answer: `⚠️ I'm having trouble connecting to the warehouse systems. Please check that the backend server is running.\n\nError: ${err.message}`,
          intent: 'GENERAL_STATUS',
          confidence: 0,
          data: [],
          recommendations: ['Ensure the backend server is running at http://localhost:5000'],
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSuggestedQs(QUICK_QUESTIONS);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-tr from-sky-500/20 to-indigo-500/20 border border-sky-500/30 rounded-xl">
            <Bot className="w-5 h-5 text-sky-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-slate-100">AI Warehouse Copilot</h2>
            <p className="text-sm text-slate-400">Deterministic warehouse intelligence — no external AI required</p>
          </div>
        </div>
        {messages.length > 0 && (
          <button onClick={clearChat}
            className="text-xs text-slate-400 hover:text-slate-200 border border-slate-700 px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5">
            <RefreshCw className="w-3.5 h-3.5" /> Clear Chat
          </button>
        )}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto space-y-5 pr-1 min-h-0">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="p-4 bg-gradient-to-tr from-sky-500/10 to-indigo-500/10 border border-sky-500/20 rounded-3xl mb-4">
              <Bot className="w-12 h-12 text-sky-400" />
            </div>
            <h3 className="text-slate-100 font-bold text-lg mb-2">Ask about your warehouse</h3>
            <p className="text-slate-500 text-sm max-w-sm mb-6">
              I can answer questions about orders, inventory risks, stockouts, bottlenecks, dispatches, and more.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-xl">
              {QUICK_QUESTIONS.slice(0, 6).map(q => (
                <button key={q} onClick={() => handleAsk(q)}
                  className="text-xs text-slate-300 bg-slate-900 border border-slate-700 hover:border-sky-500/50 hover:text-sky-300 px-3 py-2 rounded-xl transition-all text-left">
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, i) => (
              <div key={i}>
                {msg.type === 'user' ? (
                  <UserMessage text={msg.text} />
                ) : (
                  <CopilotMessage msg={msg} />
                )}
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-xl bg-sky-500/10 border border-sky-500/30 flex items-center justify-center flex-shrink-0">
                  <Sparkles className="w-4 h-4 text-sky-400 animate-pulse" />
                </div>
                <div className="bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-2">
                  <div className="flex gap-1">
                    {[0, 1, 2].map(i => (
                      <div key={i} className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />
                    ))}
                  </div>
                  <span className="text-xs text-slate-400">Analyzing warehouse data...</span>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Quick suggestions (visible when chat has messages) */}
      {messages.length > 0 && !loading && (
        <div className="flex-shrink-0">
          <div className="flex gap-2 overflow-x-auto pb-1">
            {suggestedQs.slice(0, 4).map(q => (
              <button key={q} onClick={() => handleAsk(q)}
                className="flex-shrink-0 text-[11px] text-slate-400 border border-slate-700 hover:border-sky-500/50 hover:text-sky-300 px-3 py-1.5 rounded-xl transition-all whitespace-nowrap">
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="flex-shrink-0 bg-slate-900 border border-slate-800 rounded-2xl p-3">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about orders, inventory, stockouts, bottlenecks... (Enter to send)"
            rows={2}
            disabled={loading}
            className="flex-1 bg-transparent border-0 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none leading-relaxed"
          />
          <button
            onClick={() => handleAsk()}
            disabled={!question.trim() || loading}
            className="self-end p-2.5 bg-sky-500 hover:bg-sky-400 disabled:bg-slate-700 disabled:text-slate-500 text-white rounded-xl transition-all flex-shrink-0"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-[10px] text-slate-600 mt-1 ml-1">
          Shift+Enter for new line · Works offline using deterministic warehouse intelligence
        </p>
      </div>

      <Toast type={toast.type} message={toast.message} onClose={() => setToast({ message: '', type: 'info' })} />
    </div>
  );
}
