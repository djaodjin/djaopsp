import { Chart, registerables } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation.js';
import ChartDataLabels from 'chartjs-plugin-datalabels.js';

Chart.register(...registerables);
Chart.register(annotationPlugin);
Chart.register(ChartDataLabels);

if (typeof window !== 'undefined') {
  window.Chart = Chart;
}
