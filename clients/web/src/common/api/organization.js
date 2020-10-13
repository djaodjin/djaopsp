import { APIError, request } from './base'
import Assessment from '@/common/models/Assessment'
import Organization from '@/common/models/Organization'
import OrganizationGroup from '@/common/models/OrganizationGroup'

async function getOrganization(organizationId) {
  try {
    let assessments = []

    const [
      organizationProfileResponse,
      latestAssessmentResponse,
    ] = await Promise.all([
      request(`/profile/${organizationId}/`),
      request(`/${organizationId}/sample/`),
    ])
    const [organizationProfile, latestAssessment] = await Promise.all([
      organizationProfileResponse.json(),
      latestAssessmentResponse.json(),
    ])

    if (latestAssessment.slug) {
      const sampleResponse = await request(
        `/${organizationId}/sample/${latestAssessment.slug}/`
      )
      const { created_at, is_frozen, slug } = await sampleResponse.json()
      const assessment = new Assessment({
        id: slug,
        created: created_at,
        frozen: is_frozen,
      })
      assessments = [assessment]
    }

    return new Organization({
      id: organizationProfile.slug,
      name: organizationProfile.printable_name,
      assessments,
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
