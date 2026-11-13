import { http } from './http'
import type {
  EducationStats,
  ExperienceStats,
  Overview,
  SalaryStats,
  SkillsStats,
  StatsFilters,
} from '@/types/api'

export async function fetchOverview(): Promise<Overview> {
  const { data } = await http.get<Overview>('/stats/overview')
  return data
}

export async function fetchEducationStats(
  filters: StatsFilters = {},
): Promise<EducationStats> {
  const { data } = await http.get<EducationStats>('/stats/education', {
    params: filters,
  })
  return data
}

export async function fetchExperienceStats(
  filters: StatsFilters = {},
): Promise<ExperienceStats> {
  const { data } = await http.get<ExperienceStats>('/stats/experience', {
    params: filters,
  })
  return data
}

export async function fetchSkillsStats(
  filters: StatsFilters = {},
  options: { limit?: number; perTypeLimit?: number } = {},
): Promise<SkillsStats> {
  const { data } = await http.get<SkillsStats>('/stats/skills', {
    params: {
      ...filters,
      limit: options.limit,
      per_type_limit: options.perTypeLimit,
    },
  })
  return data
}

export async function fetchSalaryStats(
  filters: StatsFilters = {},
): Promise<SalaryStats> {
  const { data } = await http.get<SalaryStats>('/stats/salary', {
    params: filters,
  })
  return data
}
