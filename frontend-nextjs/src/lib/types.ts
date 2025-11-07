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
    regulations_retrieved?: number;
    top_sources?: string[];
    compliance_score?: number;
    analysis_type?: string;
    document_length?: number;
    mandatory_requirements?: string[];
    probabilities?: Record<string, number>;
    custom_rules_applied?: number;
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
