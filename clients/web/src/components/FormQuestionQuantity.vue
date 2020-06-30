<template>
  <form @submit.prevent="processForm">
    <v-container class="px-0 pt-0">
      <v-row>
        <v-col cols="3">
          <v-text-field
            label="Quantity"
            outlined
            v-model="answer"
            hide-details="auto"
          ></v-text-field>
        </v-col>
        <v-col cols="9">
          <v-select
            :items="units"
            label="Unit"
            outlined
            v-model="unit"
            hide-details="auto"
          ></v-select>
        </v-col>
      </v-row>
    </v-container>
    <FormQuestionFooter
      :textareaPlaceholder="question.placeholder"
      :textareaValue="question.comment"
      @textareaUpdate="updateComment"
    />
  </form>
</template>

<script>
import FormQuestionFooter from '@/components/FormQuestionFooter'

export default {
  name: 'FormQuestionQuantity',

  props: ['question'],

  methods: {
    processForm: function () {
      console.log('answer: ', this.answer)
      console.log('unit: ', this.unit)
      console.log('comment: ', this.comment)
      this.$emit('submit')
    },
    updateComment(value) {
      this.comment = value
    },
  },

  data() {
    return {
      units: [
        {
          text: 'Kilowatt-hour (kWh) of Electricity  / Year',
          value: 'kwh-year',
        },
        {
          text: 'Metric Tons / Year',
          value: 'tons-year',
        },
        {
          text: 'GHG Emissions',
          value: 'ghg-emissions-generated',
        },
        {
          text: 'US Gallons / Year',
          value: 'gallons-year',
        },
        {
          text: 'mmBtu / Year',
          value: 'mmbtu-year',
        },
        {
          text: 'Cubic meters / Year',
          value: 'm3-year',
        },
        {
          text: 'Kilo liters / Year',
          value: 'kiloliters-year',
        },
        {
          text: 'Cubic feet / Year',
          value: 'ft3-year',
        },
        {
          text: 'Cubic feet / Year',
          value: 'ft3-year',
        },
      ],
      answer: this.question.answer,
      unit: this.question.unit,
      comment: this.question.comment,
    }
  },

  components: {
    FormQuestionFooter,
  },
}
</script>
