'use client';

import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '@/lib/types';
import { api } from '@/lib/api';
import { Send, Bot, User, Loader2, FileText, BookOpen, Shield, Lightbulb } from 'lucide-react';
import toast from 'react-hot-toast';

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
    // Welcome message
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
    } catch (error: any) {
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
    <div className={`flex flex-col h-full bg-white overflow-hidden ${className}`}>
      {/* Messages - Full Width */}
      <div className="flex-1 overflow-y-auto bg-gray-50">
        <div className="max-w-4xl mx-auto px-6 py-8">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center mx-auto mb-4">
                <Bot className="text-white" size={32} />
              </div>
              <h2 className="text-2xl font-bold text-gray-800 mb-2">Ask anything about this policy</h2>
              <p className="text-gray-500">Get instant answers about compliance, violations, and IRDAI regulations</p>
            </div>
          )}

          <div className="space-y-6">
            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                    <Bot className="text-white" size={16} />
                  </div>
                )}
                
                <div className={`flex-1 max-w-[85%] ${message.role === 'user' ? 'text-right' : ''}`}>
                  <div
                    className={`inline-block px-4 py-3 rounded-2xl ${
                      message.role === 'user'
                        ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white'
                        : 'bg-gray-50 text-gray-800 border border-gray-100'
                    }`}
                  >
                    <p className="text-[15px] leading-relaxed whitespace-pre-wrap">
                      {message.content}
                    </p>
                  </div>
                  <p className="text-xs text-gray-400 mt-1.5 px-1">
                    {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
                    <User className="text-white" size={16} />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-4 justify-start">
                <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                  <Bot className="text-white" size={16} />
                </div>
                <div className="flex-1">
                  <div className="inline-block px-4 py-3 rounded-2xl bg-gray-50 border border-gray-100">
                    <Loader2 className="animate-spin text-blue-600" size={20} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input Area - Bottom Sticky */}
      <div className="border-t border-gray-200 bg-white shadow-lg">
        <div className="max-w-4xl mx-auto px-6 py-4">
          {/* Quick Action Buttons */}
          {messages.length <= 1 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {quickActions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickAction(action.prompt)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-full transition-colors"
                  disabled={loading}
                >
                  <action.icon size={14} />
                  <span>{action.label}</span>
                </button>
              ))}
            </div>
          )}

          {/* Input Field */}
          <div className="relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything or @mention a Space"
              className="w-full resize-none px-5 py-4 pr-14 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-[15px] text-gray-900 placeholder:text-gray-400 bg-white disabled:bg-gray-50 disabled:text-gray-500 transition-shadow"
              rows={1}
              style={{ minHeight: '56px', maxHeight: '200px' }}
              disabled={loading}
            />
            
            {/* Send Button - Inside Input */}
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="absolute right-3 bottom-3 w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center shadow-sm"
            >
              <Send size={18} />
            </button>
          </div>

          {/* Helper Text */}
          <p className="text-xs text-gray-400 mt-2 text-center">
            Press <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded text-gray-600">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-gray-100 border border-gray-200 rounded text-gray-600">Shift + Enter</kbd> for new line
          </p>
        </div>
      </div>
    </div>
  );
}
