export default function (
  server,
  orgId,
  orgName = 'Organization With Empty Assessment'
) {
  const assessment = server.create('assessment', {})

  const previous_1 = server.create('assessment', {
    is_frozen: true,
    industryName: 'Construction',
    industryPath: '/construction/',
  })

  const previous_2 = server.create('assessment', {
    is_frozen: true,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment, previous_1, previous_2],
  })

  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions
    .where((question) => !!question.path)
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}
