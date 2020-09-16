export default class FormQuestion {
  constructor({ componentName, options = [] }) {
    this.componentName = componentName
    this.options = options
  }
  render() {
    console.error('This needs to be defined per each instance')
  }
}
