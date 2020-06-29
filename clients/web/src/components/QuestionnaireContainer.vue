<template>
  <div>
    <practice-section-header
      :category="currentQuestion.section"
      :title="currentQuestion.subcategory"
    />
    <p class="mt-3">{{ currentQuestion.text }}</p>
    <span
      class="d-block mb-4"
      style="font-size: 0.9rem;"
      v-if="currentQuestion.optional"
    >
      <sup>*</sup>This answer will not affect your score</span
    >

    <component
      :is="questionForm.component"
      :question="currentQuestion"
      :options="questionForm.options"
      :key="currentQuestion.id"
      @submit="getNextQuestion"
    />
  </div>
</template>

<script>
import { MAP_QUESTION_FORM_TYPES } from '@/config'
import FormQuestionRadio from '@/components/FormQuestionRadio'
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
      const nextQuestionIndex =
        (this.currentQuestionIdx + 1) % this.questions.length
      const nextQuestionId = this.questions[nextQuestionIndex].id
      const queryParams = {
        ...this.$route.query,
        ...{ question: nextQuestionId },
      }
      this.$router.push({
        path: this.$route.path,
        hash: this.$route.hash,
        query: queryParams,
      })
    },
  },

  data() {
    // TODO: Get all assessment questions async
    // TODO: Include section id and subcategory id so user is properly routed when clicking "back"
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
          answer: 'yes',
          comment: 'Previous comment',
          answers: [
            {
              value: 'yes',
              text: 'Yes',
              date: '2020-06-29T04:46:54.505Z',
              author: 'michael@tamerinsolutions.com',
            },
          ],
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
          answer: 'most-yes',
          comment: 'Previous comment',
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
          answer: 'leading',
          comment: 'A related comment written here',
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
          answer:
            'This is an answer for a textarea. Praesent faucibus interdum libero, tristique tempor felis dictum non. Sed a nisi ac neque pulvinar venenatis ut vitae purus. Fusce sagittis nunc massa, vel pharetra mi maximus hendrerit.',
          comment: '',
          optional: true,
        },
        {
          id: '5',
          section: 'Engineering & Design',
          subcategory: 'General',
          text:
            'Etiam sagittis risus sit amet quam iaculis, sit amet finibus mauris laoreet. Praesent faucibus interdum libero, tristique tempor felis dictum non. Suspendisse libero magna, tempus sit amet finibus vel, luctus id purus?',
          type: '5',
          textareaPlaceholder: 'Comments',
          answer: '18',
          unit: 'gallons-year',
          comment: 'Previous comment',
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
          optional: true,
        },
      ],
    }
  },

  components: {
    FormQuestionRadio,
    FormQuestionTextarea,
    FormQuestionQuantity,
    PracticeSectionHeader,
  },
}
</script>
