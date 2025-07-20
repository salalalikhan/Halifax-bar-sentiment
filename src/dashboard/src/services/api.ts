import axios from 'axios';
import {
  BarSummary,
  MentionDetail,
  AnalyticsSummary,
  QualityMetrics,
  SearchRequest,
  SearchResponse,
  TrendRequest,
  TrendResponse,
  ComparisonRequest,
  ComparisonResponse,
  HealthResponse,
} from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// API service class
export class ApiService {
  // Health check
  static async getHealth(): Promise<HealthResponse> {
    const response = await api.get<HealthResponse>('/health');
    return response.data;
  }

  // Bar endpoints
  static async getBars(limit?: number): Promise<BarSummary[]> {
    const response = await api.get<BarSummary[]>('/bars', {
      params: { limit },
    });
    return response.data;
  }

  static async getBar(barName: string): Promise<BarSummary> {
    const response = await api.get<BarSummary>(`/bars/${encodeURIComponent(barName)}`);
    return response.data;
  }

  static async getBarMentions(
    barName: string,
    options?: {
      limit?: number;
      offset?: number;
      start_date?: string;
      end_date?: string;
      sentiment?: string;
    }
  ): Promise<MentionDetail[]> {
    const response = await api.get<MentionDetail[]>(
      `/bars/${encodeURIComponent(barName)}/mentions`,
      { params: options }
    );
    return response.data;
  }

  // Mention endpoints
  static async getMentions(options?: {
    limit?: number;
    offset?: number;
    start_date?: string;
    end_date?: string;
    sentiment?: string;
  }): Promise<MentionDetail[]> {
    const response = await api.get<MentionDetail[]>('/mentions', {
      params: options,
    });
    return response.data;
  }

  static async searchMentions(searchRequest: SearchRequest): Promise<SearchResponse> {
    const response = await api.post<SearchResponse>('/search', searchRequest);
    return response.data;
  }

  // Analytics endpoints
  static async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await api.get<AnalyticsSummary>('/analytics/summary');
    return response.data;
  }

  static async getSentimentTrends(trendRequest: TrendRequest): Promise<TrendResponse> {
    const response = await api.post<TrendResponse>('/analytics/trends', trendRequest);
    return response.data;
  }

  static async compareBars(comparisonRequest: ComparisonRequest): Promise<ComparisonResponse> {
    const response = await api.post<ComparisonResponse>('/analytics/compare', comparisonRequest);
    return response.data;
  }

  // Quality endpoints
  static async getQualityMetrics(limit?: number): Promise<QualityMetrics[]> {
    const response = await api.get<QualityMetrics[]>('/quality/metrics', {
      params: { limit },
    });
    return response.data;
  }

  // Processing endpoints
  static async triggerProcessing(options?: {
    limit?: number;
    mode?: string;
    priority?: string;
  }): Promise<{ job_id: string; status: string }> {
    const response = await api.post('/process', options || {});
    return response.data;
  }

  static async getJobStatus(jobId: string): Promise<any> {
    const response = await api.get(`/process/${jobId}`);
    return response.data;
  }
}

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.message || `Error: ${error.response.status}`;
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error: Unable to connect to server';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};

export default api;