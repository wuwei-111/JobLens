import { createRouter, createWebHistory } from 'vue-router'

const AboutDataView = () => import('@/views/AboutDataView.vue')
const EducationExperienceView = () =>
  import('@/views/EducationExperienceView.vue')
const HomeView = () => import('@/views/HomeView.vue')
const NotFoundView = () => import('@/views/NotFoundView.vue')
const SalaryView = () => import('@/views/SalaryView.vue')
const SkillsView = () => import('@/views/SkillsView.vue')

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {
      path: '/education-experience',
      name: 'education-experience',
      component: EducationExperienceView,
    },
    { path: '/skills', name: 'skills', component: SkillsView },
    { path: '/salary', name: 'salary', component: SalaryView },
    { path: '/about-data', name: 'about-data', component: AboutDataView },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: NotFoundView,
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
