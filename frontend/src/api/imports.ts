import { http } from './http'
import type { ImportBatch } from '@/types/api'

export async function fetchImportBatches(limit = 5): Promise<ImportBatch[]> {
  const { data } = await http.get<ImportBatch[]>('/imports/batches', {
    params: { limit },
  })
  return data
}
