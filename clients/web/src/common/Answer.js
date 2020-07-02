export default class Answer {
  constructor(questionId, author, answer, unit = null) {
    this.questionId = questionId
    this.author = author
    this.date = new Date()
    this.answer = answer
    this.unit = unit
  }
}
