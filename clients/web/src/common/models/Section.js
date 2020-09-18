import { getUniqueId } from '../utils'

export default class Section {
  constructor({ id = getUniqueId(), name, iconPath }) {
    this.id = id
    this.name = name
    this.iconPath = iconPath
  }
}
