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

  // Assessment made up of one unanswered question
  // Per: https://www.tspproject.org/docs/api#RetrieveSampleAnswers
  server.create('answer', {
    assessment,
    organization,
    question,
  })
}