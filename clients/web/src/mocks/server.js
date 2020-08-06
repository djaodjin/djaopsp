import { INDUSTRIES } from './config'
import {
  DEFAULT_ASSESSMENT_STEP,
  STEP_SCORECARD_KEY,
  VALID_ASSESSMENT_STEPS,
  VALID_ASSESSMENT_TARGETS_KEYS,
} from '@/config/app'
import {
  RestSerializer,
  Server,
  Model,
  Factory,
  hasMany,
  belongsTo,
} from 'miragejs'
import faker from 'faker'

const ApplicationSerializer = RestSerializer.extend()

// Setting faker seed to get consistent results
faker.seed(582020)

export function makeServer({ environment = 'development' }) {
  return new Server({
    environment,

    models: {
      answer: Model.extend({
        question: belongsTo(),
      }),
      assessment: Model.extend({
        targets: hasMany(),
        improvementPlan: hasMany('practices'),
      }),
      organization: Model.extend({
        assessments: hasMany(),
      }),
      practice: Model.extend({
        question: belongsTo(),
      }),
      question: Model.extend({
        previousAnswers: hasMany('answers'),
      }),
      target: Model,
    },

    factories: {
      assessment: Factory.extend({
        industryPath() {
          return faker.random.arrayElement(INDUSTRIES).path
        },
        industryName() {
          const industry = INDUSTRIES.find((i) => i.path === this.industryPath)
          return industry.name
        },
        status() {
          return DEFAULT_ASSESSMENT_STEP
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
      organization: ApplicationSerializer.extend({
        include: ['assessments'],
      }),
      assessment: ApplicationSerializer.extend({
        include: ['targets'],
      }),
    },

    seeds(server) {
      // Organization with active assessment with existing environmental targets and improvement plan
      server.create('organization', {
        id: 'marlin',
        name: 'Blue Marlin',
        assessments: [
          server.create('assessment', {
            targets: VALID_ASSESSMENT_TARGETS_KEYS.map((key) =>
              server.create('target', { key })
            ),
            status: STEP_SCORECARD_KEY,
          }),
        ],
      })

      // Organization with active assessments at every step in the process
      server.create('organization', {
        id: 'steve-shop',
        name: 'Steve Test Shop',
        assessments: VALID_ASSESSMENT_STEPS.map((step) =>
          server.create('assessment', {
            status: step,
          })
        ),
      })

      // Organization with no assessments
      server.create('organization', {
        id: 'supplier-1',
        name: 'S1 - Tamerin (Demo)',
      })
    },

    routes() {
      this.namespace = '/envconnect/api'

      this.get('/organizations/:id', (schema, request) => {
        let id = request.params.id
        return schema.organizations.find(id)
      })

      this.get('/assessments/:id', (schema, request) => {
        let id = request.params.id
        return schema.assessments.find(id)
      })
    },
  })
}
