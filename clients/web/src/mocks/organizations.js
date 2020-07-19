import Organization from '../common/Organization'

const DELAY = 100

const organizations = [
  new Organization({
    id: 'snapper',
    name: 'Red Snapper',
  }),
  new Organization({
    id: 'marlin',
    name: 'Blue Marlin',
  }),
  new Organization({
    id: 'tamarin',
    name: 'S1 Tamarin',
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
