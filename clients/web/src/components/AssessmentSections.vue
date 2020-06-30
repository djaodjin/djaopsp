<template>
  <v-slide-x-transition mode="out-in">
    <div class="pt-2 pb-6 px-4" v-if="selectedQuestionId" key="viewQuestion">
      <!-- TODO: Include question section id and subcategory id so user is properly routed when clicking "back" -->
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
      <questionnaire-container
        :questions="questions"
        :questionId="selectedQuestionId"
      />
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
import { SectionList } from '../common/SectionList'
import NextPracticeSection from '@/components/NextPracticeSection'
import PracticesSection from '@/components/PracticesSection'
import PracticeSectionSubcategory from '@/components/PracticeSectionSubcategory'
import QuestionnaireContainer from '@/components/QuestionnaireContainer'
import SectionBackLink from '@/components/SectionBackLink'

export default {
  name: 'AssessmentSections',

  props: ['questions'],

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

  watch: {
    $route: 'setStateFromQueryParams',
  },

  computed: {
    sectionList() {
      return SectionList.createFromQuestions(this.questions)
    },
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

  data() {
    return {
      selectedSectionId: null,
      selectedSubcategoryId: null,
      selectedQuestionId: null,
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
