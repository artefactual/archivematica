'use strict';

module.exports = {
  mode: 'development',
  context:  __dirname + '/app',
  output: {
    path:  __dirname + '/../src/media/js/build',
    filename: 'dashboard.js',
  },
  module: {
    rules: [
      {
        test: /\.js$/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', { targets: "defaults" }]
            ],
            plugins: [
              '@babel/plugin-transform-object-assign',
              '@babel/plugin-transform-runtime',
              '@babel/plugin-transform-modules-commonjs',
            ],
          },
        },
        exclude: /node_modules/,
      },
      {
        test: /\.css/,
        use: [
          'style-loader',
          {
            loader: 'css-loader',
          },
        ],
      },
      {
        test: /\.(png|eot|woff|woff2|ttf|svg)(\?v=\d\.\d\.\d)?$/,
        type: 'asset/inline',
      },
      {
        test: /\.html$/,
        use: [
          {
            loader: 'html-loader',
            options: {
              minimize: true,
              sources: false,
            }
          }
        ],
      }
    ],
  },
  resolve: {
    fallback: {
      'path': require.resolve('path-browserify'),
    },
  },
};
