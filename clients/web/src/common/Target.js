import { getUniqueId } from './utils'
import { VALID_ASSESSMENT_TARGETS_KEYS } from '@/config/app'

export default class Target {
  constructor({ id = getUniqueId(), key, text = '', enabled = true }) {
    if (!VALID_ASSESSMENT_TARGETS_KEYS.includes(key)) {
      throw new Error('Invalid target key')
    }
    this.id = id
    this.key = key
    this.text = text
    this.enabled = enabled
  }

  clone() {
    return new Target({
      id: this.id,
      key: this.key,
      text: this.text,
      enabled: this.enabled,
    })
  }
}
