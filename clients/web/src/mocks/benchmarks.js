import { DELAY } from './config'
import { getRandomInt } from '../common/utils'
import { getRandomSection } from './questions'

const MAX_COMPANIES = 30
const NUM_SECTIONS = 6

export async function getBenchmarkData() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const data = []
      for (let i = 0; i < NUM_SECTIONS; i++) {
        const section = getRandomSection()
        data.push({
          section: {
            content: section,
          },
          scores: [
            {
              label: '0 - 25%',
              value: 25, // this must be the top value of the label
              number: getRandomInt(0, MAX_COMPANIES),
            },
            {
              label: '25% - 50%',
              value: 50, // this must be the top value of the label
              number: getRandomInt(0, MAX_COMPANIES),
            },
            {
              label: '50% - 75%',
              value: 75, // this must be the top value of the label
              number: getRandomInt(0, MAX_COMPANIES),
            },
            {
              label: '75% - 100%',
              value: 100, // this must be the top value of the label
              number: getRandomInt(0, MAX_COMPANIES),
            },
          ],
          companyScore: getRandomInt(10, 100),
        })
      }
      resolve(data)
    }, DELAY)
  })
}
