import format from 'date-fns/format'

export function formatDate(el) {
  const dateString = el.innerHTML
  const date = format(dateString, 'MMMM do YYYY')
  el.innerHTML = date
}
