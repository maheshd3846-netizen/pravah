import { request } from './client';
import type { DecisionSummaryResponse } from '../types';

export async function fetchDecisionSummary(): Promise<DecisionSummaryResponse> {
  return request<DecisionSummaryResponse>('/decision/summary');
}
