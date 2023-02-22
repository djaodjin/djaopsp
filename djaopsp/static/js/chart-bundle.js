import { Chart, registerables } from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation.js';

Chart.register(...registerables);
Chart.register(annotationPlugin);

if (typeof window !== 'undefined') {
  window.Chart = Chart;
}
