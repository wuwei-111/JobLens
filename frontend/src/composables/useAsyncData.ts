import { ref, shallowRef, type Ref } from 'vue'

/**
 * Small async loader used by the analysis pages.
 *
 * Initial load shows a status block; later filter changes keep the previous
 * render in place at reduced opacity instead of flashing a skeleton.
 */
export function useAsyncData<T>(loader: () => Promise<T>) {
  const data = shallowRef<T | null>(null)
  const loading = ref(false)
  const error = ref('')
  let requestId = 0

  async function load(): Promise<void> {
    const current = ++requestId
    loading.value = true
    error.value = ''
    try {
      const result = await loader()
      if (current !== requestId) return
      data.value = result
    } catch (caught) {
      if (current !== requestId) return
      error.value = caught instanceof Error ? caught.message : '未知错误'
    } finally {
      if (current === requestId) loading.value = false
    }
  }

  return {
    data: data as Ref<T | null>,
    loading,
    error,
    load,
  }
}
