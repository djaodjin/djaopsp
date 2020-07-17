import { STEP_SCORECARD_KEY, STEP_FREEZE_KEY } from '@/config/app'
import Assessment from '../common/Assessment'

const DELAY = 100

const activeAssessments = [
  new Assessment({
    id: '123-alpha',
    authorName: 'Charles Dickens',
    authorEmail: 'charlie.dickens@tamarinsolutions.com',
    industryName: 'Engineering, Procurement, Construction',
    industryPath: 'epc',
    status: STEP_FREEZE_KEY,
  }),
  new Assessment({
    id: '456-beta',
    authorName: 'Martha Blum',
    authorEmail: 'martha.blum@tamarinsolutions.com',
    industryName: 'General contracting',
    industryPath: 'general-contractors',
    status: STEP_SCORECARD_KEY,
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

export function postAssessment() {
  return new Promise((resolve, reject) => {
    const newAssessment = new Assessment({
      authorName: 'Vincent Lemassu',
      authorEmail: 'vincent.lemassu@tamarinsolutions.com',
      industryName: 'Marketing & communications',
      industryPath: 'marketing-and-communications',
    })
    activeAssessments.push(newAssessment)

    setTimeout(() => {
      resolve(newAssessment)
    }, DELAY)
  })
}