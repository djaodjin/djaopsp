import { getUniqueId } from './utils'
import Section from './Section'

export default class Benchmark {
  constructor({ id = getUniqueId(), section, scores, companyScore = 0 }) {
    this.id = id
    this.section = section instanceof Section ? section : new Section(section)
    this.scores = [
      {
        label: '0 - 25%',
        value: 25, // this must be the top value of the label
        number: scores[0].value,
      },
      {
        label: '25% - 50%',
        value: 50, // this must be the top value of the label
        number: scores[1].value,
      },
      {
        label: '50% - 75%',
        value: 75, // this must be the top value of the label
        number: scores[2].value,
      },
      {
        label: '75% - 100%',
        value: 100, // this must be the top value of the label
        number: scores[3].value,
      },
    ]
    this.ownScore = companyScore
  }
}
