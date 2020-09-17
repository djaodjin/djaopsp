import FormQuestion from './FormQuestion'

export default class FormQuestionNumber extends FormQuestion {
  constructor({ options = [] }) {
    super({ componentName: 'FormQuestionNumber', options })
  }
}
