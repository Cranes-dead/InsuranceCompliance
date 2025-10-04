import FileUpload from '@/components/upload/FileUpload';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-20">
      <div className="container mx-auto px-4">
        {/* Back Button */}
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>

        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Upload Your Policy
          </h1>
          <p className="text-lg text-gray-600">
            Get instant compliance verification powered by AI
          </p>
        </div>
        
        {/* Upload Component */}
        <FileUpload />
      </div>
    </div>
  );
}
