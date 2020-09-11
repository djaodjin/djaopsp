import FormQuestion from './FormQuestion'

export default class FormQuestionRadio extends FormQuestion {
  constructor({ options = [] }) {
    super({ componentName: 'FormQuestionRadio', options })
  }
  render(answers) {
    const selected = this.options.find((opt) => opt.value === answers[0])
    return selected ? selected.text : ''
  }
  isEmpty(answers) {
    return !answers[0]
  }
}
