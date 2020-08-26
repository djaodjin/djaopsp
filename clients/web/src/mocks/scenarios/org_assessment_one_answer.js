import faker from 'faker'

export default function (
  server,
  orgId,
  orgName = 'Organization With Assessment'
) {
  const assessment = server.create('assessment', {
    targets: [],
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  const question = server.create('question', {
    path: '/metal/boxes-and-enclosures/design/packaging-design',
  })

  // Assessment made up of one answered question
  // Per: https://www.tspproject.org/docs/api#RetrieveSampleAnswers
  server.create('answer', {
    assessment,
    organization,
    question,
    metric: 'assessment',
    measured: '2',
    created_at: faker.date.past(),
    collected_by: 'current_user@testmail.com',
  })
}
