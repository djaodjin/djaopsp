import { DELAY } from './config'
import { PRACTICE_VALUES, PRACTICE_VALUE_CATEGORIES } from '@/config/app'
import { getRandomInt } from '../common/utils'
import { getRandomSection, getRandomSubcategory } from './questions'
import Practice from '../common/Practice'
import Question from '../common/Question'

function getImplementationRate() {
  return getRandomInt(10, 95)
}

function getPracticeValues() {
  const MIN_PRACTICE_VALUE = PRACTICE_VALUES[0].value
  const MAX_PRACTICE_VALUE = PRACTICE_VALUES[PRACTICE_VALUES.length - 1].value

  return PRACTICE_VALUE_CATEGORIES.reduce((acc, category) => {
    acc[category.value] = getRandomInt(
      MIN_PRACTICE_VALUE,
      MAX_PRACTICE_VALUE + 1
    )
    return acc
  }, {})
}

export function getResults(formValues) {
  console.log(formValues)

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        new Practice({
          id: 'pa1',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'quis incididunt nisi ad ex nostrud duis non fugiat tempor cillum do excepteur reprehenderit pariatur incididunt mollit in labore aliquip Lorem tempor dolor ex qui occaecat reprehenderit adipisicing reprehenderit excepteur laborum amet sunt voluptate veniam eu nostrud do magna eiusmod?',
            '1',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pb2',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'officia sit occaecat do consequat ad ea nisi ut proident et in ad in eiusmod tempor ex laborum culpa esse magna sit ipsum anim nulla cillum culpa consectetur sint ex qui elit nostrud velit et irure dolore ex officia minim.',
            '2',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pc3',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'officia tempor nisi deserunt in amet veniam incididunt exercitation tempor ad dolor consequat pariatur ut amet velit culpa sit occaecat tempor mollit fugiat mollit irure deserunt occaecat et ullamco aliquip eiusmod aliquip ad cupidatat elit fugiat officia cillum laboris dolore',
            '3',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pd4',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'non voluptate officia laborum id velit est tempor ipsum culpa fugiat Lorem deserunt amet sint ipsum eu esse exercitation qui officia do minim laboris deserunt reprehenderit occaecat enim proident cillum exercitation sunt id commodo deserunt occaecat duis non ex est',
            '4',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pe5',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'enim veniam incididunt aliquip officia quis consectetur veniam mollit culpa aliqua do cupidatat in proident dolor culpa cupidatat est duis est ullamco adipisicing enim ut exercitation velit sit occaecat ut labore elit voluptate ullamco consequat esse mollit nulla dolore id',
            '5',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pf6',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'elit anim veniam id irure est qui ipsum aute irure incididunt ipsum mollit eiusmod dolor duis consectetur Lorem eu qui cillum ullamco eu nisi enim est sit voluptate officia occaecat in sint deserunt elit aliqua amet irure dolore excepteur tempor',
            '1',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pg7',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'ad esse reprehenderit eiusmod ipsum adipisicing mollit occaecat proident consequat eu est occaecat deserunt dolore sunt cillum quis ipsum amet ullamco exercitation amet eu incididunt enim dolor velit elit aliquip aute proident consectetur dolor dolore laboris qui sunt minim occaecat',
            '2',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'ph8',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'elit sit sint reprehenderit esse qui esse Lorem ex culpa cillum cupidatat veniam id nisi consectetur cillum minim ut id ad ea veniam elit fugiat sint sunt nostrud pariatur commodo laborum et sit deserunt consectetur dolor do ad eiusmod cillum',
            '3',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pi9',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'occaecat laboris non laborum nostrud Lorem anim laboris officia in duis et cupidatat eiusmod esse proident laborum eiusmod adipisicing fugiat magna ex non ea labore ullamco laborum amet est est in proident exercitation nostrud Lorem voluptate minim consectetur esse magna',
            '4',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pj10',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'exercitation anim ea ut est elit excepteur minim excepteur eu cillum qui excepteur sint sint ex dolore officia ut aute sint elit elit esse do et sint consectetur aliquip veniam sit aliquip aliquip consequat esse commodo laborum sint esse ut',
            '5',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pk11',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'fugiat occaecat pariatur dolor consectetur officia fugiat nisi officia sint irure laborum tempor sit consectetur adipisicing anim mollit cillum officia amet cillum laborum id qui ut ad reprehenderit consequat voluptate est dolor mollit excepteur labore proident nostrud aliquip veniam nostrud',
            '1',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pl12',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'exercitation laboris laborum anim qui amet nulla fugiat occaecat eu dolore ad officia excepteur non tempor tempor dolor aliquip cillum anim dolore irure minim commodo et fugiat cupidatat aute proident laborum dolore amet anim nisi est aliquip Lorem veniam fugiat',
            '2',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pm13',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'amet adipisicing do minim sint officia qui fugiat occaecat et velit sint in pariatur dolore mollit cillum adipisicing incididunt magna laborum exercitation elit id qui reprehenderit amet cillum pariatur aliqua aute aliquip dolore culpa tempor fugiat quis deserunt deserunt culpa',
            '3',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
        new Practice({
          id: 'pn14',
          question: new Question(
            null,
            getRandomSection(),
            getRandomSubcategory(),
            'amet adipisicing do minim sint officia qui fugiat occaecat et velit sint in pariatur dolore mollit cillum adipisicing incididunt magna laborum exercitation elit id qui reprehenderit amet cillum pariatur aliqua aute aliquip dolore culpa tempor fugiat quis deserunt deserunt culpa',
            '4',
            'Comments'
          ),
          ...getPracticeValues(),
          implementationRate: getImplementationRate(),
        }),
      ])
    }, DELAY)
  })
}
