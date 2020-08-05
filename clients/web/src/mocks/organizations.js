import { DELAY } from './config'
import { getActiveAssessments } from './assessments'
import Organization from '../common/Organization'
import OrganizationGroup from '../common/OrganizationGroup'

const organizations = [
  new Organization({
    id: 'steve-shop',
    name: 'Steve Test Shop',
    assessments: getActiveAssessments(),
  }),
  new Organization({
    id: 'marlin',
    name: 'Blue Marlin',
    assessments: getActiveAssessments(),
  }),
  new Organization({
    id: 'supplier-1',
    name: 'S1 - Tamerin (Demo)',
    assessments: getActiveAssessments(),
  }),
  new Organization({
    id: 'tamarin',
    name: 'Tamarin',
  }),
]

const organizationGroups = [
  new OrganizationGroup({
    id: 'euissca',
    name: 'EUISSCA',
    organizations: [organizations[0], organizations[1]],
  }),
  new OrganizationGroup({
    id: 'stellar',
    name: 'STELLAR',
    organizations: [organizations[1], organizations[2]],
  }),
  new OrganizationGroup({
    id: 'nascar',
    name: 'NASCAR',
    organizations: [organizations[2], organizations[3]],
  }),
]

export function getOrganizations() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(organizations)
    }, DELAY)
  })
}

export function getOrganization(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const organization = organizations.find((org) => org.id === id)
      resolve(organization)
    }, DELAY)
  })
}

export function getOrganizationGroups() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve(organizationGroups)
    }, DELAY)
  })
}

export function getOrganizationGroup(id) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const organizationGroup = organizationGroups.find(
        (group) => group.id === id
      )
      resolve(organizationGroup)
    }, DELAY)
  })
}
