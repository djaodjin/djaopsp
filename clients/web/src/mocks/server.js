import {
  RestSerializer,
  Server,
  Response,
  Model,
  Factory,
  hasMany,
  belongsTo,
} from 'miragejs'
import faker from 'faker'
import snakeCase from 'lodash/snakeCase'

import {
  NUM_BENCHMARKS,
  BENCHMARK_MAX_COMPANIES,
  INDUSTRY_SECTIONS,
} from './config'
import fixtures from './fixtures'
import scenarios from './scenarios'
import routeHandlers from './handlers'
import {
  MAP_QUESTION_FORM_TYPES,
  PRACTICE_VALUES,
  VALID_ASSESSMENT_STEPS,
  VALID_ASSESSMENT_TARGETS_KEYS,
  VALID_QUESTION_TYPES,
} from '../config/app'
import { getRandomInt } from '../common/utils'

const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
const MAX_PRACTICE_VALUE = PRACTICE_VALUES[PRACTICE_VALUES.length - 1].value

const ApplicationSerializer = RestSerializer.extend({
  keyForAttribute(attr) {
    return snakeCase(attr)
  },
})

// Setting faker seed to get consistent results
faker.seed(582020)

export function makeServer({ environment = 'development', apiBasePath }) {
  return new Server({
    environment,

    fixtures,

    models: {
      answer: Model.extend({
        organization: belongsTo(),
        assessment: belongsTo(),
        question: belongsTo(),
      }),
      assessment: Model.extend({
        targets: hasMany(),
        questions: hasMany(), // selected practices for improvement plan
        answers: hasMany(),
        score: belongsTo(),
      }),
      benchmark: Model,
      industry: Model,
      organization: Model.extend({
        assessments: hasMany(),
      }),
      organizationGroup: Model.extend({
        organizations: hasMany(),
      }),
      previousIndustry: Model,
      question: Model,
      score: Model.extend({
        benchmarks: hasMany(),
      }),
      shareEntry: Model.extend({
        organization: belongsTo(),
      }),
      target: Model,
    },

    factories: {
      assessment: Factory.extend({
        campaign() {
          return 'assessment'
        },
        created_at() {
          return faker.date.past().toISOString()
        },
        is_frozen() {
          return false
        },
        afterCreate(assessment) {
          assessment.update({ slug: assessment.id })
        },
      }),

      answer: Factory.extend({
        metric() {
          return null
        },
        unit() {
          return null
        },
        measured() {
          return null
        },
        created_at() {
          return null
        },
        collected_by() {
          return null
        },
      }),

      benchmark: Factory.extend({
        section() {
          return faker.random.arrayElement(INDUSTRY_SECTIONS)
        },
        scores() {
          return [
            {
              label: '0 - 25%', // optional
              value: getRandomInt(0, BENCHMARK_MAX_COMPANIES),
            },
            {
              label: '25% - 50%', // optional
              value: getRandomInt(0, BENCHMARK_MAX_COMPANIES),
            },
            {
              label: '50% - 75%', // optional
              value: getRandomInt(0, BENCHMARK_MAX_COMPANIES),
            },
            {
              label: '75% - 100%', // optional
              value: getRandomInt(0, BENCHMARK_MAX_COMPANIES),
            },
          ]
        },
        coefficient() {
          return 0.1
        },
        companyScore() {
          return getRandomInt(10, 100)
        },
      }),

      organization: Factory.extend({
        slug() {
          return this.id
        },
        printable_name() {
          return faker.random.words(2)
        },
      }),

      organizationGroup: Factory.extend({
        name() {
          return faker.random.word().toUpperCase()
        },
      }),

      score: Factory.extend({
        top() {
          return getRandomInt(80, 95)
        },
        own() {
          return getRandomInt(60, 80)
        },
        average() {
          return getRandomInt(60, 80)
        },
        isValid() {
          return faker.random.boolean()
        },
      }),

      shareEntry: Factory.extend({
        date() {
          return faker.date.past()
        },
      }),

      target: Factory.extend({
        text() {
          return faker.lorem.sentence()
        },
      }),
    },

    serializers: {
      application: ApplicationSerializer,
      assessment: ApplicationSerializer.extend({
        include: ['targets', 'questions'],
      }),
      organization: ApplicationSerializer.extend({
        include: ['assessments'],
      }),
      organizationGroup: ApplicationSerializer.extend({
        include: ['organizations'],
      }),
      score: ApplicationSerializer.extend({
        include: ['benchmarks'],
      }),
      shareEntry: ApplicationSerializer.extend({
        include: ['organization'],
      }),
    },

    seeds(server) {
      server.loadFixtures()

      scenarios.createOrgEmpty(server, 'empty')
      scenarios.createOrgAssessmentEmpty(server, 'alpha')
      scenarios.createOrgAssessmentOneAnswer(server, 'beta')
      scenarios.createOrgAssessmentPracticesIncomplete(server, 'gamma')
      scenarios.createOrgAssessmentPracticesComplete(server, 'delta')
    },

    routes() {
      this.namespace = apiBasePath

      this.get('/content', routeHandlers.getIndustryList)

      this.get('/content/*/', routeHandlers.getIndustryQuestions)

      /* --- ORGANIZATIONS --- */
      this.get('/organizations', (schema) => {
        return schema.organizationGroups.all()
      })

      this.get('/profile/:organizationId', routeHandlers.getOrganizationProfile)

      this.get('/:organizationId/sample/', routeHandlers.getLatestAssessment)

      /* --- ASSESSMENTS --- */
      this.get(
        '/:organizationId/sample/:assessmentId/',
        routeHandlers.getAssessmentInformation
      )

      this.get(
        '/:organizationId/sample/:assessmentId/answers/',
        routeHandlers.getAnswers
      )

      this.get(
        '/:organizationId/sample/:assessmentId/answers/*',
        routeHandlers.getAnswers
      )

      // TODO: Remove
      this.get('/practices/:organizationId/:assessmentId', (schema) => {
        return schema.questions.all()
      })

      this.get('/previous-industries', (schema) => {
        const previousIndustries = schema.previousIndustries.all()
        return {
          count: previousIndustries.length,
          next: null,
          previous: null,
          results: previousIndustries.models,
        }
      })

      this.get('/score/:organizationId/:assessmentId', (schema) => {
        return schema.scores.find('1')
      })

      this.get('/share-history/:organizationId/:assessmentId', (schema) => {
        return schema.shareEntries.all()
      })

      this.patch('/assessments/:id', (schema, request) => {
        const { id } = request.params
        const properties = JSON.parse(request.requestBody)
        const assessment = schema.assessments.find(id)
        assessment.update(properties)
        return assessment
      })

      this.post('/:organizationId/sample/', (schema, request) => {
        const { organizationId } = request.params
        const attrs = JSON.parse(request.requestBody)
        const newAssessment = this.create('assessment', attrs)

        // Create relationship to newly created entity
        const organization = schema.organizations.find(organizationId)
        organization.assessmentIds.push(newAssessment.id)
        const { campaign, created_at, slug } = newAssessment
        return { campaign, created_at, slug }
      })

      this.post('/targets/:organizationId/:assessmentId', (schema, request) => {
        const { assessmentId } = request.params
        const targets = JSON.parse(request.requestBody)

        const assessment = schema.assessments.find(assessmentId)
        targets.forEach((target) => {
          const { id, ...attrs } = target
          if (assessment.targetIds.includes(id)) {
            // update target
            schema.targets.find(id).update(attrs)
          } else {
            // create target
            const newTarget = this.create('target', attrs)
            assessment.targets.add(newTarget)
          }
        })
        return assessment
      })

      this.put(
        '/answer/:organizationId/:assessmentId/:questionId',
        (schema, request) => {
          const { organizationId, assessmentId, questionId } = request.params
          const { id, ...attrs } = JSON.parse(request.requestBody)

          const organization = schema.organizations.find(organizationId)
          const assessment = schema.assessments.find(assessmentId)
          const question = schema.questions.find(questionId)

          let answer = schema.answers.find(id)
          if (answer) {
            answer.update({
              ...attrs,
              organization,
              assessment,
              question,
            })
          } else {
            answer = this.create('answer', {
              ...attrs,
              organization,
              assessment,
              question,
            })
          }
          return answer
        }
      )
    },
  })
}
