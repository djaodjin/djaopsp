export default function (server, orgId, orgName = 'Empty Organization') {
  server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [],
  })
}
