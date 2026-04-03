const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
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
      favicon: path.resolve(__dirname, '../favicon.ico'),
    }),
    new HtmlWebpackPlugin({
      template: path.resolve(__dirname, 'src/battle.html'), // Game boot page
      filename: 'battle.html',
      chunks: ['battle'],
      favicon: path.resolve(__dirname, '../favicon.ico'),
    }),
    new CopyWebpackPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, 'public/sounds'),
          to: path.resolve(__dirname, 'dist/sounds'),
          globOptions: {
            dot: false,
            gitignore: true,
          },
        },
      ],
    }),
    new webpack.DefinePlugin({
      'process.env.API_URL': JSON.stringify(env.API_URL || 'http://localhost:8000'),
      'process.env.BATTLE_HEXES_SERVICE_MODE': JSON.stringify(env.BATTLE_HEXES_SERVICE_MODE || 'http'),
      'process.env.LOG_SERVER_RESPONSES': JSON.stringify(env.LOG_SERVER_RESPONSES || 'false'),
    }),
  ],
});
