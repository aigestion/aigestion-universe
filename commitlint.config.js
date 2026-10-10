// Config minima de commitlint (sin extends: no hay package.json ni
// node_modules en este repo legacy; npx solo baja @commitlint/cli).
module.exports = {
  rules: {
    'type-enum': [
      2,
      'always',
      ['build', 'chore', 'ci', 'docs', 'feat', 'fix', 'perf', 'refactor', 'revert', 'style', 'test', 'cross-IDE'],
    ],
    'type-empty': [2, 'never'],
    'subject-empty': [2, 'never'],
    'subject-full-stop': [2, 'never', '.'],
    'header-max-length': [2, 'always', 120],
  },
};
