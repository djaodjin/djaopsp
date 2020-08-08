import { INDUSTRIES, INDUSTRY_SECTIONS } from './config'
import {
  DEFAULT_ASSESSMENT_STEP,
  MAP_QUESTION_FORM_TYPES,
  STEP_SCORECARD_KEY,
  VALID_ASSESSMENT_STEPS,
  VALID_ASSESSMENT_TARGETS_KEYS,
  VALID_QUESTION_TYPES,
} from '@/config/app'
import {
  RestSerializer,
  Server,
  Model,
  Factory,
  hasMany,
  belongsTo,
  trait,
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
        answers: hasMany('answer'),
      }),
      target: Model,
    },

    factories: {
      assessment: Factory.extend({
        $industry() {
          return faker.random.arrayElement(INDUSTRIES)
        },
        industryPath() {
          return this.$industry.path
        },
        industryName() {
          return this.$industry.name
        },
        status() {
          return DEFAULT_ASSESSMENT_STEP
        },
      }),

      answer: Factory.extend({
        author() {
          return 'current_user@testmail.com'
        },
        answers() {
          const questionForm = MAP_QUESTION_FORM_TYPES[this.question.type]
          const options = questionForm.options.map((o) => o.value)

          if (questionForm.name === 'FormQuestionTextarea') {
            return [faker.lorem.paragraph()]
          }
          if (questionForm.name === 'FormQuestionQuantity') {
            return [faker.random.number(), faker.random.arrayElement(options)]
          }
          // Smaller chance of showing a comment
          const comment = Math.random() > 0.8 ? faker.lorem.sentences(3) : ''
          return [faker.random.arrayElement(options), comment]
        },

        // Current answers won't have a frozen date
        isPrevious: trait({
          author() {
            return faker.internet.email()
          },
          frozen() {
            return faker.date.past()
          },
        }),
      }),

      question: Factory.extend({
        section() {
          return faker.random.arrayElement(INDUSTRY_SECTIONS)
        },
        subcategory() {
          return faker.random.arrayElement(this.section.subcategories)
        },
        path() {
          return this.subcategory.path
        },
        text() {
          return faker.lorem.sentence()
        },
        type() {
          return faker.random.arrayElement(VALID_QUESTION_TYPES)
        },

        withPreviousAnswers: trait({
          afterCreate(question, server) {
            server.createList('answer', 1, 'isPrevious', { question })
          },
        }),

        withCurrentAnswer: trait({
          afterCreate(question, server) {
            server.create('answer', { question })
          },
        }),
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
      question: ApplicationSerializer.extend({
        include: ['answers'],
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

      // Add a list of questions with previous answers
      // and additionally add a current answer to each one
      server.createList('question', 10, 'withPreviousAnswers')
      // .forEach((question) => server.create('answer', { question }))
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

      this.get('/questions/:organizationId/:assessmentId', (schema) => {
        return schema.questions.all()
      })
    },
  })
}
