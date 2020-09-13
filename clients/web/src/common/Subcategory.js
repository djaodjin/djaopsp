import { getUniqueId } from './utils'

export default class Subcategory {
  constructor({ id = getUniqueId(), name }) {
    this.id = id
    this.name = name
  }
}
