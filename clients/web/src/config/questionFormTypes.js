import FormQuestion from '../common/models/FormQuestion'
import FormQuestionNumber from '../common/models/FormQuestionNumber'
import FormQuestionRadio from '../common/models/FormQuestionRadio'
import FormQuestionQuantity from '../common/models/FormQuestionQuantity'
import FormQuestionRelevantQuantity from '../common/models/FormQuestionRelevantQuantity'

const FormQuestionRadioDiscrete = new FormQuestionRadio({
  componentName: 'FormQuestionBinary',
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
      description:
        'The practice is implemented across all services, products or facilities to which it could apply.',
    },
    {
      text: 'Mostly Yes',
      value: 'most-yes',
      description:
        'The practice is implemented around <b>50% or more</b> of the services, products or facilities to which it could apply.',
    },
    {
      text: 'Mostly No',
      value: 'most-no',
      description:
        'The practice is implemented around <b>50% or less</b> of the services, products or facilities to which it could apply.',
    },
    {
      text: 'No',
      value: 'no',
      description:
        'The practice is hardly implemented across the services, products or facilities to which it could apply.',
    },
    {
      text: 'Not Applicable',
      value: 'not-app',
      description:
        'The practice is not applicable to the organization, or the organization has no influence or control over its implementation.',
    },
  ],
})

const FormQuestionRadioLabeled = new FormQuestionRadio({
  options: [
    {
      text: 'Initiating',
      value: 'initiating',
      description: 'There is minimal management support',
    },
    {
      text: 'Progressing',
      value: 'progressing',
      description: 'Support is visible and clearly demonstrated',
    },
    {
      text: 'Optimizing',
      value: 'optimizing',
      description:
        'Executive management reviews environmental performance, risks and opportunities, and endorses/sets goals',
    },
    {
      text: 'Leading',
      value: 'leading',
      description:
        'The Board of Directors annually reviews environmental performance and sets or endorses goals',
    },
    {
      text: 'Transforming',
      value: 'transforming',
      description:
        'Executive management sponsors transformative change in industry sector and beyond',
    },
  ],
})

const FormQuestionTextarea = new FormQuestion({
  componentName: 'FormQuestionTextarea',
})
FormQuestionTextarea.render = function (answers) {
  return answers[0] || ''
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

const FormQuestionEmployeeCount = new FormQuestionNumber({
  options: 'Number of Employees',
})

const FormQuestionRevenueGenerated = new FormQuestionNumber({
  options: 'Revenue in USD',
})

const FormQuestionEmissionsGenerated = new FormQuestionRelevantQuantity({
  options: [
    { value: 'relevant-and-calculated', text: 'Relevant, calculated' },
    {
      value: 'relevant-not-yet-calculated',
      text: 'Relevant, not yet calculated',
    },
    { value: 'not-relevant-calculated', text: 'Not relevant, calculated' },
    {
      value: 'not-relevant-explanation-provided',
      text: 'Not relevant, explanation provided',
    },
    { value: 'not-evaluated', text: 'Not evaluated' },
  ],
})

export const METRIC_ASSESSMENT = 'assessment'
export const METRIC_COMMENT = 'comments'
export const METRIC_EMISSIONS = 'ghg-emissions-generated'
export const METRIC_EMPLOYEE_COUNT = 'employee-counted'
export const METRIC_ENERGY_CONSUMED = 'energy-consumed'
export const METRIC_FRAMEWORK = 'framework'
export const METRIC_FREETEXT = 'freetext'
export const METRIC_RELEVANCE = 'relevance'
export const METRIC_REVENUE_GENERATED = 'revenue-generated'
export const METRIC_WATER_CONSUMED = 'water-consumed'
export const METRIC_WASTE_GENERATED = 'waste-generated'
export const METRIC_YES_NO = 'yes-no'

export const MAP_METRICS_TO_QUESTION_FORMS = {
  [METRIC_ASSESSMENT]: FormQuestionRadioRange,
  [METRIC_EMISSIONS]: FormQuestionEmissionsGenerated,
  [METRIC_EMPLOYEE_COUNT]: FormQuestionEmployeeCount,
  [METRIC_ENERGY_CONSUMED]: FormQuestionEnergyConsumed,
  [METRIC_FRAMEWORK]: FormQuestionRadioLabeled,
  [METRIC_FREETEXT]: FormQuestionTextarea,
  [METRIC_REVENUE_GENERATED]: FormQuestionRevenueGenerated,
  [METRIC_WATER_CONSUMED]: FormQuestionWaterConsumed,
  [METRIC_WASTE_GENERATED]: FormQuestionWasteGenerated,
  [METRIC_YES_NO]: FormQuestionRadioDiscrete,
}

export const METRICS_WITH_UNIT = [
  METRIC_EMISSIONS,
  METRIC_ENERGY_CONSUMED,
  METRIC_WATER_CONSUMED,
  METRIC_WASTE_GENERATED,
]
