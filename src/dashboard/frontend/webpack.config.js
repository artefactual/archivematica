'use strict';

module.exports = {
  mode: 'production',
  context:  __dirname + '/app',
  output: {
    path:  __dirname + '/../src/media/js/build',
    filename: 'dashboard.js',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        loader: 'babel-loader',
        query: {
          presets: ['es2015'],
          plugins: ['transform-object-assign', 'transform-runtime'],
        },
        exclude: /node_modules/,
      },
      {
        test: /\.css/,
        loader: 'style-loader!css-loader',
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
    ],
  },
};
