const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const webpack = require('webpack');

module.exports = (env = {}) => ({
  mode: 'development',
  entry: {
    battle: './src/battle-draw.js',
    title: './src/title-screen.js',
  },
  output: {
    filename: '[name].[contenthash:8].js',
    path: path.resolve(__dirname, 'dist'),
    clean: true,
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: path.resolve(__dirname, 'src/index.html'), // Placeholder landing page
      filename: 'index.html',
      chunks: ['title'],
      inject: 'body',
    }),
    new HtmlWebpackPlugin({
      template: path.resolve(__dirname, 'src/battle.html'), // Game boot page
      filename: 'battle.html',
      chunks: ['battle'],
    }),
    new webpack.DefinePlugin({
      'process.env.API_URL': JSON.stringify(env.API_URL || 'http://localhost:8000'),
    }),
  ],
});
