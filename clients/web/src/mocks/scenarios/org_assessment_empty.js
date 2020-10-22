import { initEmptyAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Organization With Empty Assessment'
) {
  const assessment = server.create('assessment', {})

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  initEmptyAssessment(server, organization, assessment)
}
