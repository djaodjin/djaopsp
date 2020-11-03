import { initCompleteAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Assessment With Practices Complete'
) {
  const assessment = server.create('assessment', {
    account: orgId,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  initCompleteAssessment(server, organization, assessment)
}
