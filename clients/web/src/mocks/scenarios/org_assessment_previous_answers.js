import faker from 'faker'

export default function (
  server,
  orgId,
  orgName = 'Assessment With Previous Answers'
) {
  const currentAssessment = server.create('assessment', {
    targets: [],
  })

  const previousAssessment = server.create('assessment', {
    is_frozen: true,
    targets: [],
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [currentAssessment, previousAssessment],
  })

  // Assessment with one answered question.
  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions.find(['4']).models.forEach((question) => {
    server.create('answer', {
      assessment: currentAssessment,
      organization,
      question,
      metric: question.default_metric,
      created_at: faker.date.past(),
      collected_by: 'current_user@testmail.com',
    })
  })

  // Create empty answers for unanswered questions
  server.schema.questions
    .find(['6', '8', '9', '14', '15', '17', '18', '21'])
    .models.forEach((question) => {
      server.create('answer', {
        assessment: currentAssessment,
        organization,
        question,
      })
    })

  server.schema.questions
    .find(['4', '6', '8', '9', '14', '15', '17', '18', '21'])
    .models.forEach((question) => {
      server.create('answer', {
        assessment: previousAssessment,
        organization,
        question,
        metric: question.default_metric,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
    })
}
