import { makeServer } from '../../src/mocks/server'
import createEmptyOrganization from '../../src/mocks/scenarios/emptyOrganization'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'

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
    cy.visit(`/${ORG_SLUG}/`)
    cy.contains(ORG_NAME)
  })

  it('has access to the new assessment view', () => {
    cy.visit(`/${ORG_SLUG}/`)
    cy.get('[data-cy=create-assessment]').click()
    cy.url().should('include', '/assess/new')
  })

  it('has access to the assessment history view', () => {
    cy.visit(`/${ORG_SLUG}/`)
    cy.get('[data-cy=view-history]')
    // TODO: Route to history view
  })
})
