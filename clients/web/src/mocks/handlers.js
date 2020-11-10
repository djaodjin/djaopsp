import { getRandomInt } from '../common/utils'
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
  let answers = schema.answers.where({
    organizationId,
    assessmentId,
  })
  if (!answers.models.length) {
    const organization = schema.organizations.find(organizationId)
    const assessment = schema.assessments.find(assessmentId)
    // There are no answers for the assessment => this is a new assessment
    // Initialize the assessment with all questions unanswered
    //
    // It would have been tempting to use the initEmptyAssessment method in
    // utils; however, it only seems possible to create instances with
    // server.create during app initialization when calling the seeds()
    // method.
    schema.questions
      .where((question) => !!question.path)
      .models.forEach((question) => {
        schema.answers.create({
          assessment,
          organization,
          question,
          metric: null,
          unit: null,
          measured: null,
          created_at: null,
          collected_by: null,
        })
      })

    answers = schema.answers.where({
      organizationId,
      assessmentId,
    })
  }
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

function getAssessmentHistory(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  const assessments = organization.assessments.models.map((m) => m.attrs)

  const [pastAssessments, activeAssessments] = partition(
    assessments,
    'is_frozen'
  )

  const updates = activeAssessments.map((a) => ({
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

  const results = pastAssessments.map((a, index) => ({
    key: index,
    created_at: a.created_at,
    values: [
      [
        a.industryName,
        getRandomInt(40, 100),
        `/app/${a.account}/assess/${a.slug}${a.industryPath}`,
      ],
    ],
  }))

  return {
    updates,
    results,
  }
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
  getIndustryList,
  getIndustryQuestions,
  getOrganizationProfile,
  postAnswer,
  getBenchmarks,
}
