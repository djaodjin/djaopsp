import { AssessmentStep, AssessmentFlow } from '../common/models/AssessmentFlow'

export const PRACTICE_VALUES = [
  {
    value: 1,
    label: 'Low',
    color: '#9cd868',
  },
  {
    value: 2,
    label: 'Medium',
    color: '#69b12b',
  },
  {
    value: 3,
    label: 'High',
    color: '#007040',
  },
  {
    value: 4,
    label: 'Gold',
    color: '#ffd802',
  },
]

export const PRACTICE_VALUE_CATEGORIES = [
  { text: 'Average value', value: 'avg_value' },
  { text: 'Environmental value', value: 'environmental_value' },
  { text: 'Financial value', value: 'profitability' },
  { text: 'Implementation ease', value: 'implementation_ease' },
  { text: 'Ops/Maintenance value', value: 'business_value' },
]

export const PRACTICE_VALUE_CATEGORY_DEFAULT = PRACTICE_VALUE_CATEGORIES[0]

/* --- Assessment Steps --- */
export const STEP_PRACTICE_KEY = 'practice'
export const STEP_TARGETS_KEY = 'targets'
export const STEP_PLAN_KEY = 'plan'
export const STEP_REVIEW_KEY = 'review'
export const STEP_SHARE_KEY = 'share'

export const ASSESSMENT_STEPS = {
  [STEP_PRACTICE_KEY]: {
    index: 1,
    text: 'Establish current practices',
    path: 'introPractices',
    isEditable: true,
    stepIncrease: 3,
  },
  [STEP_TARGETS_KEY]: {
    index: 2,
    text: 'Define environmental targets',
    path: 'introTargets',
    isEditable: true,
  },
  [STEP_PLAN_KEY]: {
    index: 3,
    text: 'Create improvement plan',
    path: 'introPlan',
    isEditable: true,
  },
  [STEP_REVIEW_KEY]: {
    index: 4,
    text: 'Review assessment',
    path: 'assessmentScorecard',
    stepIncrease: 1,
  },
  [STEP_SHARE_KEY]: {
    index: 5,
    text: 'Share assessment',
    path: 'assessmentShare',
  },
}

export const ASSESSMENT_FLOW = new AssessmentFlow({
  steps: Object.entries(ASSESSMENT_STEPS)
    .map(([key, obj]) => ({
      ...obj,
      key,
    }))
    .sort((a, b) => a.index - b.index)
    .map((o) => new AssessmentStep(o)),
})

export const VALID_ASSESSMENT_STEPS = Object.keys(ASSESSMENT_STEPS)

/* --- Assessment Targets --- */
export const VALID_ASSESSMENT_TARGETS = [
  {
    value: 'energy',
    text: 'Energy Reduction',
    examples: [
      'Donec accumsan ipsum ac nibh gravida ornare. Duis eget consequat enim. Sed non lorem sed mauris vestibulum tempus nec nec risus. Mauris vel dolor turpis.',
      'Vivamus faucibus metus a dui fringilla sodales. Aenean lectus felis, scelerisque sed consectetur eu, elementum quis risus. Ut et pretium nisl. Nam metus elit, ultricies interdum tortor ac, placerat bibendum urna.',
    ],
  },
  {
    value: 'emissions',
    text: 'GHG Emissions',
    examples: [
      'Praesent ac leo odio. Praesent vel tincidunt risus. In sodales nunc nec lorem vestibulum, eu blandit sapien interdum. Morbi sed auctor lorem. Class aptent taciti sociosqu ad litora torquent per conubia nostra, per inceptos himenaeos. In et turpis vel ex venenatis tempus eu in turpis.',
      'Pellentesque leo nisl, ornare vel sapien a, viverra luctus neque. In hac habitasse platea dictumst. Nullam dictum arcu eget quam tristique, at aliquam ipsum accumsan.',
      'Duis ultricies orci nec dolor dapibus volutpat. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas.',
    ],
  },
  {
    value: 'water',
    text: 'Water Usage',
    examples: [
      'Proin aliquet quam at ante semper aliquam. Nam lacinia ex in nisi tempus, vel iaculis ipsum feugiat. Praesent aliquam libero quis augue posuere tincidunt. Aenean convallis, mi eget tristique suscipit, tortor ipsum aliquet tortor, at scelerisque purus felis sed eros.',
      'Quisque facilisis semper nulla scelerisque tempus. Vivamus non metus at lectus gravida scelerisque. Interdum et malesuada fames ac ante ipsum primis in faucibus.',
    ],
  },
  {
    value: 'waste',
    text: 'Waste Reduction',
    examples: [
      'Phasellus congue, erat luctus convallis condimentum, sapien felis fringilla arcu, sed varius libero nisi efficitur lacus. Nam condimentum nisi eget ante faucibus, vel euismod tellus vestibulum. Pellentesque at nulla erat.',
      'Aliquam dignissim ipsum nec felis pellentesque finibus. Phasellus tristique elementum lobortis. Cras vel ante vitae est iaculis fringilla.',
    ],
  },
]

export const ASSESSMENT_TARGETS_LABELS = VALID_ASSESSMENT_TARGETS.reduce(
  (acc, target) => {
    acc[target.value] = target.text
    return acc
  },
  {}
)

export const VALID_ASSESSMENT_TARGETS_KEYS = VALID_ASSESSMENT_TARGETS.map(
  (target) => target.value
)
