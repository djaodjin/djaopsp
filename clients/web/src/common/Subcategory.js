import { getUniqueId } from './utils'

export default class Subcategory {
  constructor({ id = getUniqueId(), name, path }) {
    this.id = id
    this.name = name
    this.path = path
  }
}
