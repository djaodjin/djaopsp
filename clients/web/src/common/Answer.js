export default class Answer {
  constructor(questionId, questionType, author, answers = []) {
    this.questionId = questionId
    this.questionType = questionType
    this.author = author
    this.created = new Date()
    this.modified = new Date()
    this._answers = answers
  }

  get answers() {
    return this._answers
  }

  set answers(newAnswers) {
    this.modified = new Date()
    this._answers = newAnswers.splice()
  }
}
