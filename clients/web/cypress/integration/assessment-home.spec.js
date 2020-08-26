import { makeServer } from '../../src/mocks/server'
import {
  createOrgAssessmentEmpty,
  createOrgAssessmentOneAnswer,
} from '../../src/mocks/scenarios'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const ASSESSMENT_HOME_URL = `/${ORG_SLUG}/assess/1/`

describe('Supplier App: Assessment Home', () => {
  let server

  beforeEach(() => {
    // Clean before next test runs per:
    // https://docs.cypress.io/guides/references/best-practices.html#Using-after-or-afterEach-hooks
    if (server) server.shutdown()
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
  })

  it('requires selection of industry segment if assessment has no answered questions', () => {
    server.loadFixtures('industries')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-form]').as('industryForm')
    cy.get('[data-cy=industry-name]').should('not.exist')
    cy.get('.v-menu__content').should('not.exist')
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').should('exist')

    cy.get('.v-menu__content').find('.v-list-item').first().click() // "construction" per fixture
    cy.get('@industryForm').find('button[type=submit]').click()

    cy.get('[data-cy=industry-name]').contains('Construction')
    cy.get('[data-cy=industry-form]').should('not.exist')
    cy.get('[data-cy=stepper]').should('exist')
  })

  it('lets users select an industry segment from a list of industries', () => {
    server.loadFixtures('industries')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list of previously selected industries', () => {
    server.loadFixtures('previousIndustries')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').contains('PREVIOUSLY SELECTED')
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list where previous industry segments take precedence', () => {
    server.loadFixtures('industries', 'previousIndustries')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 2)
    cy.get('@dropdown').find('.v-divider').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 1)
  })

  it('offers examples to select an industry segment', () => {
    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=examples]').click()
    cy.url().should('include', '/docs/faq/#general-4')
  })

  it.only('displays the industry segment for the assessment if at least one question has already been answered', () => {
    server.loadFixtures('industries')
    createOrgAssessmentOneAnswer(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-name]').contains('Boxes & enclosures')
    cy.get('[data-cy=stepper]').should('exist')
  })
})
