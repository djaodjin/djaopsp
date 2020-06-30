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

/* Linked list for storing subcategories
 * Each new subcategory is appended to the end of the list
 */
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

  getFirst() {
    return this.head
  }

  getNext() {
    return this.current && this.current.next
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

  toArray() {
    const res = []
    let ptr = this.head
    while (ptr) {
      const subcategory = {
        id: ptr.id,
        content: { ...ptr.content },
        questions: ptr.questions.slice(),
      }
      res.push(subcategory)
      ptr = ptr.next
    }
    return res
  }

  next() {
    return (this.current = this.getNext())
  }

  reset() {
    this.current = this.head
  }
}
