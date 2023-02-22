/**

`chart.js` and `chartjs-plugin-annotation.js` do not have an ES5 distribution
by default. The annotation plugin though import chart.js and chart.js' helpers
in such a way that if we are not careful to install the whole chart.js module
in vendor/chart.js/ and update the modules path (resolveLoader.modules)
properly, we end-up with an ES6 code base in /static/cache/ (checked by
es-check in Makefile rule).
The annotation plugin also needs to be registered (done through
`chart-bundle.js`).
 */
const fs = require('fs');
const path = require('path');
const webpack = require('webpack');

var confPaths = JSON.parse(fs.readFileSync('webpack-conf-paths.json').toString())

module.exports = {
  mode: 'production',
  target: ['web', 'es5'],
  entry: {
      assess: [
          'js/chart-bundle.js',
          'js/djaodjin-survey-vue.js',
          'js/djaodjin-pages-vue.js',
          'js/assess-vue.js',
      ],
      editors: [
          'js/djaodjin-survey-vue.js',
          'js/djaodjin-pages-vue.js',
          'js/editors-vue.js',
      ],
      reporting: [
          'js/chart-bundle.js',
          'js/djaodjin-survey-vue.js',
          'js/reporting-vue.js',
      ],
  },
  module: {
    rules:[{
      test: /\.m?js$/,
      exclude: /(node_modules|bower_components)/,
      use: {
        loader: 'babel-loader',
        options: {
          presets: [['@babel/preset-env', {
              configPath: __dirname + "/package.json",
              debug: true,
              //useBuiltIns: 'usage',
              // XXX If we starts to use the polyfill, there is a problem
              // with Vue/extend in 'js/assess-vue.js'.
              corejs: "3.22"
          }]]
        }
      }
    }
    ]
  },
  output: {
      path: path.resolve(__dirname, 'htdocs/static/cache'),
      filename: '[name].js',
  },
  externals: {
    jQuery: 'jQuery',
  },
  plugins: [
      new webpack.LoaderOptionsPlugin({
       debug: true
      }),
      new webpack.ProvidePlugin({
          httpRequestMixin: [
              'js/djaodjin-resources-vue.js', 'httpRequestMixin'],
          itemMixin: ['js/djaodjin-resources-vue.js', 'itemMixin'],
          itemListMixin: ['js/djaodjin-resources-vue.js', 'itemListMixin'],
          paramsMixin: ['js/djaodjin-resources-vue.js', 'paramsMixin'],
          TypeAhead: ['js/djaodjin-resources-vue.js', 'TypeAhead'],
          practicesListMixin: [
              'js/djaopsp-resources-vue.js', 'practicesListMixin'],
      })
  ],
  resolve: {
      fallback: {
          "fs": require.resolve("fs"),
          "http": require.resolve("stream-http"),
          "https": require.resolve("https-browserify"),
          "querystring": require.resolve("querystring-es3"),
          "stream": require.resolve("stream-browserify"),
          "url": require.resolve("url/"),
          "util": require.resolve("util/")
      },
      modules: [path.resolve(__dirname, 'djaopsp/static/vendor')].concat(
          confPaths.node_modules),
  },
  resolveLoader: {
      modules: [path.resolve(__dirname, 'djaopsp/static/vendor')].concat(
          confPaths.node_modules),
  }
};
