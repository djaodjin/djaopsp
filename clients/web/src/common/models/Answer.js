import { getUniqueId } from '../utils'
import {
  METRIC_ASSESSMENT,
  METRIC_COMMENT,
  METRIC_EMISSIONS,
  METRIC_EMPLOYEE_COUNT,
  METRIC_ENERGY_CONSUMED,
  METRIC_FREETEXT,
  METRIC_REVENUE_GENERATED,
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

    debugger
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
  render() {}
  save(values) {
    this.answers = values
    this.answered = this.isAnswered()
  }
  export() {}
}
