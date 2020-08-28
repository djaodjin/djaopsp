import FormQuestion from '../common/FormQuestion'
import FormQuestionRadio from '../common/FormQuestionRadio'
import FormQuestionQuantity from '../common/FormQuestionQuantity'
import { AssessmentStep, AssessmentFlow } from '../common/AssessmentFlow'

const FormQuestionRadioDiscrete = new FormQuestionRadio({
  options: [
    {
      text: 'Yes',
      value: 'yes',
    },
    {
      text: 'No',
      value: 'no',
    },
  ],
})

const FormQuestionRadioRange = new FormQuestionRadio({
  options: [
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
  ],
})

const FormQuestionRadioLabeled = new FormQuestionRadio({
  options: [
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
  ],
})
FormQuestionRadioLabeled.render = function (answers) {
  const selected = this.options.find((opt) => opt.value === answers[0])
  if (selected) {
    const found = selected.text.match(/<b>(.*):<\/b>/)
    return found && found[1]
  }
  return ''
}

const FormQuestionTextarea = new FormQuestion({ name: 'FormQuestionTextarea' })
FormQuestionTextarea.render = function (answers) {
  return answers[0] || ''
}
FormQuestionTextarea.isEmpty = function (answers) {
  return !answers[0]
}

const FormQuestionEnergyConsumed = new FormQuestionQuantity({
  options: [
    {
      value: 'mmbtu-of-natural-gas-year',
      text: 'mmBtu of Natural gas / Year',
    },
    {
      value: 'mmbtu-of-blast-furnance-gas-year',
      text: 'mmBtu of Blast furnance gas / Year',
    },
    {
      value: 'mmbtu-of-coke-oven-gas-year',
      text: 'mmBtu of Coke oven gas / Year',
    },
    {
      value: 'mmbtu-of-fuel-gas-year',
      text: 'mmBtu of Fuel gas / Year',
    },
    {
      value: 'mmbtu-of-propane-gas-year',
      text: 'mmBtu of Propane (gas) / Year',
    },
    {
      value: 'gallon-of-aviation-gasoline-year',
      text: 'Gallon of Aviation gasoline / Year',
    },
    {
      value: 'gallon-of-kerosene-year',
      text: 'Gallon of Kerosene / Year',
    },
    {
      value: 'gallon-of-liquified-petroleum-gases-lpg-year',
      text: 'Gallon of Liquified Petroleum Gases (LPG) / Year',
    },
    {
      value: 'gallon-of-motor-gasoline-year',
      text: 'Gallon of Motor gasoline / Year',
    },
    {
      value: 'gallon-of-propane-liquid-year',
      text: 'Gallon of Propane (liquid) / Year',
    },
    {
      value: 'gallon-of-crude-oil-year',
      text: 'Gallon of Crude oil / Year',
    },
    {
      value: 'gallon-of-motor-diesel-fuel-year',
      text: 'Gallon of Motor diesel fuel / Year',
    },
    {
      value: 'gallon-of-liquified-natural-gas-lng-year',
      text: 'Gallon of Liquified Natural Gas (LNG) / Year',
    },
    {
      value: 'kwh-year',
      text: 'Kilowatt-hour (kWh) of Electricity / Year',
    },
    {
      value: 'giga-joules-year',
      text: 'Giga Joules (GJ) / Year',
    },
    {
      value: 'giga-joules-fte-year',
      text: 'Giga Joules (GJ) per full-time employee (FTE) / Year',
    },
  ],
})

const FormQuestionWaterConsumed = new FormQuestionQuantity({
  options: [
    { value: 'm3-year', text: 'Cubic meters (m3) / Year' },
    { value: 'kiloliters-year', text: 'Kilo liters / Year' },
    { value: 'ft3-year', text: 'Cubic feet (ft.3) / Year' },
    { value: 'gallons-year', text: 'US Gallon / Year' },
  ],
})

const FormQuestionWasteGenerated = new FormQuestionQuantity({
  options: [
    { value: 'tons-year', text: 'Metric tons / year' },
    { value: 'lbs-year', text: 'Pounds / year' },
    { value: 'm3-year', text: 'Cubic meters (m3) / Year' },
    { value: 'kiloliters-year', text: 'Kilo liters / Year' },
    { value: 'ft3-year', text: 'Cubic feet (ft.3) / Year' },
    { value: 'gallons-year', text: 'US Gallon / Year' },
  ],
})

export const QUESTION_COMMENT_TYPE = 'freetext'
export const QUESTION_ENERGY_CONSUMED = 'energy-consumed'
const QUESTION_RANGE_TYPE = 'assessment'
const QUESTION_YES_NO_TYPE = 'yes-no'
export const QUESTION_WASTE_GENERATED = 'waste-generated'
export const QUESTION_WATER_CONSUMED = 'water-consumed'

export const MAP_QUESTION_FORM_TYPES = {
  [QUESTION_COMMENT_TYPE]: FormQuestionTextarea,
  [QUESTION_ENERGY_CONSUMED]: FormQuestionEnergyConsumed,
  [QUESTION_RANGE_TYPE]: FormQuestionRadioRange,
  [QUESTION_YES_NO_TYPE]: FormQuestionRadioDiscrete,
  [QUESTION_WATER_CONSUMED]: FormQuestionWaterConsumed,
  [QUESTION_WASTE_GENERATED]: FormQuestionWasteGenerated,
  3: FormQuestionRadioLabeled, // TODO: Remove?
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
export const STEP_REVIEW_KEY = 'scorecard'
export const STEP_FREEZE_KEY = 'freeze'
export const STEP_SHARE_KEY = 'share'

export const ASSESSMENT_STEPS = {
  [STEP_PRACTICE_KEY]: {
    index: 1,
    text: 'Establish current practices',
    path: 'introPractices',
    isEditable: true,
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

export const VALID_ASSESSMENT_TARGETS_KEYS = VALID_ASSESSMENT_TARGETS.map(
  (target) => target.value
)
