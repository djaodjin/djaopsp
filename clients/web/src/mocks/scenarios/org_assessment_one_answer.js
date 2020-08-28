import faker from 'faker'

export default function (
  server,
  orgId,
  orgName = 'Organization With One-Answer Assessment'
) {
  const assessment = server.create('assessment', {
    targets: [],
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  // Assessment with one answered question.
  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions.find(['4']).models.forEach((question) => {
    server.create('answer', {
      assessment,
      organization,
      question,
      metric: question.default_metric,
      measured: '2',
      created_at: faker.date.past(),
      collected_by: 'current_user@testmail.com',
    })
  })

  // Create empty answers for unanswered questions
  server.schema.questions
    .find(['6', '8', '9', '14', '15', '17', '18', '21'])
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}
