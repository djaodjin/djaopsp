import faker from 'faker'

export default function (
  server,
  orgId,
  orgName = 'Assessment With Practices Incomplete'
) {
  const assessment = server.create('assessment', {
    targets: [],
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions
    .find(['4', '6', '8', '14'])
    .models.forEach((question) => {
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
}
