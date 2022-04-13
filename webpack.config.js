const fs = require('fs');
const path = require('path');
const webpack = require('webpack');

var confPaths = JSON.parse(fs.readFileSync('webpack-conf-paths.json').toString())

module.exports = {
  mode: 'production',
  entry: {
      base: [
          './htdocs/static/vendor/jquery.js',
          './htdocs/static/vendor/popper-utils.js',
          './htdocs/static/vendor/popper.js',
          './htdocs/static/vendor/bootstrap.js',
          './djaopsp/static/vendor/djaodjin-menubar.js',
          './djaopsp/static/vendor/djaodjin-dashboard.js',
      ],
      assess: [
//          'js/djaodjin-resources.js',
//          'js/djaodjin-resources-vue.js',
          'js/assess-vue.js',
          'js/scorecard-vue.js',
      ],
      'editor': [
          'vendor/dropzone.js',
          'vendor/jquery-ui.js',
          'vendor/rangy-core.js',
          'vendor/hallo.js',
          'js/djaodjin-resources.js',
          'js/djaodjin-editor.js',
          'js/djaodjin-upload.js',
          'js/djaodjin-sidebar-gallery.js'
      ],
      editors: [
          'vendor/typeahead.bundle.js',
          'vendor/dropzone.js',
          'vendor/jquery-ui.js',
          'vendor/rangy-core.js',
          'vendor/hallo.js',
          'vendor/vue-typeahead.common.js',
          'js/djaodjin-resources.js',
          'js/djaodjin-editor.js',
          'js/djaodjin-upload.js',
          'js/djaodjin-sidebar-gallery.js',
          'js/djaodjin-resources-vue.js',
          'js/djaodjin-pages-vue.js',
          'js/djaodjin-survey-vue.js',
          'js/editors-vue.js'
      ],
      reporting: [
          'vendor/chart.js',
          'vendor/vue-typeahead.common.js',
          'js/djaodjin-resources.js',
          'js/djaodjin-resources-vue.js',
          'js/djaodjin-survey-vue.js',
          'js/reporting-vue.js'
      ],
      'vendor-vue': [
          './assets/js/vendor-vue.js',
//          'vendor/moment-timezone-with-data.js',
//          'vendor/vue.js',
//          'vendor/vue-infinite-loading.js',
//          'vendor/lodash.js'
      ],
  },
  module: {
    rules: [{
      test: /jquery\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /popper-utils\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /popper\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /bootstrap\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /djaodjin-menubar\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /djaodjin-dashboard\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    },
    // assess.js
/*
    {
      test: /djaodjin-resources\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /djaodjin-resources-vue\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /assess-vue\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }, {
      test: /scorecard-vue\.js$/i,
      //use: 'raw-loader',
      type: 'asset/source'
    }
*/
    ]
  },
  output: {
      path: path.resolve(__dirname, 'htdocs/static/cache'),
      filename: '[name].js',
  },
  plugins: [
      new webpack.ProvidePlugin({
          httpRequestMixin: 'js/djaodjin-resources-vue.js',
          itemMixin: 'js/djaodjin-resources-vue.js',
          filterableMixin: 'js/djaodjin-resources-vue.js',
          paginationMixin: 'js/djaodjin-resources-vue.js',
          sortableMixin: 'js/djaodjin-resources-vue.js',
          itemListMixin: 'js/djaodjin-resources-vue.js',
          practicesListMixin: 'js/assess-vue.js',
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
          "util": require.resolve("util/"),

      },
      modules: confPaths.node_modules,
  }
};
