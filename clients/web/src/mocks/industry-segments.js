import { DELAY } from './config'

export async function getIndustrySegments() {
  // try {
  //   const response = await fetch('/envconnect/api/content/campagins?q=public')
  //   const data = await response.json()
  //   console.log(data)
  // } catch (e) {
  //   console.error('Ooops', e)
  // }

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve({
        count: 5,
        next: null,
        previous: null,
        results: [
          {
            path: '/consulting',
            title: 'Consulting/Advisory services',
            indent: 0,
          },
          { path: '/construction', title: 'Construction', indent: 0 },
          { path: null, title: 'Metal structures & equipment', indent: 0 },
          {
            path: '/metal/boxes-and-enclosures',
            title: 'Boxes & enclosures',
            indent: 1,
          },
          { path: '/metal/wire-and-cable', title: 'Wire & cable', indent: 1 },
          {
            path: '/professional-services',
            title: 'Professional services',
            indent: 0,
          },
        ],
      })
    }, DELAY)
  })
}

export function getPreviousIndustrySegments() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve({
        count: 3,
        next: null,
        previous: null,
        results: [
          { path: '/construction', title: 'Construction', indent: 0 },
          { path: null, title: 'Metal structures & equipment', indent: 0 },
          {
            path: '/metal/boxes-and-enclosures',
            title: 'Boxes & enclosures',
            indent: 1,
          },
        ],
      })
    }, DELAY)
  })
}
