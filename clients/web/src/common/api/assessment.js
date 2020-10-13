import groupBy from 'lodash/groupBy'
import kebabCase from 'lodash/kebabCase'

import { APIError, request } from './base'
import Answer from '@/common/models/Answer'
import Assessment from '@/common/models/Assessment'
import Question from '@/common/models/Question'
import Section from '@/common/models/Section'
import Subcategory from '@/common/models/Subcategory'
import { VALID_METRICS } from '@/config/questionFormTypes'

async function createAssessment(organizationId, payload) {
  const response = await request(`/${organizationId}/sample/`, {
    body: payload,
  })
  if (!response.ok) throw new APIError(response.status)
  const { slug, created_at } = await response.json()
  return new Assessment({ id: slug, created: created_at })
}

async function getAssessment(organizationId, assessmentId) {
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
    const targetQuestions = getTargetQuestionInstances(questionList)
    const answersByPath = getFlatAnswersByPath(answerList)
    const answers = getAnswerInstances(answersByPath, questions)
    const targetAnswers = getAnswerInstances(answersByPath, targetQuestions)

    // Complete questions with type and required fields
    questions.forEach((question) => {
      const answer = answersByPath[question.path][0]
      question.type = answer.default_metric
      question.optional = !answer.required
    })
    targetQuestions.forEach((targetQuestion) => {
      const answer = answersByPath[targetQuestion.path][0]
      targetQuestion.type = answer.default_metric
      targetQuestion.optional = !answer.required
    })

    return {
      answers,
      questions,
      targetAnswers,
      targetQuestions,
    }
  } catch (e) {
    throw new APIError(e)
  }
}

async function getIndustrySegments() {
  const response = await request('/content?q=public')
  if (!response.ok) throw new APIError(response.status)
  const { results } = await response.json()
  return results
}

async function getAllPreviousAnswers(organizationId, assessment) {
  try {
    let answersByPath = {}
    const response = await request(
      `/${organizationId}/benchmark/historical${assessment.industryPath}`
    )
    if (!response.ok) throw new APIError(response.status)
    const { results } = await response.json()

    if (results.length) {
      const path = results[0].values[0][2]
      // For example: /app/eta/assess/10/content/metal/boxes-and-enclosures/
      const str = path.split('/content/')[0]
      if (str) {
        const previousAssessmentId = str.substr(str.lastIndexOf('/') + 1)
        const response = await request(
          `/${organizationId}/sample/${previousAssessmentId}/answers${assessment.industryPath}`
        )
        if (!response.ok) throw new APIError(response.status)
        const { results: answerList } = await response.json()
        answersByPath = getFlatAnswersByPath(answerList)
      }
    }
    return answersByPath
  } catch (e) {
    throw new APIError(e)
  }
}

async function getPreviousAnswers(organizationId, assessment) {
  const answersByPath = await getAllPreviousAnswers(organizationId, assessment)
  return getAnswerInstances(answersByPath, assessment.questions)
}

async function getPreviousTargets(organizationId, assessment) {
  const answersByPath = await getAllPreviousAnswers(organizationId, assessment)
  return getAnswerInstances(answersByPath, assessment.targetQuestions)
}

async function getPreviousIndustrySegments(organizationId) {
  const response = await request(`/${organizationId}/benchmark/historical/`)
  if (!response.ok) throw new APIError(response.status)
  const { results } = await response.json()
  return results
}

function getFlatAnswersByPath(answerList) {
  const flatAnswers = answerList
    .filter(({ metric }) => metric === null || VALID_METRICS.includes(metric))
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

function getTargetQuestionInstances(contentList) {
  const targetQuestions = []
  contentList.forEach((node) => {
    if (node.path && node.path.includes('/targets/')) {
      const targetQuestion = new Question({
        id: kebabCase(node.path),
        path: node.path,
        text: node.title,
      })
      targetQuestions.push(targetQuestion)
    }
  })
  return targetQuestions
}

async function postTarget(organizationId, assessment, answer) {
  const question = assessment.targetQuestions.find(
    (q) => q.id === answer.question
  )
  const response = await request(
    `/${organizationId}/sample/${assessment.id}/answers${question.path}`,
    {
      body: answer.toPayload(),
    }
  )
  if (!response.ok) throw new APIError(response.status)
  return answer
}

async function postAnswer(organizationId, assessment, answer) {
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

async function setAssessmentIndustry(organizationId, assessment, industry) {
  const { id, created, frozen } = assessment
  const {
    answers,
    questions,
    targetAnswers,
    targetQuestions,
  } = await getCurrentPracticesContent(organizationId, id, industry.path)
  return new Assessment({
    id,
    created,
    frozen,
    industry,
    answers,
    questions,
    targetAnswers,
    targetQuestions,
  })
}

export default {
  createAssessment,
  getAssessment,
  getIndustrySegments,
  getPreviousAnswers,
  getPreviousIndustrySegments,
  getPreviousTargets,
  postAnswer,
  postTarget,
  setAssessmentIndustry,
}