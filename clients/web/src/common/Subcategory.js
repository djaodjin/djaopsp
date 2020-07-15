import { getUniqueId } from './utils'

export default class Subcategory {
  constructor(id, name) {
    this.id = id || getUniqueId()
    this.name = name
  }
}
