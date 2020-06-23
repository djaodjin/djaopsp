<template>
  <fragment>
    <section-title title="Current Practices" />
    <tab-container :tabs="tabs">
      <template v-slot:tab1>
        <div class="pa-4">
          <p>{{ $t('practices.tab1.intro') }}</p>
          <div class="sections">
            <ul v-for="section in sections" :key="section.id">
              <li
                v-for="subcategory in section.subcategories"
                :key="subcategory.id"
              >
                <practices-section
                  :category="section.category"
                  :title="subcategory.title"
                  :questions="subcategory.questions"
                  :answered="subcategory.answered"
                />
              </li>
            </ul>
          </div>
        </div>
      </template>
      <template v-slot:tab2>
        <div class="pa-4">
          <p>{{ $t('practices.tab2.intro') }}</p>
        </div>
      </template>
    </tab-container>
  </fragment>
</template>

<script>
import { Fragment } from 'vue-fragment'
import PracticesSection from '@/components/PracticesSection'
import SectionTitle from '@/components/SectionTitle'
import TabContainer from '@/components/TabContainer'

export default {
  name: 'AssessmentCurrentPractices',

  data() {
    return {
      sections: [
        {
          id: '1',
          category: 'Governance & Management',
          subcategories: [
            {
              id: '1',
              title: 'Responsibility and Authority',
              questions: '5',
              answered: '2',
            },
            {
              id: '2',
              title: 'Management System Rigor',
              questions: '2',
              answered: '0',
            },
          ],
        },
        {
          id: '2',
          category: 'Engineering & Design',
          subcategories: [
            {
              id: '1',
              title: 'General',
              questions: '4',
              answered: '1',
            },
            {
              id: '2',
              title: 'Material Selection',
              questions: '3',
              answered: '0',
            },
          ],
        },
        {
          id: '3',
          category: 'Construction',
          subcategories: [
            {
              id: '1',
              title: 'Electricity and GHG Emissions',
              questions: '4',
              answered: '4',
            },
          ],
        },
      ],
      tabs: [
        { text: this.$t('practices.tab1.title'), href: 'tab-1' },
        { text: this.$t('practices.tab2.title'), href: 'tab-2' },
      ],
      tab: null,
    }
  },

  components: {
    Fragment,
    PracticesSection,
    SectionTitle,
    TabContainer,
  },
}
</script>

<style lang="scss" scoped>
.sections > ul {
  margin-top: 16px;
  padding-top: 20px;
  border-top: 2px solid #eeeeee;

  &:first-child {
    margin-top: 0;
    padding-top: 0;
    border-top: 0 none;
  }
}
</style>
