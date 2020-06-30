import ListNode from './ListNode'

export class SubcategoryNode extends ListNode {
  constructor(id, subcategory) {
    super(id, subcategory)
    this.questions = []
  }
  addQuestion(question) {
    this.questions.push(question)
  }
  debug() {
    super.debug()
    console.log(this.questions)
  }
}

export class SubcategoryList {
  constructor() {
    this.head = null
    this.current = null
  }

  add(node, question) {
    if (!this.head) {
      node.addQuestion(question)
      this.head = node
      this.current = node
    } else {
      let ptr = this.head
      let exists = false

      if (node.id === ptr.id) {
        // Add question to existing node
        ptr.addQuestion(question)
        exists = true
      }

      while (ptr.next) {
        ptr = ptr.next
        if (node.id === ptr.id) {
          // Add question to existing node
          ptr.addQuestion(question)
          exists = true
          break
        }
      }

      if (!exists) {
        node.addQuestion(question)
        ptr.next = node
      }
    }
  }

  debug() {
    let ptr = this.head
    while (ptr) {
      ptr.debug()
      ptr = ptr.next
    }
  }

  getCurrent() {
    return this.current
  }

  getNode(id) {
    let ptr = this.head
    while (ptr) {
      if (ptr.id === id) {
        return (this.current = ptr)
      }
      ptr = ptr.next
    }
    return null
  }

  getNext() {
    return this.current && this.current.next
  }

  next() {
    return (this.current = this.getNext())
  }

  reset() {
    this.current = this.head
  }
}
