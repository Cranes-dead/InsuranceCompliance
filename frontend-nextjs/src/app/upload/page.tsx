import Navbar from '@/components/layout/Navbar';
import FileUpload from '@/components/upload/FileUpload';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-12">
        {/* Back Button */}
        <Link href="/">
          <Button variant="ghost" size="sm" className="gap-1.5 mb-6 -ml-2 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-3.5" />
            Back to Home
          </Button>
        </Link>

        {/* Header */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-heading text-foreground mb-3">
            Upload Your Policy
          </h1>
          <p className="text-muted-foreground text-lg">
            Get instant compliance verification powered by AI
          </p>
        </div>

        {/* Upload Component */}
        <FileUpload />
      </div>
    </div>
  );
}
