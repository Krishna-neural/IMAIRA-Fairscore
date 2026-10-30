import {
  HealthResponse,
  StartInterviewRequest,
  StartInterviewResponse,
  InterviewTurnRequest,
  InterviewTurnResponse,
  ScoreRequest,
  ScoreResponse,
} from '../types/api';

class ApiService {
  private baseUrl: string = '';

  setBaseUrl(url: string) {
    this.baseUrl = url.replace(/\/$/, '');
  }

  async checkHealth(): Promise<HealthResponse> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed with status ${res.status}`);
    }
    return res.json();
  }

  async fetchSystemOverview(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/system/overview`);
    if (!res.ok) {
      throw new Error(`System overview failed with status ${res.status}`);
    }
    return res.json();
  }

  async startInterview(req: StartInterviewRequest): Promise<StartInterviewResponse> {
    const res = await fetch(`${this.baseUrl}/interview/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Failed to start interview: ${err || res.statusText}`);
    }
    return res.json();
  }

  async submitTurn(req: InterviewTurnRequest): Promise<InterviewTurnResponse> {
    const res = await fetch(`${this.baseUrl}/interview/turn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Failed to submit turn: ${err || res.statusText}`);
    }
    return res.json();
  }

  async calculateScore(req: ScoreRequest): Promise<ScoreResponse> {
    const res = await fetch(`${this.baseUrl}/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Failed to generate evaluation: ${err || res.statusText}`);
    }
    return res.json();
  }

  async fetchFairnessAudit(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/fairness/audit`);
    if (!res.ok) {
      throw new Error(`Failed to fetch fairness audit: ${res.statusText}`);
    }
    return res.json();
  }

  async runAllTests(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/test/all`);
    if (!res.ok) {
      throw new Error(`Failed to run tests: ${res.statusText}`);
    }
    return res.json();
  }

  async fetchArchitecture(): Promise<any> {
    const res = await fetch(`${this.baseUrl}/architecture`);
    if (!res.ok) {
      throw new Error(`Failed to fetch architecture: ${res.statusText}`);
    }
    return res.json();
  }
}

export const apiService = new ApiService();
