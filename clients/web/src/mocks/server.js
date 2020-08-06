import {
  STEP_PRACTICE_KEY,
  STEP_TARGETS_KEY,
  STEP_PLAN_KEY,
  STEP_FREEZE_KEY,
  STEP_SCORECARD_KEY,
  STEP_SHARE_KEY,
} from '@/config/app'
import { RestSerializer, Server, Model, Factory, hasMany } from 'miragejs'
import faker from 'faker'

const ApplicationSerializer = RestSerializer.extend()

// Setting faker seed to get consistent results
faker.seed(582020)

export function makeServer({ environment = 'development' }) {
  return new Server({
    environment,

    models: {
      assessment: Model,
      organization: Model.extend({
        assessments: hasMany(),
      }),
    },

    factories: {
      assessment: Factory.extend({
        targets: [],
        improvementPlan: [],
      }),
    },

    serializers: {
      application: ApplicationSerializer,
      organization: ApplicationSerializer.extend({
        include: ['assessments'],
      }),
    },

    seeds(server) {
      // Organization with active assessments at every step in the process
      server.create('organization', {
        id: 'steve-shop',
        name: 'Steve Test Shop',
        assessments: [
          server.create('assessment', {
            industryName: 'Architectural Design',
            industryPath: 'sustainability-architecture-design',
            status: STEP_PRACTICE_KEY,
          }),
          server.create('assessment', {
            industryName: 'Aviation Services',
            industryPath: 'sustainability-aviation-services',
            status: STEP_TARGETS_KEY,
          }),
          server.create('assessment', {
            industryName: 'Construction',
            industryPath: 'sustainability-construction',
            status: STEP_PLAN_KEY,
          }),
          server.create('assessment', {
            industryName: 'Consulting/Advisory Services',
            industryPath: 'sustainability-consulting',
            status: STEP_SCORECARD_KEY,
          }),
          server.create('assessment', {
            industryName: 'Distribution/Logistics & Shipping',
            industryPath: 'sustainability-distribution-industry',
            status: STEP_FREEZE_KEY,
          }),
          server.create('assessment', {
            industryName: 'Energy efficiency contracting',
            industryPath: 'sustainability-energy-efficiency-contracting',
            status: STEP_SHARE_KEY,
          }),
        ],
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
