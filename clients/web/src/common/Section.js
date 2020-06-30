import { getUniqueId } from './utils'

export default class Section {
  constructor(name) {
    this._id = getUniqueId()
    this._name = name
  }

  get id() {
    return this._id
  }

  get name() {
    return this._name
  }
}
