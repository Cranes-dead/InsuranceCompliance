'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import toast, { Toaster } from 'react-hot-toast';

export default function FileUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      toast.success('File selected');
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    maxFiles: 1,
    multiple: false,
  });

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setProgress(0);

    try {
      // Show progress with status messages
      const progressSteps = [
        { progress: 10, message: 'Uploading PDF...', time: 500 },
        { progress: 25, message: 'Extracting text...', time: 1000 },
        { progress: 40, message: 'Generating embeddings...', time: 2000 },
        { progress: 60, message: 'Retrieving regulations...', time: 3000 },
        { progress: 80, message: 'LLaMA analysis in progress...', time: 10000 },
        { progress: 90, message: 'Finalizing results...', time: 15000 },
      ];

      let currentStep = 0;
      const progressInterval = setInterval(() => {
        if (currentStep < progressSteps.length) {
          const step = progressSteps[currentStep];
          setProgress(step.progress);
          toast.loading(step.message, { id: 'analysis-progress' });
          currentStep++;
        }
      }, 2000); // Update every 2 seconds

      const response = await api.uploadPolicy(file);
      
      clearInterval(progressInterval);
      toast.dismiss('analysis-progress');
      setProgress(100);

      toast.success('Policy analyzed successfully!');
      
      // Redirect to analysis page
      setTimeout(() => {
        router.push(`/analysis/${response.id}`);
      }, 500);

    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Upload failed. Please try again.');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <>
      <Toaster position="top-right" />
      <div className="max-w-2xl mx-auto">
        {/* Dropzone */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
            isDragActive
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-gray-400 bg-white'
          }`}
        >
          <input {...getInputProps()} />
          
          <Upload className={`w-16 h-16 mx-auto mb-4 ${
            isDragActive ? 'text-blue-500' : 'text-gray-400'
          }`} />
          
          {isDragActive ? (
            <p className="text-lg text-blue-600 font-medium">Drop your policy here</p>
          ) : (
            <>
              <p className="text-lg text-gray-700 font-medium mb-2">
                Drag & drop your insurance policy
              </p>
              <p className="text-sm text-gray-500 mb-4">
                or click to browse files
              </p>
              <p className="text-xs text-gray-400">
                Supports PDF files only • Max 10MB
              </p>
            </>
          )}
        </div>

        {/* Selected File */}
        {file && (
          <div className="mt-6 p-4 bg-gray-50 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-3">
              <File className="w-8 h-8 text-blue-600" />
              <div>
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            
            {!uploading && (
              <button
                onClick={() => setFile(null)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            )}
          </div>
        )}

        {/* Upload Progress */}
        {uploading && (
          <div className="mt-6 space-y-3">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing policy with RAG+LLaMA...
              </span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs text-blue-800">
              <p className="font-medium mb-1">⏱️ This may take 2-3 minutes</p>
              <p className="text-blue-600">
                We're retrieving 112 IRDAI regulations and using AI to analyze your policy for compliance.
              </p>
            </div>
          </div>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full mt-6 bg-blue-600 text-white py-4 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {uploading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze Policy'
          )}
        </button>

        {/* Info Alert */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg flex gap-3">
          <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">What happens next?</p>
            <p>
              Our AI will analyze your policy against 203 IRDAI regulations and provide
              a detailed compliance report with violations and recommendations.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
