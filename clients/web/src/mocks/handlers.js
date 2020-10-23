import { Response } from 'miragejs'
import partition from 'lodash/partition'

function createAssessment(schema, request) {
  const { organizationId } = request.params
  const attrs = JSON.parse(request.requestBody)
  const newAssessment = this.create('assessment', {
    ...attrs,
    created_at: new Date().toISOString(),
  })

  // Create relationship to newly created entity
  const organization = schema.organizations.find(organizationId)
  organization.assessmentIds.push(newAssessment.id)
  const { campaign, created_at, slug } = newAssessment
  return { campaign, created_at, slug }
}

function getAnswers(schema, request) {
  const { organizationId, assessmentId } = request.params
  const answers = schema.answers.where({
    organizationId,
    assessmentId,
  })
  const results = answers.models.map(
    ({
      metric,
      unit,
      measured,
      created_at,
      collected_by,
      question: { path, default_metric },
    }) => ({
      metric,
      unit,
      measured,
      created_at,
      collected_by,
      question: {
        path,
        default_metric,
      },
    })
  )
  return {
    count: results.length,
    next: null,
    previous: null,
    results,
  }
}

// TODO: RENAME
function getAssessmentHistoryUpdated(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  const assessments = organization.assessments.models.map((m) => m.attrs)

  const [frozenAssessments, editableAssessments] = partition(
    assessments,
    'is_frozen'
  )

  const updates = editableAssessments.map((a) => ({
    slug: a.slug,
    account: a.account,
    created_at: a.created_at,
    is_frozen: a.is_frozen,
    campaign: {
      slug: a.campaign,
      path: a.industryPath,
      title: a.industryName,
    },
  }))

  const results = frozenAssessments.map((a, index) => ({
    key: index,
    created_at: a.created_at,
    values: [
      [
        a.industryName,
        index,
        `/app/${a.account}/assess/${a.slug}${a.industryPath}`,
      ],
    ],
  }))

  return {
    updates,
    results,
  }
}

function getAssessmentHistory(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  const numAssessments = organization.assessments.length
  if (numAssessments > 0) {
    const latest = organization.assessments.models[0]
    const previous = []
    for (let i = 1; i < numAssessments; i++) {
      const assessment = organization.assessments.models[i]
      const entry = {
        key: i,
        created_at: assessment.created_at,
        values: [
          [
            assessment.industryName,
            i,
            `/app/${organizationId}/assess/${assessment.slug}/content${assessment.industryPath}`,
          ],
        ],
      }
      previous.push(entry)
    }
    return {
      latest: {
        assessment: latest.slug,
        segments: [[latest.industryPath, latest.industryName]],
      },
      results: previous,
    }
  }
  return new Response(500, {}, { errors: ['organization has no assessments'] })
}

function getIndustryList(schema) {
  const industries = schema.industries.all()
  return {
    count: industries.length,
    next: null,
    previous: null,
    results: industries.models,
  }
}

function getIndustryQuestions(schema) {
  const questions = schema.questions.all()
  const results = questions.models.map(
    ({ attrs: { id, default_metric, ...rest } }) => rest
  )
  return {
    count: results.length,
    next: null,
    previous: null,
    results,
  }
}

function getOrganizationProfile(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  return {
    slug: organization.slug,
    printable_name: organization.printable_name,
  }
}

function postAnswer(schema, request) {
  const { organizationId, assessmentId } = request.params
  const questionPath = `/${request.params['']}`
  const payload = JSON.parse(request.requestBody)
  const newAnswers = []
  let response = []

  const question = schema.questions.where({
    path: questionPath,
  }).models[0]
  // There may be more than one answer tied to a question (e.g. comments)
  const answers = schema.answers.where({
    organizationId,
    assessmentId,
    questionId: question.id,
  }).models

  payload.forEach((answerObject) => {
    const answerFound = answers.find(
      (answer) => answer.metric === answerObject.metric
    )
    if (answerFound) {
      answerFound.update(answerObject)
      response.push(answerFound)
    } else {
      newAnswers.push(answerObject)
    }
  })

  if (newAnswers.length) {
    const organization = schema.organizations.find(organizationId)
    const assessment = schema.assessments.find(assessmentId)
    newAnswers.forEach((answerObject) => {
      const newAnswer = this.create('answer', {
        ...answerObject,
        organization,
        assessment,
        question,
      })
      response.push(newAnswer)
    })
  }

  return response.map(
    ({
      metric,
      unit,
      measured,
      created_at,
      collected_by,
      question: { path, default_metric },
    }) => ({
      metric,
      unit,
      measured,
      created_at,
      collected_by,
      question: { path, default_metric },
    })
  )
}

function getBenchmarks(schema) {
  const benchmarks = schema.benchmarks.all()
  return {
    count: benchmarks.length,
    next: null,
    previous: null,
    results: benchmarks.models,
  }
}

export default {
  createAssessment,
  getAnswers,
  getAssessmentHistory,
  getAssessmentHistoryUpdated,
  getIndustryList,
  getIndustryQuestions,
  getOrganizationProfile,
  postAnswer,
  getBenchmarks,
}
