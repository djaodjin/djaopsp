import { DELAY } from './config'
import Organization from '../common/Organization'

const organizations = [
  new Organization({
    id: 'steve-shop',
    name: 'Steve Test Shop',
  }),
  new Organization({
    id: 'marlin',
    name: 'Blue Marlin',
  }),
  new Organization({
    id: 'supplier-1',
    name: 'S1 - Tamerin (Demo)',
  }),
  new Organization({
    id: 'tamarin',
    name: 'Tamarin',
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
