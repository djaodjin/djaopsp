import { makeServer } from '../../src/mocks/server'
import {
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
const HOME_URL = `/${ORG_SLUG}/`
const ASSESSMENT_HOME_URL = `/${ORG_SLUG}/assess/1/metal/boxes-and-enclosures/`

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

  it('displays stepper and industry segment for the assessment', () => {
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

    cy.visit(HOME_URL)
    // Select frozen assessment appearing under active assessment list
    cy.get('.assessment-info').last().contains('Completed').click()
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
