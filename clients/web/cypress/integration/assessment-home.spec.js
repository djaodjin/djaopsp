import { makeServer } from '../../src/mocks/server'
import {
  createOrgAssessmentEmpty,
  createOrgAssessmentEmptyMultiple,
  createOrgAssessmentPracticesIncomplete,
  createOrgAssessmentPracticesComplete,
  createOrgAssessmentFrozen,
} from '../../src/mocks/scenarios'
import {
  STEP_PRACTICE_KEY,
  STEP_TARGETS_KEY,
  STEP_PLAN_KEY,
  STEP_REVIEW_KEY,
  STEP_SHARE_KEY,
} from '../../src/config/app'

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
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
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

    cy.get('[data-cy=industry-name]').contains('Boxes & enclosures')
    cy.get('[data-cy=industry-form]').should('not.exist')

    // Sets the stepper to "Practices" step if none of the practice questions have been answered
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

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=examples]').click()
    cy.url().should('include', '/docs/faq/#general-4')
  })

  it('lets users select an industry segment from a list of industries', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list of previously selected industries', () => {
    server.loadFixtures('questions')
    createOrgAssessmentEmptyMultiple(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').contains('PREVIOUSLY SELECTED')
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 2)
  })

  it('lets users select an industry segment from a list where previous industry segments take precedence', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmptyMultiple(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content').as('dropdown')
    cy.get('@dropdown').find('.v-subheader').its('length').should('eq', 2)
    cy.get('@dropdown').find('.v-divider').its('length').should('eq', 1)
    cy.get('@dropdown').find('.v-list-item').its('length').should('eq', 4)
    cy.get('@dropdown').find('.child').its('length').should('eq', 1)
  })

  it('displays stepper and industry segment for the assessment if at least one question has already been answered', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentPracticesIncomplete(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-name]').contains('Boxes & enclosures')
    cy.get('[data-cy=stepper]').as('stepper')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PRACTICE_KEY}]`)
      .should('have.class', 'v-stepper__step--active')
    cy.get('@stepper')
      .find('.v-stepper__step--inactive')
      .its('length')
      .should('eq', 4)
  })

  it('sets the stepper to "Review" step after all practice questions have been answered', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentPracticesComplete(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=stepper]').as('stepper')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PRACTICE_KEY}]`)
      .should('have.class', 'v-stepper__step--editable')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_TARGETS_KEY}]`)
      .should('have.class', 'v-stepper__step--editable')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PLAN_KEY}]`)
      .should('have.class', 'v-stepper__step--editable')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_REVIEW_KEY}]`)
      .should('have.class', 'v-stepper__step--active')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_SHARE_KEY}]`)
      .should('have.class', 'v-stepper__step--inactive')
  })

  it('sets the stepper to "Share" step after the assessment has been frozen', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentFrozen(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=stepper]').as('stepper')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PRACTICE_KEY}]`)
      .should(($div) => {
        expect($div[0].className).to.eq('v-stepper__step')
      })
    cy.get('@stepper')
      .get(`[data-cy=${STEP_TARGETS_KEY}]`)
      .should(($div) => {
        expect($div[0].className).to.eq('v-stepper__step')
      })
    cy.get('@stepper')
      .get(`[data-cy=${STEP_PLAN_KEY}]`)
      .should(($div) => {
        expect($div[0].className).to.eq('v-stepper__step')
      })
    cy.get('@stepper')
      .get(`[data-cy=${STEP_REVIEW_KEY}]`)
      .should('have.class', 'v-stepper__step--editable')
      .should('have.class', 'active')
      .should('have.class', 'v-stepper__step--complete')
    cy.get('@stepper')
      .get(`[data-cy=${STEP_SHARE_KEY}]`)
      .should('have.class', 'v-stepper__step--active')
  })
})
