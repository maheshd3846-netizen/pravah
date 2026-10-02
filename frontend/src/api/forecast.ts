import { request } from './client';
import type { ForecastItemResponse } from '../types';

export interface RunForecastParams {
  node_id: string;
  item_id: string;
  horizon_hours?: number;
  model_type?: string;
  include_stockout_simulation?: boolean;
  current_inventory_override?: number;
}

export async function runForecast(params: RunForecastParams): Promise<ForecastItemResponse> {
  return request<ForecastItemResponse>('/forecast/run', {
    method: 'POST',
    body: JSON.stringify({
      node_id: params.node_id,
      item_id: params.item_id,
      horizon_hours: params.horizon_hours ?? 72,
      model_type: params.model_type ?? 'xgboost',
      include_stockout_simulation: params.include_stockout_simulation ?? true,
      current_inventory_override: params.current_inventory_override,
    }),
  });
}

export async function getForecastForNodeItem(nodeId: string, itemId: string): Promise<ForecastItemResponse> {
  return request<ForecastItemResponse>(`/forecast/${nodeId}/${itemId}`);
}
