import FormQuestion from './FormQuestion'

export default class FormQuestionRadio extends FormQuestion {
  constructor({ componentName = 'FormQuestionRadio', options = [] }) {
    super({ componentName: componentName, options })
  }
}
