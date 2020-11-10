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

import fixtures from './fixtures'
import scenarios from './scenarios'
import routeHandlers from './handlers'
import {
  MAP_METRICS_TO_QUESTION_FORMS,
  METRIC_ASSESSMENT,
  METRIC_COMMENT,
  METRIC_EMISSIONS,
  METRIC_EMPLOYEE_COUNT,
  METRIC_ENERGY_CONSUMED,
  METRIC_FRAMEWORK,
  METRIC_FREETEXT,
  METRIC_RELEVANCE,
  METRIC_REVENUE_GENERATED,
  METRIC_WASTE_GENERATED,
  METRIC_WATER_CONSUMED,
  METRIC_YES_NO,
} from '../config/questionFormTypes'

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
        questions: hasMany(), // selected practices for improvement plan
        answers: hasMany(),
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
      shareEntry: Model.extend({
        organization: belongsTo(),
      }),
    },

    factories: {
      assessment: Factory.extend({
        account() {
          return null // organization slug (orgId
        },
        campaign() {
          return 'assessment'
        },
        created_at() {
          return faker.date.past().toISOString()
        },
        industryName() {
          return 'Boxes & enclosures'
        },
        industryPath() {
          return '/metal/boxes-and-enclosures/'
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
              case METRIC_ENERGY_CONSUMED:
              case METRIC_WATER_CONSUMED:
              case METRIC_WASTE_GENERATED:
                questionForm = MAP_METRICS_TO_QUESTION_FORMS[this.metric]
                options = questionForm.options.map((o) => o.value)
                value = faker.random.arrayElement(options)
                break
              case METRIC_EMISSIONS:
                // Assuming this question type has only one unit value
                value = MAP_METRICS_TO_QUESTION_FORMS[this.metric].unit.value
            }
          }
          return value
        },
        measured() {
          let questionForm, options
          let value = null
          if (this.metric) {
            switch (this.metric) {
              case METRIC_COMMENT:
              case METRIC_FREETEXT:
                value = faker.lorem.paragraph()
                break
              case METRIC_EMPLOYEE_COUNT:
              case METRIC_ENERGY_CONSUMED:
              case METRIC_EMISSIONS:
              case METRIC_REVENUE_GENERATED:
              case METRIC_WATER_CONSUMED:
              case METRIC_WASTE_GENERATED:
                value = faker.random.number()
                break
              case METRIC_FRAMEWORK:
              case METRIC_ASSESSMENT:
              case METRIC_YES_NO:
                questionForm = MAP_METRICS_TO_QUESTION_FORMS[this.metric]
                options = questionForm.options.map((o) => o.value)
                value = faker.random.arrayElement(options)
                break
              case METRIC_RELEVANCE:
                questionForm = MAP_METRICS_TO_QUESTION_FORMS[METRIC_EMISSIONS]
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

      shareEntry: Factory.extend({
        date() {
          return faker.date.past()
        },
      }),
    },

    serializers: {
      application: ApplicationSerializer,
      assessment: ApplicationSerializer.extend({
        include: ['questions'],
      }),
      organization: ApplicationSerializer.extend({
        include: ['assessments'],
      }),
      organizationGroup: ApplicationSerializer.extend({
        include: ['organizations'],
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
      scenarios.createOrgAssessmentMultiple(server, 'epsilon')
      scenarios.createOrgAssessmentPreviousAnswers(server, 'zeta')
      scenarios.createOrgAssessmentPreviousTargets(server, 'eta')
    },

    routes() {
      this.namespace = apiBasePath

      this.get('/content', routeHandlers.getIndustryList)

      this.get('/content/*/', routeHandlers.getIndustryQuestions)

      this.get(
        '/:organizationId/benchmark/historical/',
        routeHandlers.getAssessmentHistory
      )

      /* --- ORGANIZATIONS --- */
      this.get('/organizations', (schema) => {
        return schema.organizationGroups.all()
      })

      this.get('/profile/:organizationId', routeHandlers.getOrganizationProfile)

      /* --- ASSESSMENTS --- */
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

      /* --- BENCHMARKS --- */
      this.get(
        '/:organizationId/benchmark/:assessmentId/graphs/*',
        routeHandlers.getBenchmarks
      )
    },
  })
}
