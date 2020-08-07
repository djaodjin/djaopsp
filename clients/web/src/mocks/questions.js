import { DELAY } from './config'
import { getRandomInt } from '../common/utils'
import Answer from '../common/Answer'
import Subcategory from '../common/Subcategory'
import Question from '../common/Question'

// Set IDs to null to generate automatic unique IDs
const sections = [
  // Construction industry segment
  {
    name: 'Governance & Management',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/management-basics.png',
  },
  {
    name: 'Procurement',
    path: '/construction/sustainability-construction/procurement-5d484d5',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/gas-procurement.png',
  },
  {
    name: 'Construction',
    path: '/construction/sustainability-construction/construction-bbec85a',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/construction.png',
  },
  {
    name: 'Office/grounds',
    path: '/construction/sustainability-construction/officegrounds-e661fc0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/office-space-only.png',
  },

  // Boxes & enclosures industry segment
  {
    name: 'Governance & Management',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/management-basics',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/management-basics.png',
  },
  {
    name: 'Design',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/design',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/design.png',
  },
  {
    name: 'Production',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/production',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/production.png',
  },
  {
    name: 'Distribution',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/distribution',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/distribution.png',
  },
  {
    name: 'End of Life',
    path:
      '/metal/boxes-and-enclosures/sustainability-boxes-and-enclosures/end-of-life',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/end-of-life.png',
  },
]

// Set IDs to null to generate automatic unique IDs
const subcategories = [
  // (0) Construction / Management & governance
  {
    name: 'Environmental policy',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy',
  },
  {
    name: 'Responsability & authority',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority',
  },
  {
    name: 'Environmental assessment',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment',
  },
  {
    name: 'Leadership engagement & commitment',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment',
  },
  {
    name: 'Controls, improvement plans & measurement',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/controls-improvement-plans-measurement',
  },
  {
    name: 'Management system rigor',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/management-system-rigor',
  },
  {
    name: 'Environmental reporting',
    path:
      '/construction/sustainability-construction/governance-management-49f1ad0/environmental-reporting',
  },

  // (7) Construction / Procurement
  {
    name: 'Procure environmentally prefereable version of the following:',
    path:
      '/construction/sustainability-construction/procurement-5d484d5/procure-environmentally-prefereable-version',
  },
  {
    name: 'Measure',
    path: '/construction/sustainability-construction/construction-bbec85a/',
  },

  // (9) Contruction / Construction
  {
    name: 'Electricity & greenhouse gas emissions',
    path:
      '/construction/sustainability-construction/construction-bbec85a/electricity-greenhouse',
  },
  {
    name: 'Vehicles & equipment',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/vehicles-equipment',
  },
  {
    name: 'Other',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/other',
  },
  {
    name: 'General',
    path:
      '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/general',
  },
  {
    name: 'Air emissions (NOX, SOX, particules, CO2)',
    path:
      '/construction/sustainability-construction/construction-bbec85a/air-emissions',
  },
  {
    name: 'Waste',
    path:
      '/construction/sustainability-construction/construction-bbec85a/waste',
  },
  {
    name: 'Hazardous chemical subsctances',
    path:
      '/construction/sustainability-construction/construction-bbec85a/hazardous',
  },
  {
    name: 'Physical footprint',
    path:
      '/construction/sustainability-construction/construction-bbec85a/physical-footprint',
  },
  {
    name: 'Water',
    path:
      '/construction/sustainability-construction/construction-bbec85a/water',
  },

  // (18) Construction / Office & grounds / Electricity & gas
  {
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/general',
  },
  {
    name: 'Energy source',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/energy-source',
  },
  {
    name: 'Lighting',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/lighting',
  },
  {
    name: 'HVAC',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/hvac',
  },
  {
    name: 'Electronics, equipment & appliances',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/electronics',
  },

  // (23) Construction / Office & grounds / Fuel
  {
    name: 'Company vehicles',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/fuel/company-vehicles',
  },
  {
    name: 'Employee transport & travel',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/fuel/employee-transport',
  },

  // (25) Construction / Office & grounds / Waste
  {
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/general',
  },
  {
    name: 'Purchasing practices to avoid pollution/waste',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing',
  },
  {
    name: 'Procure environmentally preferable versions of the following:',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure',
  },
  {
    name: 'Paper',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure/paper',
  },
  {
    name: 'Waste recycling and disposal',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/waste/waste-recycling',
  },

  // (30) Construction / Office & grounds / Water
  {
    name: 'General',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/general',
  },
  {
    name: 'Indoors',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/indoors',
  },
  {
    name: 'Outdoors',
    path:
      '/construction/sustainability-construction/officegrounds-e661fc0/water/outdoors',
  },
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
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-adequate-policy',
          section: sections[0],
          subcategory: subcategories[0],
          text:
            'Have adequate policy level commitments, and be internally and externally communicated.',
          type: 1,
          previousAnswers: [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-adequate-policy',
              questionType: '1',
              author: 'michael@tamarinsolutions.com',
              answers: ['yes'],
            }),
          ],
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-highest-level-leadership',
          section: sections[0],
          subcategory: subcategories[0],
          text:
            'Have the highest level of leadership at the organization sign the policy.',
          type: 2,
          placeholder:
            'Please explain how you plan to use the results of the assessment.',
          previousAnswers: [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-policy/have-highest-level-leadership',
              questionType: '2',
              author: 'michael@tamarinsolutions.com',
              answers: ['most-no'],
            }),
          ],
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority/assign-formal-responsability',
          section: sections[0],
          subcategory: subcategories[1],
          text:
            'Assign formal responsibility for directing and overseeing environmental performance to top/executive management.',
          type: 3,
          optional: true,
          previousAnswers: [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/responsability-authority/assign-formal-responsability',
              questionType: '3',
              author: 'michael@tamarinsolutions.com',
              answers: ['leading'],
            }),
          ],
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment/conduct-assessment',
          section: sections[0],
          subcategory: subcategories[2],
          text:
            'Conduct a systematic, rigorous assessment to identify and prioritize material environmental impacts, issues and type: pportunities.',
          type: 4,
          optional: true,
          previousAnswers: [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/environmental-assessment/conduct-assessment',
              questionType: '4',
              author: 'michael@tamarinsolutions.com',
              answers: [
                'Nullam gravida leo vel libero imperdiet rhoncus tincidunt at enim. Sed vel enim ac leo mattis dapibus. Suspendisse ligula nisl, elementum sit amet velit in, tincidunt commodo sapien. In tincidunt at felis ac laoreet. Phasellus blandit velit in sem cursus tincidunt. Sed in tortor eget mauris rutrum eleifend. Sed quis dolor rutrum, ultrices eros ut, blandit turpis.',
              ],
            }),
          ],
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment/give-priorities',
          section: sections[0],
          subcategory: subcategories[3],
          text:
            "Give the priorities identified in the materiality assessment meaningful inclusion in the organization's goal setting and practical planning.",
          type: 5,
          optional: true,
          previousAnswers: [
            new Answer({
              questionId:
                '/construction/sustainability-construction/governance-management-49f1ad0/leadership-engagement-commitment/give-priorities',
              questionType: '5',
              author: 'michael@tamarinsolutions.com',
              answers: ['14', 'ghg-emissions-generated'],
            }),
          ],
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/controls-improvement-plans-measurement/implement-controls',
          section: sections[0],
          subcategory: subcategories[4],
          text:
            'Implement controls, improvement plans and measurement processes to address all priorities identified in the assessment.',
          type: 1,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/management-system-rigor/implement-environmental-management',
          section: sections[0],
          subcategory: subcategories[5],
          text:
            'Implement an environmental management system that conforms with a recognized international (e.g. ISO 14001) or local standard.',
          type: 2,
          placeholder:
            'Please explain how you plan to use the results of the assessment.',
        }),
        new Question({
          path:
            '/construction/sustainability-construction/governance-management-49f1ad0/environmental-reporting/report-internally',
          section: sections[0],
          subcategory: subcategories[6],
          text:
            'Report internally, including to top management, on key environmental issues, progress toward goals, and plans/needs to type: ddress shortfalls.',
          type: 3,
        }),

        // (7) Construction / Procurement
        new Question({
          path:
            '/construction/sustainability-construction/procurement-5d484d5/procure-environmentally-prefereable-version/asphalt',
          section: sections[1],
          subcategory: subcategories[7],
          text: 'Asphalt',
          type: 4,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/procurement-5d484d5/measure/actions',
          section: sections[1],
          subcategory: subcategories[8],
          text:
            'Measure success of actions and identify opportunities for improvement (Purchasing).',
          type: 5,
        }),

        // (9) Contruction / Construction
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/electricity-greenhouse/use-renewable',
          section: sections[2],
          subcategory: subcategories[9],
          text: 'Use renewable energy to power site operations.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/vehicles-equipment/implement-policy',
          section: sections[2],
          subcategory: subcategories[10],
          text:
            'Implement a policy to procure new vehicles or vehicle leases that optimize carbon efficiency and improve other key environmental performance areas compared to existing assets.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/other/minimize-trucking',
          section: sections[2],
          subcategory: subcategories[11],
          text: 'Minimize trucking and travel miles.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/fuel-greenhouse/general/measure-success',
          section: sections[2],
          subcategory: subcategories[12],
          text:
            'Measure success of actions and identify opportunities for improvement.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/air-emissions/fuel-burning',
          section: sections[2],
          subcategory: subcategories[13],
          text:
            'Ensure that fuel burning vehicles and equipment meet applicable limits for particulates, NOx, SOx and CO2.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/waste/develop',
          section: sections[2],
          subcategory: subcategories[14],
          text:
            'Develop and implement a waste minimization and management plan for each work site.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/hazardous/store',
          section: sections[2],
          subcategory: subcategories[15],
          text:
            'Store, handle and transport hazardous materials or equipment containing same to prevent leaks/spills to soil or water, and in compliance with applicable legal requirements.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/physical-footprint/create-site-access',
          section: sections[2],
          subcategory: subcategories[16],
          text:
            'Create site access plans that minimize impacts on vegetation and impervious surfaces.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/construction-bbec85a/water/minimize',
          section: sections[2],
          subcategory: subcategories[17],
          text: 'Minimize water use in water-challenged or restricted areas.',
          type: 5,
        }),

        // (18) Construction / Office & grounds / Electricity & gas
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/general',
          section: sections[3],
          subcategory: subcategories[18],
          text:
            'When sourcing/ selecting new lease space, give meaningful weight to building energy efficiency in the evaluation process.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/energy-source',
          section: sections[3],
          subcategory: subcategories[19],
          text: 'Convert to using renewable energy.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/lighting',
          section: sections[3],
          subcategory: subcategories[20],
          text: 'Install high efficiency lighting.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/hvac',
          section: sections[3],
          subcategory: subcategories[21],
          text: 'Reduce the need for/use of HVAC systems.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/electricity-gas/electronics',
          section: sections[3],
          subcategory: subcategories[22],
          text: 'Optimize data center energy efficiency.',
          type: 5,
        }),

        // (23) Construction / Office & grounds / Fuel
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/fuel/company-vehicles',
          section: sections[3],
          subcategory: subcategories[23],
          text:
            'Optimize fuel efficiency for existing fleet of conventional fuel vehicles.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/fuel/employee-transport',
          section: sections[3],
          subcategory: subcategories[24],
          text: 'Use video/web/tele-conferencing to minimize travel.',
          type: 5,
        }),

        // (25) Construction / Office & grounds / Waste
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/waste/general',
          section: sections[3],
          subcategory: subcategories[25],
          text:
            'When sourcing/selecting new lease space, give meaningful weight to buildings with strong waste management infrastructure and services in the evaluation process.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing',
          section: sections[3],
          subcategory: subcategories[26],
          text: 'Minimize paper use.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure',
          section: sections[3],
          subcategory: subcategories[27],
          text: 'Appliances',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/waste/purchasing/procure/paper',
          section: sections[3],
          subcategory: subcategories[28],
          text: 'Office supplies',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/waste/waste-recycling',
          section: sections[3],
          subcategory: subcategories[29],
          text: 'Recycle all paper waste.',
          type: 5,
        }),

        // (30) Construction / Office & grounds / Water
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/water/general',
          section: sections[3],
          subcategory: subcategories[30],
          text:
            'When sourcing/ selecting new lease space, give meaningful weight to building water efficiency in the evaluation process.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/water/indoors',
          section: sections[3],
          subcategory: subcategories[31],
          text:
            'Install high efficiency and water conserving plumbing components.',
          type: 5,
        }),
        new Question({
          path:
            '/construction/sustainability-construction/officegrounds-e661fc0/water/outdoors',
          section: sections[3],
          subcategory: subcategories[32],
          text: 'Do not hose off outdoor areas.',
          type: 5,
        }),
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
