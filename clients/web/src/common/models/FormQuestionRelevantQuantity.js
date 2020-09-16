import FormQuestion from './FormQuestion'

export default class FormQuestionRelevantQuantity extends FormQuestion {
  constructor({ options = [] }) {
    super({ componentName: 'FormQuestionRelevantQuantity', options })
    this.unit = {
      text: 'Metric Tons CO<sup>2</sup> / Year',
      value: 'tons-year',
    }
  }
  render(answers) {
    const quantity = answers[0]
    if (quantity) {
      const relevance = this.options.find((opt) => opt.value === answers[2])
      return relevance
        ? `${answers[0]} <small>${
            this.unit.text
          }, ${relevance.text.toLowerCase()}</small>`
        : `${answers[0]} <small>${this.unit.text}</small>`
    } else {
      return ''
    }
  }
}
