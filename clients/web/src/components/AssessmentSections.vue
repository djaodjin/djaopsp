<template>
  <v-slide-x-transition mode="out-in">
    <div class="pt-2 pb-6 px-4" v-if="selectedQuestionId" key="viewQuestion">
      <section-back-link
        v-if="selectedSectionId && selectedSubcategoryId"
        :to="{
          path: `${$route.path}${$route.hash}`,
          query: {
            section: selectedSectionId,
            subcategory: selectedSubcategoryId,
          },
        }"
        exact
      />
      <section-back-link
        v-else
        :to="{
          path: `${$route.path}${$route.hash}`,
        }"
        exact
      />
      View Question
    </div>
    <div
      class="pt-2 pb-6 px-4"
      v-else-if="selectedSectionId && selectedSubcategoryId"
      key="viewSubcategory"
    >
      <section-back-link
        :to="{
          path: `${$route.path}${$route.hash}`,
        }"
        exact
      />
      <practice-section-subcategory
        :section="section"
        :subcategory="subcategory"
      />
    </div>
    <div v-else class="sections pa-4" key="viewSections">
      <p>{{ $t('practices.tab1.intro') }}</p>
      <v-list
        class="mb-4"
        outlined
        v-for="section in sections"
        :key="section.id"
      >
        <v-list-item
          v-for="subcategory in section.subcategories"
          :key="subcategory.id"
          :to="{
            path: $route.fullPath,
            query: { section: section.id, subcategory: subcategory.id },
          }"
          exact
        >
          <practices-section
            :category="section.category"
            :title="subcategory.title"
            :questions="subcategory.questions.length"
            :answers="subcategory.answers.length"
          />
        </v-list-item>
      </v-list>
    </div>
  </v-slide-x-transition>
</template>

<script>
import { Fragment } from 'vue-fragment'
import PracticesSection from '@/components/PracticesSection'
import PracticeSectionSubcategory from '@/components/PracticeSectionSubcategory'
import SectionBackLink from '@/components/SectionBackLink'

export default {
  name: 'AssessmentSections',

  created() {
    this.setStateFromQueryParams()
  },

  methods: {
    setStateFromQueryParams() {
      const { section, subcategory, question } = this.$route.query
      this.selectedSectionId = section
      this.selectedSubcategoryId = subcategory
      this.selectedQuestionId = question
    },
  },

  computed: {
    section() {
      return this.sections.find((s) => s.id === this.selectedSectionId)
    },
    subcategory() {
      const section = this.sections.find((s) => s.id === this.selectedSectionId)
      return (
        section &&
        section.subcategories.find((s) => s.id === this.selectedSubcategoryId)
      )
    },
  },

  watch: {
    $route: 'setStateFromQueryParams',
  },

  data() {
    return {
      selectedSectionId: null,
      selectedQuestionId: null,
      sections: [
        {
          id: '1',
          category: 'Governance & Management',
          subcategories: [
            {
              id: '1',
              title: 'Responsibility and Authority',
              questions: [
                {
                  id: '1',
                  text:
                    'Suspendisse ultricies, nunc aliquam laoreet pellentesque, odio mi pretium metus, facilisis pulvinar mi sapien in leo?',
                  type: '3',
                },
                {
                  id: '2',
                  text:
                    'Praesent bibendum, felis in scelerisque porta, lacus mauris elementum neque, non pretium sem sapien eu justo?',
                  type: '3',
                },
                {
                  id: '3',
                  text:
                    'Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae?',
                  type: '3',
                },
                {
                  id: '4',
                  text:
                    'Aenean faucibus eu lectus ac imperdiet. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit. Curabitur diam mi, tristique sit amet diam ut, luctus blandit felis?',
                  type: '3',
                },
                {
                  id: '5',
                  text:
                    'Quisque vel est ac nunc vulputate sagittis nec sit amet nulla. Pellentesque rutrum enim mattis fermentum cursus?',
                  type: '3',
                },
              ],
              answers: [
                {
                  questionId: '3',
                  value: 'yes',
                  textValue: 'Yes',
                },
                {
                  questionId: '5',
                  value: 'most-yes',
                  textValue: 'Mostly Yes',
                },
              ],
            },
            {
              id: '2',
              title: 'Management System Rigor',
              questions: [],
              answers: [],
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
              questions: [],
              answers: [],
            },
            {
              id: '2',
              title: 'Material Selection',
              questions: [],
              answers: [],
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
              questions: [],
              answers: [],
            },
          ],
        },
      ],
    }
  },

  components: {
    SectionBackLink,
    PracticesSection,
    PracticeSectionSubcategory,
  },
}
</script>
