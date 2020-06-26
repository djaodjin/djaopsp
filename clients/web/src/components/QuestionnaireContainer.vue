<template>
  <div>
    <practice-section-header
      :category="currentQuestion.section"
      :title="currentQuestion.subcategory"
    />
    <p class="mt-3">{{ currentQuestion.text }}</p>

    <component :is="questionForm" :id="currentQuestion.id" />
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'
import FormQuestionRadioButtons from '@/components/FormQuestionRadioButtons'
import FormQuestionTextarea from '@/components/FormQuestionTextarea'
import FormQuestionQuantity from '@/components/FormQuestionQuantity'
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
    questionForm() {
      return MAP_QUESTION_FORM_TYPES[this.currentQuestion.type]
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
          type: '1',
        },
        {
          id: '2',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Aenean faucibus eu lectus ac imperdiet. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit. Curabitur diam mi, tristique sit amet diam ut, luctus blandit felis?',
          type: '2',
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
          type: '1',
        },
        {
          id: '5',
          section: 'Engineering & Design',
          subcategory: 'General',
          text:
            'Etiam sagittis risus sit amet quam iaculis, sit amet finibus mauris laoreet. Praesent faucibus interdum libero, tristique tempor felis dictum non. Suspendisse libero magna, tempus sit amet finibus vel, luctus id purus?',
          type: '2',
        },
        {
          id: '6',
          section: 'Engineering & Design',
          subcategory: 'Material Selection',
          text:
            'Praesent bibendum, felis in scelerisque porta, lacus mauris elementum neque, non pretium sem sapien eu justo?',
          type: '2',
        },
      ],
    }
  },

  components: {
    FormQuestionRadioButtons,
    FormQuestionTextarea,
    FormQuestionQuantity,
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
