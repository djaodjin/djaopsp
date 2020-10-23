import { APIError, request } from './base'
import Assessment from '@/common/models/Assessment'
import Organization from '@/common/models/Organization'
import OrganizationGroup from '@/common/models/OrganizationGroup'

function parseAssessmentResult(assessmentValues) {
  const industryTitle = assessmentValues[0]
  const path = assessmentValues[2]
  let id = null
  let industryPath = ''

  // For example: /app/supplier-1/assess/10/metal/boxes-and-enclosures/
  const str = path.split('/assess/')[1]
  if (str) {
    const delimiterIdx = str.indexOf('/')
    id = str.substring(0, delimiterIdx)
    industryPath = str.substring(delimiterIdx)
  }
  return {
    id,
    industry: industryPath
      ? {
          title: industryTitle,
          path: industryPath,
        }
      : null,
  }
}

async function getOrganization(organizationId) {
  try {
    const [
      organizationProfileResponse,
      assessmentHistoryResponse,
    ] = await Promise.all([
      request(`/profile/${organizationId}/`),
      request(`/${organizationId}/benchmark/new-historical/`),
    ])
    const [organizationProfile, assessmentHistory] = await Promise.all([
      organizationProfileResponse.json(),
      assessmentHistoryResponse.json(),
    ])

    const assessments = assessmentHistory.updates.map((a) => {
      return new Assessment({
        id: a.slug,
        created: a.created_at,
        frozen: a.is_frozen,
        industry: {
          title: a.campaign.title,
          path: a.campaign.path,
        },
      })
    })

    const previousAssessments = assessmentHistory.results.map((a) => {
      const created = a.created_at
      const { id, industry } = parseAssessmentResult(a.values[0])
      return new Assessment({
        id,
        created,
        frozen: true,
        industry,
      })
    })

    return new Organization({
      id: organizationProfile.slug,
      name: organizationProfile.printable_name,
      assessments,
      previousAssessments,
    })
  } catch (e) {
    throw new APIError(e)
  }
}

// TODO: Review
async function getOrganizations() {
  const response = await request('/organizations')
  if (!response.ok) throw new APIError(response.status)
  const { organizationGroups, organizations } = await response.json()
  const groups = organizationGroups.map(
    ({ id, name }) => new OrganizationGroup({ id, name })
  )
  const individuals = organizations.map(
    ({ id, name }) => new Organization({ id, name })
  )
  return {
    groups,
    individuals,
  }
}

export default {
  getOrganization,
  getOrganizations,
}
