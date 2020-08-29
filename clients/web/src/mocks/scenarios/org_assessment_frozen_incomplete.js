import faker from 'faker'

export default function (
  server,
  orgId,
  orgName = 'Frozen Assessment Without Targets & Plan'
) {
  const assessment = server.create('assessment', {
    is_frozen: true,
    targets: [],
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions
    .find(['4', '6', '8', '9', '14', '15', '17', '18', '21'])
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
