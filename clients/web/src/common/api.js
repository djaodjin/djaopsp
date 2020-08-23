import Answer from './Answer'
import Assessment from './Assessment'
import Benchmark from './Benchmark'
import Organization from './Organization'
import OrganizationGroup from './OrganizationGroup'
import Question from './Question'
import Score from './Score'
import { getPracticeList } from './Practice'
import { getShareEntryList } from './ShareEntry'
import { VALID_ASSESSMENT_STEPS } from '../config/app'

const API_BASE_URL = process.env.VUE_APP_STANDALONE
  ? `${window.location.origin}/envconnect/api`
  : `${process.env.BASE_URL}api`

class APIError extends Error {
  constructor(message) {
    super(message)
    this.name = 'APIError'
  }
}

function request(endpoint, { body, method, ...customConfig } = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = { 'content-type': 'application/json' }
  const config = {
    method: method ? method : body ? 'POST' : 'GET',
    ...customConfig,
    headers: {
      ...headers,
      ...customConfig.headers,
    },
  }
  if (body) {
    config.body = JSON.stringify(body)
  }

  return fetch(url, config)
}

export async function advanceAssessment(assessment) {
  const { id, status, targets, practices, questions, answers } = assessment
  const currentStepIndex = VALID_ASSESSMENT_STEPS.indexOf(status)
  if (
    currentStepIndex >= 0 &&
    currentStepIndex < VALID_ASSESSMENT_STEPS.length - 1
  ) {
    const nextStep = VALID_ASSESSMENT_STEPS[currentStepIndex + 1]
    const response = await request(`/assessments/${id}`, {
      method: 'PATCH',
      body: { status: nextStep },
    })
    if (!response.ok) throw new APIError(response.status)
    const data = await response.json()
    return new Assessment({
      ...data.assessment,
      targets,
      practices,
      questions,
      answers,
    })
  }
  return assessment
}

export async function createAssessment(payload) {
  const response = await request('/assessments', { body: payload })
  if (!response.ok) throw new APIError(response.status)
  const { assessment } = await response.json()
  return new Assessment(assessment)
}

export async function getAnswers(organizationId, assessmentId) {
  const response = await request(`/answers/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { answers } = await response.json()
  return answers.map((answer) => new Answer(answer))
}

export async function getAssessment(assessmentId) {
  const response = await request(`/assessments/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const {
    assessment,
    targets,
    practices,
    questions,
    answers,
  } = await response.json()
  return new Assessment({
    ...assessment,
    targets,
    practices,
    questions,
    answers,
  })
}

export async function getBenchmarks(organizationId, assessmentId) {
  const response = await request(
    `/benchmarks/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { benchmarks } = await response.json()

  return benchmarks.map((benchmark) => {
    return new Benchmark(benchmark)
  })
}

export async function getIndustrySegments() {
  const response = await request('/industries')
  if (!response.ok) throw new APIError(response.status)
  const { industries } = await response.json()
  return industries
}

export async function getPreviousIndustrySegments() {
  const response = await request('/previous-industries')
  if (!response.ok) throw new APIError(response.status)
  const { previousIndustries } = await response.json()
  return previousIndustries
}

export async function getOrganization(organizationId) {
  const response = await request(`/organizations/${organizationId}`)
  if (!response.ok) throw new APIError(response.status)
  const {
    organization: { id, name },
    assessments,
    ...rest
  } = await response.json()
  const organization = new Organization({
    id,
    name,
    assessments: assessments.map((a) => new Assessment({ ...a, ...rest })),
  })
  return organization
}

export async function getOrganizations() {
  const response = await request('/organizations')
  if (!response.ok) throw new APIError(response.status)
  const { organizationGroups, organizations } = await response.json()
  const groups = organizationGroups.map(
    ({ id, name }) => new OrganizationGroup({ id, name })
  )
  const individuals = organizations.map(
    ({ id, name }) => new Organization({ id, name })
  )
  return {
    groups,
    individuals,
  }
}

export async function getPractices(organizationId, assessmentId) {
  const response = await request(`/practices/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { practices, questions } = await response.json()
  return getPracticeList(practices, questions)
}

export async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

export async function getQuestions(organizationId, assessmentId) {
  const response = await request(`/questions/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { questions } = await response.json()
  return questions.map((question) => new Question(question))
}

export async function getScore(organizationId, assessmentId) {
  const response = await request(`/score/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { score, benchmarks } = await response.json()
  return new Score({ ...score, benchmarks })
}

export async function getShareHistory(organizationId, assessmentId) {
  const response = await request(
    `/share-history/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { shareEntries, organizations } = await response.json()
  const history = getShareEntryList(shareEntries, organizations)
  return history
}

export async function postTargets(organizationId, assessmentId, payload) {
  const response = await request(`/targets/${organizationId}/${assessmentId}`, {
    body: payload,
  })
  if (!response.ok) throw new APIError(response.status)
  const { assessment, targets } = await response.json()
  return new Assessment({ ...assessment, targets })
}

export async function putAnswer(answer) {
  const { organization, assessment, question } = answer
  const response = await request(
    `/answer/${organization}/${assessment}/${question}`,
    {
      method: 'PUT',
      body: answer,
    }
  )
  if (!response.ok) throw new APIError(response.status)
  const data = await response.json()
  return new Answer(data.answer)
}
