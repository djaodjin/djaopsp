import {
  STEP_PRACTICE_KEY,
  STEP_REVIEW_KEY,
  STEP_SHARE_KEY,
} from '@/config/app'
import { getUniqueId } from '../utils'
import { getPracticeList } from './Practice'

export default class Assessment {
  // TODO: Add list of contributors to the assessment
  constructor({
    id = getUniqueId(),
    created = new Date(),
    frozen = false,
    industry = { title: '', path: '' },
    practices = [],
    answers = [],
    questions = [],
    targetAnswers = [],
    targetQuestions = [],
  }) {
    this.id = id
    this.created = created
    this.frozen = frozen
    this.industryName = industry.title
    this.industryPath = industry.path
    this.improvementPlan = getPracticeList(practices, questions)
    this.answers = answers
    this.questions = questions
    this.targetAnswers = targetAnswers
    this.targetQuestions = targetQuestions

    // Determine assessment status
    if (
      this.answers.length === 0 ||
      this.answers.some((answer) => !answer.answered)
    ) {
      // Do not proceed until all questions have been answered
      this.status = STEP_PRACTICE_KEY
    } else if (!this.frozen) {
      this.status = STEP_REVIEW_KEY
    } else {
      this.status = STEP_SHARE_KEY
    }
  }
}
