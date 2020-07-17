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
export const STEP_FREEZE_KEY = 'freeze'
export const STEP_SHARE_KEY = 'share'
export const STEP_SCORECARD_KEY = 'scorecard'

export const ASSESSMENT_STEPS = {
  practice: {
    index: 1,
    text: 'Establish current practices',
    path: 'assessmentPractices',
    introPath: 'introPractices',
    isEditable: true,
  },
  targets: {
    index: 2,
    text: 'Define environmental targets',
    path: 'assessmentTargets',
    introPath: 'introTargets',
    isEditable: true,
  },
  plan: {
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
