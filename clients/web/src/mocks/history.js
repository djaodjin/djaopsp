import { DELAY } from './config'

export async function getShareHistory() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        {
          date: '2020-07-29T23:33:52.813Z',
          id: '135ab',
          name: 'Accenture',
        },
        {
          date: '2020-07-29T23:33:52.813Z',
          id: '137bc',
          name: 'ADB Companies',
        },
        {
          date: '2020-07-29T23:33:52.813Z',
          id: '139cd',
          name: 'HP',
        },
        {
          date: '2020-07-29T23:50:30.617Z',
          id: '141de',
          name: 'Amazon',
        },
        {
          date: '2020-07-29T23:50:30.617Z',
          id: '143ef',
          name: '3M',
        },
        {
          date: '2020-07-29T23:50:30.617Z',
          id: '143fg',
          name: 'PG&E',
        },
        {
          date: '2020-07-29T23:50:30.617Z',
          id: '145gh',
          name: 'Plasma Energy',
        },
      ])
    }, DELAY)
  })
}
