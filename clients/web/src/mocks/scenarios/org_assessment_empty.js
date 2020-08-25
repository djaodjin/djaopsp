export default function (
  server,
  orgId,
  orgName = 'Organization With Assessment'
) {
  const assessment = server.create('assessment', {
    targets: [],
  })

  server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })
}
