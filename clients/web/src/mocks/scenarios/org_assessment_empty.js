export default function (
  server,
  orgId,
  orgName = 'Organization With Empty Assessment'
) {
  const assessment = server.create('assessment', {
    targets: [],
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  // Assessment made up of one unanswered question
  // Per: https://www.tspproject.org/docs/api#RetrieveSampleAnswers
  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions.find(['4']).models.forEach((question) => {
    server.create('answer', {
      assessment,
      organization,
      question,
    })
  })
}
