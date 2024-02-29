module.exports = function(config){
  config.set({

    basePath : '../',

    files : [
      'test/tests.webpack.js'
    ],

    autoWatch : true,

    frameworks: ['jasmine'],

    browsers : ['ChromeHeadless', 'FirefoxHeadless'],

    customLaunchers: {
        ChromeHeadless: {
            base: 'Chrome',
            flags: ['--no-sandbox', '--headless', '--disable-gpu', '--remote-debugging-port=9222']
        },
        FirefoxHeadless: {
            base: 'Firefox',
            flags: ['--headless']
        }
    },

    plugins : [
            'karma-chrome-launcher',
            'karma-firefox-launcher',
            'karma-jasmine',
            'karma-webpack',
            ],

    junitReporter : {
      outputFile: 'test_out/unit.xml',
      suite: 'unit',
    },

    preprocessors: {
      'test/tests.webpack.js': ['webpack'],
    },

    webpack: {
      mode: 'development',
      devtool: 'inline-source-map',
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
          },
        ],
      },
      resolve: {
        fallback: {
          'path': require.resolve("path-browserify"),
        },
      },
    },
  });
};
