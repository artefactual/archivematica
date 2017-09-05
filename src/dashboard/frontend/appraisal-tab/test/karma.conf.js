module.exports = function(config){
  config.set({

    basePath : '../',

    files : [
      'test/tests.webpack.js',
      'app/vendor/base64.js',
    ],

    autoWatch : true,

    frameworks: ['jasmine'],

    browsers : ['Chrome'],

    plugins : [
            'karma-chrome-launcher',
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
      devtool: 'inline-source-map',
      module: {
        loaders: [
          { test: /\.js$/, loader: 'babel?presets[]=es2015' },
        ],
      },
    },

  });
};
