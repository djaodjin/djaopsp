<template>
  <div
    v-show="
      !Object.keys($route.query).length ||
      ($route.query.question &&
        !$route.query.section &&
        !$route.query.subcategory)
    "
  >
    <tab-header :text="header" />
    <tsp-transition name="v-slide-x-transition" mode="out-in">
      <div
        class="pt-2 pb-6 px-4"
        v-if="
          $route.query.question &&
          !$route.query.section &&
          !$route.query.subcategory
        "
        key="viewQuestion"
      >
        <section-back-link
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
      <div v-else class="pending-questions py-4" key="pendingQuestions">
        <tsp-transition name="v-fade-transition" mode="out-in">
          <div class="my-6 mx-4" v-if="!questions.length">
            <p class="text-h5 text-center">
              Congratulations! You have answered all the questions.
            </p>
            <p class="text-subtitle-1 text-center">
              Save the questionnaire by clicking on the button below.
            </p>
          </div>
          <div v-else>
            <p class="mx-4 mb-0 mx-md-8">{{ $t('practices.tab2.intro') }}</p>
            <v-list class="pa-0">
              <v-list-item
                class="question d-block py-4 px-md-8"
                v-for="question in questions"
                :key="question.id"
              >
                <practice-section-header
                  :section="question.section.name"
                  :subcategory="question.subcategory.name"
                />
                <div class="content pt-3">
                  <p>{{ question.text }}</p>
                  <div class="action">
                    <v-btn
                      class="mx-auto"
                      color="primary"
                      text
                      :to="{
                        path: `${$route.path}${$route.hash}`,
                        query: {
                          question: question.id,
                        },
                      }"
                      exact
                      >Answer</v-btn
                    >
                  </div>
                </div>
              </v-list-item>
            </v-list>
          </div>
        </tsp-transition>
      </div>
    </tsp-transition>
  </div>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import QuestionnaireContainer from '@/components/QuestionnaireContainer'
import SectionBackLink from '@/components/SectionBackLink'
import TabHeader from '@/components/TabHeader'
import TspTransition from '@/components/TspTransition'

export default {
  name: 'PendingQuestions',

  props: ['header', 'questions', 'answers', 'previousAnswers'],

  methods: {
    saveAnswer(...args) {
      this.$emit('saveAnswer', ...args)
    },
  },

  components: {
    PracticeSectionHeader,
    QuestionnaireContainer,
    SectionBackLink,
    TabHeader,
    TspTransition,
  },
}
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.pending-questions {
  & ::v-deep .v-list-item {
    div:last-child {
      display: flex;
      align-items: center;

      > p {
        display: inline-block;
        margin-bottom: 0;
        width: 72%;
      }
      .action {
        flex: 1;
      }
    }
    &:nth-child(even) {
      background-color: $background-row-alternate;
    }
  }
}
</style>
