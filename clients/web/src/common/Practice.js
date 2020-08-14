import { PRACTICE_VALUES, PRACTICE_VALUE_CATEGORIES } from '@/config/app'
import { getUniqueId } from './utils'
import Question, { getQuestionList } from './Question'

const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
const values = PRACTICE_VALUE_CATEGORIES.map((c) => c.value)

export default class Practice {
  constructor({
    id = getUniqueId(),
    question,
    implementationRate = 0,
    ...rest
  }) {
    this.id = id
    this.question =
      question instanceof Question ? question : new Question(question)
    this.implementationRate = implementationRate
    values.forEach((v) => {
      this[v] = rest[v] || MIN_PRACTICE_VALUE
    })
  }
}

export function getPracticeList(practices, questions, answers) {
  const questionList = getQuestionList(questions, answers)
  return practices.map((practice) => {
    const question = questionList.find((q) => q.id === practice.question)
    return new Practice({ ...practice, question })
  })
}
