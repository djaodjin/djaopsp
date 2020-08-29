import {
  STEP_PRACTICE_KEY,
  STEP_REVIEW_KEY,
  STEP_SHARE_KEY,
  VALID_ASSESSMENT_TARGETS,
} from '@/config/app'
import { getUniqueId } from './utils'
import { getPracticeList } from './Practice'
import Target from './Target'

export default class Assessment {
  // TODO: Add list of contributors to the assessment
  constructor({
    id = getUniqueId(),
    created = new Date(),
    frozen = false,
    industry = { title: '', path: '' },
    targets,
    practices = [],
    questions = [],
    answers = [],
  }) {
    this.id = id
    this.industryName = industry.title
    this.industryPath = industry.path
    this.targets =
      targets && targets.length
        ? targets.map((t) => new Target(t))
        : VALID_ASSESSMENT_TARGETS.map((t) => new Target({ key: t.value }))
    this.improvementPlan = getPracticeList(practices, questions)
    this.questions = questions
    this.answers = answers
    this.created = created
    this.frozen = frozen

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

  setIndustry(industry) {
    if (industry) {
      const { title, path } = industry
      this.industryName = title
      this.industryPath = path
    }
  }
}
