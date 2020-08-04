export default class Target {
  constructor({ key, text = '' }) {
    this.key = key
    this.text = text
  }

  clone() {
    return new Target({ key: this.key, text: this.text })
  }
}
