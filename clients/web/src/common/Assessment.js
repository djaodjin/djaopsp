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
    industry_name, // TODO: Remove this. It should be possible to get the name from industryPath
    industry_path,
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
    this.industryName = industry_name
    this.industryPath = industry_path
    this.targets =
      targets && targets.length
        ? targets.map((t) => new Target(t))
        : VALID_ASSESSMENT_TARGETS.map((t) => new Target({ key: t.value }))
    this.improvementPlan = getPracticeList(practices, questions)
    this.modified = modified
    this.created = created
    this.status = status
  }
}
