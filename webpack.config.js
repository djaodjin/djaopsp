const fs = require('fs');
const path = require('path');
const webpack = require('webpack');

var confPaths = JSON.parse(fs.readFileSync('webpack-conf-paths.json').toString())

module.exports = {
  mode: 'production',
  target: ['web', 'es5'],
  entry: {
      assess: [
          'vendor/chart.js',
          'js/djaodjin-pages-vue.js',
          'js/assess-vue.js',
      ],
      editors: [
          'js/djaodjin-survey-vue.js',
          'js/djaodjin-pages-vue.js',
          'js/editors-vue.js',
      ],
      reporting: [
          'vendor/chart.js',
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
          Chart: ['vendor/chart.js', 'Chart'],
          httpRequestMixin: ['js/djaodjin-resources-vue.js', 'httpRequestMixin'],
          itemMixin: ['js/djaodjin-resources-vue.js', 'itemMixin'],
          itemListMixin: ['js/djaodjin-resources-vue.js', 'itemListMixin'],
          TypeAhead: ['js/djaodjin-resources-vue.js', 'TypeAhead'],
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
      modules: confPaths.node_modules,
  },
  resolveLoader: {
      modules: confPaths.node_modules,
  }
};
