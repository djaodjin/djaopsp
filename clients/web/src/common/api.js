import Assessment from './Assessment'
import Benchmark from './Benchmark'
import Organization from './Organization'
import OrganizationGroup from './OrganizationGroup'
import Score from './Score'
import { getPracticeList } from './Practice'
import { getQuestionList } from './Question'
import { getShareEntryList } from './ShareEntry'

const API_HOST = process.env.VUE_APP_API_HOST || ''
const API_BASE_URL = `${API_HOST}/envconnect/api`

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
  const { practices, questions, answers } = await response.json()
  return getPracticeList(practices, questions, answers)
}

export async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

export async function getQuestions(organizationId, assessmentId) {
  const response = await request(`/questions/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { questions, answers } = await response.json()
  return getQuestionList(questions, answers)
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

export async function postAssessment(payload) {
  const response = await request('/assessments', { body: payload })
  if (!response.ok) throw new APIError(response.status)
  const { assessment } = await response.json()
  return new Assessment(assessment)
}
