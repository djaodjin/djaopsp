import {
  RestSerializer,
  Server,
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
import { PRACTICE_VALUES } from '../config/app'
import {
  MAP_QUESTION_FORM_TYPES,
  QUESTION_COMMENT_TYPE,
  QUESTION_EMPLOYEE_COUNT,
  QUESTION_ENERGY_CONSUMED,
  QUESTION_RANGE_TYPE,
  QUESTION_REVENUE_GENERATED,
  QUESTION_WASTE_GENERATED,
  QUESTION_WATER_CONSUMED,
  QUESTION_YES_NO_TYPE,
} from '../config/questionFormTypes'
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
        industryName() {
          return 'Boxes & enclosures'
        },
        industryPath() {
          return '/metal/boxes-and-enclosures/'
        },
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
          let questionForm, options
          let value = null
          if (this.metric) {
            switch (this.metric) {
              case QUESTION_ENERGY_CONSUMED:
              case QUESTION_WATER_CONSUMED:
              case QUESTION_WASTE_GENERATED:
                questionForm = MAP_QUESTION_FORM_TYPES[this.metric]
                options = questionForm.options.map((o) => o.value)
                value = faker.random.arrayElement(options)
                break
            }
          }
          return value
        },
        measured() {
          let questionForm, options
          let value = null
          if (this.metric) {
            switch (this.metric) {
              case QUESTION_COMMENT_TYPE:
                value = faker.lorem.paragraph()
                break
              case QUESTION_EMPLOYEE_COUNT:
              case QUESTION_ENERGY_CONSUMED:
              case QUESTION_REVENUE_GENERATED:
              case QUESTION_WATER_CONSUMED:
              case QUESTION_WASTE_GENERATED:
                value = faker.random.number()
                break
              case QUESTION_RANGE_TYPE:
              case QUESTION_YES_NO_TYPE:
                questionForm = MAP_QUESTION_FORM_TYPES[this.metric]
                options = questionForm.options.map((o) => o.value)
                value = faker.random.arrayElement(options)
                break
            }
          }
          return value
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

      scenarios.createOrgEmpty(server, 'supplier-1', 'S1 - Tamerin (Demo)')
      scenarios.createOrgEmpty(server, 'empty')
      scenarios.createOrgAssessmentEmpty(server, 'alpha')
      scenarios.createOrgAssessmentPracticesIncomplete(server, 'beta')
      scenarios.createOrgAssessmentPracticesComplete(server, 'gamma')
      scenarios.createOrgAssessmentFrozen(server, 'delta')
      scenarios.createOrgAssessmentEmptyMultiple(server, 'epsilon')
      scenarios.createOrgAssessmentPreviousAnswers(server, 'zeta')
    },

    routes() {
      this.namespace = apiBasePath

      this.get('/content', routeHandlers.getIndustryList)

      this.get('/content/*/', routeHandlers.getIndustryQuestions)

      this.get(
        '/:organizationId/benchmark/historical/',
        routeHandlers.getAssessmentHistory
      )

      this.get(
        '/:organizationId/benchmark/historical/*/',
        routeHandlers.getAssessmentHistory
      )

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

      this.post(
        '/:organizationId/sample/',
        routeHandlers.createAssessment.bind(this)
      )

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

      this.post(
        '/:organizationId/sample/:assessmentId/answers/*',
        routeHandlers.postAnswer.bind(this)
      )
    },
  })
}
