import { APIError, request } from './base'
import { getPracticeList } from '@/common/models/Practice'
import { getShareEntryList } from '@/common/models/ShareEntry'

// TODO: Remove
async function getPractices(organizationId, assessmentId) {
  const response = await request(`/practices/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { practices, questions } = await response.json()
  return getPracticeList(practices, questions)
}

// TODO: Review
async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

// TODO: Review
async function getShareHistory(organizationId, assessmentId) {
  const response = await request(
    `/share-history/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { shareEntries, organizations } = await response.json()
  const history = getShareEntryList(shareEntries, organizations)
  return history
}

export default {
  getPractices,
  getPracticeSearchResults,
  getShareHistory,
}
