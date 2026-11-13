import { http } from './http'
import type { FilterMeta } from '@/types/api'

export async function fetchFilterMeta(): Promise<FilterMeta> {
  const { data } = await http.get<FilterMeta>('/meta/filters')
  return data
}
