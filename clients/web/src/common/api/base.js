const API_HOST = process.env.VUE_APP_STANDALONE ? window.location.origin : ''
const API_BASE_URL = `${API_HOST}${process.env.VUE_APP_ROOT}${process.env.VUE_APP_API_BASE}`

export class APIError extends Error {
  constructor(message) {
    super(message)
    this.name = 'APIError'
  }
}

export function request(endpoint, { body, method, ...customConfig } = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = { 'content-type': 'application/json' }
  const config = {
    method: method ? method : body ? 'POST' : 'GET',
    ...customConfig,
    headers: {
      ...headers,
      ...customConfig.headers,
    },
  }
  if (body) {
    config.body = JSON.stringify(body)
  }

  return fetch(url, config)
}
