export class ListNode {
  constructor(id, content) {
    this.id = id
    this.content = content
    this._prev = null
    this._next = null
  }

  get prev() {
    return this._prev
  }
  set prev(node) {
    this._prev = node
  }

  get next() {
    return this._next
  }
  set next(node) {
    this._next = node
  }

  debug() {
    console.log(this.content)
  }
}

/* Doubly-linked list */
export class LinkedList {
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

  getNext() {
    return this.head && this.head.next
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

  next() {
    return (this.head = this.getNext())
  }
}
