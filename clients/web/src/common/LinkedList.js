export default class LinkedList {
  constructor() {
    this.head = null
  }

  add(node, question, onAddFn) {
    if (!this.head) {
      node.prev = node
      node.next = node
      if (typeof onAddFn === 'function') {
        onAddFn.call(node, question)
      }
      this.head = node
    } else {
      let current = this.head
      let exists = false
      do {
        if (node.id === current.id) {
          // Add question to existing node
          if (typeof onAddFn === 'function') {
            onAddFn.call(current, question)
          }
          exists = true
          break
        }
        current = current.next
      } while (current !== this.head)

      if (!exists) {
        const last = this.head.prev
        // Add new node
        node.prev = last
        node.next = this.head
        if (typeof onAddFn === 'function') {
          onAddFn.call(node, question)
        }
        last.next = node
        this.head.prev = node
      }
    }
  }

  debug() {
    if (!this.head) return
    let current = this.head
    do {
      current.debug()
      current = current.next
    } while (current !== this.head)
  }

  getCurrent() {
    return this.head
  }

  getNode(id) {
    if (!this.head) return null
    let current = this.head
    do {
      if (current.id === id) {
        return (this.head = current)
      }
      current = current.next
    } while (current !== this.head)
    return null
  }

  getNext() {
    return this.head && this.head.next
  }

  next() {
    return (this.head = this.getNext())
  }
}
