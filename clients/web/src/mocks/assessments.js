import { DELAY } from './config'
import { getBestPractices } from './improvement-plan'
import {
  STEP_SHARE_KEY,
  STEP_FREEZE_KEY,
  VALID_ASSESSMENT_TARGETS,
} from '@/config/app'
import Assessment from '../common/Assessment'
import Target from '../common/Target'

const activeAssessments = [
  new Assessment({
    id: '123-alpha',
    authorName: 'Charles Dickens',
    authorEmail: 'charlie.dickens@tamarinsolutions.com',
    industryName: 'Engineering, Procurement, Construction',
    industryPath: 'epc',
    targets: getAssessmentTargets(),
    improvementPlan: getAssessmentImprovementPlan(),
    status: STEP_FREEZE_KEY,
  }),
  new Assessment({
    id: 'f1e2e916eb494b90f9ff0a36982342',
    authorName: 'Martha Blum',
    authorEmail: 'martha.blum@tamarinsolutions.com',
    industryName: 'Construction',
    industryPath: 'construction',
    status: STEP_SHARE_KEY,
  }),
]

export function getActiveAssessments() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(activeAssessments)
    }, DELAY)
  })
}

export function getAssessment(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const assessment = activeAssessments.find(
        (assessment) => assessment.id === id
      )
      resolve(assessment)
    }, DELAY)
  })
}

export function getAssessmentTargets() {
  return VALID_ASSESSMENT_TARGETS.map(
    (target) =>
      new Target({
        key: target.value,
        text:
          'Cras semper aliquet leo, ultricies lacinia ante facilisis eu curabitur porttitor.',
      })
  )
}

export function getAssessmentImprovementPlan() {
  return getBestPractices(6)
}

export function postAssessment() {
  return new Promise((resolve, reject) => {
    const newAssessment = new Assessment({
      authorName: 'Vincent Lemassu',
      authorEmail: 'vincent.lemassu@tamarinsolutions.com',
      industryName: 'Construction',
      industryPath: 'construction',
    })
    activeAssessments.push(newAssessment)

    setTimeout(() => {
      resolve(newAssessment)
    }, DELAY)
  })
}
