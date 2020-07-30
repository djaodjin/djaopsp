import { getUniqueId } from './utils'

export default class OrganizationGroup {
  constructor({ id = getUniqueId(), name, organizations = [] }) {
    this.id = id
    this.name = name
    this.organizations = organizations
  }
}
