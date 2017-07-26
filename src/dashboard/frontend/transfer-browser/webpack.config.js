'use strict';

require('webpack');
var APP = __dirname + '/app';

module.exports = {
  context: APP,
  output: {
    path: APP,
    filename: 'transfer_browser.js',
  },
  module: {
    loaders: [
      {
        test: /\.js$/,
        loader: 'babel?presets[]=es2015',
        exclude: /node_modules/,
      },
      {
        test: /\.css/,
        loader: 'style!css',
      },
      {
          test: /\.png$/,
          loader: 'url-loader',
          query: {
            mimetype: 'image/png',
          },
      },
      {
          test: /\.(eot|woff|woff2|ttf|svg)(\?v=\d\.\d\.\d)?$/,
          loader: 'url-loader',
      },
      // The imports loader injects names for libraries which expect
      // to be able to access them globally;
      // the bootstrap transition plugin requires jQuery under the
      // name "jQuery", for example
      {
          test: /bootstrap\/js\//,
          loader: 'imports?jQuery=jquery',
      },
    ],
  },
};
