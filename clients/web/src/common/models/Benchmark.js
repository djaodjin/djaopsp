import { transform } from 'lodash'
import { getUniqueId } from '../utils'
import Section from './Section'

export default class Benchmark {
  constructor({
    id = getUniqueId(),
    section,
    distribution,
    scoreCoefficient,
    ownScore = 0,
    topScore,
    averageScore,
  }) {
    const { x, y, organization_rate } = distribution
    this.id = id
    this.section = section instanceof Section ? section : new Section(section)
    this.distribution = this.getDistribution(x, y, organization_rate)
    this.scoreCoefficient = scoreCoefficient
    this.ownScore = ownScore
    this.topScore = topScore
    this.averageScore = averageScore
  }

  getDistribution(buckets, values, orgBucket) {
    const numBuckets = buckets.length
    const distribution = []
    for (let i = 0; i < numBuckets; i++) {
      distribution[i] = {
        label: buckets[i],
        value: values[i],
        isOrgBucket: buckets[i] === orgBucket,
      }
    }
    return distribution
  }
}
