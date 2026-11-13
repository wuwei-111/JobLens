/** Types mirroring backend/app/schemas. Keep in sync with the FastAPI schemas. */

export interface CountItem {
  name: string
  count: number
  ratio: number
}

export interface GroupedCounts {
  group: string
  total: number
  distribution: CountItem[]
}

export interface Overview {
  total_jobs: number
  total_companies: number
  total_cities: number
  total_job_types: number
  total_skills: number
  salary_available: number
  salary_avg: number | null
  salary_median: number | null
  fresh_graduate_count: number
  fresh_graduate_ratio: number
  last_collected_at: string | null
}

export interface EducationStats {
  total: number
  breakdown: CountItem[]
  by_job_type: GroupedCounts[]
}

export interface FreshGraduateStats {
  count: number
  ratio: number
  breakdown: CountItem[]
}

export interface ExperienceStats {
  total: number
  breakdown: CountItem[]
  by_job_type: GroupedCounts[]
  fresh_graduate: FreshGraduateStats
}

export interface SkillItem {
  skill: string
  category: string
  count: number
  ratio: number
}

export interface SkillCategoryItem {
  category: string
  count: number
  ratio: number
}

export interface JobTypeSkillGroup {
  job_type: string
  total_jobs: number
  skills: SkillItem[]
}

export interface SkillsStats {
  total_jobs: number
  total_skills: number
  items: SkillItem[]
  categories: SkillCategoryItem[]
  by_job_type: JobTypeSkillGroup[]
}

export interface SalarySummary {
  count: number
  avg: number | null
  median: number | null
  p25: number | null
  p75: number | null
  min: number | null
  max: number | null
}

export interface SalaryBin {
  label: string
  range_min: number | null
  range_max: number | null
  count: number
  ratio: number
}

export interface SalaryGroup extends SalarySummary {
  group: string
}

export interface SalaryStats {
  total_jobs: number
  salary_available: number
  overall: SalarySummary
  distribution: SalaryBin[]
  by_job_type: SalaryGroup[]
  by_education: SalaryGroup[]
  by_experience: SalaryGroup[]
}

export interface FilterMeta {
  job_types: string[]
  educations: string[]
  experiences: string[]
  cities: string[]
  skills: string[]
}

export interface JobOut {
  id: string
  company: string
  position: string
  job_type: string
  city: string
  salary_min: number | null
  salary_max: number | null
  education: string
  experience: string
  is_fresh_graduate: boolean
  description: string
  source: string
  source_url: string
  collected_at: string | null
  skills: string[]
}

export interface JobListResponse {
  total: number
  page: number
  page_size: number
  items: JobOut[]
}

export interface JobQuery {
  job_type?: string
  education?: string
  experience?: string
  city?: string
  skill?: string
  salary_min?: number
  salary_max?: number
  q?: string
  page?: number
  page_size?: number
}

export interface StatsFilters {
  job_type?: string
  education?: string
  experience?: string
  city?: string
}

/** Backend additions that are documented now and may be surfaced later. */

export interface ValueCount {
  value: string
  count: number
}

export interface QualityStats {
  total_jobs: number
  salary_available: number
  salary_missing: number
  salary_single_bound: number
  salary_invalid_range: number
  salary_outliers: number
  unknown_education: ValueCount[]
  unknown_experience: ValueCount[]
  jobs_without_skills: number
  duplicate_source_urls: ValueCount[]
  demo_records: number
  total_companies: number
  total_cities: number
  collected_from: string | null
  collected_to: string | null
  warnings: string[]
}

export interface CrossStats {
  row_dimension: string
  column_dimension: string
  total: number
  groups: GroupedCounts[]
}

export interface ImportBatch {
  id: number
  dataset_name: string
  source_file: string | null
  on_conflict: string
  total_records: number
  imported: number
  updated: number
  skipped: number
  failed: number
  created_at: string
}

export interface ValidationIssue {
  row: number | null
  record_id: string | null
  message: string
}

export interface ValidationReport {
  dataset_name: string
  total_records: number
  valid_records: number
  invalid_records: number
  duplicate_ids: number
  existing_in_database: number
  missing_fields: Record<string, number>
  salary_missing: number
  salary_single_bound: number
  salary_outliers: number
  unknown_education: ValueCount[]
  unknown_experience: ValueCount[]
  empty_skills: number
  over_limit_skills: number
  duplicate_skill_entries: number
  duplicate_source_urls: ValueCount[]
  demo_records: number
  errors: ValidationIssue[]
  warnings: ValidationIssue[]
  warning_count: number
}

export interface ApiError {
  detail: string | unknown[] | Record<string, unknown>
  code: string
  errors?: unknown[]
}
