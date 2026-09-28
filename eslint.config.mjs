import neostandard from 'neostandard'

export default [
  ...neostandard({
    env: ['browser', 'node'],
    ignores: [
      'benchmark/extra/**',
      'demo/**',
      'dist/**'
    ]
  }),

  {
    rules: {
      camelcase: 'off'
    }
  }
]
