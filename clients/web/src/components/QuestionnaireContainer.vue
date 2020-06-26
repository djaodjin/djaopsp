<template>
  <div>
    <practice-section-header
      :category="currentQuestion.section"
      :title="currentQuestion.subcategory"
    />
    <p class="mt-3">{{ currentQuestion.text }}</p>

    <div class="mt-2 text-right">
      <v-btn
        text
        color="secondary"
        :to="{
          path: `${$route.path}#tab-2`,
        }"
        exact
      >
        <v-icon small>mdi-playlist-edit</v-icon>
        <span class="ml-1">See Pending Questions</span>
      </v-btn>
    </div>
  </div>
</template>

<script>
import PracticeSectionHeader from '@/components/PracticeSectionHeader'

export default {
  name: 'QuestionnaireContainer',

  props: ['questionId'],

  computed: {
    currentQuestionIdx() {
      return this.questions.findIndex((q) => q.id === this.questionId)
    },
    currentQuestion() {
      return this.questions[this.currentQuestionIdx]
    },
  },

  data() {
    // TODO: Get all assessment questions async
    return {
      questions: [
        {
          id: '1',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Suspendisse ultricies, nunc aliquam laoreet pellentesque, odio mi pretium metus, facilisis pulvinar mi sapien in leo?',
          type: '3',
        },
        {
          id: '2',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Aenean faucibus eu lectus ac imperdiet. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit. Curabitur diam mi, tristique sit amet diam ut, luctus blandit felis?',
          type: '3',
        },
        {
          id: '3',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Quisque vel est ac nunc vulputate sagittis nec sit amet nulla. Pellentesque rutrum enim mattis fermentum cursus?',
          type: '3',
        },
        {
          id: '4',
          section: 'Governance & Management',
          subcategory: 'Management System Rigor',
          text:
            'Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae?',
          type: '3',
        },
        {
          id: '5',
          section: 'Engineering & Design',
          subcategory: 'General',
          text:
            'Etiam sagittis risus sit amet quam iaculis, sit amet finibus mauris laoreet. Praesent faucibus interdum libero, tristique tempor felis dictum non. Suspendisse libero magna, tempus sit amet finibus vel, luctus id purus?',
          type: '3',
        },
        {
          id: '6',
          section: 'Engineering & Design',
          subcategory: 'Material Selection',
          text:
            'Praesent bibendum, felis in scelerisque porta, lacus mauris elementum neque, non pretium sem sapien eu justo?',
          type: '3',
        },
      ],
    }
  },

  components: {
    PracticeSectionHeader,
  },
}
</script>

<style lang="scss" scoped>
h1 {
  text-align: left;
  font-size: 1.2rem;
  font-weight: 500;
  margin-top: 0;
  line-height: 0.9;
}

@media #{map-get($display-breakpoints, 'sm-and-up')} {
  h1 {
    font-size: 1.8;
    line-height: 1;
  }
  small {
    font-size: 1rem;
  }
}
</style>
