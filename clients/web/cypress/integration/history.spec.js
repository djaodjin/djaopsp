import compareDesc from 'date-fns/compareDesc'
import parseISO from 'date-fns/parseISO'
import { makeServer } from '../../src/mocks/server'
import {
  createOrgAssessmentEmpty,
  createOrgAssessmentFrozen,
} from '../../src/mocks/scenarios'

const ORG_SLUG = 'test_org'
const ORG_NAME = 'Test Organization'
const HISTORY_URL = `/${ORG_SLUG}/history/`

describe('Supplier App: Assessment History', () => {
  let server

  beforeEach(() => {
    if (server) server.shutdown()
    server = makeServer({
      environment: 'test',
      apiBasePath: `${Cypress.env('ROOT')}${Cypress.env('API_BASE')}`,
    })
  })

  it('shows a placeholder message if the organization has no archived assessments', () => {
    server.loadFixtures('questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HISTORY_URL)
    cy.get('[data-cy=empty-placeholder]').should('exist')
    cy.get('[data-cy=history-table]').should('not.exist')
  })

  it('shows a table with a list of archived assessments sorted by date (descending)', () => {
    server.loadFixtures('questions')
    createOrgAssessmentFrozen(server, ORG_SLUG, ORG_NAME)

    cy.visit(HISTORY_URL)
    cy.get('[data-cy=empty-placeholder]').should('not.exist')
    cy.get('[data-cy=history-table]').should('exist')
    cy.get('.v-data-table table').as('table')
    cy.get('@table').find('thead th').its('length').should('eq', 4)
    cy.get('@table').find('tbody tr').its('length').should('eq', 2)

    // Check the table header
    cy.get('@table')
      .find('thead th:nth-child(1)')
      .should('have.text', 'Completed')
    cy.get('@table')
      .find('thead th:nth-child(2)')
      .should('have.text', 'Industry Segment')
    cy.get('@table')
      .find('thead th:nth-child(3)')
      .should('have.text', 'Overall Score')
    cy.get('@table')
      .find('thead th:nth-child(4)')
      .should('have.text', 'Scorecard')

    cy.get('@table').find('tbody tr:nth-child(1)').as('firstRow')
    cy.get('@table').find('tbody tr:nth-child(2)').as('secondRow')
    // Check row sort order
    cy.get('@firstRow')
      .find('time')
      .then(($firstRowTime) => {
        cy.get('@secondRow')
          .find('time')
          .then(($secondRowTime) => {
            const firstRowDate = $firstRowTime.attr('datetime')
            const secondRowDate = $secondRowTime.attr('datetime')
            const order = compareDesc(
              parseISO(firstRowDate),
              parseISO(secondRowDate)
            )
            expect(order).to.equal(-1)
          })
      })

    // Check the table content
    cy.get('@firstRow')
      .find('td:nth-child(2)')
      .should('have.text', 'Professional services')
    cy.get('@firstRow')
      .find('td:nth-child(3)')
      .should(($tableCell) => {
        expect(parseInt($tableCell.text(), 10)).to.be.a('number')
      })
    cy.get('@firstRow')
      .find('td:nth-child(4) a')
      .should(($tableCell) => {
        expect($tableCell.text()).to.have.string('View scorecard')
        expect($tableCell.attr('href')).to.match(
          /\/scorecard\/\d\/content\/professional-services\/$/
        )
      })
  })

  it('lets users navigate back to the home view', () => {
    server.loadFixtures('questions')
    createOrgAssessmentEmpty(server, ORG_SLUG, ORG_NAME)

    cy.visit(HISTORY_URL)
    cy.get('[data-cy=back-link]').click()
    cy.url().should('match', new RegExp(`/${ORG_SLUG}/$`))
  })
})
