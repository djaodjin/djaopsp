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

  // Assessment made up of one answered question
  // Per: https://www.tspproject.org/docs/api#RetrieveSampleAnswers
  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions.find(['4']).models.forEach((question) => {
    server.create('answer', {
      assessment,
      organization,
      question,
      metric: 'assessment',
      measured: '2',
      created_at: faker.date.past(),
      collected_by: 'current_user@testmail.com',
    })
  })
}
