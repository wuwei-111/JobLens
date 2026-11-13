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

  async function load(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      data.value = await loader()
    } catch (caught) {
      error.value = caught instanceof Error ? caught.message : '未知错误'
    } finally {
      loading.value = false
    }
  }

  return {
    data: data as Ref<T | null>,
    loading,
    error,
    load,
  }
}
