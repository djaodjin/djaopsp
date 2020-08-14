import { getUniqueId } from './utils'
import Organization from './Organization'

export default class ShareEntry {
  constructor({ id = getUniqueId(), date, organization }) {
    this.id = id
    this.date = date
    this.organization =
      organization instanceof Organization
        ? organization
        : new Organization(organization)
  }
}

export function getShareEntryList(shareEntries, organizations) {
  return shareEntries.map((shareEntry) => {
    const organization = organizations.find(
      (org) => org.id === shareEntry.organization
    )
    return new ShareEntry({ ...shareEntry, organization })
  })
}
