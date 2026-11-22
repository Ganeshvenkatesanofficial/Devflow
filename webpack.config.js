/**
 * Webpack config for the DevFlow extension bundle.
 * Production mode: Terser minify + mangle, no source map in the .vsix,
 * `vscode` kept external so it resolves at runtime.
 */

const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');

module.exports = (_env, argv) => {
  const isProd = (argv && argv.mode) === 'production';

  return {
    target: 'node',
    mode: isProd ? 'production' : 'development',
    entry: './extension/src/extension.js',
    output: {
      path: path.resolve(__dirname, 'dist'),
      filename: 'extension.js',
      libraryTarget: 'commonjs2',
      devtoolModuleFilenameTemplate: '../[resource-path]',
      clean: true,
    },
    devtool: isProd ? false : 'nosources-source-map',
    externals: {
      vscode: 'commonjs vscode',
    },
    resolve: { extensions: ['.js'] },
    optimization: {
      minimize: isProd,
      minimizer: [
        new TerserPlugin({
          terserOptions: {
            format: { comments: false },
            compress: { drop_console: false, passes: 2 },
            mangle: true,
          },
          extractComments: false,
        }),
      ],
    },
    performance: { hints: false },
    infrastructureLogging: { level: 'warn' },
  };
};
