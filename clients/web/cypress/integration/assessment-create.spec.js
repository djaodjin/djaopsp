import { makeServer } from '../../src/mocks/server'
import {
  createOrgAssessmentEmpty,
  createOrgAssessmentMultiple,
} from '../../src/mocks/scenarios'
import { STEP_PRACTICE_KEY } from '../../src/config/app'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const ASSESSMENT_CREATE_URL = `/${ORG_SLUG}/assess/`

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

  it('creates an assessment after selecting and submitting an industry segment selection', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_CREATE_URL)
    cy.get('[data-cy=industry-form]').as('industryForm')
    cy.get('[data-cy=industry-name]').should('not.exist')
    cy.get('.v-menu__content').should('not.exist')
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').should('exist')

    cy.get('.v-menu__content')
      .find('.v-list-item')
      .contains('Boxes & enclosures')
      .click()
    cy.get('@industryForm').find('button[type=submit]').click()

    cy.url().should('include', '/assess/2/metal/boxes-and-enclosures/') // new assessment ID = 2
    cy.get('[data-cy=industry-name]').contains('Boxes & enclosures')
    cy.get('[data-cy=industry-form]').should('not.exist')

    // Sets the stepper to "Practices" step
    cy.get('[data-cy=stepper]').as('stepper')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PRACTICE_KEY}]`)
      .should('have.class', 'v-stepper__step--active')
    cy.get('@stepper')
      .find('.v-stepper__step--inactive')
      .its('length')
      .should('eq', 4)
  })

  it('offers examples to select an industry segment', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_CREATE_URL)
    cy.get('[data-cy=examples]').click()
    cy.url().should('include', '/docs/faq/#general-4')
  })

  it('lets users select an industry segment from a list of industries', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_CREATE_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list of previously selected industries', () => {
    server.loadFixtures('questions')
    createOrgAssessmentMultiple(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_CREATE_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').contains('PREVIOUSLY SELECTED')
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list where previous industry segments take precedence', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentMultiple(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_CREATE_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 2)
    cy.get('@dropdown').find('.v-divider').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 1)
  })
})
