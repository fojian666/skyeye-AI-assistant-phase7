<template></template>

<script>
/**
 * 三维场景管理（对齐 demo/LAIS-Web SceneLayerManager.initScene）
 * 使用 index.html 全局 SuperMap Cesium
 */
export default {
    name: 'SceneLayerManager',
    props: {
        mapId: {
            type: String,
            default: 'cesiumContainer'
        },
        /** 是否加载 scene_url 等扩展资源（不含底图，底图由 oneMap 显式 loadBaseMap） */
        loadResources: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            viewer: null,
            _basemapImageryLayer: null,
            _onWindowResize: null,
            _resizeObserver: null,
            _resizeDebounceTimer: null
        };
    },
    beforeDestroy() {
        this.destroyScene();
    },
    methods: {
        getCesium() {
            return window.Cesium || null;
        },

        resizeScene() {
            if (!this.viewer || this.viewer.isDestroyed()) return;
            this.viewer.resize();
            if (this.viewer.scene && this.viewer.scene.requestRender) {
                this.viewer.scene.requestRender();
            }
        },

        scheduleResize() {
            if (this._resizeDebounceTimer) {
                clearTimeout(this._resizeDebounceTimer);
            }
            this._resizeDebounceTimer = setTimeout(() => {
                this._resizeDebounceTimer = null;
                this.resizeScene();
            }, 100);
        },

        bindResizeListeners() {
            this.unbindResizeListeners();
            const container = document.getElementById(this.mapId);
            if (!container) return;
            this._onWindowResize = () => this.scheduleResize();
            window.addEventListener('resize', this._onWindowResize);
            if (typeof ResizeObserver !== 'undefined') {
                this._resizeObserver = new ResizeObserver(() => this.scheduleResize());
                this._resizeObserver.observe(container);
            }
        },

        unbindResizeListeners() {
            if (this._resizeDebounceTimer) {
                clearTimeout(this._resizeDebounceTimer);
                this._resizeDebounceTimer = null;
            }
            if (this._onWindowResize) {
                window.removeEventListener('resize', this._onWindowResize);
                this._onWindowResize = null;
            }
            if (this._resizeObserver) {
                this._resizeObserver.disconnect();
                this._resizeObserver = null;
            }
        },

        removeBaseMap() {
            if (!this.viewer || this.viewer.isDestroyed()) {
                this._basemapImageryLayer = null;
                return;
            }
            if (this._basemapImageryLayer) {
                try {
                    this.viewer.imageryLayers.remove(this._basemapImageryLayer, true);
                } catch (e) {
                    /* ignore */
                }
                this._basemapImageryLayer = null;
            }
        },

        /**
         * 加载底图（对齐 demo loadBaseMap，仅 type 1 / 2）
         * @param {{ type: string, url: string, minZoom?: number, maxZoom?: number, maxNativeZoom?: number }} config
         */
        loadBaseMap(config) {
            const Cesium = this.getCesium();
            if (!this.viewer || this.viewer.isDestroyed() || !Cesium || !config || !config.url) {
                return null;
            }

            this.removeBaseMap();

            const type = String(config.type != null ? config.type : '2');
            const minZoom = config.minZoom != null ? config.minZoom : 0;
            const maxZoom = config.maxZoom != null ? config.maxZoom : 18;
            const maxNativeZoom = config.maxNativeZoom != null ? config.maxNativeZoom : maxZoom;
            let imageryLayer = null;

            try {
                let provider = null;
                if (type === '1') {
                    if (!Cesium.SuperMapImageryProvider) {
                        console.warn('SuperMapImageryProvider 不可用，无法加载 type=1 底图');
                        return null;
                    }
                    provider = new Cesium.SuperMapImageryProvider({
                        url: config.url,
                        name: '底图',
                        maximumLevel: maxNativeZoom
                    });
                } else {
                    let url = config.url;
                    if (!url.includes('{z}')) {
                        url = `${url}/tile/{z}/{y}/{x}`;
                    }
                    provider = new Cesium.UrlTemplateImageryProvider({
                        url,
                        name: '底图',
                        tilingScheme: new Cesium.WebMercatorTilingScheme(),
                        minimumLevel: minZoom,
                        maximumLevel: maxNativeZoom
                    });
                }

                if (this.viewer.scene && this.viewer.scene.globe) {
                    this.viewer.scene.globe.preloadAncestors = false;
                    this.viewer.scene.globe.preloadSiblings = false;
                }

                imageryLayer = this.viewer.imageryLayers.addImageryProvider(provider);
                this._basemapImageryLayer = imageryLayer;
                if (this.viewer.scene && this.viewer.scene.requestRender) {
                    this.viewer.scene.requestRender();
                }
                return imageryLayer;
            } catch (e) {
                console.error('三维底图加载失败:', e);
                return null;
            }
        },

        normalizeImageryServiceUrl(mapUrl) {
            if (!mapUrl) return mapUrl;
            if (process.env.NODE_ENV === 'development') {
                try {
                    const urlObj = new URL(mapUrl);
                    return urlObj.pathname;
                } catch (e) {
                    return mapUrl;
                }
            }
            return mapUrl;
        },

        isGeographicWkid(wkid) {
            if (wkid == null) return false;
            const id = Number(wkid);
            return id === 4490 || id === 4326 || id === 4214 || id === 4610;
        },

        isGeographicExtent(xmin, ymin, xmax, ymax) {
            return Math.abs(xmin) <= 180 && Math.abs(xmax) <= 180 && Math.abs(ymin) <= 90 && Math.abs(ymax) <= 90 && xmin < xmax && ymin < ymax;
        },

        isExtentTooLarge(xmin, ymin, xmax, ymax, maxSpan = 5) {
            return Math.abs(xmax - xmin) > maxSpan || Math.abs(ymax - ymin) > maxSpan;
        },

        extentToGeographicRectangle(ext, allowLargeExtent = false) {
            const Cesium = this.getCesium();
            if (!Cesium || !ext) return null;
            const { xmin, ymin, xmax, ymax } = ext;
            if ([xmin, ymin, xmax, ymax].some((v) => v == null || Number.isNaN(Number(v)))) {
                return null;
            }
            const wkid = ext.spatialReference && (ext.spatialReference.latestWkid || ext.spatialReference.wkid);
            const geographic = this.isGeographicWkid(wkid) || this.isGeographicExtent(xmin, ymin, xmax, ymax);
            if (!geographic) return null;
            if (!allowLargeExtent && this.isExtentTooLarge(xmin, ymin, xmax, ymax)) {
                return null;
            }
            return Cesium.Rectangle.fromDegrees(xmin, ymin, xmax, ymax);
        },

        async fetchArcGisViewExtents(mapUrl) {
            const serviceUrl = this.normalizeImageryServiceUrl(mapUrl).replace(/\/$/, '');
            try {
                const res = await fetch(`${serviceUrl}?f=json`);
                if (!res.ok) return null;
                const data = await res.json();
                return {
                    initialExtent: data.initialExtent,
                    fullExtent: data.fullExtent || data.extent
                };
            } catch (e) {
                return null;
            }
        },

        async resolveImageryViewRectangle(mapUrl, imageryProvider) {
            const Cesium = this.getCesium();
            const extents = await this.fetchArcGisViewExtents(mapUrl);
            if (extents) {
                const initialRect = this.extentToGeographicRectangle(extents.initialExtent, true);
                if (initialRect) return initialRect;

                const fullRect = this.extentToGeographicRectangle(extents.fullExtent, false);
                if (fullRect) return fullRect;
            }

            const rectangle = imageryProvider && imageryProvider.rectangle;
            if (Cesium && rectangle && !Cesium.Rectangle.equals(rectangle, Cesium.Rectangle.MAX_VALUE)) {
                return rectangle;
            }
            return null;
        },

        frameImageryView(rectangle) {
            const Cesium = this.getCesium();
            if (!rectangle || !this.viewer || !Cesium) return;
            const camera = this.viewer.camera;
            const topDownOrientation = {
                heading: 0,
                pitch: -Cesium.Math.PI_OVER_TWO,
                roll: 0
            };

            if (typeof camera.viewRectangle === 'function') {
                camera.viewRectangle(rectangle, new Cesium.HeadingPitchRange(0, -Cesium.Math.PI_OVER_TWO, 0));
                return;
            }

            camera.flyTo({
                destination: rectangle,
                orientation: topDownOrientation,
                duration: 1.5
            });
        },

        /**
         * 打开基础地理影像服务（对齐 demo，ArcGIS CGCS2000）
         * @param {object} node 资源树影像节点
         * @param {{ frameView?: boolean }} options frameView 为 true 时按服务范围定位
         */
        async openImageryService(node, options = {}) {
            const Cesium = this.getCesium();
            if (!node || !node.service) {
                console.warn('影像服务节点或地址缺失');
                return null;
            }
            const format = node.gis_server_format != null ? node.gis_server_format : node.gis_service_format;
            const serverType = String(node.gis_server_type != null ? node.gis_server_type : node.gis_service_type);
            const isArcGisTile = format == null || format === undefined || String(format) === '1';
            if (serverType !== '2' || !isArcGisTile) {
                console.warn(`暂不支持的三维影像类型：gis_server_type=${serverType}, gis_server_format=${format}`);
                return null;
            }
            if (window.viewer) {
                this.viewer = window.viewer;
            }
            if (!this.viewer || this.viewer.isDestroyed() || !Cesium) {
                console.warn('Cesium viewer 未初始化');
                return null;
            }

            this.removeBaseMap();

            const mapUrl = this.normalizeImageryServiceUrl(node.service);
            try {
                if (!Cesium.CGCS2000MapServerImageryProvider) {
                    console.warn('CGCS2000MapServerImageryProvider 不可用');
                    return null;
                }
                const imageryProvider = new Cesium.CGCS2000MapServerImageryProvider({ url: mapUrl });
                imageryProvider.type = 'arcgis2000';
                imageryProvider.name = node.label || '底图';

                const imageryLayer = this.viewer.imageryLayers.addImageryProvider(imageryProvider);
                this._basemapImageryLayer = imageryLayer;

                if (imageryProvider.readyPromise) {
                    await imageryProvider.readyPromise;
                }

                if (options.frameView) {
                    const rectangle = await this.resolveImageryViewRectangle(mapUrl, imageryProvider);
                    try {
                        this.frameImageryView(rectangle);
                    } catch (frameErr) {
                        console.warn('影像定位失败:', frameErr);
                    }
                }

                if (this.viewer.scene && this.viewer.scene.requestRender) {
                    this.viewer.scene.requestRender();
                }
                return imageryLayer;
            } catch (e) {
                console.error('三维影像服务加载失败:', e);
                return null;
            }
        },

        closeImageryService() {
            this.removeBaseMap();
        },

        flyToView(center, zoom) {
            const Cesium = this.getCesium();
            if (!this.viewer || !Cesium || !center) return;
            const lat = center.lat != null ? center.lat : center[0];
            const lng = center.lng != null ? center.lng : center[1];
            const z = zoom != null ? zoom : 10;
            const equatorCircumference = 40075016.686;
            const height = equatorCircumference / (2 * Math.PI * Math.pow(2, z));
            this.viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(lng, lat, height),
                orientation: {
                    heading: 0,
                    pitch: Cesium.Math.toRadians(-90),
                    roll: 0
                },
                duration: 0
            });
            if (this.viewer.scene && this.viewer.scene.requestRender) {
                this.viewer.scene.requestRender();
            }
        },

        initScene(options = {}) {
            const Cesium = this.getCesium();
            if (!Cesium) {
                console.error('Cesium 未加载，请检查 public/index.html 中 static/Cesium 脚本是否引入');
                return null;
            }

            if (this.viewer && !this.viewer.isDestroyed()) {
                this.$nextTick(() => {
                    this.resizeScene();
                    if (options.center) {
                        this.flyToView(options.center, options.zoom);
                    }
                });
                return this.viewer;
            }

            this.viewer = new Cesium.Viewer(this.mapId, {
                timeline: false,
                animation: false,
                baseLayerPicker: false,
                fullscreenButton: false,
                geocoder: false,
                homeButton: false,
                infoBox: false,
                sceneModePicker: false,
                selectionIndicator: false,
                navigationHelpButton: false,
                imageryProvider: false,
                terrainProvider: new Cesium.EllipsoidTerrainProvider(),
                requestRenderMode: true,
                maximumRenderTimeChange: Infinity,
                targetFrameRate: 30
            });

            if (this.viewer.cesiumWidget && this.viewer.cesiumWidget.creditContainer) {
                this.viewer.cesiumWidget.creditContainer.style.display = 'none';
            }

            window.viewer = this.viewer;

            if (this.loadResources && window.config && window.config.scene_url) {
                const promise = this.viewer.scene.open(window.config.scene_url);
                if (promise && typeof promise.then === 'function') {
                    promise.then(() => this.resizeScene());
                }
            }

            if (options.center) {
                this.flyToView(options.center, options.zoom);
            }

            if (this.viewer.scene && this.viewer.scene.globe) {
                this.viewer.scene.globe.preloadAncestors = false;
                this.viewer.scene.globe.preloadSiblings = false;
                this.viewer.scene.globe.tileCacheSize = 200;
            }

            this.$nextTick(() => {
                this.resizeScene();
                this.bindResizeListeners();
            });

            return this.viewer;
        },

        destroyScene() {
            this.removeBaseMap();
            this.unbindResizeListeners();
            if (this.viewer && !this.viewer.isDestroyed()) {
                this.viewer.destroy();
            }
            this.viewer = null;
            if (window.viewer) {
                window.viewer = null;
            }
        }
    }
};
</script>
