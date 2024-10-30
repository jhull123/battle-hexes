export default {
  // Use this if you're using Jest in ESM mode
  transform: {
    // Use Babel to transpile your modules
    '^.+\\.jsx?$': 'babel-jest',
  },
  testEnvironment: 'node', // or 'jsdom' if you're testing browser-like functionality
};

