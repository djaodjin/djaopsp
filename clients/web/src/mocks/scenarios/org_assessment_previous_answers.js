import { initCompleteAssessment, initIncompleteAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Assessment With Previous Answers'
) {
  const currentAssessment = server.create('assessment', {})

  const previousAssessment = server.create('assessment', {
    is_frozen: true,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [currentAssessment, previousAssessment],
  })

  initIncompleteAssessment(server, organization, currentAssessment)
  initCompleteAssessment(server, organization, previousAssessment)
}
