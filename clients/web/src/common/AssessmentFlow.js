export class AssessmentStep {
  constructor({ key, text, path, isEditable = false }) {
    this.key = key
    this.text = text
    this.path = path
    this.isEditable = isEditable
    this.isComplete = false
  }

  canEdit() {
    return this.isComplete && this.isEditable
  }

  onClick(router, { organization, assessment }, isActive) {
    if (typeof isActive === 'boolean' && isActive) {
      const route = router.options.routes.find(
        (route) => route.name === this.path
      )
      const routePath = route.path
        .replace(':org', organization.id)
        .replace(':id', assessment.id)
        .replace('*', assessment.industryPath.substr(1))
      router.push(routePath)
    }
  }
}

export class AssessmentFlow {
  constructor({ steps }) {
    this.steps = steps
    this.currentStep = 0
  }

  getStep() {
    return this.steps[this.currentStep]
  }

  getStepIndex() {
    return this.currentStep
  }

  nextStep() {
    if (this.currentStep < this.steps.length) {
      this.currentStep++
      this.updateComplete()
    }
    return this.getStep()
  }

  start(stepKey) {
    const index = this.steps.findIndex((s) => s.key === stepKey)
    if (index >= 0) {
      this.currentStep = index
    } else {
      console.error(`${stepKey} is not a valid step in the assessment flow`)
      this.currentStep = 0
    }
    this.updateComplete()
    return this.currentStep
  }

  updateComplete() {
    const len = this.steps.length
    for (let i = 0; i < len; i++) {
      if (i < this.currentStep) {
        this.steps[i].isComplete = true
      } else {
        this.steps[i].isComplete = false
      }
    }
  }

  reset() {
    this.currentStep = 0
    this.updateComplete()
  }
}
