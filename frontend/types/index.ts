// frontend/types/index.ts

export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string | null;
  role: 'USER' | 'ADMIN';
  is_active: boolean;
  created_at: string;
  last_login?: string | null;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Source {
  title: string;
  source_type?: string;
  url?: string;
  university?: string;
  academic_year?: string;
  page?: number;
  similarity?: number;
}

export interface Message {
  id: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM';
  content: string;
  sources?: Source[];
  createdAt?: string;
}

export interface Conversation {
  id: string;
  title: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string | null;
  messages?: Message[];
}

export interface University {
  id: string;
  name: string;
  abbreviation?: string | null;
  type: 'PUBLIC' | 'PRIVATE';
  ownership?: string | null;
  location?: string | null;
  region?: string | null;
  city?: string | null;
  website?: string | null;
  description?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  contact_address?: string | null;
  established_year?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string | null;
}

export interface UniversityDetail extends University {
  programme_count?: number;
}

export interface Programme {
  id: string;
  university_id: string;
  name: string;
  code?: string | null;
  level?: string | null;
  duration?: string | null;
  faculty?: string | null;
  description?: string | null;
  study_mode?: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string | null;
}

export interface SearchResults {
  universities: University[];
  programmes: Programme[];
}

export interface EligibilityRequest {
  programme: string;
  university?: string;
  qualifications: {
    qualification_type?: string;
    subjects?: string[];
    grades?: string;
    points?: number;
    division?: string;
  };
}

export interface EligibilityResponse {
  status:
    | 'ELIGIBLE'
    | 'NOT_ELIGIBLE'
    | 'POTENTIALLY_ELIGIBLE'
    | 'MORE_INFO_REQUIRED';
  programme: string;
  university: string;
  requirements: any[];
  student_qualifications: any;
  reasoning: string;
  sources: Source[];
}

export interface CompareUniversity {
  university_id: string;
  university_name: string;
  location?: string | null;
  type?: string | null;
  ownership?: string | null;
  programme?: string | null;
  duration?: string | null;
  entry_requirements?: string | null;
  fees?: string | null;
  accommodation?: string | null;
  application_info?: string | null;
  sources: any[];
}

export interface CompareResponse {
  programme?: string | null;
  universities: CompareUniversity[];
  notes?: string | null;
}