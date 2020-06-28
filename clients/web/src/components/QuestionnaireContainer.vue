<template>
  <div>
    <practice-section-header
      :category="currentQuestion.section"
      :title="currentQuestion.subcategory"
    />
    <p class="mt-3">{{ currentQuestion.text }}</p>

    <component
      :is="questionForm"
      :question="currentQuestion"
      @submit="getNextQuestion"
    />
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'
import FormQuestionRadioDiscrete from '@/components/FormQuestionRadioDiscrete'
import FormQuestionRadioRange from '@/components/FormQuestionRadioRange'
import FormQuestionRadioState from '@/components/FormQuestionRadioState'
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

  methods: {
    getNextQuestion() {
      console.log('Get next question ...')
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
          textareaPlaceholder: 'Comments',
          answer: null,
          comment: '',
        },
        {
          id: '2',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Aenean faucibus eu lectus ac imperdiet. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit. Curabitur diam mi, tristique sit amet diam ut, luctus blandit felis?',
          type: '2',
          textareaPlaceholder:
            'Please explain how you plan to use the results of the assessment.',
          answer: null,
          comment: '',
        },
        {
          id: '3',
          section: 'Governance & Management',
          subcategory: 'Responsibility and Authority',
          text:
            'Quisque vel est ac nunc vulputate sagittis nec sit amet nulla. Pellentesque rutrum enim mattis fermentum cursus?',
          type: '3',
          textareaPlaceholder:
            'If you do not report energy consumed, please explain why.',
          answer: null,
          comment: '',
          optional: true,
        },
        {
          id: '4',
          section: 'Governance & Management',
          subcategory: 'Management System Rigor',
          text:
            'Vestibulum ante ipsum primis in faucibus orci luctus et ultrices posuere cubilia curae?',
          type: '4',
          textareaPlaceholder:
            'Please explain how you plan to use the results of the assessment.',
          answer: null,
          comment: '',
        },
        {
          id: '5',
          section: 'Engineering & Design',
          subcategory: 'General',
          text:
            'Etiam sagittis risus sit amet quam iaculis, sit amet finibus mauris laoreet. Praesent faucibus interdum libero, tristique tempor felis dictum non. Suspendisse libero magna, tempus sit amet finibus vel, luctus id purus?',
          type: '5',
          textareaPlaceholder: 'Comments',
          answer: null,
          comment: '',
        },
        {
          id: '6',
          section: 'Engineering & Design',
          subcategory: 'Material Selection',
          text:
            'Praesent bibendum, felis in scelerisque porta, lacus mauris elementum neque, non pretium sem sapien eu justo?',
          type: '2',
          textareaPlaceholder:
            'Please explain how you plan to use the results of the assessment.',
          answer: null,
          comment: '',
        },
      ],
    }
  },

  components: {
    FormQuestionRadioDiscrete,
    FormQuestionRadioRange,
    FormQuestionRadioState,
    FormQuestionTextarea,
    FormQuestionQuantity,
    PracticeSectionHeader,
  },
}
</script>
