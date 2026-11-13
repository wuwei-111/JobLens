import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { filtersFromQuery, filtersToQuery } from '@/lib/filters'
import type { StatsFilters } from '@/types/api'

/**
 * Keeps the analysis-page filters in the URL query.
 *
 * The URL is the source of truth on entry; changes use router.replace so the
 * browser back button is not flooded by every select change.
 */
export function useStatsFilters() {
  const route = useRoute()
  const router = useRouter()
  const filters = ref<StatsFilters>(filtersFromQuery(route.query))

  watch(
    filters,
    (value) => {
      const next = filtersToQuery(value)
      const current = filtersToQuery(filtersFromQuery(route.query))
      if (JSON.stringify(next) !== JSON.stringify(current)) {
        void router.replace({ query: next })
      }
    },
    { deep: true },
  )

  watch(
    () => route.query,
    (query) => {
      const next = filtersFromQuery(query)
      if (JSON.stringify(next) !== JSON.stringify(filters.value)) {
        filters.value = next
      }
    },
    { deep: true },
  )

  return { filters }
}
