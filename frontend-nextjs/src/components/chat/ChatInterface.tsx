'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/lib/types';
import { api } from '@/lib/api';
import { Send, Bot, User, Loader2, FileText, BookOpen, Shield, Lightbulb } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';

interface ChatInterfaceProps {
  policyId: string;
  className?: string;
}

export default function ChatInterface({ policyId, className = '' }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setMessages([
      {
        role: 'assistant',
        content: 'Hello! I\'m your AI compliance assistant. I can answer questions about this policy analysis, explain violations, and provide guidance on IRDAI regulations. How can I help you?',
        timestamp: new Date().toISOString()
      }
    ]);
  }, []);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.sendChatMessage(policyId, input.trim());

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: unknown) {
      console.error('Chat error:', error);
      toast.error('Failed to send message');

      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your message. Please try again.',
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    { icon: FileText, label: 'Summarize', prompt: 'Can you provide a summary of the key compliance issues?' },
    { icon: Shield, label: 'Violations', prompt: 'What are the critical violations found in this policy?' },
    { icon: BookOpen, label: 'Regulations', prompt: 'Which IRDAI regulations apply to this policy?' },
    { icon: Lightbulb, label: 'Recommendations', prompt: 'What are your top recommendations for improving compliance?' }
  ];

  const handleQuickAction = (prompt: string) => {
    setInput(prompt);
    inputRef.current?.focus();
  };

  return (
    <div className={`flex flex-col h-full bg-background overflow-hidden ${className}`}>
      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="max-w-3xl mx-auto px-4 py-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <Avatar className="size-12 mx-auto mb-3">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="size-6" />
                </AvatarFallback>
              </Avatar>
              <h2 className="text-xl font-heading text-foreground mb-1">Ask anything about this policy</h2>
              <p className="text-sm text-muted-foreground">Get instant answers about compliance, violations, and IRDAI regulations</p>
            </div>
          )}

          <div className="space-y-5">
            {messages.map((message, index) => (
              <div
                key={index}
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
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                  <p className="text-[10px] text-muted-foreground/60 mt-1 px-1">
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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

            {loading && (
              <div className="flex gap-3 justify-start">
                <Avatar className="size-7 flex-shrink-0">
                  <AvatarFallback className="bg-primary text-primary-foreground text-xs">
                    <Bot className="size-3.5" />
                  </AvatarFallback>
                </Avatar>
                <div className="flex-1">
                  <div className="inline-block px-3.5 py-2.5 rounded-xl bg-muted">
                    <Loader2 className="size-4 animate-spin text-muted-foreground" />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </ScrollArea>

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
                  onClick={() => handleQuickAction(action.prompt)}
                  disabled={loading}
                >
                  <action.icon className="size-3" />
                  {action.label}
                </Button>
              ))}
            </div>
          )}

          {/* Input Field */}
          <div className="relative">
            <Textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about this policy..."
              className="resize-none pr-12 min-h-[48px] max-h-[160px] text-sm"
              rows={1}
              disabled={loading}
            />

            <Button
              size="icon"
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 size-8"
            >
              <Send className="size-3.5" />
            </Button>
          </div>

          <p className="text-[10px] text-muted-foreground/60 mt-1.5 text-center">
            Press <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-[9px]">Enter</kbd> to send, <kbd className="px-1 py-0.5 bg-muted border border-border rounded text-[9px]">Shift + Enter</kbd> for new line
          </p>
        </div>
      </div>
    </div>
  );
}
