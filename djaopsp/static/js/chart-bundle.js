import { Chart, registerables } from 'chart.js';
import * as helpers from 'chart.js/helpers';
import annotationPlugin from 'chartjs-plugin-annotation.js';
import ChartDataLabels from 'chartjs-plugin-datalabels.js';

Chart.helpers = helpers;
Chart.register(...registerables);
Chart.register(annotationPlugin);
Chart.register(ChartDataLabels);

if (typeof window !== 'undefined') {
  window.Chart = Chart;
}
