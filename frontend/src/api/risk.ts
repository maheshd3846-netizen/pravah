import { request } from './client';
import type { RiskOverviewResponse, NodeRiskDetail } from '../types';

export async function fetchRiskOverview(): Promise<RiskOverviewResponse> {
  return request<RiskOverviewResponse>('/risk/overview');
}

export async function fetchNodeRisks(): Promise<NodeRiskDetail[]> {
  return request<NodeRiskDetail[]>('/risk/nodes');
}

export async function fetchNodeRisk(nodeId: string): Promise<NodeRiskDetail> {
  return request<NodeRiskDetail>(`/risk/${nodeId}`);
}

export async function recalculateRisk(seed: number = 42): Promise<RiskOverviewResponse> {
  return request<RiskOverviewResponse>(`/risk/recalculate?seed=${seed}`, {
    method: 'POST',
  });
}
