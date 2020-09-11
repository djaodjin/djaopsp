import FormQuestion from './FormQuestion'

export default class FormQuestionNumber extends FormQuestion {
  constructor({ options = [] }) {
    super({ componentName: 'FormQuestionNumber', options })
  }
  render(answers) {
    return answers[0] || ''
  }
  isEmpty(answers) {
    return !answers[0]
  }
}
