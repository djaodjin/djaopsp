import FormQuestion from '../common/FormQuestion'
import { AssessmentStep, AssessmentFlow } from '../common/AssessmentFlow'

function answersWarning(answers) {
  console.warn('Unable to find matching answer in ', answers)
  console.trace()
  return ''
}

const FormQuestionRadioDiscrete = new FormQuestion('FormQuestionRadio', [
  {
    text: 'Yes',
    value: 'yes',
  },
  {
    text: 'No',
    value: 'no',
  },
])
FormQuestionRadioDiscrete.render = function (answers) {
  const selected = this.options.find((opt) => opt.value === answers[0])
  if (selected) return selected.text
  return answersWarning(answers)
}

const FormQuestionRadioRange = new FormQuestion('FormQuestionRadio', [
  {
    text: 'Yes',
    value: 'yes',
  },
  {
    text: 'Mostly Yes',
    value: 'most-yes',
  },
  {
    text: 'Mostly No',
    value: 'most-no',
  },
  {
    text: 'No',
    value: 'no',
  },
  {
    text: 'Not Applicable',
    value: 'not-app',
  },
])
FormQuestionRadioRange.render = function (answers) {
  const selected = this.options.find((opt) => opt.value === answers[0])
  if (selected) return selected.text
  return answersWarning(answers)
}

const FormQuestionRadioLabeled = new FormQuestion('FormQuestionRadio', [
  {
    text:
      "<b>Initiating:</b><span class='ml-1'>There is minimal management support</span>",
    value: 'initiating',
  },
  {
    text:
      "<b>Progressing:</b><span class='ml-1'>Support is visible and clearly demonstrated</span>",
    value: 'progressing',
  },
  {
    text:
      "<b>Optimizing:</b><span class='ml-1'>Executive management reviews environmental performance, risks and opportunities, and endorses/sets goals</span>",
    value: 'optimizing',
  },
  {
    text:
      "<b>Leading:</b><span class='ml-1'>The Board of Directors annually reviews environmental performance and sets or endorses goals</span>",
    value: 'leading',
  },
  {
    text:
      "<b>Transforming:</b><span class='ml-1'>Executive management sponsors transformative change in industry sector and beyond</span>",
    value: 'transforming',
  },
])
FormQuestionRadioLabeled.render = function (answers) {
  const selected = this.options.find((opt) => opt.value === answers[0])
  if (selected) {
    const found = selected.text.match(/<b>(.*):<\/b>/)
    return found && found[1]
  }
  return answersWarning(answers)
}

const FormQuestionTextarea = new FormQuestion('FormQuestionTextarea')
FormQuestionTextarea.render = function (answers) {
  return answers[0] || ''
}

const FormQuestionQuantity = new FormQuestion('FormQuestionQuantity', [
  {
    text: 'Kilowatt-hour (kWh) of Electricity  / Year',
    value: 'kwh-year',
  },
  {
    text: 'Metric Tons / Year',
    value: 'tons-year',
  },
  {
    text: 'GHG Emissions',
    value: 'ghg-emissions-generated',
  },
  {
    text: 'US Gallons / Year',
    value: 'gallons-year',
  },
  {
    text: 'mmBtu / Year',
    value: 'mmbtu-year',
  },
  {
    text: 'Cubic meters / Year',
    value: 'm3-year',
  },
  {
    text: 'Kilo liters / Year',
    value: 'kiloliters-year',
  },
  {
    text: 'Cubic feet / Year',
    value: 'ft3-year',
  },
  {
    text: 'Cubic feet / Year',
    value: 'ft3-year',
  },
])
FormQuestionQuantity.render = function (answers) {
  const unit = this.options.find((opt) => opt.value === answers[1])
  if (unit) return `${answers[0]} ${unit.text}`
  return answersWarning(answers)
}

export const MAP_QUESTION_FORM_TYPES = {
  1: FormQuestionRadioDiscrete,
  2: FormQuestionRadioRange,
  3: FormQuestionRadioLabeled,
  4: FormQuestionTextarea,
  5: FormQuestionQuantity,
}

export const VALID_QUESTION_TYPES = Object.keys(MAP_QUESTION_FORM_TYPES)

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
  { text: 'Average Value', value: 'averageValue' },
  { text: 'Environmental Value', value: 'environmentalValue' },
  { text: 'Cost Savings', value: 'financialValue' },
  { text: 'Operational Benefits', value: 'operationalValue' },
]

export const PRACTICE_VALUE_CATEGORY_DEFAULT = PRACTICE_VALUE_CATEGORIES[0]

/* --- Assessment Steps --- */
export const STEP_TARGETS_KEY = 'targets'
export const STEP_PLAN_KEY = 'plan'
export const STEP_FREEZE_KEY = 'freeze'
export const STEP_SCORECARD_KEY = 'scorecard'
export const STEP_SHARE_KEY = 'share'

export const ASSESSMENT_STEPS = {
  practice: {
    index: 1,
    text: 'Establish current practices',
    path: 'assessmentPractices',
    introPath: 'introPractices',
    isEditable: true,
  },
  [STEP_TARGETS_KEY]: {
    index: 2,
    text: 'Define environmental targets',
    path: 'assessmentTargets',
    introPath: 'introTargets',
    isEditable: true,
  },
  [STEP_PLAN_KEY]: {
    index: 3,
    text: 'Create improvement plan',
    path: 'assessmentPlan',
    introPath: 'introPlan',
    isEditable: true,
  },
  [STEP_SCORECARD_KEY]: {
    index: 4,
    text: 'Review scorecard',
    path: 'assessmentScorecard',
  },
  [STEP_FREEZE_KEY]: {
    index: 5,
    text: 'Freeze assessment',
  },
  [STEP_SHARE_KEY]: {
    index: 6,
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

export const DEFAULT_ASSESSMENT_STEP = VALID_ASSESSMENT_STEPS[0]

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
