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
    .where((question) => !!question.path)
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
        metric: question.default_metric,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
    })
}
