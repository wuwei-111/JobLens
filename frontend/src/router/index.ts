import { createRouter, createWebHistory } from 'vue-router'

import AboutDataView from '@/views/AboutDataView.vue'
import EducationExperienceView from '@/views/EducationExperienceView.vue'
import HomeView from '@/views/HomeView.vue'
import NotFoundView from '@/views/NotFoundView.vue'
import SalaryView from '@/views/SalaryView.vue'
import SkillsView from '@/views/SkillsView.vue'

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
