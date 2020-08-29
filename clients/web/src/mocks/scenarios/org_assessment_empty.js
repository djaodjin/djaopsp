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

  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions
    .find(['4', '6', '8', '9', '14', '15', '17', '18', '21'])
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}
