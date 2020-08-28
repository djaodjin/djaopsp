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

function getAssessmentInformation(schema, request) {
  const { organizationId, assessmentId } = request.params
  const organization = schema.organizations.find(organizationId)
  if (organization.assessments.length) {
    const assessment = organization.assessments.models.find(
      (assessment) => assessment.slug === assessmentId
    )
    const { campaign, created_at, is_frozen, slug } = assessment
    return { campaign, created_at, is_frozen, slug }
  }
  return new Response(404, {}, { errors: ['assessment not found'] })
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

function getLatestAssessment(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  if (organization.assessments.length) {
    const { slug, created_at, campaign } = organization.assessments.models[0]
    return { campaign, created_at, slug }
  }
  return {}
}

function getOrganizationProfile(schema, request) {
  const { organizationId } = request.params
  const organization = schema.organizations.find(organizationId)
  return {
    slug: organization.slug,
    printable_name: organization.printable_name,
  }
}

export default {
  getAnswers,
  getAssessmentInformation,
  getIndustryList,
  getIndustryQuestions,
  getLatestAssessment,
  getOrganizationProfile,
}
