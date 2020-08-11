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
    industryName, // TODO: Remove this. It should be possible to get the name from industryPath
    industryPath,
    targets,
    practices = [],
    questions = [],
    answers = [],
    modified = new Date(),
    created = new Date(),
    status = DEFAULT_ASSESSMENT_STEP,
  }) {
    if (!VALID_ASSESSMENT_STEPS.includes(status)) {
      throw new Error('Invalid assessment status')
    }
    this.id = id
    this.industryName = industryName
    this.industryPath = industryPath
    this.targets =
      targets && targets.length
        ? targets.map((t) => new Target(t))
        : VALID_ASSESSMENT_TARGETS.map((t) => new Target({ key: t.value }))
    this.improvementPlan = getPracticeList(practices, questions, answers)
    this.modified = modified
    this.created = created
    this.status = status
  }
}
