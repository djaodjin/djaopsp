import { DELAY } from './config'
import { getRandomInt } from '../common/utils'
import Answer from '../common/Answer'
import Section from '../common/Section'
import Subcategory from '../common/Subcategory'
import Question from '../common/Question'

// Set IDs to null to generate automatic unique IDs
const sections = [
  // Construction industry segment
  new Section({
    name: 'Governance & Management',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/management-basics.png',
  }),
  new Section({
    name: 'Procurement',
    path: '/construction/sustainability-construction/procurement-5d484d5',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/gas-procurement.png',
  }),
  new Section({
    name: 'Construction',
    path: '/construction/sustainability-construction/construction-bbec85a',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/construction.png',
  }),
  new Section({
    name: 'Office/grounds',
    path: '/construction/sustainability-construction/officegrounds-e661fc0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/office-space-only.png',
  }),

  // Boxes & enclosures industry segment
  new Section({
    name: 'Governance & Management',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/management-basics',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/management-basics.png',
  }),
  new Section({
    name: 'Design',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/design',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/design.png',
  }),
  new Section({
    name: 'Production',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/production',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/production.png',
  }),
  new Section({
    name: 'Distribution',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/distribution',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/distribution.png',
  }),
  new Section({
    name: 'End of Life',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/end-of-life',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/end-of-life.png',
  }),
]

// Set IDs to null to generate automatic unique IDs
const subcategories = [
  // (0) Construction / Management & governance
  new Subcategory({
    name: 'Environmental policy',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy',
  }),
  new Subcategory({
    name: 'Responsability & authority',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority',
  }),
  new Subcategory({
    name: 'Environmental assessment',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment',
  }),
  new Subcategory({
    name: 'Leadership engagement & commitment',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment',
  }),
  new Subcategory({
    name: 'Controls, improvement plans & measurement',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/controls-improvement-plans-measurement',
  }),
  new Subcategory({
    name: 'Management system rigor',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/management-system-rigor',
  }),
  new Subcategory({
    name: 'Environmental reporting',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-reporting',
  }),

  // (7) Construction / Procurement
  new Subcategory({
    name: 'Procure environmentally prefereable version of the following:',
    path:
      '/construction/sustainability-construction/procurement-5d484d5/procure-environmentally-prefereable-version',
  }),
  new Subcategory({
    name: 'Measure',
    path: '/construction/sustainability-construction/construction-bbec85a/',
  }),

  // (9) Contruction / Construction
  new Subcategory({
    name: 'Electricity & greenhouse gas emissions',
    path:
      '/construction/sustainability-construction/construction-bbec85a/electricity-greenhouse',
  }),
  new Subcategory({
    name: 'Vehicles & equipment',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/vehicles-equipment',
  }),
  new Subcategory({
    name: 'Other',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/other',
  }),
  new Subcategory({
    name: 'General',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/general',
  }),
  new Subcategory({
    name: 'Air emissions (NOX, SOX, particules, CO2)',
    path:
      '/construction/sustainability-construction/construction-bbec85a/air-emissions',
  }),
  new Subcategory({
    name: 'Waste',
    path:
      '/construction/sustainability-construction/construction-bbec85a/waste',
  }),
  new Subcategory({
    name: 'Hazardous chemical subsctances',
    path:
      '/construction/sustainability-construction/construction-bbec85a/hazardous',
  }),
  new Subcategory({
    name: 'Physical footprint',
    path:
      '/construction/sustainability-construction/construction-bbec85a/physical-footprint',
  }),
  new Subcategory({
    name: 'Water',
    path:
      '/construction/sustainability-construction/construction-bbec85a/water',
  }),

  // (18) Construction / Office & grounds / Electricity & gas
  new Subcategory({
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/general',
  }),
  new Subcategory({
    name: 'Energy source',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/energy-source',
  }),
  new Subcategory({
    name: 'Lighting',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/lighting',
  }),
  new Subcategory({
    name: 'HVAC',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/hvac',
  }),
  new Subcategory({
    name: 'Electronics, equipment & appliances',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/electronics',
  }),

  // (23) Construction / Office & grounds / Fuel
  new Subcategory({
    name: 'Company vehicles',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/fuel/company-vehicles',
  }),
  new Subcategory({
    name: 'Employee transport & travel',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/fuel/employee-transport',
  }),

  // (25) Construction / Office & grounds / Waste
  new Subcategory({
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/general',
  }),
  new Subcategory({
    name: 'Purchasing practices to avoid pollution/waste',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing',
  }),
  new Subcategory({
    name: 'Procure environmentally preferable versions of the following:',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure',
  }),
  new Subcategory({
    name: 'Paper',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure/paper',
  }),
  new Subcategory({
    name: 'Waste recycling and disposal',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/waste-recycling',
  }),

  // (30) Construction / Office & grounds / Water
  new Subcategory({
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/general',
  }),
  new Subcategory({
    name: 'Indoors',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/indoors',
  }),
  new Subcategory({
    name: 'Outdoors',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/outdoors',
  }),
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
