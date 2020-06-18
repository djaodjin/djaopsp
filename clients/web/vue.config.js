const HtmlWebpackPlugin = require('html-webpack-plugin')

module.exports = {
  outputDir: '../../htdocs',
  assetsDir: 'static/cache',
  publicPath: '/envconnect',
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

  // Fix: https://github.com/vuejs/vue-cli/issues/1132
  chainWebpack: (config) => {
    if (process.env.NODE_ENV === 'development') {
      config.output.filename('[name].[hash].js').end()
    }
  },
}
