import { request } from './client';
import type { NetworkResponse } from '../types';

export async function fetchNetwork(seed: number = 42): Promise<NetworkResponse> {
  return request<NetworkResponse>(`/network?seed=${seed}`);
}
