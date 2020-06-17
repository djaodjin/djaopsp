const HtmlWebpackPlugin = require('html-webpack-plugin')

module.exports = {
  outputDir: "../../htdocs",
  assetsDir: "static/cache",
  publicPath: "/envconnect",
  configureWebpack: {
    plugins: [
      new HtmlWebpackPlugin({
        inject: false,
        minify: false,
        filename: "../envconnect/templates/cache/envconnect/base.html",
        template: "../../envconnect/templates/envconnect/base.html"
      })
    ]
  }
}
