'use client';

import { useParams, useRouter } from 'next/navigation';
import ChatInterface from '@/components/chat/ChatInterface';
import { ArrowLeft } from 'lucide-react';

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  return (
    <div className="h-screen bg-white flex flex-col overflow-hidden">
      {/* Compact Header */}
      <div className="border-b border-gray-200 px-6 py-3 flex items-center justify-between bg-white">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push(`/analysis/${id}`)}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft size={20} />
            <span className="text-sm font-medium">Back to Analysis</span>
          </button>
          <div className="h-6 w-px bg-gray-300"></div>
          <h1 className="text-lg font-semibold text-gray-900">AI Policy Chat</h1>
        </div>
      </div>

      {/* Full-Screen Chat Interface */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface policyId={id} />
      </div>
    </div>
  );
}
