// postcss.config.js
const purgecss = require('@fullhuman/postcss-purgecss')({
  // Specify the paths to all of the template files in your project
  content: [
    './src/**/*.html'
  ],

  // Include any special characters you're using in this regular expression
  defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
})

const tailwindcss = require('tailwindcss')
module.exports = {
  plugins: [
    require('postcss-import', {}),
    tailwindcss('tailwind.config.js'),
    require('autoprefixer', { browsers: 'last 10 versions' }),
    // require('postcss-responsive-type')(), unistalled via npm
    require('cssnano', {
      preset: ['default', { discardComments: { removeAll: true } }]
    }),
    ...process.env.NODE_ENV === 'prod'
      ? [purgecss]
      : []
    // require('postcss-object-fit-images')
  ]
}
