import isValid from 'date-fns/isValid'
import format from 'date-fns/format'
import parseISO from 'date-fns/parseISO'

export function formatDate(el) {
  const dateString = el.innerHTML

  try {
    let date = parseISO(dateString)
    if (isValid(date)) {
      date = format(date, 'MMMM do, yyyy')
      el.innerHTML = date
    }
  } catch (e) {
    console.error(e)
  }
}
