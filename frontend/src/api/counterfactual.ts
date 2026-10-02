import { request } from './client';
import type { CounterfactualEvaluationResponse } from '../types';

export interface EvaluatePlanParams {
  optimization_run_id?: string;
  scenario_id?: string;
  horizon_hours?: number;
  seed?: number;
}

export async function evaluatePlan(params: EvaluatePlanParams = {}): Promise<CounterfactualEvaluationResponse> {
  return request<CounterfactualEvaluationResponse>('/optimization/evaluate', {
    method: 'POST',
    body: JSON.stringify({
      optimization_run_id: params.optimization_run_id,
      scenario_id: params.scenario_id ?? 'COMPOUND_DISRUPTION',
      horizon_hours: params.horizon_hours ?? 72,
      seed: params.seed ?? 42,
    }),
  });
}

export async function getEvaluationRecord(evaluationId: string): Promise<CounterfactualEvaluationResponse> {
  return request<CounterfactualEvaluationResponse>(`/optimization/evaluations/${evaluationId}`);
}
