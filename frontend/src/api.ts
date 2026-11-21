import { ChatMetadata, HealthStatus } from './types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== 'undefined' && (window.location.hostname.includes('vercel.app') || window.location.hostname.includes('render.com'))
    ? 'https://lyftr-chatbot-backend.onrender.com'
    : 'http://localhost:8000');

export async function fetchHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed with status: ${res.status}`);
  }
  return res.json();
}

export interface ChatResponsePayload {
  session_id: string;
  reply: string;
  metadata: ChatMetadata;
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
  systemPrompt?: string,
  simulateFailureHeader?: string,
): Promise<ChatResponsePayload> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (simulateFailureHeader && simulateFailureHeader.trim()) {
    headers['X-Simulate-Failure'] = simulateFailureHeader.trim();
  }

  const payload: { session_id: string; message: string; system_prompt?: string } = {
    session_id: sessionId,
    message,
  };

  if (systemPrompt && systemPrompt.trim()) {
    payload.system_prompt = systemPrompt.trim();
  }

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  const data = await res.json();

  if (!res.ok) {
    let errorDetail = 'Request failed';
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        errorDetail = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorDetail = data.detail.map((e: { msg?: string }) => e.msg || JSON.stringify(e)).join(', ');
      } else {
        errorDetail = JSON.stringify(data.detail);
      }
    }
    throw new Error(errorDetail);
  }

  return data;
}

export async function fetchSessionMessages(sessionId: string): Promise<Array<{ role: string; content: string; metadata?: ChatMetadata }>> {
  const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
  if (!res.ok) {
    if (res.status === 404) {
      return [];
    }
    throw new Error(`Failed to load messages for session ${sessionId}`);
  }
  const data = await res.json();
  return data.messages || [];
}
