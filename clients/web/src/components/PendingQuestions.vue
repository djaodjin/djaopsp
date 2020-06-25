<template>
  <v-slide-x-transition mode="out-in">
    <div class="pt-2 pb-6 px-4" v-if="selectedQuestionId" key="viewQuestion">
      <section-back-link
        :to="{
          path: `${$route.path}${$route.hash}`,
        }"
        exact
      />
      View Question
    </div>
    <div v-else class="pending-questions py-4" key="pendingQuestions">
      <v-fade-transition mode="out-in">
        <div class="my-6 mx-4" v-if="!questions.length">
          <p class="text-h5 text-center">
            Congratulations! You have answered all the questions.
          </p>
          <p class="text-subtitle-1 text-center">
            Submit the questionnaire by clicking on the button below.
          </p>
        </div>
        <div v-else>
          <p class="mx-4 mb-0">{{ $t('practices.tab2.intro') }}</p>
          <v-list class="pa-0">
            <v-list-item
              class="question d-block py-4"
              v-for="question in questions"
              :key="question.id"
            >
              <practice-section-header
                :category="question.category"
                :title="question.subcategory"
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
      </v-fade-transition>
    </div>
  </v-slide-x-transition>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'
import SectionBackLink from '@/components/SectionBackLink'

export default {
  name: 'PendingQuestions',

  created() {
    this.setStateFromQueryParams()
  },

  methods: {
    setStateFromQueryParams() {
      const { question } = this.$route.query
      this.selectedQuestionId = question
    },
  },

  watch: {
    $route: 'setStateFromQueryParams',
  },

  data() {
    return {
      selectedQuestionId: null,
      questions: [
        {
          category: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          id: '1',
          text:
            'Suspendisse ultricies, nunc aliquam laoreet pellentesque, odio mi pretium metus, facilisis pulvinar mi sapien in leo?',
          type: '3',
        },
        {
          category: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          id: '3',
          text:
            'Aenean faucibus eu lectus ac imperdiet. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit. Curabitur diam mi, tristique sit amet diam ut, luctus blandit felis?',
          type: '3',
        },
        {
          category: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          id: '4',
          text:
            'Quisque vel est ac nunc vulputate sagittis nec sit amet nulla. Pellentesque rutrum enim mattis fermentum cursus?',
          type: '3',
        },
        {
          category: 'Governance & Management',
          subcategory: 'Management System Rigor',
          id: '6',
          text:
            'Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae?',
          type: '3',
        },
        {
          category: 'Engineering & Design',
          subcategory: 'General',
          id: '9',
          text:
            'Etiam sagittis risus sit amet quam iaculis, sit amet finibus mauris laoreet. Praesent faucibus interdum libero, tristique tempor felis dictum non. Suspendisse libero magna, tempus sit amet finibus vel, luctus id purus?',
          type: '3',
        },
        {
          category: 'Engineering & Design',
          subcategory: 'Material Selection',
          id: '12',
          text:
            'Praesent bibendum, felis in scelerisque porta, lacus mauris elementum neque, non pretium sem sapien eu justo?',
          type: '3',
        },
      ],
    }
  },

  components: {
    PracticeSectionHeader,
    SectionBackLink,
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
