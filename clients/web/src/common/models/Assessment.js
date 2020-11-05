import kebabCase from 'lodash/kebabCase'
import {
  STEP_PRACTICE_KEY,
  STEP_REVIEW_KEY,
  STEP_SHARE_KEY,
} from '@/config/app'
import { getPracticeList } from './Practice'

export default class Assessment {
  // TODO: Add list of contributors to the assessment
  constructor({
    slug,
    created = new Date(),
    frozen = false,
    industry = { title: '', path: '' },
    practices = [],
    answers = [],
    questions = [],
    targetAnswers = [],
    targetQuestions = [],
    score,
  }) {
    // An assessment can be uniquely identified by its sample slug and its industry segment path
    this.id = Assessment.getId(slug, industry.path)
    this.slug = slug
    this.created = created
    this.frozen = frozen
    this.industryName = industry.title
    this.industryPath = industry.path
    this.improvementPlan = getPracticeList(practices, questions)
    this.answers = answers
    this.questions = questions
    this.targetAnswers = targetAnswers
    this.targetQuestions = targetQuestions
    this.score = score

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

  static getId(slug, path) {
    return `${slug}-${kebabCase(path)}`
  }
}
