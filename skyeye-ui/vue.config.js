const CompressionWebpackPlugin = require('compression-webpack-plugin');
const WebpackCdnPlugin = require('webpack-cdn-plugin');
const productionGzipExtensions = ['js', 'css'];
const { defineConfig } = require('@vue/cli-service');
const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = defineConfig({
    publicPath: process.env.VUE_APP_BASE_URL,
    outputDir: 'dist',
    assetsDir: 'static',
    transpileDependencies: true,
    lintOnSave: false,
    productionSourceMap: false,
    parallel: false,
    devServer: {
        host: '0.0.0.0',
        allowedHosts: ['localhost', '127.0.0.1', '192.168.50.20'],
        port: 8088,
        https: false,
        client: {
            overlay: false
        },
        headers: {
            'Access-Control-Allow-Origin': '*'
        },
        proxy: {
            '/api': {
                target: 'http://127.0.0.1:8009/api/',
                changeOrigin: true,
                secure: false,
                pathRewrite: {
                    '^/api': ''
                }
            },
            '/panoramaUrl': {
                target: 'http://127.0.0.1:8009/',
                changeOrigin: true,
                secure: false,
                pathRewrite: {
                    '^/panoramaUrl': ''
                }
            },
            '/live-stream-proxy': {
                target: 'http://2.20.41.1:8089',
                changeOrigin: true,
                secure: false,
                pathRewrite: {
                    '^/live-stream-proxy': ''
                }
            },
            '/drone-whep': {
                target: 'http://2.20.41.1:8089',
                changeOrigin: true,
                secure: false
            },
            // 仅代理无人机轨迹 WS，勿用 /ws（会与 webpack-dev-server 热更新 WebSocket 冲突）
            '/ws/drone': {
                target: 'http://127.0.0.1:8009',
                ws: true,
                changeOrigin: true,
                secure: false
            }
        }
    },
    chainWebpack: (config) => {
        config.devtool('source-map');
        config.plugins.delete('prefetch');
        config.plugins.delete('preload');
        config.optimization.minimize(false);

        const isProduction = process.env.NODE_ENV === 'production';
        config.plugin('webpack-cdn-plugin').use(WebpackCdnPlugin, [
            {
                modules: [
                    {
                        name: 'leaflet',
                        var: 'L',
                        path: 'dist/leaflet.js',
                        style: 'dist/leaflet.css'
                    },
                    {
                        name: '@supermap/iclient-leaflet',
                        var: 'L',
                        path: 'dist/iclient-leaflet-es6.js',
                        style: 'dist/iclient-leaflet.min.css'
                    }
                ],
                prodUrl: isProduction ? '/static/lib/cdn/:name/:path' : '/static/lib/cdn/:name/:path'
            }
        ]);

        config.module
            .rule('md')
            .test(/\.md/)
            .use('vue-loader')
            .loader('vue-loader')
            .end()
            .use('vue-markdown-loader')
            .loader('vue-markdown-loader/lib/markdown-compiler')
            .options({
                raw: true,
                preventExtract: true
            });

        config.module
            .rule('js')
            .use('babel-loader')
            .loader('babel-loader')
            .tap((options) => {
                return {
                    ...options,
                    presets: ['@babel/preset-env'],
                    plugins: ['@babel/plugin-proposal-optional-chaining', '@babel/plugin-proposal-nullish-coalescing-operator']
                };
            });
    },
    configureWebpack: {
        plugins: [
            new webpack.DefinePlugin({
                CESIUM_BASE_URL: JSON.stringify('/cesium')
            }),
            new CopyWebpackPlugin({
                patterns: [
                    {
                        from: path.join(__dirname, 'node_modules/cesium/Build/Cesium'),
                        to: 'cesium'
                    }
                ]
            })
        ],
        resolve: {
            alias: {
                '@zip.js/zip.js/lib/zip-no-worker.js': path.resolve(__dirname, 'node_modules/@zip.js/zip.js/lib/zip-no-worker.js')
            },
            fallback: {
                url: require.resolve('url/'),
                querystring: false,
                util: require.resolve('util/')
            }
        }
    }
});
