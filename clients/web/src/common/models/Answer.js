import { getUniqueId } from '../utils'
import {
  MAP_METRICS_TO_QUESTION_FORMS,
  METRIC_ASSESSMENT,
  METRIC_EMISSIONS,
  METRIC_ENERGY_CONSUMED,
  METRIC_FRAMEWORK,
  METRIC_RELEVANCE,
  METRIC_WASTE_GENERATED,
  METRIC_WATER_CONSUMED,
  METRIC_YES_NO,
  METRICS_WITH_UNIT,
} from '../../config/questionFormTypes'

export default class Answer {
  constructor({
    id = getUniqueId(),
    question,
    author,
    created = new Date().toISOString(),
  }) {
    this.id = id
    this.question = question // question ID
    this.metric = null
    this.author = author
    this.created = created
    this.answers = []
    this.answered = false
  }
  isAnswered() {
    const answer = this.answers.find((answer) => answer.default)
    if (METRICS_WITH_UNIT.includes(answer.metric)) {
      return !!answer.measured && !!answer.unit
    } else if (answer.metric === METRIC_EMISSIONS) {
      const relevance = this.answers.find(
        (answer) => answer.metric === METRIC_RELEVANCE
      )
      return !!answer.measured && !!relevance.measured
    } else {
      return !!answer.measured
    }
  }
  load(answerObjects) {
    let answer
    let metric
    let values = []

    for (let i = 0; i < answerObjects.length; i++) {
      const item = answerObjects[i]
      metric = item.default_metric
      if (
        item.metric === item.default_metric ||
        (answerObjects.length === 1 && item.metric === null)
      ) {
        answer = item
      } else {
        values.push({
          metric: item.metric,
          measured: item.measured,
        })
      }
    }

    if (answer) {
      if (METRICS_WITH_UNIT.includes(metric)) {
        values.unshift({
          default: true,
          metric,
          measured: answer.measured,
          unit: answer.unit,
        })
      } else {
        values.unshift({
          default: true,
          metric,
          measured: answer.measured,
        })
      }
    }

    this.author = answer && answer.collected_by
    this.created = answer && answer.created_at
    this.metric = metric
    this.answers = values
    this.answered = this.isAnswered()
  }
  render() {
    let output = ''
    if (
      this.metric === METRIC_ASSESSMENT ||
      this.metric === METRIC_FRAMEWORK ||
      this.metric === METRIC_YES_NO
    ) {
      const options = MAP_METRICS_TO_QUESTION_FORMS[this.metric].options
      const selected = options.find(
        (opt) => opt.value === this.answers[0].measured
      )
      output = selected ? selected.text : ''
    } else if (this.metric === METRIC_EMISSIONS) {
      const answer = this.answers[0]
      const questionForm = MAP_METRICS_TO_QUESTION_FORMS[this.metric]
      const relevance = this.answers.find(
        (answer) => answer.metric === METRIC_RELEVANCE
      )
      const selected = questionForm.options.find(
        (opt) => opt.value === relevance.measured
      )
      output = selected
        ? `${answer.measured} <small>${questionForm.unit.text} | ${selected.text}</small>`
        : `${answer.measured} <small>${questionForm.unit.text}</small>`
    } else if (
      this.metric === METRIC_ENERGY_CONSUMED ||
      this.metric === METRIC_WATER_CONSUMED ||
      this.metric === METRIC_WASTE_GENERATED
    ) {
      const questionForm = MAP_METRICS_TO_QUESTION_FORMS[this.metric]
      const answer = this.answers[0]
      const selected = questionForm.options.find(
        (opt) => opt.value === answer.unit
      )
      output = selected ? `${answer.measured} ${selected.text}` : ''
    } else {
      // METRIC_EMPLOYEE_COUNT
      // METRIC_REVENUE_GENERATED
      // METRIC_FREETEXT
      output = this.answers[0].measured
    }
    return output
  }
  save(values) {
    this.answers = values
    this.answered = this.isAnswered()
  }
  export() {}
}
