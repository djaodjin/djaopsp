const HtmlWebpackPlugin = require('html-webpack-plugin')
const assetsDir = 'static/cache'

module.exports = {
  outputDir: '../../htdocs',
  assetsDir: assetsDir,
  publicPath: process.env.VUE_APP_ROOT,
  configureWebpack: {
    plugins: [
      new HtmlWebpackPlugin({
        inject: false,
        minify: false,
        filename: '../envconnect/templates/cache/envconnect/base.html',
        template: '../../envconnect/templates/envconnect/base.html',
      }),
    ],
  },

  transpileDependencies: ['vuetify'],

  pluginOptions: {
    i18n: {
      locale: 'en',
      fallbackLocale: 'es',
      localeDir: 'locales',
      enableInSFC: false,
    },
  },

  /*
  // If we use a fix derived from https://github.com/vuejs/vue-cli/issues/1132
  // we fill the assets cache very quickly because we must run
  // `build --no-clean` to aggregate assets in the htdocs directory.
  chainWebpack: (config) => {
      config.output.filename(assetsDir + '/[name].[hash].js')
  },
  */
}
