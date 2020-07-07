const DELAY = 100

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
