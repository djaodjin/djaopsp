export default function (
  server,
  orgId,
  orgName = 'Organization With Assessment'
) {
  const assessment = server.create('assessment', {
    practices: server.createList('practice', 10),
    targets: [],
  })

  server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })
}
