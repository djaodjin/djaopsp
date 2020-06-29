export const MAP_QUESTION_FORM_TYPES = {
  1: {
    component: 'FormQuestionRadio',
    options: [
      {
        text: 'Yes',
        value: 'yes',
      },
      {
        text: 'No',
        value: 'no',
      },
    ],
  },
  2: {
    component: 'FormQuestionRadio',
    options: [
      {
        text: 'Yes',
        value: 'yes',
      },
      {
        text: 'Mostly Yes',
        value: 'most-yes',
      },
      {
        text: 'Mostly No',
        value: 'most-no',
      },
      {
        text: 'No',
        value: 'no',
      },
      {
        text: 'Not Applicable',
        value: 'not-app',
      },
    ],
  },
  3: {
    component: 'FormQuestionRadio',
    options: [
      {
        text:
          "<b class='mr-1'>Initiating:</b>There is minimal management support",
        value: 'initiating',
      },
      {
        text:
          "<b class='mr-1'>Progresssing:</b>Support is visible and clearly demonstrated",
        value: 'progressing',
      },
      {
        text:
          "<b class='mr-1'>Optimizing:</b>Executive management reviews environmental performance, risks and opportunities, and endorses/sets goals",
        value: 'optimizing',
      },
      {
        text:
          "<b class='mr-1'>Leading:</b>The Board of Directors annually reviews environmental performance and sets or endorses goals",
        value: 'leading',
      },
      {
        text:
          "<b class='mr-1'>Transforming:</b>Executive management sponsors transformative change in industry sector and beyond",
        value: 'transforming',
      },
    ],
  },
  4: {
    component: 'FormQuestionTextarea',
  },
  5: {
    component: 'FormQuestionQuantity',
  },
}
