import { initIncompleteAssessment, initCompleteAssessment } from '../utils'
import addDays from 'date-fns/addDays'
import subMonths from 'date-fns/subMonths'

export default function (server, orgId, orgName = 'Frozen Assessments') {
  const activeAssessment = server.create('assessment', {
    account: orgId,
    created_at: subMonths(new Date(), 1).toISOString(),
    industryName: 'Professional services',
    industryPath: '/professional-services/',
    is_frozen: false,
  })

  const pastAssessment1 = server.create('assessment', {
    account: orgId,
    created_at: subMonths(new Date(), 5).toISOString(), // replaced by active assessment
    industryName: 'Professional services',
    industryPath: '/professional-services/',
    is_frozen: true,
  })

  const pastAssessment2 = server.create('assessment', {
    account: orgId,
    created_at: subMonths(addDays(new Date(), 1), 6).toISOString(), // last modified less than 6 months ago
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
    is_frozen: true,
  })

  const archivedAssessment = server.create('assessment', {
    account: orgId,
    created_at: subMonths(new Date(), 6).toISOString(), // last modified 6 months ago
    industryName: 'Construction',
    industryPath: '/construction/',
    is_frozen: true,
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [
      activeAssessment,
      pastAssessment1,
      pastAssessment2,
      archivedAssessment,
    ],
  })

  initIncompleteAssessment(server, organization, activeAssessment)
  initCompleteAssessment(server, organization, pastAssessment1)
  initCompleteAssessment(server, organization, pastAssessment2)
  initCompleteAssessment(server, organization, archivedAssessment)
}
