import { initIncompleteAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Organization With One-Answer Assessment'
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

  initIncompleteAssessment(server, organization, assessment)
}
