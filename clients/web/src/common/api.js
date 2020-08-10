import Assessment from './Assessment'
import Benchmark from './Benchmark'
import Organization from './Organization'
import Practice from './Practice'
import Question from './Question'
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
  const {
    assessment,
    targets,
    practices,
    questions,
    answers,
  } = await response.json()
  return new Assessment({
    ...assessment,
    targets: targets.map((t) => new Target(t)),
    improvementPlan: getPracticeInstances(practices, questions, answers),
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

export async function getPractices(organizationId, assessmentId) {
  const response = await request(`/practices/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { practices, questions, answers } = await response.json()
  return getPracticeInstances(practices, questions, answers)
}

export async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

export async function getQuestions(organizationId, assessmentId) {
  const response = await request(`/questions/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { questions, answers } = await response.json()
  return getQuestionInstances(questions, answers)
}

function getPracticeInstances(practices, questions, answers) {
  const questionInstances = getQuestionInstances(questions, answers)
  return practices.map((practice) => {
    const question = questionInstances.find((q) => q.id === practice.question)
    return new Practice({ ...practice, question })
  })
}

function getQuestionInstances(questions, answers) {
  return questions.map((question) => {
    const questionAnswers = question.answers.map((answerId) => {
      return answers.find((answer) => answer.id === answerId)
    })
    return new Question({ ...question, answers: questionAnswers })
  })
}
