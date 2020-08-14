import {
  RestSerializer,
  Server,
  Model,
  Factory,
  hasMany,
  belongsTo,
  trait,
  association,
} from 'miragejs'
import faker from 'faker'

import {
  NUM_BENCHMARKS,
  BENCHMARK_MAX_COMPANIES,
  INDUSTRIES,
  INDUSTRY_SECTIONS,
} from './config'
import industries from './fixtures/industries'
import previousIndustries from './fixtures/previousIndustries'
import {
  DEFAULT_ASSESSMENT_STEP,
  MAP_QUESTION_FORM_TYPES,
  PRACTICE_VALUES,
  STEP_SHARE_KEY,
  VALID_ASSESSMENT_STEPS,
  VALID_ASSESSMENT_TARGETS_KEYS,
  VALID_QUESTION_TYPES,
} from '@/config/app'
import { getRandomInt } from '@/common/utils'

const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
const MAX_PRACTICE_VALUE = PRACTICE_VALUES[PRACTICE_VALUES.length - 1].value

const ApplicationSerializer = RestSerializer.extend()

// Setting faker seed to get consistent results
faker.seed(582020)

export function makeServer({ environment = 'development' }) {
  return new Server({
    environment,

    fixtures: {
      industries,
      previousIndustries,
    },

    models: {
      answer: Model.extend({
        question: belongsTo(),
      }),
      assessment: Model.extend({
        targets: hasMany(),
        practices: hasMany(),
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
      practice: Model.extend({
        question: belongsTo(),
      }),
      previousIndustry: Model,
      question: Model.extend({
        practice: belongsTo(),
        answers: hasMany(),
      }),
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
        name() {
          return faker.random.words(2)
        },
      }),

      organizationGroup: Factory.extend({
        name() {
          return faker.random.word().toUpperCase()
        },
      }),

      practice: Factory.extend({
        question: association(),

        averageValue() {
          return getRandomInt(MIN_PRACTICE_VALUE, MAX_PRACTICE_VALUE + 1)
        },
        environmentalValue() {
          return getRandomInt(MIN_PRACTICE_VALUE, MAX_PRACTICE_VALUE + 1)
        },
        financialValue() {
          return getRandomInt(MIN_PRACTICE_VALUE, MAX_PRACTICE_VALUE + 1)
        },
        operationalValue() {
          return getRandomInt(MIN_PRACTICE_VALUE, MAX_PRACTICE_VALUE + 1)
        },
        implementationRate() {
          return getRandomInt(10, 95)
        },
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
        include: ['targets', 'practices'],
      }),
      organization: ApplicationSerializer.extend({
        include: ['assessments'],
      }),
      organizationGroup: ApplicationSerializer.extend({
        include: ['organizations'],
      }),
      question: ApplicationSerializer.extend({
        include: ['answers'],
      }),
      practice: ApplicationSerializer.extend({
        include: ['question'],
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

      // Organization with active assessment with existing environmental targets and improvement plan
      server.create('organization', {
        id: 'marlin',
        name: 'Blue Marlin',
        assessments: [
          server.create('assessment', {
            targets: VALID_ASSESSMENT_TARGETS_KEYS.map((key) =>
              server.create('target', { key })
            ),
            practices: server.createList('practice', 10),
            score: server.create('score', {
              benchmarks: server.createList('benchmark', NUM_BENCHMARKS, {
                coefficient: (1 / NUM_BENCHMARKS).toFixed(2),
              }),
            }),
            status: STEP_SHARE_KEY,
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

      server.createList('organizationGroup', 5, {
        organizations: server.createList('organization', 10),
      })

      server
        .createList('practice', 20)
        .forEach((practice) =>
          server.create('question', 'withPreviousAnswers', { practice })
        )

      // Add a list of questions with previous answers
      // and additionally add a current answer to each one
      // server.createList('question', 10, 'withPreviousAnswers')
      // .forEach((question) => server.create('answer', { question }))

      server.createList('shareEntry', 30, {
        organization: server.create('organization'),
      })
    },

    routes() {
      this.namespace = '/envconnect/api'

      this.get('/assessments/:id')

      this.get('/industries', (schema) => {
        return schema.industries.all()
      })

      this.get('/organizations', (schema) => {
        return schema.organizationGroups.all()
      })

      this.get('/organizations/:id')

      this.get('/practices/:organizationId/:assessmentId', (schema) => {
        return schema.practices.all()
      })

      this.get('/previous-industries', (schema) => {
        return schema.previousIndustries.all()
      })

      this.get('/questions/:organizationId/:assessmentId', (schema) => {
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

      this.post('/assessments', (schema, request) => {
        // let attrs = JSON.parse(request.requestBody)
        // TODO: Create assessment with attrs
        return this.create('assessment')
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
    },
  })
}
