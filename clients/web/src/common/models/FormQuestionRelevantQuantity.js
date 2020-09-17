import FormQuestion from './FormQuestion'

export default class FormQuestionRelevantQuantity extends FormQuestion {
  constructor({ options = [] }) {
    super({ componentName: 'FormQuestionRelevantQuantity', options })
    this.unit = {
      text: 'Metric Tons CO<sup>2</sup> / Year',
      value: 'tons-year',
    }
  }
}
