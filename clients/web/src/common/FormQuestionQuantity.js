import FormQuestion from './FormQuestion'

export default class FormQuestionQuantity extends FormQuestion {
  constructor({ options = [] }) {
    super({ name: 'FormQuestionQuantity', options })
  }
  render(answers) {
    const unit = this.options.find((opt) => opt.value === answers[1])
    return unit ? `${answers[0]} ${unit.text}` : ''
  }
  isEmpty(answers) {
    return !answers[0] || !answers[1]
  }
}
