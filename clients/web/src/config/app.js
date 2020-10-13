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
  },
  {
    value: 'emissions',
    text: 'GHG Emissions',
  },
  {
    value: 'water',
    text: 'Water Usage',
  },
  {
    value: 'waste',
    text: 'Waste Reduction',
  },
]

export const ASSESSMENT_TARGETS_LABELS = VALID_ASSESSMENT_TARGETS.reduce(
  (acc, target) => {
    acc[target.value] = target.text
    return acc
  },
  {}
)
