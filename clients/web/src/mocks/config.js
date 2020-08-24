export const NUM_BENCHMARKS = 6

export const BENCHMARK_MAX_COMPANIES = 30

// TODO: Remove this if there is no relationship between industry and assessment
export const INDUSTRIES = [
  {
    name: 'Architectural Design',
    path: 'sustainability-architecture-design',
  },
  {
    name: 'Aviation Services',
    path: 'sustainability-aviation-services',
  },
  {
    name: 'Construction',
    path: 'sustainability-construction',
  },
  {
    name: 'Consulting/Advisory Services',
    path: 'sustainability-consulting',
  },
  {
    name: 'Distribution/Logistics & Shipping',
    path: 'sustainability-distribution-industry',
  },
  {
    name: 'Energy efficiency contracting',
    path: 'sustainability-energy-efficiency-contracting',
  },
  {
    name: 'Freight & Shipping',
    path: 'sustainability-freight-and-shipping',
  },
]

export const INDUSTRY_SECTIONS = [
  {
    name: 'Governance & Management',
    path: '/governance-management-49f1ad0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/management-basics.png',
    subcategories: [
      {
        name: 'Environmental policy',
        path: '/governance-management-49f1ad0/environmental-policy',
      },
      {
        name: 'Responsability & authority',
        path: '/governance-management-49f1ad0/responsability-authority',
      },
      {
        name: 'Environmental assessment',
        path: '/governance-management-49f1ad0/environmental-assessment',
      },
      {
        name: 'Leadership engagement & commitment',
        path: '/governance-management-49f1ad0/leadership-engagement-commitment',
      },
      {
        name: 'Controls, improvement plans & measurement',
        path:
          '/governance-management-49f1ad0/controls-improvement-plans-measurement',
      },
      {
        name: 'Management system rigor',
        path: '/governance-management-49f1ad0/management-system-rigor',
      },
      {
        name: 'Environmental reporting',
        path: '/governance-management-49f1ad0/environmental-reporting',
      },
    ],
  },
  {
    name: 'Procurement',
    path: '/procurement-5d484d5',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/gas-procurement.png',
    subcategories: [
      {
        name: 'Procure environmentally prefereable version of the following:',
        path:
          '/procurement-5d484d5/procure-environmentally-prefereable-version',
      },
      {
        name: 'Measure',
        path: '/procurement-5d484d5/measure',
      },
    ],
  },
  {
    name: 'Construction',
    path: '/construction-bbec85a',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/construction.png',
    subcategories: [
      {
        name: 'Electricity & greenhouse gas emissions',
        path: '/construction-bbec85a/electricity-greenhouse',
      },
      {
        name: 'Vehicles & equipment',
        path: '/construction-bbec85a/fuel-greenhouse/vehicles-equipment',
      },
      {
        name: 'Other',
        path: '/construction-bbec85a/fuel-greenhouse/other',
      },
      {
        name: 'General',
        path: '/construction-bbec85a/fuel-greenhouse/general',
      },
      {
        name: 'Air emissions (NOX, SOX, particules, CO2)',
        path: '/construction-bbec85a/air-emissions',
      },
      {
        name: 'Waste',
        path: '/construction-bbec85a/waste',
      },
      {
        name: 'Hazardous chemical subsctances',
        path: '/construction-bbec85a/hazardous',
      },
      {
        name: 'Physical footprint',
        path: '/construction-bbec85a/physical-footprint',
      },
      {
        name: 'Water',
        path: '/construction-bbec85a/water',
      },
    ],
  },
  {
    name: 'Office/grounds',
    path: '/officegrounds-e661fc0',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/office-space-only.png',
    subcategories: [
      {
        name: 'General',
        path: '/officegrounds-e661fc0/electricity-gas/general',
      },
      {
        name: 'Energy source',
        path: '/officegrounds-e661fc0/electricity-gas/energy-source',
      },
      {
        name: 'Lighting',
        path: '/officegrounds-e661fc0/electricity-gas/lighting',
      },
      {
        name: 'HVAC',
        path: '/officegrounds-e661fc0/electricity-gas/hvac',
      },
      {
        name: 'Electronics, equipment & appliances',
        path: '/officegrounds-e661fc0/electricity-gas/electronics',
      },
    ],
  },
  {
    name: 'Design',
    path: '/design',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/design.png',
    subcategories: [
      {
        name: 'Company vehicles',
        path: '/design-e661fc0/fuel/company-vehicles',
      },
      {
        name: 'Employee transport & travel',
        path: '/design-e661fc0/fuel/employee-transport',
      },
    ],
  },
  {
    name: 'Production',
    path: '/production',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/production.png',
    subcategories: [
      {
        name: 'General',
        path: '/production-e661fc0/waste/general',
      },
      {
        name: 'Purchasing practices to avoid pollution/waste',
        path: '/production-e661fc0/waste/purchasing',
      },
      {
        name: 'Procure environmentally preferable versions of the following:',
        path: '/production-e661fc0/waste/purchasing/procure',
      },
      {
        name: 'Paper',
        path: '/production-e661fc0/waste/purchasing/procure/paper',
      },
      {
        name: 'Waste recycling and disposal',
        path: '/production-e661fc0/waste/waste-recycling',
      },
    ],
  },
  {
    name: 'Distribution',
    path: '/distribution',
    iconPath: 'https://envconnect.s3.amazonaws.com/media/distribution.png',
    subcategories: [
      {
        name: 'General',
        path: '/distribution-e661fc0/water/general',
      },
      {
        name: 'Indoors',
        path: '/distribution-e661fc0/water/indoors',
      },
      {
        name: 'Outdoors',
        path: '/distribution-e661fc0/water/outdoors',
      },
    ],
  },
]
