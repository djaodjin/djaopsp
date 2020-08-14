import { getUniqueId } from './utils'

export default class Section {
  constructor({ id = getUniqueId(), name, path, iconPath }) {
    this.id = id
    this.name = name
    this.path = path
    this.iconPath = iconPath
  }
}
