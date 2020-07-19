import { getUniqueId } from './utils'
import { VALID_ASSESSMENT_STEPS, DEFAULT_ASSESSMENT_STEP } from '../config/app'

export default class Assessment {
  constructor({
    id = getUniqueId(),
    authorName,
    authorEmail,
    industryName,
    industryPath,
    modified = new Date(),
    created = new Date(),
    status = DEFAULT_ASSESSMENT_STEP,
  }) {
    if (!VALID_ASSESSMENT_STEPS.includes(status)) {
      throw new Error('Invalid assessment status')
    }
    this.id = id
    this.authorName = authorName
    this.authorEmail = authorEmail
    this.industryName = industryName
    this.industryPath = industryPath
    this.modified = modified
    this.created = created
    this.status = status
  }
}
