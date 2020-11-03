import { initIncompleteAssessment, initCompleteAssessment } from '../utils'

export default function (
  server,
  orgId,
  orgName = 'Organization With Multiple Assessments'
) {
  const current_construction = server.create('assessment', {
    account: orgId,
    industryName: 'Construction',
    industryPath: '/construction/',
  })

  const current_enclosures = server.create('assessment', {
    account: orgId,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const previous_1_construction = server.create('assessment', {
    account: orgId,
    industryName: 'Construction',
    industryPath: '/construction/',
    is_frozen: true,
  })

  const previous_2_construction = server.create('assessment', {
    account: orgId,
    industryName: 'Construction',
    industryPath: '/construction/',
    is_frozen: true,
  })

  const previous_1_enclosures = server.create('assessment', {
    account: orgId,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
    is_frozen: true,
  })

  const previous_2_enclosures = server.create('assessment', {
    account: orgId,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
    is_frozen: true,
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [
      current_construction,
      current_enclosures,
      previous_1_construction,
      previous_1_enclosures,
      previous_2_construction,
      previous_2_enclosures,
    ],
  })

  initIncompleteAssessment(server, organization, current_construction)
  initIncompleteAssessment(server, organization, current_enclosures)
  initCompleteAssessment(server, organization, previous_1_construction)
  initCompleteAssessment(server, organization, previous_1_enclosures)
  initCompleteAssessment(server, organization, previous_2_construction)
  initCompleteAssessment(server, organization, previous_2_enclosures)
}
