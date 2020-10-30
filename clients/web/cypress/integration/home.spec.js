import { makeServer } from '../../src/mocks/server'
import {
  createOrgEmpty,
  createOrgAssessmentEmpty,
} from '../../src/mocks/scenarios'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const HOME_URL = `/${ORG_SLUG}/`

describe('Supplier App: Home', () => {
  let server

  beforeEach(() => {
    if (server) server.shutdown()
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
  })

  it('loads the home screen for an empty organization and lets users create a new assessment', () => {
    createOrgEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HOME_URL)
    cy.contains(ORG_NAME)
    cy.contains('Take Sustainability Assessment')

    cy.get('[data-cy=create-assessment]').click()
    cy.url().should('include', '/assess/')
  })

  it('loads the home screen for an organization with an assessment and lets users create a new assessment', () => {
    server.loadFixtures('questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HOME_URL)
    cy.contains(ORG_NAME)
    cy.get('.assessment-info').its('length').should('eq', 1)
    cy.contains('Take Sustainability Assessment')

    cy.get('[data-cy=create-assessment]').click()
    cy.url().should('include', '/assess/')
  })

  it('lets users continue working on an existing assessment', () => {
    server.loadFixtures('questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HOME_URL)
    cy.get('[data-cy=continue-assessment]').click()
    cy.url().should('include', '/assess/1/metal/boxes-and-enclosures/')
  })

  it('has access to the assessment history view', () => {
    createOrgEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HOME_URL)
    cy.get('[data-cy=view-history]')
    // TODO: Route to history view
  })
})
