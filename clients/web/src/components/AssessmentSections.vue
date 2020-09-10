<template>
  <div
    v-show="
      !Object.keys($route.query).length ||
      ($route.query.section && $route.query.subcategory) ||
      ($route.query.question &&
        $route.query.section &&
        $route.query.subcategory)
    "
  >
    <tab-header :text="header" />
    <tsp-transition name="v-slide-x-transition" mode="out-in">
      <div
        class="pt-2 pb-6 px-4"
        v-if="$route.query.question"
        key="viewQuestion"
      >
        <!-- TODO: Include question section id and subcategory id so user is properly routed when clicking "back" -->
        <section-back-link
          v-if="$route.query.section && $route.query.subcategory"
          :to="{
            path: `${$route.path}${$route.hash}`,
            query: {
              section: $route.query.section,
              subcategory: $route.query.subcategory,
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
          :questionId="$route.query.question"
          :questions="questions"
          :answers="answers"
          :previousAnswers="previousAnswers"
          @saveAnswer="saveAnswer"
        />
      </div>
      <div
        class="pt-2 pb-6 px-4"
        v-else-if="$route.query.section && $route.query.subcategory"
        key="viewSubcategory"
      >
        <section-back-link
          :to="{
            path: `${$route.path}${$route.hash}`,
          }"
          exact
        />
        <div class="subcategory-container">
          <practice-section-subcategory
            :section="section"
            :subcategory="subcategory"
            :answers="answers"
            :previousAnswers="previousAnswers"
            @usePreviousAnswers="usePreviousAnswers"
          />
          <next-practice-section
            class="mt-4"
            :section="nextSection"
            :subcategory="nextSubcategory"
          />
        </div>
      </div>
      <div v-else class="pa-4 px-md-8" key="viewSections">
        <p>{{ $t('practices.tab1.intro') }}</p>
        <div class="sections">
          <v-list
            data-cy="assessment-section"
            class="mb-4"
            outlined
            v-for="loopSection in sections"
            :key="loopSection.id"
          >
            <practice-group-header
              class="mt-2 mb-4"
              :section="loopSection.content"
            />
            <v-list-item
              v-for="loopSubcategory in loopSection.subcategories"
              :key="loopSubcategory.id"
              :to="{
                path: `${$route.path}${$route.hash}`,
                query: {
                  section: loopSection.id,
                  subcategory: loopSubcategory.id,
                },
              }"
              exact
            >
              <practices-section
                :section="loopSection"
                :subcategory="loopSubcategory"
                :unanswered="unanswered"
              />
            </v-list-item>
          </v-list>
        </div>
      </div>
    </tsp-transition>
  </div>
</template>

<script>
import { SectionList } from '@/common/models/SectionList'
import NextPracticeSection from '@/components/NextPracticeSection'
import PracticeGroupHeader from '@/components/PracticeGroupHeader'
import PracticesSection from '@/components/PracticesSection'
import PracticeSectionSubcategory from '@/components/PracticeSectionSubcategory'
import QuestionnaireContainer from '@/components/QuestionnaireContainer'
import SectionBackLink from '@/components/SectionBackLink'
import TabHeader from '@/components/TabHeader'
import TspTransition from '@/components/TspTransition'

export default {
  name: 'AssessmentSections',

  props: ['header', 'questions', 'answers', 'unanswered', 'previousAnswers'],

  methods: {
    saveAnswer(...args) {
      this.$emit('saveAnswer', ...args)
    },
    usePreviousAnswers(...args) {
      this.$emit('usePreviousAnswers', ...args)
    },
  },

  computed: {
    sectionList() {
      return SectionList.createFromQuestions(this.questions)
    },
    sections() {
      return this.sectionList.toArray()
    },
    section() {
      return this.sectionList.getNode(this.$route.query.section)
    },
    subcategory() {
      return (
        this.section &&
        this.section.subcategories.getNode(this.$route.query.subcategory)
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

  components: {
    NextPracticeSection,
    SectionBackLink,
    PracticeGroupHeader,
    PracticesSection,
    PracticeSectionSubcategory,
    QuestionnaireContainer,
    TabHeader,
    TspTransition,
  },
}
</script>

<style lang="scss" scoped>
@media #{map-get($display-breakpoints, 'md-and-up')} {
  .sections {
    display: grid;
    column-gap: 16px;
    grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
    align-items: start;
    grid-auto-flow: row dense;
  }
}

@media #{map-get($display-breakpoints, 'xl-only')} {
  .subcategory-container {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }
}
</style>
