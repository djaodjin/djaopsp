const DELAY = 100

export function getScores() {
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
