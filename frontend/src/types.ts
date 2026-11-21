export interface ChatMetadata {
  resolution_source: 'LIVE_INFERENCE' | 'LLM_CACHE';
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  key_id: string | null;
  fallback_attempts: number;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  metadata?: ChatMetadata;
  createdAt?: string;
}

export interface HealthStatus {
  status: string;
  keys_configured: number;
  cache_enabled: boolean;
}

export interface SessionInfo {
  session_id: string;
  lastMessage?: string;
  timestamp: number;
}

export interface TelemetryStats {
  totalTurns: number;
  cacheHits: number;
  liveTurns: number;
  totalLiveLatency: number;
  totalCacheLatency: number;
  failoversCount: number;
}
