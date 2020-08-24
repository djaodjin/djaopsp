import { makeServer } from '../../src/mocks/server'
import createEmptyOrganization from '../../src/mocks/scenarios/emptyOrganization'
import createOrganizationWithAssessment from '../../src/mocks/scenarios/organizationWithAssessment'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'

describe('Supplier App: Home', () => {
  let server

  beforeEach(() => {
    if (server) server.shutdown()
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
  })

  it('loads the home screen for an empty organization', () => {
    createEmptyOrganization(server, ORG_SLUG, ORG_NAME)

    cy.visit(`/${ORG_SLUG}/`)
    cy.contains(ORG_NAME)
    cy.contains('Take Sustainability Assessment')
  })

  it('loads the home screen for an organization with an assessment', () => {
    createOrganizationWithAssessment(server, ORG_SLUG, ORG_NAME)

    cy.visit(`/${ORG_SLUG}/`)
    cy.contains(ORG_NAME)
    cy.get('.assessment-info').its('length').should('eq', 1)
    cy.contains('Continue Sustainability Assessment')
  })

  it('lets users create a new assessment', () => {
    createEmptyOrganization(server, ORG_SLUG, ORG_NAME)

    cy.visit(`/${ORG_SLUG}/`)
    cy.get('[data-cy=create-assessment]').click()
    cy.url().should('include', '/assess/1') // first assessment ID = 1
  })

  it('lets users continue working on an existing assessment', () => {
    createOrganizationWithAssessment(server, ORG_SLUG, ORG_NAME)

    cy.visit(`/${ORG_SLUG}/`)
    cy.get('[data-cy=continue-assessment]').click()
    cy.url().should('include', '/assess/1')
  })

  it('has access to the assessment history view', () => {
    createEmptyOrganization(server, ORG_SLUG, ORG_NAME)

    cy.visit(`/${ORG_SLUG}/`)
    cy.get('[data-cy=view-history]')
    // TODO: Route to history view
  })
})
