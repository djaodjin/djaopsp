import FormQuestion from './FormQuestion'

export default class FormQuestionRadio extends FormQuestion {
  constructor({ componentName = 'FormQuestionRadio', options = [] }) {
    super({ componentName: componentName, options })
  }
  render(answers) {
    const selected = this.options.find((opt) => opt.value === answers[0])
    return selected ? selected.text : ''
  }
}
