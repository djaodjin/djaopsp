const DELAY = 100

export function getResults({
  areas,
  practiceValue,
  practiceValueRange,
  implementationRange,
}) {
  console.log('Getting results ...')
  console.log('areas', areas)
  console.log('practiceValue', practiceValue)
  console.log('practiceValueRange', practiceValueRange)
  console.log('implementationRange', implementationRange)

  return new Promise((resolve, reject) => {
    setTimeout(() => {
      resolve([
        {
          id: '5f064350acc312eaf16cc091',
          section: {
            id: 123,
            name: 'Governance & Management',
          },
          subcategory: {
            id: '457',
            name: 'Material Selection',
          },
          text:
            'quis incididunt nisi ad ex nostrud duis non fugiat tempor cillum do excepteur reprehenderit pariatur incididunt mollit in labore aliquip Lorem tempor dolor ex qui occaecat reprehenderit adipisicing reprehenderit excepteur laborum amet sunt voluptate veniam eu nostrud do magna eiusmod',
          value: 3,
          implementation: 91,
        },
        {
          id: '5f064350190c345f16c04392',
          section: {
            id: 123,
            name: 'Governance & Management',
          },
          subcategory: {
            id: '346',
            name: 'General',
          },
          text:
            'officia sit occaecat do consequat ad ea nisi ut proident et in ad in eiusmod tempor ex laborum culpa esse magna sit ipsum anim nulla cillum culpa consectetur sint ex qui elit nostrud velit et irure dolore ex officia minim',
          value: 4,
          implementation: 53,
        },
        {
          id: '5f064350e60d001a14be2e9c',
          section: {
            id: 123,
            name: 'Governance & Management',
          },
          subcategory: {
            id: '457',
            name: 'Material Selection',
          },
          text:
            'officia tempor nisi deserunt in amet veniam incididunt exercitation tempor ad dolor consequat pariatur ut amet velit culpa sit occaecat tempor mollit fugiat mollit irure deserunt occaecat et ullamco aliquip eiusmod aliquip ad cupidatat elit fugiat officia cillum laboris dolore',
          value: 4,
          implementation: 14,
        },
        {
          id: '5f0643508582571636382d7b',
          section: {
            id: 123,
            name: 'Governance & Management',
          },
          subcategory: {
            id: '235',
            name: 'Management System Rigor',
          },
          text:
            'non voluptate officia laborum id velit est tempor ipsum culpa fugiat Lorem deserunt amet sint ipsum eu esse exercitation qui officia do minim laboris deserunt reprehenderit occaecat enim proident cillum exercitation sunt id commodo deserunt occaecat duis non ex est',
          value: 2,
          implementation: 24,
        },
        {
          id: '5f06435005953246a1ed1b15',
          section: {
            id: 123,
            name: 'Governance & Management',
          },
          subcategory: {
            id: '457',
            name: 'Material Selection',
          },
          text:
            'enim veniam incididunt aliquip officia quis consectetur veniam mollit culpa aliqua do cupidatat in proident dolor culpa cupidatat est duis est ullamco adipisicing enim ut exercitation velit sit occaecat ut labore elit voluptate ullamco consequat esse mollit nulla dolore id',
          value: 4,
          implementation: 32,
        },
        {
          id: '5f064432654d29d8c1c82f3d',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '124',
            name: 'Responsibility and Authority',
          },
          text:
            'elit anim veniam id irure est qui ipsum aute irure incididunt ipsum mollit eiusmod dolor duis consectetur Lorem eu qui cillum ullamco eu nisi enim est sit voluptate officia occaecat in sint deserunt elit aliqua amet irure dolore excepteur tempor',
          value: 1,
          implementation: 33,
        },
        {
          id: '5f0644325d07885e40b78374',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '235',
            name: 'Management System Rigor',
          },
          text:
            'ad esse reprehenderit eiusmod ipsum adipisicing mollit occaecat proident consequat eu est occaecat deserunt dolore sunt cillum quis ipsum amet ullamco exercitation amet eu incididunt enim dolor velit elit aliquip aute proident consectetur dolor dolore laboris qui sunt minim occaecat',
          value: 3,
          implementation: 66,
        },
        {
          id: '5f064432ace52ec55ef71433',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '235',
            name: 'Management System Rigor',
          },
          text:
            'elit sit sint reprehenderit esse qui esse Lorem ex culpa cillum cupidatat veniam id nisi consectetur cillum minim ut id ad ea veniam elit fugiat sint sunt nostrud pariatur commodo laborum et sit deserunt consectetur dolor do ad eiusmod cillum',
          value: 4,
          implementation: 56,
        },
        {
          id: '5f0644325e58ae41648f6727',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '235',
            name: 'Management System Rigor',
          },
          text:
            'occaecat laboris non laborum nostrud Lorem anim laboris officia in duis et cupidatat eiusmod esse proident laborum eiusmod adipisicing fugiat magna ex non ea labore ullamco laborum amet est est in proident exercitation nostrud Lorem voluptate minim consectetur esse magna',
          value: 3,
          implementation: 75,
        },
        {
          id: '5f064432417606deec1e3db5',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '346',
            name: 'General',
          },
          text:
            'exercitation anim ea ut est elit excepteur minim excepteur eu cillum qui excepteur sint sint ex dolore officia ut aute sint elit elit esse do et sint consectetur aliquip veniam sit aliquip aliquip consequat esse commodo laborum sint esse ut',
          value: 3,
          implementation: 83,
        },
        {
          id: '5f064432854e87d4aad02216',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '124',
            name: 'Responsibility and Authority',
          },
          text:
            'fugiat occaecat pariatur dolor consectetur officia fugiat nisi officia sint irure laborum tempor sit consectetur adipisicing anim mollit cillum officia amet cillum laborum id qui ut ad reprehenderit consequat voluptate est dolor mollit excepteur labore proident nostrud aliquip veniam nostrud',
          value: 1,
          implementation: 49,
        },
        {
          id: '5f06443228a98c0fdcebb3ce',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '457',
            name: 'Material Selection',
          },
          text:
            'exercitation laboris laborum anim qui amet nulla fugiat occaecat eu dolore ad officia excepteur non tempor tempor dolor aliquip cillum anim dolore irure minim commodo et fugiat cupidatat aute proident laborum dolore amet anim nisi est aliquip Lorem veniam fugiat',
          value: 1,
          implementation: 66,
        },
        {
          id: '5f064432e6c7e50cb30f7c22',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '124',
            name: 'Responsibility and Authority',
          },
          text:
            'amet adipisicing do minim sint officia qui fugiat occaecat et velit sint in pariatur dolore mollit cillum adipisicing incididunt magna laborum exercitation elit id qui reprehenderit amet cillum pariatur aliqua aute aliquip dolore culpa tempor fugiat quis deserunt deserunt culpa',
          value: 3,
          implementation: 49,
        },
        {
          id: '5f06443281f2cad3f0c780d7',
          section: {
            id: '345',
            name: 'Engineering & Design',
          },
          subcategory: {
            id: '124',
            name: 'Responsibility and Authority',
          },
          text:
            'in ut laborum et aliquip culpa id ex nulla veniam proident proident magna dolore Lorem occaecat do nostrud nostrud consectetur ipsum excepteur dolore exercitation voluptate exercitation voluptate non id incididunt tempor laboris nulla aliqua cupidatat commodo dolore Lorem laborum pariatur',
          value: 3,
          implementation: 48,
        },
      ])
    }, DELAY)
  })
}
