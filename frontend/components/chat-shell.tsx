"use client";

import { FormEvent, useMemo, useState, useRef, useEffect } from "react";
import { motion, AnimatePresence, useReducedMotion } from "framer-motion";
import { Send, User, Bot, Loader2, MapPin, RotateCcw } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { askChat } from "@/lib/api";
import type { Message } from "@/types/chat";

const MAX_QUESTION_LENGTH = 500;

type MarkdownProps = {
  text: string;
  isUser: boolean;
};

function MarkdownText({ text, isUser }: MarkdownProps) {
  const textColor = isUser ? "text-white" : "text-stone-800";

  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children }) => <p className={`whitespace-pre-wrap ${textColor}`}>{children}</p>,
        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        ul: ({ children }) => <ul className="list-disc pl-5">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal pl-5">{children}</ol>,
        li: ({ children }) => <li className={textColor}>{children}</li>,
        code: ({ children }) => (
          <code className={`rounded px-1.5 py-0.5 text-[0.82rem] ${isUser ? "bg-white/20" : "bg-stone-200"} ${textColor}`}>
            {children}
          </code>
        ),
        a: ({ children, href }) => (
          <a
            href={href}
            target="_blank"
            rel="noreferrer"
            className={`underline ${isUser ? "text-stone-100" : "text-stone-700"}`}
          >
            {children}
          </a>
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  );
}

export default function ChatShell() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const shouldReduceMotion = useReducedMotion();

  const remainingChars = useMemo(
    () => MAX_QUESTION_LENGTH - question.length,
    [question.length],
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isLoading) return;

    const sanitized = question.trim();
    if (!sanitized) return;
    if (sanitized.length > MAX_QUESTION_LENGTH) {
      setError(`Pertanyaan maksimal ${MAX_QUESTION_LENGTH} karakter.`);
      return;
    }

    setError(null);
    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      text: sanitized,
    };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");
    setIsLoading(true);

    try {
      const result = await askChat(sanitized);
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        text: result.answer,
        sources: result.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Terjadi kesalahan tidak terduga.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      // Only submit if form is valid and not already submitting
      if (question.trim() && !isLoading && remainingChars >= 0) {
        // We trigger submit through the form event to keep logic consistent
        const form = e.currentTarget.form;
        if (form) form.requestSubmit();
      }
    }
  };

  const handleResetChat = () => {
    if (isLoading) return;
    setMessages([]);
    setQuestion("");
    setError(null);
  };

  return (
    <div className="mx-auto flex h-screen w-full max-w-5xl flex-col">
      <header className="sticky top-0 z-10 flex flex-col items-center justify-center border-b border-stone-200/60 bg-[color:var(--surface)]/90 px-6 py-4 backdrop-blur-md">
        <div className="flex w-full max-w-3xl items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[var(--primary-accent)] text-white shadow-sm">
              <Bot size={22} className="stroke-[1.5]" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-stone-900">
                CoffeeMate <span className="text-stone-400 font-normal">| Jogja</span>
              </h1>
              <p className="text-xs font-medium text-stone-700">
                Asisten RAG coffee shop Yogyakarta
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden rounded-full border border-[color:color-mix(in_oklch,var(--accent-amber)_40%,white)] bg-[color:color-mix(in_oklch,var(--accent-amber)_10%,white)] px-2.5 py-1 text-[10px] font-semibold text-stone-700 sm:inline">
              Sumber: @referensikopi
            </span>
            <button
              type="button"
              onClick={handleResetChat}
              disabled={isLoading || messages.length === 0}
              className="inline-flex min-h-11 items-center gap-1 rounded-lg border border-stone-300 bg-white px-3 py-2 text-xs font-medium text-stone-700 transition hover:bg-stone-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)] disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Reset chat"
            >
              <RotateCcw size={14} />
              Reset Chat
            </button>
          </div>
        </div>
      </header>

      {/* Chat Timeline */}
      <main className="flex-1 overflow-y-auto px-4 py-8 pb-6 sm:px-8">
        <AnimatePresence mode="popLayout">
          {messages.length === 0 ? (
            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
              animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
              className="mx-auto flex h-full max-w-xl flex-col items-center justify-center text-center"
            >
              <div className="mb-6 rounded-2xl border border-stone-200/70 bg-[color:var(--surface)] p-6 text-stone-600 shadow-sm">
                <Bot size={40} className="mx-auto mb-4 opacity-50 stroke-[1.5]" />
                <p className="text-base font-medium text-stone-800 mb-1">
                  Halo! Saya CoffeeMate.
                </p>
                <p className="text-sm text-stone-500">
                  Tanyakan rekomendasi coffee shop Jogja berdasarkan kebutuhanmu, seperti WFC, suasana tenang, atau area tertentu.
                </p>
                <p className="mt-3 text-xs text-stone-600">
                  Jawaban disusun dari data Instagram{" "}
                  <a
                    href="https://www.instagram.com/referensikopi/"
                    target="_blank"
                    rel="noreferrer"
                    className="font-semibold underline hover:text-stone-800"
                  >
                    @referensikopi
                  </a>
                  .
                </p>
              </div>
              <div className="flex w-full snap-x snap-mandatory items-center justify-start gap-2 overflow-x-auto px-1 pb-1 text-xs sm:flex-wrap sm:justify-center sm:overflow-visible">
                {[
                  "WFC di Sleman",
                  "Tempat tenang untuk meeting",
                  "Kopi susu di sekitar Kota Jogja",
                ].map((tag) => (
                  <button
                    key={tag}
                    onClick={() => setQuestion(`Rekomendasikan coffee shop ${tag}`)}
                    className="min-h-11 shrink-0 snap-start rounded-full border border-stone-200 bg-white px-4 py-1.5 text-stone-700 shadow-sm transition-colors hover:border-stone-300 hover:bg-stone-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--background)]"
                    aria-label={`Gunakan contoh pertanyaan ${tag}`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            </motion.div>
          ) : (
            <div className="space-y-6">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.95, y: 10 }}
                  animate={shouldReduceMotion ? undefined : { opacity: 1, scale: 1, y: 0 }}
                  transition={shouldReduceMotion ? { duration: 0 } : { duration: 0.26, ease: [0.16, 1, 0.3, 1] }}
                  className={`flex w-full ${
                    message.role === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  <div className={`flex max-w-[85%] sm:max-w-[75%] gap-3 group ${
                    message.role === "user" ? "flex-row-reverse" : "flex-row"
                  }`}>
                    {/* Avatar */}
                    <div className="flex-shrink-0 mt-1">
                      {message.role === "user" ? (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-stone-200 text-stone-600 shadow-inner">
                          <User size={16} className="stroke-[2]" />
                        </div>
                      ) : (
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary-accent)] text-white shadow-sm">
                          <Bot size={16} className="stroke-[1.5]" />
                        </div>
                      )}
                    </div>
                    
                    {/* Bubble Content */}
                    <div className="flex flex-col gap-2 min-w-0">
                      <div
                        className={`rounded-2xl px-5 py-3.5 text-[0.9375rem] leading-relaxed shadow-sm border ${
                          message.role === "user"
                            ? "bg-[var(--primary-accent)] text-white border-transparent rounded-tr-sm"
                            : "bg-white text-stone-800 border-stone-200/60 rounded-tl-sm ring-1 ring-stone-900/5"
                        }`}
                      >
                        <MarkdownText text={message.text} isUser={message.role === "user"} />
                      </div>

                      {/* Source Cards */}
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-1 flex flex-wrap gap-2">
                          {message.sources.map((source, index) => (
                            <motion.div 
                              key={`${message.id}-${source.nama}-${index}`}
                              initial={shouldReduceMotion ? false : { opacity: 0, x: -5 }}
                              animate={shouldReduceMotion ? undefined : { opacity: 1, x: 0 }}
                              transition={shouldReduceMotion ? { duration: 0 } : { delay: 0.18 + (index * 0.08) }}
                              className={`group/card flex max-w-full cursor-default items-start gap-2 rounded-xl border bg-[color:var(--surface)] p-2.5 text-xs shadow-sm transition-all hover:bg-white ${
                                index % 3 === 0
                                  ? "border-[color:color-mix(in_oklch,var(--accent-amber)_35%,white)]"
                                  : index % 3 === 1
                                    ? "border-[color:color-mix(in_oklch,var(--accent-leaf)_35%,white)]"
                                    : "border-[color:color-mix(in_oklch,var(--accent-berry)_30%,white)]"
                              }`}
                              title={source.lokasi}
                            >
                              <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-stone-100 text-stone-500">
                                <span className="font-semibold">{index + 1}</span>
                              </div>
                              <div className="flex flex-col overflow-hidden">
                                <span className="font-semibold text-stone-700 truncate">{source.nama}</span>
                                <span className="text-stone-500 truncate flex items-center gap-1">
                                  <MapPin size={10} className="shrink-0" />
                                  <span className="truncate">{source.lokasi}</span>
                                </span>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              ))}
              
              {isLoading && (
                <motion.div
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 10 }}
                  animate={shouldReduceMotion ? undefined : { opacity: 1, y: 0 }}
                  className="flex w-full justify-start"
                >
                  <div className="flex max-w-[85%] sm:max-w-[75%] gap-3 flex-row">
                    <div className="flex-shrink-0 mt-1">
                      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--primary-accent)] text-white shadow-sm opacity-50">
                        <Bot size={16} className="stroke-[1.5]" />
                      </div>
                    </div>
                    <div className="rounded-2xl bg-white border border-stone-200/60 rounded-tl-sm px-5 py-3.5 shadow-sm text-stone-500 flex items-center gap-3">
                      <Loader2 size={16} className="animate-spin text-[var(--primary-accent)]" />
                      <span className="text-sm font-medium animate-pulse">Mencari referensi yang relevan...</span>
                    </div>
                  </div>
                </motion.div>
              )}
              <div ref={messagesEndRef} className="h-1" />
            </div>
          )}
        </AnimatePresence>
      </main>

      <div className="sticky bottom-0 border-t border-stone-200/70 bg-[color:var(--surface)]/95 px-4 pb-[calc(env(safe-area-inset-bottom)+0.8rem)] pt-3 backdrop-blur-md sm:static sm:border-t-0 sm:bg-transparent sm:px-6 sm:pb-6 sm:pt-3">
        <form
          onSubmit={onSubmit}
          className="mx-auto flex max-w-3xl flex-col gap-2"
        >
          {error && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              className="mb-2 px-3 py-2 bg-red-50 text-red-600 text-xs rounded-lg border border-red-100 flex items-center gap-2"
            >
              <div className="h-1.5 w-1.5 rounded-full bg-red-500 shrink-0" />
              {error}
            </motion.div>
          )}
          <div className="relative flex items-end gap-2">
            <textarea
              id="question"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={question.split("\n").length > 1 ? Math.min(question.split("\n").length, 5) : 1}
              className="max-h-32 min-h-[44px] w-full resize-none rounded-xl border border-stone-300 bg-[var(--background)] px-3 py-3 text-[0.9375rem] leading-relaxed text-stone-800 outline-none placeholder:text-stone-500 transition-colors focus:border-stone-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)] scrollbar-thin scrollbar-thumb-stone-200"
              placeholder="Contoh: rekomendasi coffee shop untuk WFC di Sleman"
              disabled={isLoading}
              aria-label="Pertanyaan untuk CoffeeMate"
            />
            <div className="shrink-0 flex items-center gap-2 pb-1 pr-1">
              <span
                className={`text-[10px] sm:text-xs font-medium transition-colors ${
                  remainingChars >= 0
                    ? remainingChars < 100 ? "text-amber-500" : "text-stone-400"
                    : "text-red-500"
                }`}
              >
                {remainingChars}
              </span>
              <button
                type="submit"
                disabled={isLoading || !question.trim() || remainingChars < 0}
                className="group flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--primary-accent)] text-white shadow-md transition-all hover:bg-stone-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--focus-ring)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--surface)] active:scale-95 disabled:cursor-not-allowed disabled:bg-stone-300 disabled:shadow-none sm:h-auto sm:w-auto sm:px-4 sm:py-2.5"
                aria-label="Kirim pertanyaan"
              >
                {isLoading ? (
                  <Loader2 size={18} className="animate-spin text-white sm:mr-0" />
                ) : (
                  <>
                    <span className="hidden sm:inline text-sm font-semibold tracking-wide pr-2">Kirim</span>
                    <Send size={18} className="translate-y-[1px] -translate-x-[1px] sm:translate-x-0 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
