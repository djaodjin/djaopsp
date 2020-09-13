import FormQuestion from '../common/FormQuestion'
import FormQuestionNumber from '../common/FormQuestionNumber'
import FormQuestionRadio from '../common/FormQuestionRadio'
import FormQuestionQuantity from '../common/FormQuestionQuantity'

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

const FormQuestionEmployeeCount = new FormQuestionNumber({
  options: 'Number of Employees',
})

const FormQuestionRevenueGenerated = new FormQuestionNumber({
  options: 'Revenue in USD',
})

export const QUESTION_COMMENT_TYPE = 'freetext'
export const QUESTION_EMPLOYEE_COUNT = 'employee-counted'
export const QUESTION_ENERGY_CONSUMED = 'energy-consumed'
export const QUESTION_RANGE_TYPE = 'assessment'
export const QUESTION_REVENUE_GENERATED = 'revenue-generated'
export const QUESTION_YES_NO_TYPE = 'yes-no'
export const QUESTION_WASTE_GENERATED = 'waste-generated'
export const QUESTION_WATER_CONSUMED = 'water-consumed'

export const MAP_QUESTION_FORM_TYPES = {
  [QUESTION_COMMENT_TYPE]: FormQuestionTextarea,
  [QUESTION_EMPLOYEE_COUNT]: FormQuestionEmployeeCount,
  [QUESTION_ENERGY_CONSUMED]: FormQuestionEnergyConsumed,
  [QUESTION_RANGE_TYPE]: FormQuestionRadioRange,
  [QUESTION_REVENUE_GENERATED]: FormQuestionRevenueGenerated,
  [QUESTION_YES_NO_TYPE]: FormQuestionRadioDiscrete,
  [QUESTION_WATER_CONSUMED]: FormQuestionWaterConsumed,
  [QUESTION_WASTE_GENERATED]: FormQuestionWasteGenerated,
  3: FormQuestionRadioLabeled, // TODO: Remove?
}

export const VALID_QUESTION_TYPES = Object.keys(MAP_QUESTION_FORM_TYPES)
