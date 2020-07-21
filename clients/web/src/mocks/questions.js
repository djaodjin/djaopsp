import { DELAY } from './config'
import { getRandomInt } from '../common/utils'
import Answer from '../common/Answer'
import Section from '../common/Section'
import Subcategory from '../common/Subcategory'
import Question from '../common/Question'

// Set IDs to null to generate automatic unique IDs
const sections = [
  // Construction industry segment
  new Section(
    '/construction/sustainability-construction/governance-management-49f1ad0',
    'Governance & Management'
  ),
  new Section(
    '/construction/sustainability-construction/procurement-5d484d5',
    'Procurement'
  ),
  new Section(
    '/construction/sustainability-construction/construction-bbec85a',
    'Construction'
  ),
  new Section(
    '/construction/sustainability-construction/officegrounds-e661fc0',
    'Office/grounds'
  ),

  // Boxes & enclosures industry segment
  new Section(
    '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/management-basics',
    'Governance & Management'
  ),
  new Section(
    '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/design',
    'Design'
  ),
  new Section(
    '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/production',
    'Production'
  ),
  new Section(
    '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/distribution',
    'Distribution'
  ),
  new Section(
    '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/end-of-life',
    'End of Life'
  ),
]

// Set IDs to null to generate automatic unique IDs
const subcategories = [
  // (0) Construction / Management & governance
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy',
    'Environmental policy'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority',
    'Responsability & authority'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment',
    'Environmental assessment'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment',
    'Leadership engagement & commitment'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/controls-improvement-plans-measurement',
    'Controls, improvement plans & measurement'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/management-system-rigor',
    'Management system rigor'
  ),
  new Subcategory(
    '/construction/sustainability-construction/governance-management-49f1ad0/environmental-reporting',
    'Environmental reporting'
  ),

  // (7) Construction / Procurement
  new Subcategory(
    '/construction/sustainability-construction/procurement-5d484d5/procure-environmentally-prefereable-version',
    'Procure environmentally prefereable version of the following:'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/',
    'Measure'
  ),

  // (9) Contruction / Construction
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/electricity-greenhouse',
    'Electricity & greenhouse gas emissions'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/vehicles-equipment',
    'Vehicles & equipment'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/other',
    'Other'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/general',
    'General'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/air-emissions',
    'Air emissions (NOX, SOX, particules, CO2)'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/waste',
    'Waste'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/hazardous',
    'Hazardous chemical subsctances'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/physical-footprint',
    'Physical footprint'
  ),
  new Subcategory(
    '/construction/sustainability-construction/construction-bbec85a/water',
    'Water'
  ),

  // (18) Construction / Office & grounds / Electricity & gas
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/general',
    'General'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/energy-source',
    'Energy source'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/lighting',
    'Lighting'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/hvac',
    'HVAC'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/electronics',
    'Electronics, equipment & appliances'
  ),

  // (23) Construction / Office & grounds / Fuel
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/fuel/company-vehicles',
    'Company vehicles'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/fuel/employee-transport',
    'Employee transport & travel'
  ),

  // (25) Construction / Office & grounds / Waste
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/waste/general',
    'General'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing',
    'Purchasing practices to avoid pollution/waste'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure',
    'Procure environmentally preferable versions of the following:'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure/paper',
    'Paper'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/waste/waste-recycling',
    'Waste recycling and disposal'
  ),

  // (30) Construction / Office & grounds / Water
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/water/general',
    'General'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/water/indoors',
    'Indoors'
  ),
  new Subcategory(
    '/construction/sustainability-construction/officegrounds-e661fc0/water/outdoors',
    'Outdoors'
  ),
]

export function getRandomSection() {
  const index = getRandomInt(0, sections.length)
  return sections[index]
}

export function getRandomSubcategory() {
  const index = getRandomInt(0, subcategories.length)
  return subcategories[index]
}

export function getQuestions() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        // (0) Construction / Management & governance
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-adequate-policy',
          sections[0],
          subcategories[0],
          'Have adequate policy level commitments, and be internally and externally communicated.',
          '1',
          'Comments',
          false,
          [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-adequate-policy',
              questionType: '1',
              author: 'michael@tamarinsolutions.com',
              answers: ['yes'],
            }),
          ]
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-highest-level-leadership',
          sections[0],
          subcategories[0],
          'Have the highest level of leadership at the organization sign the policy.',
          '2',
          'Please explain how you plan to use the results of the assessment.',
          false,
          [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-highest-level-leadership',
              questionType: '2',
              author: 'michael@tamarinsolutions.com',
              answers: ['most-no'],
            }),
          ]
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority/assign-formal-responsability',
          sections[0],
          subcategories[1],
          'Assign formal responsibility for directing and overseeing environmental performance to top/executive management.',
          '3',
          'Comments',
          true,
          [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority/assign-formal-responsability',
              questionType: '3',
              author: 'michael@tamarinsolutions.com',
              answers: ['leading'],
            }),
          ]
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment/conduct-assessment',
          sections[0],
          subcategories[2],
          'Conduct a systematic, rigorous assessment to identify and prioritize material environmental impacts, issues and opportunities.',
          '4',
          'Comments',
          true,
          [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment/conduct-assessment',
              questionType: '4',
              author: 'michael@tamarinsolutions.com',
              answers: [
                'Nullam gravida leo vel libero imperdiet rhoncus tincidunt at enim. Sed vel enim ac leo mattis dapibus. Suspendisse ligula nisl, elementum sit amet velit in, tincidunt commodo sapien. In tincidunt at felis ac laoreet. Phasellus blandit velit in sem cursus tincidunt. Sed in tortor eget mauris rutrum eleifend. Sed quis dolor rutrum, ultrices eros ut, blandit turpis.',
              ],
            }),
          ]
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment/give-priorities',
          sections[0],
          subcategories[3],
          "Give the priorities identified in the materiality assessment meaningful inclusion in the organization's goal setting and tactical planning.",
          '5',
          'Comments',
          true,
          [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment/give-priorities',
              questionType: '5',
              author: 'michael@tamarinsolutions.com',
              answers: ['14', 'ghg-emissions-generated'],
            }),
          ]
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/controls-improvement-plans-measurement/implement-controls',
          sections[0],
          subcategories[4],
          'Implement controls, improvement plans and measurement processes to address all priorities identified in the assessment.',
          '1',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/management-system-rigor/implement-environmental-management',
          sections[0],
          subcategories[5],
          'Implement an environmental management system that conforms with a recognized international (e.g. ISO 14001) or local standard.',
          '2',
          'Please explain how you plan to use the results of the assessment.'
        ),
        new Question(
          '/construction/sustainability-construction/governance-management-49f1ad0/environmental-reporting/report-internally',
          sections[0],
          subcategories[6],
          'Report internally, including to top management, on key environmental issues, progress toward goals, and plans/needs to address shortfalls.',
          '3',
          'Comments'
        ),

        // (7) Construction / Procurement
        new Question(
          '/construction/sustainability-construction/procurement-5d484d5/procure-environmentally-prefereable-version/asphalt',
          sections[1],
          subcategories[7],
          'Asphalt',
          '4',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/procurement-5d484d5/measure/actions',
          sections[1],
          subcategories[8],
          'Measure success of actions and identify opportunities for improvement (Purchasing).',
          '5',
          'Comments'
        ),

        // (9) Contruction / Construction
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/electricity-greenhouse/use-renewable',
          sections[2],
          subcategories[9],
          'Use renewable energy to power site operations.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/vehicles-equipment/implement-policy',
          sections[2],
          subcategories[10],
          'Implement a policy to procure new vehicles or vehicle leases that optimize carbon efficiency and improve other key environmental performance areas compared to existing assets.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/other/minimize-trucking',
          sections[2],
          subcategories[11],
          'Minimize trucking and travel miles.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/general/measure-success',
          sections[2],
          subcategories[12],
          'Measure success of actions and identify opportunities for improvement.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/air-emissions/fuel-burning',
          sections[2],
          subcategories[13],
          'Ensure that fuel burning vehicles and equipment meet applicable limits for particulates, NOx, SOx and CO2.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/waste/develop',
          sections[2],
          subcategories[14],
          'Develop and implement a waste minimization and management plan for each work site.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/hazardous/store',
          sections[2],
          subcategories[15],
          'Store, handle and transport hazardous materials or equipment containing same to prevent leaks/spills to soil or water, and in compliance with applicable legal requirements.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/physical-footprint/create-site-access',
          sections[2],
          subcategories[16],
          'Create site access plans that minimize impacts on vegetation and impervious surfaces.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/construction-bbec85a/water/minimize',
          sections[2],
          subcategories[17],
          'Minimize water use in water-challenged or restricted areas.',
          '5',
          'Comments'
        ),

        // (18) Construction / Office & grounds / Electricity & gas
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/general',
          sections[3],
          subcategories[18],
          'When sourcing/ selecting new lease space, give meaningful weight to building energy efficiency in the evaluation process.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/energy-source',
          sections[3],
          subcategories[19],
          'Convert to using renewable energy.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/lighting',
          sections[3],
          subcategories[20],
          'Install high efficiency lighting.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/hvac',
          sections[3],
          subcategories[21],
          'Reduce the need for/use of HVAC systems.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/electronics',
          sections[3],
          subcategories[22],
          'Optimize data center energy efficiency.',
          '5',
          'Comments'
        ),

        // (23) Construction / Office & grounds / Fuel
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/fuel/company-vehicles',
          sections[3],
          subcategories[23],
          'Optimize fuel efficiency for existing fleet of conventional fuel vehicles.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/fuel/employee-transport',
          sections[3],
          subcategories[24],
          'Use video/web/tele-conferencing to minimize travel.',
          '5',
          'Comments'
        ),

        // (25) Construction / Office & grounds / Waste
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/waste/general',
          sections[3],
          subcategories[25],
          'When sourcing/ selecting new lease space, give meaningful weight to buildings with strong waste management infrastructure and services in the evaluation process.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing',
          sections[3],
          subcategories[26],
          'Minimize paper use.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure',
          sections[3],
          subcategories[27],
          'Appliances',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure/paper',
          sections[3],
          subcategories[28],
          'Office supplies',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/waste/waste-recycling',
          sections[3],
          subcategories[29],
          'Recycle all paper waste.',
          '5',
          'Comments'
        ),

        // (30) Construction / Office & grounds / Water
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/water/general',
          sections[3],
          subcategories[30],
          'When sourcing/ selecting new lease space, give meaningful weight to building water efficiency in the evaluation process.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/water/indoors',
          sections[3],
          subcategories[31],
          'Install high efficiency and water conserving plumbing components.',
          '5',
          'Comments'
        ),
        new Question(
          '/construction/sustainability-construction/officegrounds-e661fc0/water/outdoors',
          sections[3],
          subcategories[32],
          'Do not hose off outdoor areas.',
          '5',
          'Comments'
        ),
      ])
    }, DELAY)
  })
}

export function getAnswers() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        new Answer({
          questionId: 'qa1',
          questionType: '1',
          author: 'stephanie@tamarinsolutions.com',
          answers: [
            'yes',
            'Sed volutpat ligula ante. Integer accumsan sollicitudin interdum.',
          ],
        }),
        new Answer({
          questionId: 'qb2',
          questionType: '2',
          author: 'stephanie@tamarinsolutions.com',
          answers: [
            'most-yes',
            'Nam leo elit, bibendum id tincidunt ut, commodo malesuada felis.',
          ],
        }),
        new Answer({
          questionId: 'qc3',
          questionType: '3',
          author: 'stephanie@tamarinsolutions.com',
          answers: ['leading', ''],
        }),
        new Answer({
          questionId: 'qd4',
          questionType: '4',
          author: 'stephanie@tamarinsolutions.com',
          answers: [
            'Etiam aliquam eleifend magna sed iaculis. Suspendisse rhoncus maximus justo, ut pellentesque leo pharetra eget. In non orci lorem. Vivamus consequat turpis id cursus volutpat.',
          ],
        }),
        new Answer({
          questionId: 'qj10',
          questionType: '5',
          author: 'stephanie@tamarinsolutions.com',
          answers: ['14', 'ghg-emissions-generated', ''],
        }),
      ])
    }, DELAY)
  })
}
