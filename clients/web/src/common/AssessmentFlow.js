export class AssessmentStep {
  constructor({
    key,
    text,
    path = null,
    introPath = null,
    isEditable = false,
  }) {
    this.key = key
    this.text = text
    this.path = path
    this.introPath = introPath
    this.isEditable = isEditable
    this.isComplete = false
  }

  canEdit() {
    return this.isComplete && this.isEditable
  }

  onClick(router, pathParams, isActive) {
    if (typeof isActive === 'boolean' && isActive) {
      if (this.introPath || this.path) {
        router.push({
          name: this.introPath || this.path,
          params: pathParams,
        })
      }
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
