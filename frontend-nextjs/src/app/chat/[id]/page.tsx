'use client';

import { useParams, useRouter } from 'next/navigation';
import ChatInterface from '@/components/chat/ChatInterface';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function ChatPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      {/* Compact Header */}
      <div className="border-b border-border/50 px-4 py-2.5 flex items-center justify-between bg-background/80 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-muted-foreground hover:text-foreground -ml-1"
            onClick={() => router.push(`/analysis/${id}`)}
          >
            <ArrowLeft className="size-3.5" />
            Back to Analysis
          </Button>
          <div className="h-5 w-px bg-border" />
          <h1 className="text-sm font-semibold text-foreground">AI Policy Chat</h1>
        </div>
      </div>

      {/* Full-Screen Chat Interface */}
      <div className="flex-1 overflow-hidden">
        <ChatInterface policyId={id} />
      </div>
    </div>
  );
}
