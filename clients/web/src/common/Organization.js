import { getUniqueId } from './utils'

export default class Organization {
  constructor({ id = getUniqueId(), name }) {
    this.id = id
    this.name = name
  }
}
