'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Send, Bot, User, Loader2, FileText, BookOpen, Shield, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface ChatInterfaceProps {
  policyId: string;
  className?: string;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: Date;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ChatInterface({ policyId, className = '' }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI compliance assistant. I can answer questions about this policy analysis, explain violations, and provide guidance on IRDAI regulations. How can I help you?",
      createdAt: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = (instant = false) => {
    const el = scrollContainerRef.current;
    if (!el) return;
    setTimeout(() => {
      el.scrollTo({ top: el.scrollHeight, behavior: instant ? 'instant' : 'smooth' });
    }, 50);
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading]);

  const sendMessage = async (userText: string) => {
    if (!userText.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: userText.trim(),
      createdAt: new Date(),
    };

    // Add user message and a blank assistant placeholder
    const assistantId = (Date.now() + 1).toString();
    const assistantPlaceholder: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      createdAt: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, assistantPlaceholder]);
    setInput('');
    setIsLoading(true);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(`${API_BASE}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: policyId,
          message: userText.trim(),
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete lines from the buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? ''; // keep the incomplete last chunk

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed) continue;

          // Vercel AI Data Stream Protocol: `0:"chunk text"`
          if (trimmed.startsWith('0:')) {
            try {
              const jsonStr = trimmed.slice(2); // remove `0:`
              const chunk: string = JSON.parse(jsonStr);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId ? { ...m, content: m.content + chunk } : m
                )
              );
            } catch {
              // ignore malformed lines
            }
          }
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') return;

      console.error('Chat stream error:', err);
      toast.error('Failed to get a response. Please try again.');

      // Replace the empty placeholder with an error message
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId
            ? { ...m, content: 'I apologize, but I encountered an error. Please try again.' }
            : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  const quickActions = [
    { icon: FileText, label: 'Summarize', prompt: 'Can you provide a summary of the key compliance issues?' },
    { icon: Shield, label: 'Violations', prompt: 'What are the critical violations found in this policy?' },
    { icon: BookOpen, label: 'Regulations', prompt: 'Which IRDAI regulations apply to this policy?' },
    { icon: Lightbulb, label: 'Recommendations', prompt: 'What are your top recommendations for improving compliance?' },
  ];

  return (
    <div className={`flex flex-col h-full bg-background overflow-hidden ${className}`}>
      {/* Messages — native scrollable div so scrollTop works reliably */}
      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto px-4 py-6">
          {messages.length === 1 && (
            <div className="text-center py-12">
              <Avatar className="size-12 mx-auto mb-3">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="size-6" />
                </AvatarFallback>
              </Avatar>
              <h2 className="text-xl font-heading text-foreground mb-1">Ask anything about this policy</h2>
              <p className="text-sm text-muted-foreground">
                Get instant answers about compliance, violations, and IRDAI regulations
              </p>
            </div>
          )}

          <div className="space-y-5">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <Avatar className="size-7 flex-shrink-0 mt-0.5">
                    <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                      <Bot className="size-3.5" />
                    </AvatarFallback>
                  </Avatar>
                )}

                <div className={`flex-1 max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`inline-block px-3.5 py-2.5 rounded-xl text-sm leading-relaxed ${
                      message.role === 'user'
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-muted text-foreground'
                    }`}
                  >
                    {message.role === 'user' ? (
                      <p className="whitespace-pre-wrap">{message.content}</p>
                    ) : message.content === '' && isLoading ? (
                      <Loader2 className="size-4 animate-spin text-muted-foreground" />
                    ) : (
                      <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-background/80 prose-pre:border prose-pre:border-border prose-pre:p-3 prose-pre:rounded-lg overflow-hidden">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                    )}
                  </div>
                  <p suppressHydrationWarning className="text-[10px] text-muted-foreground/60 mt-1 px-1">
                    {message.createdAt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>

                {message.role === 'user' && (
                  <Avatar className="size-7 flex-shrink-0 mt-0.5">
                    <AvatarFallback className="bg-secondary text-secondary-foreground text-xs">
                      <User className="size-3.5" />
                    </AvatarFallback>
                  </Avatar>
                )}
              </div>
            ))}


          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-border/50 bg-background">
        <div className="max-w-3xl mx-auto px-4 py-3">
          {/* Quick Action Buttons */}
          {messages.length <= 1 && (
            <div className="flex flex-wrap gap-1.5 mb-2.5">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="gap-1.5 text-xs h-7"
                  onClick={() => sendMessage(action.prompt)}
                  disabled={isLoading}
                >
                  <action.icon className="size-3" />
                  {action.label}
                </Button>
              ))}
            </div>
          )}

          {/* Input Field */}
          <form onSubmit={handleSubmit} className="relative">
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about this policy..."
              className="resize-none pr-12 min-h-[48px] max-h-[160px] text-sm"
              rows={1}
              disabled={isLoading}
            />

            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 size-8"
            >
              <Send className="size-3.5" />
            </Button>
          </form>

          <p className="text-[10px] text-muted-foreground/60 mt-1.5 text-center">
            Press{' '}
            <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-[9px]">Enter</kbd> to
            send,{' '}
            <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-[9px]">Shift + Enter</kbd>{' '}
            for new line
          </p>
        </div>
      </div>
    </div>
  );
}
