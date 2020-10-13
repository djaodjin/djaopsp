import assessment from './assessment'
import benchmark from './benchmark'
import organization from './organization'
// TODO: Convert to specific entity files
import other from './other'

export default {
  ...assessment,
  ...benchmark,
  ...organization,
  ...other,
}
