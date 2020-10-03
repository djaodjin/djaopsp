import faker from 'faker'
import {
  METRIC_COMMENT,
  METRIC_EMISSIONS,
  METRIC_FREETEXT,
  METRIC_RELEVANCE,
  METRIC_YES_NO,
} from '../../config/questionFormTypes'

export default function (
  server,
  orgId,
  orgName = 'Assessment With Previous Targets'
) {
  const currentAssessment = server.create('assessment', {})

  const previousAssessment = server.create('assessment', {
    is_frozen: true,
    industryName: 'Boxes & enclosures',
    industryPath: '/metal/boxes-and-enclosures/',
  })

  const organization = server.create('organization', {
    id: orgId,
    printable_name: orgName,
    assessments: [currentAssessment, previousAssessment],
  })

  // Per fixture: /mocks/fixtures/questions.js
  server.schema.questions
    .where((question) => !!question.path)
    .models.forEach((question) => {
      if (question.default_metric === METRIC_EMISSIONS) {
        server.create('answer', {
          assessment: currentAssessment,
          organization,
          question,
          metric: METRIC_RELEVANCE,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      if (question.default_metric === METRIC_YES_NO) {
        server.create('answer', {
          assessment: currentAssessment,
          organization,
          question,
          metric: METRIC_FREETEXT,
          created_at: faker.date.past(),
          collected_by: 'current_user@testmail.com',
        })
      }
      server.create('answer', {
        assessment: currentAssessment,
        organization,
        question,
        metric: question.default_metric,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
      server.create('answer', {
        assessment: currentAssessment,
        organization,
        question,
        metric: METRIC_COMMENT,
        created_at: faker.date.past(),
        collected_by: 'current_user@testmail.com',
      })
    })

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
