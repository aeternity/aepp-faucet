const webpack = require('webpack')
const path = require('path')
const { CleanWebpackPlugin } = require('clean-webpack-plugin')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')

const mainJSPath = path.resolve(__dirname, './src', 'main.js')
const mainCSSPath = path.resolve(__dirname, './src', 'main.css')
const imagesPath = path.resolve(__dirname, './src/images')
// const fontsPath = path.resolve(__dirname, './src/fonts')
const publicPath = path.resolve(__dirname, './assets')

module.exports = {
  entry: {
    main: [
      mainJSPath,
      mainCSSPath
    ] // ,
    // vendor: []
  },
  output: {
    filename:
      process.env.NODE_ENV === 'prod'
        ? 'scripts/[name].min.js?h=[hash]'
        : 'scripts/[name].js?h=[hash]',
    path: publicPath,
    publicPath: '/assets/'
  },
  optimization: {
    splitChunks: {
      chunks: 'all'
    }
  },
  plugins: [
    // new webpack.optimize.AggressiveSplittingPlugin(js_split_options),
    new webpack.ProvidePlugin({
      // $: 'jquery',
      // jQuery: 'jquery',
      // objectFitImages: 'object-fit-images'
    }),
    new CleanWebpackPlugin(
      {
        dry: false,
        verbose: true,
        cleanStaleWebpackAssets: false
      }
    ),
    // Simply copy assets to dist folder
    new CopyWebpackPlugin([
      { from: imagesPath, to: 'images' }
      // { from: fontsPath, to: 'fonts' }
    ]),
    new HtmlWebpackPlugin({
      template: path.resolve(__dirname, './src/index.html'),
      filename: path.resolve(__dirname, './templates/index.html'),
      hash: true,
      inject: true
    }),
    new MiniCssExtractPlugin({
      filename: 'styles/main.css?h=[hash]',
      fallback: 'style-loader',
      ignoreOrder: false
    })
  ],
  resolve: {
    alias: {
      // styles:  path.resolve(__dirname, '../src/sass'), // relative to the location of the webpack config file!
    }
  },
  module: {
    rules: [
      // ES2015 to ES5 compilation
      {
        test: /\.js$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader'
          },
          {
            loader: 'standard-loader?error=true'
          }
        ]
      },
      {
        test: /\.css$/,
        use: [
          {
            loader: MiniCssExtractPlugin.loader,
            options: {
              // you can specify a publicPath here
              // by default it uses publicPath in webpackOptions.output
              publicPath: 'public/styles',
              hmr: process.env.NODE_ENV === 'dev'
            }
          },
          'css-loader',
          {
            loader: 'postcss-loader',
            options: {
              config: {
                path: 'postcss.config.js'
              }
            }
          }
        ]
      }
    ]
  }
}
