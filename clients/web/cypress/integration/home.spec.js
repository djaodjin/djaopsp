import { makeServer } from '../../src/mocks/server'
import createEmptyOrganization from '../../src/mocks/scenarios/emptyOrganization'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const HOST = 'http://127.0.0.1:8080'
const HOME_URL = `${HOST}${Cypress.env('ROOT')}${Cypress.env(
  'CLIENT_BASE'
)}/${ORG_SLUG}`

describe('Supplier App: Home', () => {
  let server

  beforeEach(() => {
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
    createEmptyOrganization(server, ORG_SLUG, ORG_NAME)
  })

  afterEach(() => {
    server.shutdown()
  })

  it('loads the home screen', () => {
    cy.visit(`${HOME_URL}/`).contains(ORG_NAME)
  })
})
