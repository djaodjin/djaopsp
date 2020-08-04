import { DELAY } from './config'
import Target from '../common/Target'

export function getTopLevelScores() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve({
        top: 84,
        own: {
          score: 64,
          isValid: true,
        },
        average: 57,
      })
    }, DELAY)
  })
}

export function getScoresByBusinessAreas() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        {
          name: 'Governance & Management',
          icon: 'static/img/envconnect-logo.png',
          score: 36,
          coefficient: 0.15,
        },
        {
          name: 'Engineering & Design',
          icon: 'static/img/envconnect-logo.png',
          score: 95,
          coefficient: 0.3,
        },
        {
          name: 'Procurement',
          icon: 'static/img/envconnect-logo.png',
          score: 27,
          coefficient: 0.3,
        },
        {
          name: 'Construction',
          icon: 'static/img/envconnect-logo.png',
          score: 40,
          coefficient: 0.2,
        },
        {
          name: 'Office/Grounds',
          icon: 'static/img/envconnect-logo.png',
          score: 34,
          coefficient: 0.05,
        },
      ])
    }, DELAY)
  })
}

export function getTargets() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        new Target({
          category: 'Energy Reduction',
          text:
            'Cras semper aliquet leo, ultricies lacinia ante facilisis eu curabitur porttitor.',
          deadlineDate: new Date().toISOString().substr(0, 10),
          baselineDate: new Date().toISOString().substr(0, 10),
        }),
        new Target({
          category: 'GHG Emissions',
          text:
            'Nunc egestas aliquet ipsum, placerat condimentum risus tempor nec vulputate augue magna nec cursus turpis blandit',
          deadlineDate: new Date().toISOString().substr(0, 10),
          baselineDate: new Date().toISOString().substr(0, 10),
        }),
        new Target({
          category: 'Water Usage',
          text: 'Pellentesque suscipit lectus sed magna pulvinar scelerisque.',
          deadlineDate: new Date().toISOString().substr(0, 10),
          baselineDate: new Date().toISOString().substr(0, 10),
        }),
        new Target({
          category: 'Waste Reduction',
          text:
            'Fusce sodales risus eget mi luctus hendrerit semper enim consequat.',
          deadlineDate: new Date().toISOString().substr(0, 10),
          baselineDate: new Date().toISOString().substr(0, 10),
        }),
      ])
    }, DELAY)
  })
}
