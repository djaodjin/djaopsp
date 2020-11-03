import { initCompleteAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Frozen Assessment Without Targets & Plan'
) {
  const assessment = server.create('assessment', {
    account: orgId,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
    is_frozen: true,
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [assessment],
  })

  initCompleteAssessment(server, organization, assessment)
}
