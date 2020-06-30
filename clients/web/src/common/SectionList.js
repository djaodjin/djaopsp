import ListNode from './ListNode'
import LinkedList from './LinkedList'
import { SubcategoryNode, SubcategoryList } from './SubcategoryList'

class SectionNode extends ListNode {
  constructor(id, section) {
    super(id, section)
    this.subcategories = new SubcategoryList()
  }
  addSubcategory(question) {
    const subcategory = new SubcategoryNode(
      question.subcategory.id,
      question.subcategory
    )
    this.subcategories.add(subcategory, question)
  }
  debug() {
    super.debug()
    this.subcategories.debug()
  }
}

export class SectionList extends LinkedList {
  static createFromQuestions(questions) {
    const list = new SectionList()
    questions.forEach((q) => {
      const node = new SectionNode(q.section.id, q.section)
      list.add(node, q)
    })
    return list
  }

  add(node, question) {
    super.add(node, question, node.addSubcategory)
  }

  toArray() {
    const res = []
    if (!this.head) return res
    let current = this.head
    do {
      const section = {
        id: current.id,
        content: { ...current.content },
        subcategories: current.subcategories.toArray(),
      }
      res.push(section)
      current = current.next
    } while (current !== this.head)
    return res
  }
}
