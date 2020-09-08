import { makeServer } from '../../src/mocks/server'
import {
  createOrgAssessmentEmpty,
  createOrgAssessmentOneAnswer,
  createOrgAssessmentPreviousAnswers,
} from '../../src/mocks/scenarios'
import { STEP_PRACTICE_KEY } from '../../src/config/app'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const ASSESSMENT_HOME_URL = `/${ORG_SLUG}/assess/1/`

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
  })

  it('displays the main content correctly for a new assessment', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get('[data-cy=industry-form]').as('industryForm')
    cy.get('[data-cy=industry-label]').click()
    cy.get('.v-menu__content')
      .find('.v-list-item')
      .contains('Boxes & enclosures')
      .click()
    cy.get('@industryForm').find('button[type=submit]').click()
    cy.get(`[data-cy=${STEP_PRACTICE_KEY}]`).click()

    // Displays an intro view before the main content
    cy.url().should('include', `${ASSESSMENT_HOME_URL}intro/`)
    cy.get(`[data-cy=btn-continue]`).click()
    cy.url().should('include', `${ASSESSMENT_HOME_URL}content/`)
    cy.get('[data-cy=assessment-section]').its('length').should('eq', 3)
    cy.contains('0 / 8 questions')
  })

  it('displays the main content correctly for an existing assessment', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentOneAnswer(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get(`[data-cy=${STEP_PRACTICE_KEY}]`).click()

    // Displays an intro view before the main content
    cy.url().should('include', `${ASSESSMENT_HOME_URL}intro/`)
    cy.get(`[data-cy=btn-continue]`).click()
    cy.url().should('include', `${ASSESSMENT_HOME_URL}content/`)
    cy.get('[data-cy=assessment-section]').its('length').should('eq', 3)
    cy.get('[data-cy=assessment-section]').first().as('firstSection')
    cy.get('@firstSection')
      .find('[data-cy=practice-group-header]')
      .contains('Governance & management')
    cy.get('@firstSection').find('h4').contains('Assessment')
    cy.get('@firstSection').find('.progress-label').contains('1 / 1 questions')
    cy.contains('1 / 8 questions')
  })

  it('displays a dialog if a previous assessment in the same industry has been submitted', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentPreviousAnswers(server, ORG_SLUG, ORG_NAME)

    cy.visit(`${ASSESSMENT_HOME_URL}content/metal/boxes-and-enclosures/`)
    cy.get('.v-dialog--persistent').within(($dialog) => {
      cy.wrap($dialog).should('be.visible')
      cy.get('.headline').contains('Previous Answers')
      cy.get('button').click()
      cy.wrap($dialog).should('not.be.visible')
    })
  })

  it('displays answers from a previous assessment in the same industry', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentPreviousAnswers(server, ORG_SLUG, ORG_NAME)

    cy.visit(`${ASSESSMENT_HOME_URL}content/metal/boxes-and-enclosures/`)

    // Close previous assessments dialog
    cy.get('.v-dialog--persistent button').click()

    // Subcategory 1
    cy.get('[data-cy=assessment-section]:nth-of-type(1)')
      .find('.v-list-item:nth-of-type(1)')
      .click()
    cy.get('[data-cy=previous-answers-column]').contains('Previous Answers')
    cy.get('[data-cy=previous-answer]').each(($prevAnswer) => {
      cy.wrap($prevAnswer).should('not.be.empty')
    })
    cy.get('[data-cy=back-link]').click()

    // Subcategory 2
    cy.get('[data-cy=assessment-section]:nth-of-type(1)')
      .find('.v-list-item:nth-of-type(2)')
      .click()
    cy.get('[data-cy=previous-answers-column]').contains('Previous Answers')
    cy.get('[data-cy=previous-answer]').each(($prevAnswer) => {
      cy.wrap($prevAnswer).should('not.be.empty')
    })
    cy.get('[data-cy=back-link]').click()

    // Subcategory 3
    cy.get('[data-cy=assessment-section]:nth-of-type(2)')
      .find('.v-list-item:nth-of-type(1)')
      .click()
    cy.get('[data-cy=previous-answers-column]').contains('Previous Answers')
    cy.get('[data-cy=previous-answer]').each(($prevAnswer) => {
      cy.wrap($prevAnswer).should('not.be.empty')
    })
    cy.get('[data-cy=back-link]').click()

    // Subcategory 4
    cy.get('[data-cy=assessment-section]:nth-of-type(3)')
      .find('.v-list-item:nth-of-type(1)')
      .click()
    cy.get('[data-cy=previous-answers-column]').contains('Previous Answers')
    cy.get('[data-cy=previous-answer]').each(($prevAnswer) => {
      cy.wrap($prevAnswer).should('not.be.empty')
    })
    cy.get('[data-cy=back-link]').click()

    // Subcategory 5
    cy.get('[data-cy=assessment-section]:nth-of-type(3)')
      .find('.v-list-item:nth-of-type(2)')
      .click()
    cy.get('[data-cy=previous-answers-column]').contains('Previous Answers')
    cy.get('[data-cy=previous-answer]').each(($prevAnswer) => {
      cy.wrap($prevAnswer).should('not.be.empty')
    })
    cy.get('[data-cy=back-link]').click()

    cy.contains('1 / 8 questions')
  })
})
