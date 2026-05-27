'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

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
      toast.loading('Uploading and analyzing policy...', { id: 'analysis-progress' });
      setProgress(50);

      const response = await api.uploadPolicy(file);

      toast.dismiss('analysis-progress');
      setProgress(100);
      toast.success('Policy analyzed successfully!');

      setFile(null);
      const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
      if (fileInput) fileInput.value = '';

      setTimeout(() => {
        router.push(`/analysis/${response.id}`);
      }, 500);
    } catch (err: unknown) {
      const error = err as { code?: string; message?: string; response?: { status?: number; data?: { detail?: string; message?: string } } };
      toast.dismiss('analysis-progress');
      setProgress(0);

      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        toast.error('Analysis is taking longer than expected. Check the policy list in a few minutes.', { duration: 8000 });
      } else if (error.response?.status === 429) {
        toast.error('Too many requests. Please wait a moment and try again.');
      } else if (error.response?.status === 400) {
        toast.error(error.response?.data?.detail || 'Invalid file. Please check file format and size.');
      } else {
        toast.error(error.response?.data?.message || error.response?.data?.detail || 'Upload failed. Please try again.');
      }
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Dropzone */}
      <Card
        {...getRootProps()}
        className={`p-12 text-center cursor-pointer transition-all border-dashed border-2 hover:border-primary/40 ${
          isDragActive
            ? 'border-primary bg-primary/5'
            : 'border-border'
        }`}
      >
        <input {...getInputProps()} />

        <Upload className={`size-12 mx-auto mb-4 ${
          isDragActive ? 'text-primary' : 'text-muted-foreground/50'
        }`} />

        {isDragActive ? (
          <p className="text-base text-primary font-medium">Drop your policy here</p>
        ) : (
          <>
            <p className="text-base text-foreground font-medium mb-1.5">
              Drag & drop your insurance policy
            </p>
            <p className="text-sm text-muted-foreground mb-3">
              or click to browse files
            </p>
            <p className="text-xs text-muted-foreground/70">
              Supports PDF files only · Max 50MB
            </p>
          </>
        )}
      </Card>

      {/* Selected File */}
      {file && (
        <Card className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="size-10 rounded-md bg-primary/10 flex items-center justify-center">
              <File className="size-5 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">{file.name}</p>
              <p className="text-xs text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          </div>

          {!uploading && (
            <Button
              variant="ghost"
              size="icon"
              className="size-8"
              onClick={() => setFile(null)}
            >
              <X className="size-4" />
            </Button>
          )}
        </Card>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className="space-y-3">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span className="flex items-center gap-2">
              <Loader2 className="size-3.5 animate-spin" />
              Analyzing policy with RAG+LLaMA...
            </span>
            <span className="tabular-nums">{progress}%</span>
          </div>
          <Progress value={progress} className="h-1.5" />
          <Alert className="border-chart-1/30 bg-chart-1/5">
            <AlertCircle className="size-4 text-chart-1" />
            <AlertTitle className="text-sm font-sans">This may take 2-3 minutes</AlertTitle>
            <AlertDescription className="text-xs">
              We&apos;re retrieving 112 IRDAI regulations and using AI to analyze your policy for compliance.
            </AlertDescription>
          </Alert>
        </div>
      )}

      {/* Upload Button */}
      <Button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full h-12 text-base"
        size="lg"
      >
        {uploading ? (
          <>
            <Loader2 className="size-4 animate-spin mr-2" />
            Analyzing...
          </>
        ) : (
          'Analyze Policy'
        )}
      </Button>

      {/* Info Alert */}
      <Alert>
        <AlertCircle className="size-4" />
        <AlertTitle className="font-sans">What happens next?</AlertTitle>
        <AlertDescription>
          Our AI will analyze your policy against 203 IRDAI regulations and provide
          a detailed compliance report with violations and recommendations.
        </AlertDescription>
      </Alert>
    </div>
  );
}
