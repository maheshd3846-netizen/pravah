import { request } from './client';
import type { AlertsListResponse } from '../types';

export async function fetchAlerts(severity?: string, nodeId?: string): Promise<AlertsListResponse> {
  const query = new URLSearchParams();
  if (severity) query.append('severity', severity);
  if (nodeId) query.append('node_id', nodeId);
  const qStr = query.toString();
  return request<AlertsListResponse>(`/alerts${qStr ? `?${qStr}` : ''}`);
}
