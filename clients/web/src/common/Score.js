import { getUniqueId } from './utils'
import Benchmark from './Benchmark'

export default class Score {
  constructor({
    id = getUniqueId(),
    top = 0,
    own = 0,
    average = 0,
    isValid = false,
    benchmarks,
  }) {
    this.id = id
    this.top = top
    this.own = own
    this.average = average
    this.isValid = isValid
    this.benchmarks = benchmarks.map((benchmark) => new Benchmark(benchmark))
  }
}
