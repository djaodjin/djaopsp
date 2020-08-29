import { makeServer } from '../../src/mocks/server'
import { createOrgAssessmentOneAnswer } from '../../src/mocks/scenarios'
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

  it('displays an intro view', () => {
    server.loadFixtures('industries', 'questions')
    createOrgAssessmentOneAnswer(server, ORG_SLUG, ORG_NAME)

    cy.visit(ASSESSMENT_HOME_URL)
    cy.get(`[data-cy=${STEP_PRACTICE_KEY}]`)
      .contains('Establish current practices')
      .click()
    cy.url().should(($url) => {
      const re = RegExp(`${ASSESSMENT_HOME_URL}intro/`)
      expect($url).to.match(re)
    })
  })
})
