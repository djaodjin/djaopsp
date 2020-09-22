import groupBy from 'lodash/groupBy'
import kebabCase from 'lodash/kebabCase'

import Answer from './models/Answer'
import Assessment from './models/Assessment'
import Benchmark from './models/Benchmark'
import Organization from './models/Organization'
import OrganizationGroup from './models/OrganizationGroup'
import Question from './models/Question'
import Score from './models/Score'
import Section from './models/Section'
import Subcategory from './models/Subcategory'
import { getPracticeList } from './models/Practice'
import { getShareEntryList } from './models/ShareEntry'
import { METRIC_SCORE } from '../config/questionFormTypes'

const API_HOST = process.env.VUE_APP_STANDALONE ? window.location.origin : ''
const API_BASE_URL = `${API_HOST}${process.env.VUE_APP_ROOT}${process.env.VUE_APP_API_BASE}`

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

export async function createAssessment(organizationId, payload) {
  const response = await request(`/${organizationId}/sample/`, {
    body: payload,
  })
  if (!response.ok) throw new APIError(response.status)
  const { slug, created_at } = await response.json()
  return new Assessment({ id: slug, created: created_at })
}

export async function getAssessment(organizationId, assessmentId) {
  try {
    const responses = await Promise.all([
      request(`/${organizationId}/sample/${assessmentId}/`),
      request(`/${organizationId}/sample/${assessmentId}/answers/`),
      request('/content?q=public'),
    ])
    const error = responses.find((response) => !response.ok)
    if (error) {
      throw new APIError(`Failed to get assessment: ${error.statusText}`)
    }

    const [
      { created_at, is_frozen, slug },
      { results: answers },
      { results: industries },
    ] = await Promise.all(responses.map((response) => response.json()))

    let assessment = new Assessment({
      id: slug,
      created: created_at,
      frozen: is_frozen,
    })

    // Find an answer with content
    const answered = answers.find((answer) => answer.metric)
    if (answered) {
      const answerPath = answered.question.path
      const industry = industries.find((obj) => answerPath.startsWith(obj.path))
      assessment = await setAssessmentIndustry(
        organizationId,
        assessment,
        industry
      )
    }
    return assessment
  } catch (e) {
    throw new APIError(e)
  }
}

async function getCurrentPracticesContent(
  organizationId,
  assessmentId,
  industryPath
) {
  try {
    const responses = await Promise.all([
      request(`/content${industryPath}`),
      request(
        `/${organizationId}/sample/${assessmentId}/answers${industryPath}`
      ),
    ])
    const error = responses.find((response) => !response.ok)
    if (error) {
      throw new APIError(
        `Failed to load practices content for assessment: ${error.statusText}`
      )
    }
    const [
      { results: questionList },
      { results: answerList },
    ] = await Promise.all(responses.map((response) => response.json()))

    const questions = getQuestionInstances(questionList)
    const answersByPath = getFlatAnswersByPath(answerList)
    const answers = getAnswerInstances(answersByPath, questions)

    // Complete questions with type and required fields
    questions.forEach((question) => {
      const answer = answersByPath[question.path][0]
      question.type = answer.default_metric
      question.optional = !answer.required
    })

    return {
      questions,
      answers,
    }
  } catch (e) {
    throw new APIError(e)
  }
}

// TODO: Review
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
  const response = await request('/content?q=public')
  if (!response.ok) throw new APIError(response.status)
  const { results } = await response.json()
  return results
}

export async function getPreviousAnswers(organizationId, assessment) {
  try {
    let previousAnswers = []
    const response = await request(
      `/${organizationId}/benchmark/historical${assessment.industryPath}`
    )
    if (!response.ok) throw new APIError(response.status)
    const { results } = await response.json()

    if (results.length) {
      const path = results[0].values[0][2]
      // For example: /app/eta/assess/10/sample/metal/boxes-and-enclosures/
      const str = path.split('/content/')[0]
      if (str) {
        const previousAssessmentId = str.substr(str.lastIndexOf('/') + 1)
        const response = await request(
          `/${organizationId}/sample/${previousAssessmentId}/answers${assessment.industryPath}`
        )
        if (!response.ok) throw new APIError(response.status)
        const { results: answerList } = await response.json()
        const answersByPath = getFlatAnswersByPath(answerList)
        previousAnswers = getAnswerInstances(
          answersByPath,
          assessment.questions
        )
      }
    }
    return previousAnswers
  } catch (e) {
    throw new APIError(e)
  }
}

export async function getPreviousIndustrySegments(organizationId) {
  const response = await request(`/${organizationId}/benchmark/historical/`)
  if (!response.ok) throw new APIError(response.status)
  const { results } = await response.json()
  return results
}

export async function getOrganization(organizationId) {
  try {
    let assessments = []

    const [
      organizationProfileResponse,
      latestAssessmentResponse,
    ] = await Promise.all([
      request(`/profile/${organizationId}/`),
      request(`/${organizationId}/sample/`),
    ])
    const [organizationProfile, latestAssessment] = await Promise.all([
      organizationProfileResponse.json(),
      latestAssessmentResponse.json(),
    ])

    if (latestAssessment.slug) {
      const sampleResponse = await request(
        `/${organizationId}/sample/${latestAssessment.slug}/`
      )
      const { created_at, is_frozen, slug } = await sampleResponse.json()
      const assessment = new Assessment({
        id: slug,
        created: created_at,
        frozen: is_frozen,
      })
      assessments = [assessment]
    }

    return new Organization({
      id: organizationProfile.slug,
      name: organizationProfile.printable_name,
      assessments,
    })
  } catch (e) {
    throw new APIError(e)
  }
}

// TODO: Review
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

// TODO: Remove
export async function getPractices(organizationId, assessmentId) {
  const response = await request(`/practices/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { practices, questions } = await response.json()
  return getPracticeList(practices, questions)
}

// TODO: Review
export async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

function getFlatAnswersByPath(answerList) {
  const flatAnswers = answerList
    .filter(({ metric }) => metric !== METRIC_SCORE) // filter out individual answer scores
    .map(({ question, ...attrs }) => ({
      ...attrs,
      ...question,
    }))
  return groupBy(flatAnswers, 'path')
}

function getAnswerInstances(answersByPath, questions) {
  const answers = []
  const items = questions.map((question) => ({
    qid: question.id,
    answerObjects: answersByPath[question.path],
  }))
  items.forEach(({ qid, answerObjects }) => {
    if (answerObjects) {
      const answer = new Answer({ question: qid })
      answer.load(answerObjects)
      answers.push(answer)
    }
  })
  return answers
}

function getQuestionInstances(contentList) {
  const questions = []
  const len = contentList.length
  let section, subcategory

  for (let i = 1; i < len; i++) {
    const node = contentList[i]
    if (node.indent === 1) {
      section = new Section({
        id: kebabCase(node.title),
        name: node.title,
        iconPath: node.picture,
      })
      subcategory = null
    } else if (node.tags && node.tags.includes('pagebreak')) {
      // TODO: Pagebreak nodes will need to be processed differently
      continue
    } else if (node.path && !node.path.includes('/targets/')) {
      // Do not include target questions; they will be processed separately
      const question = new Question({
        id: kebabCase(node.path),
        path: node.path,
        section,
        subcategory: !subcategory ? section : subcategory,
        text: node.title,
      })
      questions.push(question)
    } else {
      // Override subcategory.
      // In the end, what matters is the parent of the question
      subcategory = new Subcategory({
        id: `${kebabCase(section.name)}-${kebabCase(node.title)}`,
        name: node.title,
      })
    }
  }
  return questions
}

// TODO: Review
export async function getScore(organizationId, assessmentId) {
  const response = await request(`/score/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { score, benchmarks } = await response.json()
  return new Score({ ...score, benchmarks })
}

// TODO: Review
export async function getShareHistory(organizationId, assessmentId) {
  const response = await request(
    `/share-history/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { shareEntries, organizations } = await response.json()
  const history = getShareEntryList(shareEntries, organizations)
  return history
}

// TODO: Review
export async function postTargets(organizationId, assessmentId, payload) {
  const response = await request(`/targets/${organizationId}/${assessmentId}`, {
    body: payload,
  })
  if (!response.ok) throw new APIError(response.status)
  const { assessment, targets } = await response.json()
  return new Assessment({ ...assessment, targets })
}

export async function postAnswer(organizationId, assessment, answer) {
  const question = assessment.questions.find((q) => q.id === answer.question)
  const response = await request(
    `/${organizationId}/sample/${assessment.id}/answers${question.path}`,
    {
      body: answer.toPayload(),
    }
  )

  if (!response.ok) throw new APIError(response.status)
  return answer
}

export async function setAssessmentIndustry(
  organizationId,
  assessment,
  industry
) {
  const { id, created, frozen } = assessment
  const { questions, answers } = await getCurrentPracticesContent(
    organizationId,
    id,
    industry.path
  )
  return new Assessment({
    id,
    created,
    frozen,
    industry,
    questions,
    answers,
  })
}
