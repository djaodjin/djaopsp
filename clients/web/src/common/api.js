import groupBy from 'lodash/groupBy'
import kebabCase from 'lodash/kebabCase'

import Answer from './Answer'
import Assessment from './Assessment'
import Benchmark from './Benchmark'
import Organization from './Organization'
import OrganizationGroup from './OrganizationGroup'
import Question from './Question'
import Score from './Score'
import Section from './Section'
import Subcategory from './Subcategory'
import { getPracticeList } from './Practice'
import { getShareEntryList } from './ShareEntry'
import {
  MAP_QUESTION_FORM_TYPES,
  QUESTION_COMMENT_TYPE,
  QUESTION_ENERGY_CONSUMED,
  QUESTION_WATER_CONSUMED,
  QUESTION_WASTE_GENERATED,
} from '../config/app'

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
      const str = path.split('/sample/')[0]
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
  const flatAnswers = answerList.map(({ question, ...attrs }) => ({
    ...attrs,
    ...question,
  }))
  return groupBy(flatAnswers, 'path')
}

function getAnswerInstances(answersByPath, questions) {
  return questions.map((question) => {
    let answer, comment
    let answerValues = []

    const answers = answersByPath[question.path]
    if (answers.length === 1) {
      answer = answers[0]
    } else if (answers.length > 1) {
      answer = answers.find((answer) => answer.metric === answer.default_metric)
      comment = answers.find(
        (answer) => answer.metric === QUESTION_COMMENT_TYPE
      )
    }

    if (answer) {
      if (
        answer.default_metric === QUESTION_ENERGY_CONSUMED ||
        answer.default_metric === QUESTION_WATER_CONSUMED ||
        answer.default_metric === QUESTION_WASTE_GENERATED
      ) {
        answerValues = [answer.measured, answer.unit]
      } else {
        answerValues = [answer.measured]
      }
    }
    if (comment) {
      answerValues.push(comment.measured)
    }

    return new Answer({
      question: question.id,
      author: answer.collected_by,
      created: answer.created_at,
      answers: answerValues,
      answered: !MAP_QUESTION_FORM_TYPES[answer.default_metric].isEmpty(
        answerValues
      ),
    })
  })
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

// TODO: Review
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
