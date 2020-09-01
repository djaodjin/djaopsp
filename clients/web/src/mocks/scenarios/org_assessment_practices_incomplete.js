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
  // Even though all answers for the assessment are present,
  // empty answers mean unanswered questions.
  server.schema.questions
    .find(['4', '6', '8', '14'])
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

  // Create empty answers for unanswered questions
  server.schema.questions
    .find(['9', '15', '17', '18', '21'])
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}
