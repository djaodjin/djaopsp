import { APIError, request } from './base'
import Benchmark from '@/common/models/Benchmark'
import Section from '@/common/models/Section'

async function getBenchmarks(organizationId, assessmentId, industryPath) {
  const response = await request(
    `/${organizationId}/benchmark/${assessmentId}/graphs/${industryPath}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { results } = await response.json()

  const benchmarks = results.map((benchmark) => {
    const {
      slug,
      title,
      text,
      normalized_score,
      highest_normalized_score,
      avg_normalized_score,
      distribution,
      score_weight,
    } = benchmark

    const section = new Section({
      name: title,
      iconPath: text,
    })

    return new Benchmark({
      id: slug,
      section,
      distribution,
      ownScore: normalized_score,
      averageScore: avg_normalized_score,
      topScore: highest_normalized_score,
      scoreCoefficient: score_weight,
    })
  })

  const totalsIndex = benchmarks.findIndex((b) => b.id === 'totals')
  if (totalsIndex === -1) {
    // No totals benchmark was found
    return [{}, benchmarks]
  }
  const totals = benchmarks.splice(totalsIndex, 1)
  return [totals, benchmarks]
}

export default {
  getBenchmarks,
}
