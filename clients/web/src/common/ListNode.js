export default class ListNode {
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
