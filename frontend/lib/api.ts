import type {
  AuthTokens,
  CompareResponse,
  Conversation,
  EligibilityRequest,
  EligibilityResponse,
  Message,
  Programme,
  SearchResults,
  Source,
  University,
  UniversityDetail,
  User,
} from '@/types';

// NEXT_PUBLIC_API_URL is inlined by Next.js at build time:
//   - local dev: set in frontend/.env (http://localhost:8000/api)
//   - production: set as a Vercel env var (https://chuoai.onrender.com/api)
// If it is missing from a production build, fail loudly during the build
// instead of silently falling back to localhost, which caused "Failed to fetch"
// in production.
function getApiBaseUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL;
  if (fromEnv) return fromEnv;

  // Local development fallback only. Never reachable in production builds.
  if (process.env.NODE_ENV !== 'production') {
    return 'http://localhost:8000/api';
  }

  throw new Error(
    'NEXT_PUBLIC_API_URL is not set. Configure it on Vercel ' +
      '(Production value: https://chuoai.onrender.com/api) or in frontend/.env for local development.'
  );
}

const API_BASE_URL = getApiBaseUrl();

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor() {
    this.baseUrl = API_BASE_URL;
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('access_token');
    }
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('access_token', token);
      } else {
        localStorage.removeItem('access_token');
      }
    }
  }

  private authHeaders(): HeadersInit {
    return this.accessToken
      ? { 'Content-Type': 'application/json', Authorization: `Bearer ${this.accessToken}` }
      : { 'Content-Type': 'application/json' };
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: { ...this.authHeaders(), ...(options.headers || {}) },
    });

    if (response.status === 401) {
      const refreshed = await this.refreshToken();
      if (refreshed) {
        return this.request<T>(endpoint, options);
      }
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw new ApiError('Unauthorized', 401);
    }

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new ApiError(error?.detail || `Request failed (${response.status})`, response.status);
    }

    if (response.status === 204 || response.headers.get('content-length') === '0') {
      return undefined as T;
    }

    return response.json();
  }

  private async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) return false;

      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!response.ok) return false;

      const data = await response.json();
      this.setAccessToken(data.tokens.access_token);
      localStorage.setItem('refresh_token', data.tokens.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  // ---------- Auth ----------
  async register(data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
  }) {
    const response = await this.request<{
      message: string;
      user: User;
      tokens: AuthTokens;
    }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.setAccessToken(response.tokens.access_token);
    localStorage.setItem('refresh_token', response.tokens.refresh_token);
    return response;
  }

  async login(data: { email: string; password: string }) {
    const response = await this.request<{
      message: string;
      user: User;
      tokens: AuthTokens;
    }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    this.setAccessToken(response.tokens.access_token);
    localStorage.setItem('refresh_token', response.tokens.refresh_token);
    return response;
  }

  async logout() {
    this.setAccessToken(null);
    localStorage.removeItem('refresh_token');
  }

  async getCurrentUser() {
    return this.request<User>('/auth/me');
  }

  // ---------- Chat ----------
  private mapMessage(raw: any): Message {
    return {
      id: raw.id,
      role: raw.role,
      content: raw.content,
      sources: raw.sources || undefined,
      createdAt: raw.created_at,
    };
  }

  async streamChat(
    message: string,
    conversationId?: string,
    language?: string,
    onChunk?: (chunk: { content: string; sources?: Source[] }) => void,
    signal?: AbortSignal
  ): Promise<{ conversationId: string; sources: Source[] }> {
    const response = await fetch(`${this.baseUrl}/chat/stream`, {
      method: 'POST',
      headers: this.authHeaders(),
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        language: language || 'auto',
      }),
      signal,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new ApiError(error?.detail || 'Failed to send message', response.status);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();
    let sources: Source[] = [];
    let convId = conversationId || '';

    if (!reader) {
      throw new ApiError('Streaming unavailable', 0);
    }

    let buffer = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed.startsWith('data: ')) continue;
        const data = trimmed.slice(6);
        if (data === '[DONE]') continue;

        try {
          const parsed = JSON.parse(data);
          if (parsed.error) throw new ApiError(parsed.error, 500);
          if (parsed.content) {
            onChunk?.({ content: parsed.content });
          }
          if (parsed.sources) sources = parsed.sources;
          if (parsed.conversation_id) convId = parsed.conversation_id;
        } catch (e) {
          if (e instanceof ApiError) throw e;
        }
      }
    }

    return { conversationId: convId, sources };
  }

  async sendMessage(message: string, conversationId?: string, language?: string) {
    return this.request<{ message: string; conversation_id: string; sources: Source[] }>(
      '/chat',
      {
        method: 'POST',
        body: JSON.stringify({ message, conversation_id: conversationId, language: language || 'auto' }),
      }
    );
  }

  async getConversations(params?: { skip?: number; limit?: number; search?: string }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.set('skip', params.skip.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.search) queryParams.set('search', params.search);

    return this.request<Conversation[]>(`/chat/conversations?${queryParams}`);
  }

  async getConversation(id: string): Promise<Conversation> {
    const raw = await this.request<any>(`/chat/conversations/${id}`);
    return {
      ...raw,
      messages: (raw.messages || []).map((m: any) => this.mapMessage(m)),
    };
  }

  async updateConversation(id: string, title: string) {
    return this.request<Conversation>(`/chat/conversations/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    });
  }

  async deleteConversation(id: string) {
    return this.request<void>(`/chat/conversations/${id}`, { method: 'DELETE' });
  }

  // ---------- Universities / Programmes ----------
  async getUniversities(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    region?: string;
    type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.set('skip', params.skip.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.search) queryParams.set('search', params.search);
    if (params?.region) queryParams.set('region', params.region);
    if (params?.type) queryParams.set('type', params.type);

    return this.request<University[]>(`/universities?${queryParams}`);
  }

  async getUniversity(id: string) {
    return this.request<UniversityDetail>(`/universities/${id}`);
  }

  async searchUniversitiesByProgramme(programme: string, limit = 20) {
    const queryParams = new URLSearchParams({ programme, limit: limit.toString() });
    return this.request<{ university: University; programmes: Programme[] }[]>(
      `/universities/search/programme?${queryParams}`
    );
  }

  async getProgrammes(params?: {
    skip?: number;
    limit?: number;
    search?: string;
    university_id?: string;
    level?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.skip) queryParams.set('skip', params.skip.toString());
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.search) queryParams.set('search', params.search);
    if (params?.university_id) queryParams.set('university_id', params.university_id);
    if (params?.level) queryParams.set('level', params.level);

    return this.request<Programme[]>(`/programmes?${queryParams}`);
  }

  async search(q: string, limit = 20): Promise<SearchResults> {
    const queryParams = new URLSearchParams({ q, limit: limit.toString() });
    return this.request<SearchResults>(`/search?${queryParams}`);
  }

  // ---------- Eligibility / Compare ----------
  async checkEligibility(data: EligibilityRequest) {
    return this.request<EligibilityResponse>('/eligibility/check', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async compareUniversities(data: { university_ids: string[]; programme?: string }) {
    return this.request<CompareResponse>('/compare', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();
