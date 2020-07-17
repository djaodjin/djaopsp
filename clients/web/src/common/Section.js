import { getUniqueId } from './utils'

export default class Section {
  constructor(id, name) {
    this.id = id || getUniqueId()
    this.name = name
  }
}
