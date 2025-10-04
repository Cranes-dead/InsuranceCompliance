# Next.js Frontend Implementation Plan

## 🎯 Overview

Build a modern Next.js frontend for the Insurance Compliance System with:
- Professional landing page
- Policy upload and analysis flow
- Interactive dashboard with visualizations
- AI chat integration

---

## 📋 Project Setup

### Step 1: Initialize Next.js Project

```bash
# Navigate to project root
cd C:/Users/adity/OneDrive/Desktop/Capstone

# Create Next.js app
npx create-next-app@latest frontend-nextjs --typescript --tailwind --app --src-dir

# Navigate to frontend
cd frontend-nextjs

# Install required dependencies
npm install axios recharts framer-motion lucide-react date-fns
npm install @tanstack/react-query zustand react-dropzone
npm install chart.js react-chartjs-2
npm install react-hot-toast sonner
```

### Step 2: Project Structure

```
frontend-nextjs/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Landing page
│   │   ├── upload/
│   │   │   └── page.tsx         # Upload flow
│   │   ├── analysis/
│   │   │   └── [id]/
│   │   │       └── page.tsx     # Analysis results
│   │   └── dashboard/
│   │       └── page.tsx         # Main dashboard
│   │
│   ├── components/
│   │   ├── landing/             # Landing page components
│   │   ├── upload/              # Upload components
│   │   ├── analysis/            # Analysis display components
│   │   ├── dashboard/           # Dashboard components
│   │   ├── charts/              # Reusable charts
│   │   ├── chat/                # AI chat components
│   │   └── ui/                  # Shared UI components
│   │
│   ├── lib/
│   │   ├── api.ts               # API client for backend
│   │   ├── types.ts             # TypeScript types
│   │   └── utils.ts             # Helper functions
│   │
│   └── store/
│       └── useStore.ts          # Zustand state management
│
└── public/
    └── images/                  # Static assets
```

---

## 🔗 Backend Integration

### API Configuration

**File: `src/lib/api.ts`**

```typescript
import axios from 'axios';

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minutes for LLaMA analysis
});

// API endpoints
export const API_ENDPOINTS = {
  // Health check
  health: '/api/v1/health',
  
  // Policy analysis
  analyzePolicy: '/api/v1/analyze',
  uploadPolicy: '/api/v1/upload',
  
  // Chat
  chat: '/api/v1/chat',
  createChatSession: '/api/v1/chat/session',
  
  // Dashboard
  getPolicies: '/api/v1/policies',
  getPolicyById: (id: string) => `/api/v1/policies/${id}`,
  getStatistics: '/api/v1/statistics',
};

// API functions
export const api = {
  // Upload and analyze policy
  uploadPolicy: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(API_ENDPOINTS.uploadPolicy, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // Get analysis by ID
  getAnalysis: async (id: string) => {
    const response = await apiClient.get(API_ENDPOINTS.getPolicyById(id));
    return response.data;
  },

  // Chat with AI
  sendChatMessage: async (sessionId: string, message: string, policyContext?: any) => {
    const response = await apiClient.post(API_ENDPOINTS.chat, {
      session_id: sessionId,
      message,
      policy_context: policyContext,
    });
    return response.data;
  },

  // Get all policies
  getAllPolicies: async () => {
    const response = await apiClient.get(API_ENDPOINTS.getPolicies);
    return response.data;
  },

  // Get dashboard statistics
  getStatistics: async () => {
    const response = await apiClient.get(API_ENDPOINTS.getStatistics);
    return response.data;
  },
};
```

### TypeScript Types

**File: `src/lib/types.ts`**

```typescript
export type ComplianceStatus = 'COMPLIANT' | 'NON_COMPLIANT' | 'REQUIRES_REVIEW';

export interface PolicyAnalysis {
  id: string;
  filename: string;
  classification: ComplianceStatus;
  confidence: number;
  compliance_score: number;
  violations: Violation[];
  recommendations: string[];
  explanation: string;
  rag_metadata: {
    regulations_retrieved: number;
    top_sources: string[];
  };
  created_at: string;
}

export interface Violation {
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  type: string;
  description: string;
  regulation_reference: string;
  recommendation: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Policy {
  id: string;
  filename: string;
  status: ComplianceStatus;
  uploadedAt: string;
  lastAnalyzed: string;
  score: number;
}

export interface DashboardStats {
  totalPolicies: number;
  compliantPolicies: number;
  nonCompliantPolicies: number;
  reviewRequired: number;
  averageScore: number;
  recentAnalyses: PolicyAnalysis[];
}
```

---

## 🏗️ Component-by-Component Implementation

### PHASE 1: Landing Page (Start Here)

#### Component 1.1: Hero Section

**File: `src/components/landing/HeroSection.tsx`**

```typescript
'use client';

import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function HeroSection() {
  const router = useRouter();

  return (
    <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-medium">AI-Powered Compliance Verification</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Insurance Policy
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              {' '}Compliance{' '}
            </span>
            Made Simple
          </h1>

          {/* Subheading */}
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Verify motor vehicle insurance policies against IRDAI regulations in seconds.
            Get detailed compliance reports with AI-powered analysis.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push('/upload')}
              className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl"
            >
              Start Analysis
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => router.push('/dashboard')}
              className="inline-flex items-center justify-center gap-2 bg-white text-gray-700 px-8 py-4 rounded-lg font-semibold hover:bg-gray-50 transition-all border-2 border-gray-200"
            >
              <Shield className="w-5 h-5" />
              View Dashboard
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 mt-16 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-blue-600">92%</div>
              <div className="text-sm text-gray-600 mt-1">Accuracy</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">&lt;5s</div>
              <div className="text-sm text-gray-600 mt-1">Analysis Time</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">203</div>
              <div className="text-sm text-gray-600 mt-1">Regulations</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
```

**Test Command:**
```bash
# After creating component, test with:
npm run dev
# Visit http://localhost:3000
```

---

#### Component 1.2: Features Section

**File: `src/components/landing/FeaturesSection.tsx`**

```typescript
'use client';

import { Brain, Zap, Shield, MessageSquare, FileCheck, TrendingUp } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Legal-BERT + RAG + LLaMA 3.1 for intelligent compliance checking',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Get comprehensive compliance reports in under 5 seconds',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
  },
  {
    icon: Shield,
    title: '203 Regulations',
    description: 'Verified against complete IRDAI and MoRTH regulatory database',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    icon: MessageSquare,
    title: 'Interactive Chat',
    description: 'Ask questions about your policy and get AI-powered answers',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  {
    icon: FileCheck,
    title: 'Detailed Reports',
    description: 'Violations, recommendations, and regulatory citations included',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  {
    icon: TrendingUp,
    title: 'Dashboard Analytics',
    description: 'Track compliance trends and manage multiple policies',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
  },
];

export default function FeaturesSection() {
  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Why Choose Our System?
          </h2>
          <p className="text-lg text-gray-600">
            Powered by cutting-edge AI technology for accurate, fast, and explainable compliance verification
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="p-6 rounded-xl border-2 border-gray-100 hover:border-blue-200 hover:shadow-lg transition-all"
              >
                <div className={`w-12 h-12 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
```

---

#### Component 1.3: Landing Page (Complete)

**File: `src/app/page.tsx`**

```typescript
import HeroSection from '@/components/landing/HeroSection';
import FeaturesSection from '@/components/landing/FeaturesSection';

export default function Home() {
  return (
    <main>
      <HeroSection />
      <FeaturesSection />
    </main>
  );
}
```

**Test Command:**
```bash
npm run dev
# Visit http://localhost:3000 - Landing page should be visible
```

---

### PHASE 2: Upload Flow

#### Component 2.1: File Upload Component

**File: `src/components/upload/FileUpload.tsx`**

```typescript
'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { useRouter } from 'next/navigation';
import toast from 'react-hot-toast';

export default function FileUpload() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
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
      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90));
      }, 200);

      const response = await api.uploadPolicy(file);
      
      clearInterval(progressInterval);
      setProgress(100);

      toast.success('Policy analyzed successfully!');
      
      // Redirect to analysis page
      setTimeout(() => {
        router.push(`/analysis/${response.id}`);
      }, 500);

    } catch (error: any) {
      toast.error(error.response?.data?.message || 'Upload failed');
      setProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
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
          
          <button
            onClick={() => setFile(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      {/* Upload Progress */}
      {uploading && (
        <div className="mt-6">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Analyzing policy...</span>
            <span>{progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Upload Button */}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full mt-6 bg-blue-600 text-white py-4 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
      >
        {uploading ? 'Analyzing...' : 'Analyze Policy'}
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
  );
}
```

**File: `src/app/upload/page.tsx`**

```typescript
import FileUpload from '@/components/upload/FileUpload';

export default function UploadPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50 py-20">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Upload Your Policy
          </h1>
          <p className="text-lg text-gray-600">
            Get instant compliance verification powered by AI
          </p>
        </div>
        
        <FileUpload />
      </div>
    </div>
  );
}
```

**Test Command:**
```bash
# Make sure backend is running first:
cd backend
python -m uvicorn api.main:app --reload

# Then test frontend:
cd frontend-nextjs
npm run dev
# Visit http://localhost:3000/upload
```

---

## 🔄 Testing Each Component

### Component Testing Checklist

- [ ] **Hero Section**: Does it display correctly? Do buttons navigate?
- [ ] **Features Section**: Are all 6 features showing with icons?
- [ ] **File Upload**: Can you drag & drop PDF files?
- [ ] **Upload Progress**: Does progress bar animate during upload?
- [ ] **API Connection**: Does backend receive the file?

### Debug Tips

1. **API Connection Issues**:
   ```typescript
   // Add to api.ts for debugging
   apiClient.interceptors.response.use(
     response => {
       console.log('✅ API Response:', response.config.url);
       return response;
     },
     error => {
       console.error('❌ API Error:', error.config?.url, error.message);
       return Promise.reject(error);
     }
   );
   ```

2. **CORS Issues**: Add to FastAPI backend:
   ```python
   # backend/api/main.py
   from fastapi.middleware.cors import CORSMiddleware
   
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## 📝 Next Steps

You've completed **Phase 1 (Landing)** and **Phase 2 (Upload)** setup! 

**To continue with the remaining components, copy and paste this prompt:**

```
Continue the Next.js frontend implementation. We've completed:
✅ Landing page (Hero + Features)
✅ Upload flow (FileUpload component)

Now implement:
1. Analysis Results Page (/analysis/[id])
   - Display classification (COMPLIANT/NON_COMPLIANT/REQUIRES_REVIEW)
   - Show confidence score and compliance score
   - List violations with severity badges
   - Display recommendations
   - Show RAG metadata (regulations used)
   - Add "Chat about this policy" button

2. AI Chat Component
   - Chat interface with message history
   - Send messages to backend /api/v1/chat
   - Display policy context
   - Auto-scroll to latest message
   - Loading states

3. Dashboard Page (/dashboard)
   - Policy portfolio grid (all uploaded policies)
   - Statistics cards (total, compliant, non-compliant, review required)
   - Compliance score gauge chart
   - Violation frequency bar chart
   - Policy status pie chart
   - Recent analyses table

Provide complete code for each component with proper TypeScript types, error handling, and loading states. Include test commands for each component.
```

---

**Current Progress: 20% Complete** ⚡
- ✅ Project setup
- ✅ API integration layer
- ✅ Landing page
- ✅ Upload flow
- ⏳ Analysis results (Next)
- ⏳ Dashboard
- ⏳ Charts & visualizations
