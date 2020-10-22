import faker from 'faker'
import {
  METRIC_COMMENT,
  METRIC_EMISSIONS,
  METRIC_FREETEXT,
  METRIC_RELEVANCE,
  METRIC_YES_NO,
} from '../../config/questionFormTypes'

/* Initialize an empty assessment i.e. with all questions unanswered
 * Per fixture: /mocks/fixtures/questions.js
 */
export function initEmptyAssessment(server, organization, assessment) {
  server.schema.questions
    .where((question) => !!question.path)
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}

/* Initialize an assessment as incomplete -with one answered question
 * and all other questions unanswered.
 * Per fixture: /mocks/fixtures/questions.js
 */
export function initIncompleteAssessment(server, organization, assessment) {
  // Answered question
  server.schema.questions.find(['4']).models.forEach((question) => {
    server.create('answer', {
      assessment,
      organization,
      question,
      metric: question.default_metric,
      created_at: faker.date.past(),
      collected_by: 'current_user@testmail.com',
    })
  })

  // Create empty answers for unanswered questions
  server.schema.questions
    .where((question) => question.id !== '4' && !!question.path)
    .models.forEach((question) => {
      server.create('answer', {
        assessment,
        organization,
        question,
      })
    })
}

/* Initialize a complete assessment where all questions have been
 * answered (answers do not include comments).
 * Per fixture: /mocks/fixtures/questions.js
 */
export function initCompleteAssessment(server, organization, assessment) {
  server.schema.questions
    .where((question) => !!question.path)
    .models.forEach((question) => {
      if (question.default_metric === METRIC_EMISSIONS) {
        server.create('answer', {
          assessment: previousAssessment,
          organization,
          question,
          metric: METRIC_RELEVANCE,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      if (question.default_metric === METRIC_YES_NO) {
        server.create('answer', {
          assessment: previousAssessment,
          organization,
          question,
          metric: METRIC_FREETEXT,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      server.create('answer', {
        assessment: previousAssessment,
        organization,
        question,
        metric: question.default_metric,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
    })
}

/* Initialize a complete assessment where all questions have been
 * answered and also include comments in each answer.
 * Per fixture: /mocks/fixtures/questions.js
 */
export function initCompleteAssessmentWithComments(
  server,
  organization,
  assessment
) {
  server.schema.questions
    .where((question) => !!question.path)
    .models.forEach((question) => {
      if (question.default_metric === METRIC_EMISSIONS) {
        server.create('answer', {
          assessment,
          organization,
          question,
          metric: METRIC_RELEVANCE,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      if (question.default_metric === METRIC_YES_NO) {
        server.create('answer', {
          assessment,
          organization,
          question,
          metric: METRIC_FREETEXT,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      server.create('answer', {
        assessment,
        organization,
        question,
        metric: question.default_metric,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
      server.create('answer', {
        assessment,
        organization,
        question,
        metric: METRIC_COMMENT,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
    })
}
