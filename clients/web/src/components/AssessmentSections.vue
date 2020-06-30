<template>
  <v-slide-x-transition mode="out-in">
    <div v-if="loading">
      Loading ...
    </div>
    <div
      class="pt-2 pb-6 px-4"
      v-else-if="selectedQuestionId"
      key="viewQuestion"
    >
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
      <questionnaire-container :questionId="selectedQuestionId" />
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
      <next-practice-section
        class="mt-4"
        :section="nextSection"
        :subcategory="nextSubcategory"
      />
    </div>
    <div v-else class="sections pa-4" key="viewSections">
      <p>{{ $t('practices.tab1.intro') }}</p>
      <v-list
        class="mb-4"
        outlined
        v-for="loopSection in sections"
        :key="loopSection.id"
      >
        <v-list-item
          v-for="loopSubcategory in loopSection.subcategories"
          :key="loopSubcategory.id"
          :to="{
            path: `${$route.path}${$route.hash}`,
            query: { section: loopSection.id, subcategory: loopSubcategory.id },
          }"
          exact
        >
          <practices-section
            :section="loopSection"
            :subcategory="loopSubcategory"
            :answers="0"
          />
        </v-list-item>
      </v-list>
    </div>
  </v-slide-x-transition>
</template>

<script>
import { Fragment } from 'vue-fragment'
import { getQuestions } from '../mocks/questions'
import { SectionList } from '../common/SectionList'
import NextPracticeSection from '@/components/NextPracticeSection'
import PracticesSection from '@/components/PracticesSection'
import PracticeSectionSubcategory from '@/components/PracticeSectionSubcategory'
import QuestionnaireContainer from '@/components/QuestionnaireContainer'
import SectionBackLink from '@/components/SectionBackLink'

export default {
  name: 'AssessmentSections',

  created() {
    this.fetchData()
    this.setStateFromQueryParams()
  },

  methods: {
    async fetchData() {
      this.loading = true
      const questions = await getQuestions()
      this.sectionList = SectionList.createFromQuestions(questions)
      this.loading = false
    },
    setStateFromQueryParams() {
      const { section, subcategory, question } = this.$route.query
      this.selectedSectionId = section
      this.selectedSubcategoryId = subcategory
      this.selectedQuestionId = question
    },
  },

  computed: {
    sections() {
      return this.sectionList.toArray()
    },
    section() {
      return this.sectionList.getNode(this.selectedSectionId)
    },
    subcategory() {
      return (
        this.section &&
        this.section.subcategories.getNode(this.selectedSubcategoryId)
      )
    },
    nextSection() {
      if (!this.section) return null
      const nextSubcategory = this.section.subcategories.getNext()
      return nextSubcategory ? this.section : this.sectionList.getNext()
    },
    nextSubcategory() {
      if (!this.section) return null
      const nextSubcategory = this.section.subcategories.getNext()
      if (nextSubcategory) return nextSubcategory

      // If there are no more subcategories to display for the current section,
      // start from the first subcategory of the next section
      return this.nextSection && this.nextSection.subcategories.getFirst()
    },
  },

  watch: {
    $route: 'setStateFromQueryParams',
  },

  data() {
    return {
      loading: false,
      selectedSectionId: null,
      selectedSubcategoryId: null,
      selectedQuestionId: null,
      sectionList: new SectionList(),
    }
  },

  components: {
    NextPracticeSection,
    SectionBackLink,
    PracticesSection,
    PracticeSectionSubcategory,
    QuestionnaireContainer,
  },
}
</script>
