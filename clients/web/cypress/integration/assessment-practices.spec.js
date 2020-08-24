import { makeServer } from '../../src/mocks/server'
import createOrganizationWithAssessment from '../../src/mocks/scenarios/organizationWithAssessment'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const PRACTICES_INTRO_URL = `/${ORG_SLUG}/assess/1/intro/`

describe('Supplier App: Assessment Practices', () => {
  let server

  beforeEach(() => {
    // Clean before next test runs per:
    // https://docs.cypress.io/guides/references/best-practices.html#Using-after-or-afterEach-hooks
    if (server) server.shutdown()
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
    createOrganizationWithAssessment(server, ORG_SLUG, ORG_NAME)
  })

  it('displays an intro view', () => {
    cy.visit(`/${ORG_SLUG}/assess/1/`)
    cy.contains('Establish current practices')
    cy.get('[data-cy=practice]').click()
    cy.url().should('include', '/assess/1/intro/')
  })

  it('let users select an industry segment', () => {
    server.loadFixtures('industries')

    cy.visit(PRACTICES_INTRO_URL)
    cy.get('.v-menu__content').should('not.exist')
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 2)

    cy.get('@dropdown').find('.v-list-item').first().click() // "construction" per fixture
    cy.get('button[type=submit]').click()
    cy.url().should('include', '/assess/1/content/construction/')
  })

  it('lets users select an industry segment from a list of previously selected industries', () => {
    server.loadFixtures('previousIndustries')

    cy.visit(PRACTICES_INTRO_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').contains('PREVIOUSLY SELECTED')
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list where previous industry segments take precedence', () => {
    server.loadFixtures('industries', 'previousIndustries')

    cy.visit(PRACTICES_INTRO_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 2)
    cy.get('@dropdown').find('.v-divider').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 1)
  })

  it('offers examples to select an industry segment', () => {
    cy.visit(PRACTICES_INTRO_URL)
    cy.get('[data-cy=examples]').click()
    cy.url().should('include', '/docs/faq/#general-4')
  })
})
