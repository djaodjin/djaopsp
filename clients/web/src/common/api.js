import Answer from './Answer'
import Assessment from './Assessment'
import Benchmark from './Benchmark'
import Organization from './Organization'
import OrganizationGroup from './OrganizationGroup'
import Question from './Question'
import Score from './Score'
import { getPracticeList } from './Practice'
import { getShareEntryList } from './ShareEntry'
import { VALID_ASSESSMENT_STEPS } from '../config/app'

const API_BASE_URL =
  process.env.VUE_APP_API_BASE_URL || `${process.env.BASE_URL}api`

class APIError extends Error {
  constructor(message) {
    super(message)
    this.name = 'APIError'
  }
}

function request(endpoint, { body, method, ...customConfig } = {}) {
  const url = `${API_BASE_URL}${endpoint}`
  const headers = { 'content-type': 'application/json' }
  const config = {
    method: method ? method : body ? 'POST' : 'GET',
    ...customConfig,
    headers: {
      ...headers,
      ...customConfig.headers,
    },
  }
  if (body) {
    config.body = JSON.stringify(body)
  }

  return fetch(url, config)
}

export async function advanceAssessment(assessment) {
  const { id, status, targets, practices, questions, answers } = assessment
  const currentStepIndex = VALID_ASSESSMENT_STEPS.indexOf(status)
  if (
    currentStepIndex >= 0 &&
    currentStepIndex < VALID_ASSESSMENT_STEPS.length - 1
  ) {
    const nextStep = VALID_ASSESSMENT_STEPS[currentStepIndex + 1]
    /* Example, updating answer for the default metric:

       POST /api/supplier-1/sample/f1e2e916eb494b90f9ff0a36982342/answers/metal/boxes-and-enclosures/management-basics/assessment/the-assessment-process-is-rigorous
      with body:
      {
        "measured": "yes"
      }

      Example adding a comment:

       POST /api/supplier-1/sample/f1e2e916eb494b90f9ff0a36982342/answers/metal/boxes-and-enclosures/management-basics/assessment/the-assessment-process-is-rigorous
      with body:
      {
        "metric": "freetext",
        "measured": "my comment",
      }

      See for previous implementation:
      https://github.com/djaodjin/envconnect/blob/d55b195fc16397712588e0358848b8423f8f32f2/envconnect/static/js/envconnect.js#L1260
     */
    const response = await request(`/assessments/${id}`, {
      method: 'PATCH',
      body: { status: nextStep },
    })
    if (!response.ok) throw new APIError(response.status)
    const data = await response.json()
    return new Assessment({
      ...data.assessment,
      targets,
      practices,
      questions,
      answers,
    })
  }
  return assessment
}

export async function createAssessment(payload) {
  /* POST /api/supplier-1/sample/
     with body:
     {
       "campaign": "assessment"
     }
   */
  const response = await request('/assessments', { body: payload })
  if (!response.ok) throw new APIError(response.status)
  const { assessment } = await response.json()
  return new Assessment(assessment)
}

export async function getAnswers(organizationId, assessmentId) {
  const response = await request(`/answers/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { answers } = await response.json()
  return answers.map((answer) => new Answer(answer))
}

export async function getAssessment(assessmentId) {
  /* The method must call:
     1. /api/{organizationId}/sample/{assessmentId}/
     to retrieve some details about the assesment itself like the
     `is_frozen` status.
     (See https://www.tspproject.org/docs/api#RetrieveSample)

     2. /api/{organizationId}/sample/{assessmentId}/answers/{path}/
     to retrieve answered and unanswered questions. The list of questions
     can be filtered down through a {path} prefix which typically is
     an industry segment.

     All targets are starting with the `{path}/targets/` prefix.

     Example:
     GET ${API_BASE_URL}/api/supplier-1/sample/f1e2e916eb494b90f9ff0a36982342/answers/metal/boxes-and-enclosures

{
  "count": 60,
  "next": null,
  "previous": null,
  "results": [
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/additional-information/additional-certifications",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-energy/energy-3rd-party-verified",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-energy/energy-measured-and-trended/energy-consumed",
        "default_metric": "energy-consumed",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-energy/energy-measured-and-trended/energy-measured-and-trended-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-energy/energy-performance-publicly-reported",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-3rd-party-verified",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/business-travel",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/capital-goods",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/downstream-leased-assets",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/downstream-transportation-and-distribution",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/employee-commuting",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/end-of-life-treatment-of-sold-products",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/franchise",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/fuel-and-energy-related-activities",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/investments",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/processing-of-sold-products",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/purchased-good-and-services",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/upstream-leased-assets",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/upstream-transportation-and-distribution",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/use-of-sold-products",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-breakdown-of-scope-3-emissions/waste-generated-in-operations",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-measured-and-trended-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-total-scope-1-emissions",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-total-scope-2-emissions",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-measured-and-trended/ghg-emissions-total-scope-3-emissions",
        "default_metric": "ghg-emissions-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-ghg-emissions/ghg-emissions-performance-publicly-reported",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-3rd-party-verified",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-measured-and-trended/waste-measured-and-trended-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-measured-and-trended/waste-total-hazardous-waste",
        "default_metric": "waste-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-measured-and-trended/waste-total-non-hazardous-waste",
        "default_metric": "waste-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-measured-and-trended/waste-total-waste-recycled",
        "default_metric": "waste-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-waste/waste-performance-publicly-reported",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-3rd-party-verified",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-measured-and-trended/water-measured-and-trended-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-measured-and-trended/water-total-water-discharged",
        "default_metric": "water-consumed",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-measured-and-trended/water-total-water-recycled-and-reused",
        "default_metric": "water-consumed",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-measured-and-trended/water-total-water-withdrawn",
        "default_metric": "water-consumed",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/environmental-metrics-and-targets/additional-water/water-performance-publicly-reported",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/general-information/employee-code-of-conduct",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/general-information/environmental-fines",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/general-information/fte-count",
        "default_metric": "employee-counted",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/general-information/gross-revenue",
        "default_metric": "revenue-generated",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/additional-questions/general-information/supplier-code-of-conduct",
        "default_metric": "yes-no",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/design/packaging-design",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/design/product-design",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/management-basics/assessment/the-assessment-process-is-rigorous",
        "default_metric": "assessment",
        "title": "The assessment process is rigorous and thorough*"
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/management-basics/general/hello/new-best-practice",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/management-basics/general/report-externally",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/production/energy-efficiency/process-heating/combustion/adjust-air-fuel-ratio",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/production/energy-efficiency/process-heating/combustion/reduce-combustion-air-flow-to-optimum",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": "assessment",
      "unit": null,
      "measured": "2",
      "created_at": "2016-05-01T00:36:19.448000Z",
      "collected_by": "steve",
      "question": {
        "path": "/metal/boxes-and-enclosures/production/energy-efficiency/process-heating/hot-water-system/recover-heat-from-hot-waste-water",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/production/energy-efficiency/process-heating/hot-water-system/reduce-hot-water-temperature-to-minimum-required",
        "default_metric": "assessment",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/energy-improvement-target/energy-improvement-target-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/energy-improvement-target/energy-target",
        "default_metric": "target-reduced",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/ghg-emissions-improvement-target/ghg-emissions-improvement-target-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/ghg-emissions-improvement-target/ghg-emissions-scope-1-emissions-target",
        "default_metric": "target-reduced",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/waste-improvement-target/hazardous-waste-target",
        "default_metric": "target-reduced",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/waste-improvement-target/waste-improvement-target-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/water-improvement-target/water-improvement-target-comments",
        "default_metric": "freetext",
        "title": ""
      }
    },
    {
      "metric": null,
      "unit": null,
      "measured": null,
      "created_at": null,
      "collected_by": null,
      "question": {
        "path": "/metal/boxes-and-enclosures/targets/water-improvement-target/water-withdrawn-target",
        "default_metric": "target-reduced",
        "title": ""
      }
    }
  ]
}
   */
  const response = await request(`/assessments/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const {
    assessment,
    targets,
    practices,
    questions,
    answers,
  } = await response.json()
  return new Assessment({
    ...assessment,
    targets,
    practices,
    questions,
    answers,
  })
}

export async function getBenchmarks(organizationId, assessmentId) {
  const response = await request(
    `/benchmarks/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { benchmarks } = await response.json()

  return benchmarks.map((benchmark) => {
    return new Benchmark(benchmark)
  })
}

export async function getIndustrySegments() {
  /* `GET /api/content/?q=public` for supplier organizations
     and `GET /api/content/?q=energy-procurement` for energy utility
     organizations.
   */
  const response = await request('/industries')
  if (!response.ok) throw new APIError(response.status)
  const { industries } = await response.json()
  return industries
}

export async function getPreviousIndustrySegments() {
  /* The information is available (and already retrieved in `getOrganization`)
     through /api/{organizationId}/benchmark/historical. (See `getOrganization`)
   */
  const response = await request('/previous-industries')
  if (!response.ok) throw new APIError(response.status)
  const { previousIndustries } = await response.json()
  return previousIndustries
}

export async function getOrganization(organizationId) {
  /* The code will call /api/profile/{organizationId}/ to retrieve information
     specified at:
    https://www.djaodjin.com/docs/djaoapp/latest/api/#RetrieveOrganizationDetail

     `id` (as an integer) is a concept internal to the database. All API
     endpoints always return a `slug` which is a unique identifier that
     can be used in URLs.

     There are no `name` field in the data returned. Instead there are
     `full_name` and `printable_name`, which is guarentee to be printable
     (in case full_name == "", printable_name defaults to the slug).
     The web client should use `printable_name` unless there is a specific
     use case for `full_name`.

     The current `assessments` are returned as part of the history API call
     /api/{organizationId}/benchmark/historical.
     (See https://www.tspproject.org/docs/api#RetrieveHistoricalScore)

     The "latest" field contains the slug for the "assessment" in progress
     and "segments" contains the segments the current assessment covers.

     The "results" field contains all previous assessment taken.

     Example:
     `GET /api/supplier-1/benchmark/historical/`

{
  "results": [
    {
      "key": "Jan 2017",
      "values": [
        [
          "Boxes & enclosures",
          90,
          "http://localhost:8000/envconnect/app/supplier-1/assess/f1e2e916eb494b90f9ff0a36982341/content/boxes-and-enclosures/"
        ]
      ],
      "created_at": "2017-01-01T00:00:00Z"
    },
    {
      "key": "Jul 2016",
      "values": [
        [
          "Boxes & enclosures",
          60,
          "http://localhost:8000/envconnect/app/supplier-1/assess/f1e2e916eb494b90f9ff0a36982340/content/boxes-and-enclosures/"
        ]
      ],
      "created_at": "2016-07-15T00:35:26.565000Z"
    }
  ],
  "latest": {
    "assessment": "f1e2e916eb494b90f9ff0a36982342",
    "segments": [
      {
        "title": "Boxes & enclosures",
        "path": "/metal/boxes-and-enclosures",
        "indent": 1
      }
    ]
  }
}
   */
  const response = await request(`/organizations/${organizationId}`)
  if (!response.ok) throw new APIError(response.status)
  const {
    organization: { id, name },
    assessments,
    ...rest
  } = await response.json()
  const organization = new Organization({
    id,
    name,
    assessments: assessments.map((a) => new Assessment({ ...a, ...rest })),
  })
  return organization
}

export async function getOrganizations() {
  const response = await request('/organizations')
  if (!response.ok) throw new APIError(response.status)
  const { organizationGroups, organizations } = await response.json()
  const groups = organizationGroups.map(
    ({ id, name }) => new OrganizationGroup({ id, name })
  )
  const individuals = organizations.map(
    ({ id, name }) => new Organization({ id, name })
  )
  return {
    groups,
    individuals,
  }
}

export async function getPractices(organizationId, assessmentId) {
  const response = await request(`/practices/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { practices, questions } = await response.json()
  return getPracticeList(practices, questions)
}

export async function getPracticeSearchResults(organizationId, assessmentId) {
  return getPractices(organizationId, assessmentId)
}

export async function getQuestions(organizationId, assessmentId) {
  const response = await request(`/questions/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { questions } = await response.json()
  return questions.map((question) => new Question(question))
}

export async function getScore(organizationId, assessmentId) {
  const response = await request(`/score/${organizationId}/${assessmentId}`)
  if (!response.ok) throw new APIError(response.status)
  const { score, benchmarks } = await response.json()
  return new Score({ ...score, benchmarks })
}

export async function getShareHistory(organizationId, assessmentId) {
  const response = await request(
    `/share-history/${organizationId}/${assessmentId}`
  )
  if (!response.ok) throw new APIError(response.status)
  const { shareEntries, organizations } = await response.json()
  const history = getShareEntryList(shareEntries, organizations)
  return history
}

export async function postTargets(organizationId, assessmentId, payload) {
  const response = await request(`/targets/${organizationId}/${assessmentId}`, {
    body: payload,
  })
  if (!response.ok) throw new APIError(response.status)
  const { assessment, targets } = await response.json()
  return new Assessment({ ...assessment, targets })
}

export async function putAnswer(answer) {
  const { organization, assessment, question } = answer
  const response = await request(
    `/answer/${organization}/${assessment}/${question}`,
    {
      method: 'PUT',
      body: answer,
    }
  )
  if (!response.ok) throw new APIError(response.status)
  const data = await response.json()
  return new Answer(data.answer)
}
