import Assessment from './Assessment'
import Organization from './Organization'
import Target from './Target'

const API_HOST = process.env.VUE_APP_API_HOST || 'http://127.0.0.1:8000'
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
  const data = await response.json()
  const assessment = new Assessment({
    ...data.assessment,
    targets: data.targets.map((t) => new Target(t)),
  })
  return assessment
}

export async function getOrganization(organizationId) {
  const response = await request(`/organizations/${organizationId}`)
  if (!response.ok) throw new APIError(response.status)
  const {
    organization: { id, name },
    assessments,
  } = await response.json()
  const organization = new Organization({
    id,
    name,
    assessments: assessments.map((a) => new Assessment(a)),
  })
  return organization
}

export function getQuestions(organizationId, assessmentId) {}
