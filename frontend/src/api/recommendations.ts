import { request } from './client';
import type { RecommendationListResponse, RecommendationItem } from '../types';

export interface GenerateRecommendationsParams {
  scenario_id?: string;
  optimization_run_id?: string;
  evaluation_id?: string;
  demand_policy?: string;
  data_quality_state?: string;
  horizon_hours?: number;
  seed?: number;
}

export interface RecommendationFilterParams {
  scenario_id?: string;
  status?: string;
  priority?: number;
  node?: string;
  item?: string;
}

export async function generateRecommendations(
  params: GenerateRecommendationsParams = {}
): Promise<RecommendationListResponse> {
  return request<RecommendationListResponse>('/recommendations/generate', {
    method: 'POST',
    body: JSON.stringify({
      scenario_id: params.scenario_id ?? 'COMPOUND_DISRUPTION',
      optimization_run_id: params.optimization_run_id,
      evaluation_id: params.evaluation_id,
      demand_policy: params.demand_policy ?? 'P80',
      data_quality_state: params.data_quality_state ?? 'READY',
      horizon_hours: params.horizon_hours ?? 72,
      seed: params.seed ?? 42,
    }),
  });
}

export async function listRecommendations(
  filters: RecommendationFilterParams = {}
): Promise<RecommendationListResponse> {
  const query = new URLSearchParams();
  if (filters.scenario_id) query.append('scenario_id', filters.scenario_id);
  if (filters.status) query.append('status', filters.status);
  if (filters.priority !== undefined) query.append('priority', filters.priority.toString());
  if (filters.node) query.append('node', filters.node);
  if (filters.item) query.append('item', filters.item);
  const qStr = query.toString();
  return request<RecommendationListResponse>(`/recommendations${qStr ? `?${qStr}` : ''}`);
}

export async function getRecommendation(recommendationId: string): Promise<RecommendationItem> {
  return request<RecommendationItem>(`/recommendations/${recommendationId}`);
}
