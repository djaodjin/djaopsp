import { makeServer } from '../../src/mocks/server'
import createEmptyOrganization from '../../src/mocks/scenarios/emptyOrganization'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const NEW_ASSESSMENT_URL = `/${ORG_SLUG}/assess/new/`

describe('Supplier App: New Assessment', () => {
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

  it('opens an industry segment dropdown', () => {
    server.loadFixtures('industries')

    cy.visit(NEW_ASSESSMENT_URL)
    cy.get('.v-menu__content').should('not.exist')
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').should('exist')
  })

  it('shows a list of industry segments', () => {
    server.loadFixtures('industries')

    cy.visit(NEW_ASSESSMENT_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 2)
  })

  it('shows a list of previous industry segments for the supplier', () => {
    server.loadFixtures('previousIndustries')

    cy.visit(NEW_ASSESSMENT_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').contains('PREVIOUSLY SELECTED')
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 2)
  })

  it('shows a combined list of industry segments where previous industry segments take precedence', () => {
    server.loadFixtures('industries', 'previousIndustries')

    cy.visit(NEW_ASSESSMENT_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 2)
    cy.get('@dropdown').find('.v-divider').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 1)
  })

  // TODO: Test assessment creation
  // it('lets users create a new assessment', () => {
  //   cy.visit(NEW_ASSESSMENT_URL)
  //   cy.get('[data-cy=industry-dropdown]').click()
  // })

  it('offers examples to select industry segment', () => {
    cy.visit(NEW_ASSESSMENT_URL)
    cy.get('[data-cy=examples]').click()
    cy.url().should('include', '/docs/faq/#general-4')
  })
})
