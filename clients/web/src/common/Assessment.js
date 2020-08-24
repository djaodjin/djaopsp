import {
  VALID_ASSESSMENT_STEPS,
  VALID_ASSESSMENT_TARGETS,
  DEFAULT_ASSESSMENT_STEP,
} from '@/config/app'
import { getUniqueId } from './utils'
import { getPracticeList } from './Practice'
import Target from './Target'

export default class Assessment {
  // TODO: Add list of contributors to the assessment
  constructor({
    id = getUniqueId(),
    industry = { title: '', path: '' },
    targets,
    practices = [],
    questions = [],
    modified = new Date(),
    created = new Date(),
    status = DEFAULT_ASSESSMENT_STEP,
  }) {
    if (!VALID_ASSESSMENT_STEPS.includes(status)) {
      throw new Error('Invalid assessment status')
    }
    this.id = id
    this.industry = { name: industry.title, path: industry.path }
    this.targets =
      targets && targets.length
        ? targets.map((t) => new Target(t))
        : VALID_ASSESSMENT_TARGETS.map((t) => new Target({ key: t.value }))
    this.improvementPlan = getPracticeList(practices, questions)
    this.modified = modified
    this.created = created
    this.status = status
  }

  setIndustry(industry) {
    if (industry) {
      const { title, path } = industry
      this.industry = { name: title, path: path }
    }
  }
}
