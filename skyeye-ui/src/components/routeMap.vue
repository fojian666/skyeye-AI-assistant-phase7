<template>
    <div class="se-container">
        <div class="map-container" ref="mapContainer"></div>
        <div class="se-map-tool">
            <div class="zoom-num">{{ currentShowZoom }}</div>
            <div class="map-reset" @click="map_reset" title="地图复位"><i class="iconfont icon-quantu"></i></div>
        </div>
        <div class="toolbar" :style="targetDivStyle" v-if="isShowToolBar">
            <div @click="startDrawing" :class="{ active: activeToolBarIndex === 1 }">
                <span class="icon iconfont icon-duobianxing"></span><span>绘制面</span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="editPolygon" :class="{ active: activeToolBarIndex === 2 }">
                <span class="icon iconfont icon-geoai-edit"></span><span>编辑面</span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="finishEditPolygon" :class="{ active: activeToolBarIndex === 3 }">
                <span class="icon iconfont icon-wancheng"></span><span>完成</span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="clearPolygon">
                <span class="icon iconfont icon-qingchu" :class="{ active: activeToolBarIndex === 4 }"></span><span>清除面</span>
            </div>
        </div>
    </div>
</template>

<script>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '@supermap/iclient-leaflet';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import proj4 from 'proj4';
import { getMapInfoApi, viewPlanApi } from '@/api/commonApi';
import { normalizeLatLngList } from '@/utils/utils';
import { create4528LeafletMap, createGeoCrs, createGeoBaseLayer } from '@/utils/map4528Loader';

export default {
    name: 'MapContainer',
    props: {
        tableData: Array,
        // 交互控制
        enableClick: {
            type: Boolean,
            default: false
        }
    },
    data() {
        return {
            clickRowId: '',
            currentClickMarker: null,
            pointLists: [],
            //地图相关
            map: null, //地图对象
            baseMapLayer: null,
            baseMapService: window.config.baseMapService,
            baseMapServiceType: window.config.baseMapServiceType,
            baseMaxNativeZoom: window.config.baseMaxNativeZoom,
            baseMapUse4528: window.config.baseMapUse4528 === true,
            baseMap4528Epsg: window.config.baseMap4528Epsg || 'EPSG:4528',
            baseMap4528Proj:
                window.config.baseMap4528Proj || '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs',
            mapResetCenter: window.config.center,
            mapResetZoom: window.config.zoom,
            mapFitBounds: null,
            projectCity: window.config.projectCity,
            center: window.config.center, //地图中心点
            minZoom: window.config.minZoom, //最小层级
            maxZoom: window.config.maxZoom, // 最大层级
            zoom: window.config.zoom, //初始层级
            layerRandList: [],
            targetDivPosition: { x: 0 }, // 初始 X 轴位置
            activeToolBarIndex: 0,
            isShowToolBar: false,
            currentPolygon: null, // 当前正在绘制的多边形
            mapService: null, //地图服务

            gisServiceType: '', //地图服务类型
            dataSourceName: null, //数据源名称
            datasetsName: null, //数据集名称
            currentShowZoom: window.config.zoom, //当前层级
            showControls: false,
            layers: {
                baseLayer: null,
                overlays: [] // 存储叠加图层
            },
            markers: [], // 存储标记
            markerGroup: L.layerGroup(),
            polylines: [], // 存储线
            polygons: [], // 存储多边形
            eventHandlers: {}, // 存储事件处理器
            saveMarkers: [],
            selectedPolygon: null, //当前选中的图斑
            drawnItems: new L.FeatureGroup(), // 存储所有绘制的多边形
            defaultIconviolet: L.icon({
                iconUrl: require('@/assets/images/marker-icon-blue.png'),
                iconSize: [25, 40], // 图标大小
                iconAnchor: [12.5, 40], // 图标锚点（中心点）
                popupAnchor: [-3, -40] // 弹出窗偏移量
            })
        };
    },
    async mounted() {
        //获取地图信息
        const res = await getMapInfoApi();
        if (res.code === 0) {
            this.mapService = res.data.map_service;
            this.datasetsName = res.data.datasets_name;
            this.dataSourceName = res.data.datasource_name;
            this.gisServiceType = String(res.data.gis_service_type || '');
        }
        this.$nextTick(async () => {
            await this.initMap();
        });
    },
    beforeDestroy() {
        this.destroyMap();
    },
    watch: {
        enableClick(newVal) {
            this.toggleClickEvent(newVal);
        },
        isShowToolBar(newVal) {}
    },
    computed: {
        targetDivStyle() {
            return {
                transform: `translateX(${this.targetDivPosition.x}px)`
            };
        }
    },
    methods: {
        /**
         * 开始标绘
         * @returns null
         */
        startDrawing() {
            this.activeToolBarIndex = 1;
            this.currentPolygon = null; // 重置当前多边形
            this.$message.success('开始绘制多边形，双击结束绘制');
            this.map.on('click', this.handleMapClick);
            this.map.on('contextmenu', this.handleMapDblClick); // 关闭绘制模式
        },
        closeMapClick() {
            this.map.off('click', this.handleMapClick);
        },
        /**
         * 编辑标绘
         * @returns null
         */
        editPolygon() {
            this.closeMapClick();
            if (this.selectedPolygon) {
                this.activeToolBarIndex = 2;
                const latLngs = this.selectedPolygon.getLatLngs()[0];
                latLngs.forEach((latLng, index) => {
                    const marker = L.marker(latLng, {
                        draggable: true,
                        icon: L.divIcon({
                            className: 'polygon-vertex',
                            html: `<div style="width: 8px; height: 8px; border-radius: 50%; background-color: #49B8FF;"></div>`
                        })
                    }).addTo(this.map);
                    this.saveMarkers.push(marker); // 将标记存储起来
                    marker.on('dragend', () => {
                        latLngs[index] = marker.getLatLng();
                        this.selectedPolygon.setLatLngs(latLngs); // 更新多边形的顶点
                    });
                });
            } else {
                this.$message.warning('请先选择一个多边形');
            }
        },
        /**
         * 选择图斑
         * @author yhj
         * @date 2025年12月10日
         * @returns null
         */
        selectPolygon(polygon) {
            if (this.selectedPolygon) {
                this.selectedPolygon.setStyle({ color: '#49B8FF' }); // 恢复默认样式
            }
            this.selectedPolygon = polygon;
            this.selectedPolygon.setStyle({ color: 'red' }); // 高亮选中的多边形
            this.drawnItems.removeLayer(polygon);
            this.drawnItems.addLayer(this.selectedPolygon);
        },
        /**
         * 结束标绘
         * @author yhj
         * @date 2025年12月10日
         * @returns null
         */
        finishEditPolygon() {
            this.activeToolBarIndex = 3;
            this.map.off('click', this.handleMapClick);
            this.saveMarkers.forEach((marker) => {
                this.map.removeLayer(marker); // 移除每个临时标记
            });
            if (this.selectedPolygon) {
                this.selectedPolygon.setStyle({ color: '#49B8FF' }); // 恢复默认样式
            }
            this.selectedPolygon = null;
            this.$emit('finishDraw', this.drawnItems);
        },
        /**
         * 清除图斑
         * @returns null
         */
        clearPolygon() {
            // this.activeToolBarIndex = 4
            this.activeToolBarIndex = null;
            if (this.selectedPolygon) {
                this.drawnItems.removeLayer(this.selectedPolygon);
                this.map.addLayer(this.drawnItems);
                this.selectedPolygon = null; // 重置选中的多边形
                this.map.off('click', this.handleMapClick); // 关闭绘制模式
            } else {
                this.$message.warning('请先选择一个多边形');
            }
        },
        handleMapClick(e) {
            const latLng = e.latlng;
            if (!this.currentPolygon) {
                // 初始化新的多边形
                this.currentPolygon = L.polygon([latLng], { color: '#49B8FF' }).addTo(this.map);
            } else {
                // 添加新的点到当前多边形
                this.currentPolygon.addLatLng(latLng);
            }
        },
        handleMapDblClick(e) {
            if (this.currentPolygon) {
                // 双击结束绘制，闭合多边形
                const latLngs = this.currentPolygon.getLatLngs()[0];
                if (latLngs.length > 2) {
                    this.currentPolygon.addLatLng(latLngs[0]); // 闭合多边形
                    const currentPolygon = this.currentPolygon;
                    this.drawnItems.addLayer(currentPolygon); // 将多边形添加到图层组
                    // 为多边形添加 click 事件
                    currentPolygon.on('click', () => {
                        this.selectPolygon(currentPolygon);
                        this.map.off('click', this.handleMapClick);
                    });
                }
                this.currentPolygon = null; // 重置当前多边形
                // this.map.off("click", this.handleMapClick); // 关闭绘制模式
            }
        },
        // 地图重置
        map_reset() {
            if (!this.map) return;
            if (this.mapFitBounds && this.mapFitBounds.isValid()) {
                this.map.fitBounds(this.mapFitBounds);
                return;
            }
            this.map.setView(this.mapResetCenter || this.center, this.mapResetZoom || this.zoom);
        },
        async initMap() {
            if (this.map) {
                this.destroyMap();
            }
            try {
                if (this.baseMapUse4528 && this.baseMapService) {
                    await this.init4528Map();
                } else {
                    this.initGeoMap();
                }
            } catch (err) {
                console.error('[routeMap] 4528 底图加载失败', err);
            }
            this.setupMapAfterInit();
        },
        async init4528Map() {
            const loaded = await create4528LeafletMap(this.$refs.mapContainer, {
                serviceUrl: this.baseMapService,
                serviceType: this.baseMapServiceType,
                epsgCode: this.baseMap4528Epsg,
                projDef: this.baseMap4528Proj,
                initialZoom: this.zoom,
                center: this.center,
                mapOptions: {
                    zoomSnap: 1,
                    zoomDelta: 1
                }
            });
            this.map = loaded.map;
            this.baseMapLayer = loaded.baseMapLayer;
            this.maxZoom = loaded.maxZoom;
            this.minZoom = loaded.minZoom;
            this.mapFitBounds = loaded.fitBounds;
            if (loaded.fitBounds && loaded.fitBounds.isValid()) {
                this.mapResetCenter = loaded.fitBounds.getCenter();
                this.mapResetZoom = this.map.getZoom();
            } else {
                this.mapResetCenter = this.center;
                this.mapResetZoom = loaded.initialZoom != null ? loaded.initialZoom : this.zoom;
            }
            this.layerRandList.unshift({
                name: '底图(4528)',
                layer: this.baseMapLayer,
                shapeOption: { opacity: 1, brightness: 1, contrast: 1, saturation: 1 },
                show: true,
                expanded: false,
                source_type: '底图'
            });
        },
        initGeoMap() {
            const resolutions = [
                1.40625, 0.703125, 0.3515625, 0.17578125, 0.087890625, 0.0439453125, 0.02197265625, 0.010986328125, 0.0054931640625, 0.00274658203125,
                0.001373291015625, 0.0006866455078125, 0.00034332275390625, 0.000171661376953125, 0.0000858306884765625, 0.00004291534423828125,
                0.000021457672119140625, 0.000010728836059570312, 0.000005364418029785156
            ];
            let myCrs;
            if (this.projectCity === 'jiangyin') {
                proj4.defs('EPSG:4490', '+proj=longlat +ellps=GRS80 +no_defs');
                myCrs = new L.Proj.CRS('EPSG:4490', {
                    resolutions,
                    bounds: L.bounds([-180, -90], [180, 90]),
                    origin: [-180, 90]
                });
            } else {
                myCrs = createGeoCrs(this.projectCity);
            }

            this.map = L.map(this.$refs.mapContainer, {
                crs: myCrs,
                center: this.center,
                zoom: this.zoom,
                zoomControl: this.showControls,
                zoomSnap: 0.25,
                minZoom: this.minZoom,
                maxZoom: this.maxZoom,
                attributionControl: false
            });
            this.mapResetCenter = this.center;
            this.mapResetZoom = this.zoom;
            this.mapFitBounds = null;

            if (this.baseMapService) {
                this.baseMapLayer = createGeoBaseLayer(this.baseMapService, this.baseMapServiceType, {
                    maxZoom: this.maxZoom,
                    maxNativeZoom: this.baseMaxNativeZoom,
                    minZoom: this.minZoom
                });
                if (this.baseMapLayer) {
                    this.baseMapLayer.addTo(this.map);
                    this.baseMapLayer.bringToBack();
                    this.layerRandList.unshift({
                        name: '底图',
                        layer: this.baseMapLayer,
                        shapeOption: { opacity: 1, brightness: 1, contrast: 1, saturation: 1 },
                        show: true,
                        expanded: false,
                        source_type: '底图'
                    });
                }
            }
        },
        setupMapAfterInit() {
            if (!this.map) return;
            L.control.zoom({ position: 'bottomright' }).addTo(this.map);
            const zoomHandler = () => {
                this.currentShowZoom = Math.floor(this.map.getZoom());
            };
            zoomHandler();
            this.map.on('zoomend', zoomHandler);
            if (!this.baseMapUse4528) {
                this.addBaseLayer();
            }
            this.toggleClickEvent(this.enableClick);
            this.$nextTick(() => {
                if (this.map) {
                    this.map.invalidateSize();
                }
            });
        },

        // 添加业务影像图层（map_info 接口配置）
        addBaseLayer() {
            console.log('this.mapService', this.mapService);
            if (!this.map || !this.mapService) {
                return;
            }

            if (this.layers.baseLayer) {
                this.map.removeLayer(this.layers.baseLayer);
                this.layers.baseLayer = null;
            }
            const serviceType = String(this.gisServiceType || '');
            let layer = null;
            console.log(serviceType);
            switch (serviceType) {
                case '1':
                    layer = new TiledMapLayer(this.mapService, {
                        maxZoom: this.maxZoom,
                        maxNativeZoom: this.maxZoom,
                        reuseTiles: false,
                        updateWhenIdle: true,
                        updateInterval: 200,
                        keepBuffer: 1,
                        noWrap: true
                    });
                    break;
                case '2':
                    layer = L.tileLayer(`${this.mapService}/tile/{z}/{y}/{x}`, {
                        maxZoom: this.maxZoom,
                        minZoom: this.minZoom,
                        pane: 'tilePane',
                        updateWhenIdle: false,
                        updateWhenZooming: false,
                        keepBuffer: 3,
                        updateInterval: 200,
                        noWrap: true
                    });
                    break;
                case '3': {
                    const identifier = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
                    const matrixIds = identifier.map((id) => ({ identifier: id }));
                    if (this.mapService.includes('{z}') || this.mapService.includes('{x}')) {
                        layer = L.tileLayer(this.mapService, {
                            maxZoom: this.maxZoom,
                            minZoom: this.minZoom,
                            noWrap: true
                        });
                    } else {
                        layer = new L.supermap.WMTSLayer(this.mapService, {
                            layer: 'img',
                            style: 'default',
                            tilematrixSet: 'c',
                            format: 'tiles',
                            matrixIds,
                            maxZoom: identifier.length - 1
                        });
                    }
                    this.map.setView(this.center, 13);
                    break;
                }
                case '4':
                    layer = L.tileLayer.wms(this.mapService, {
                        layers: `${this.dataSourceName}:${this.datasetsName}`,
                        format: 'image/png',
                        transparent: true,
                        attribution: 'Your Attribution'
                    });
                    break;
                default:
                    layer = new TiledMapLayer(this.mapService, {
                        maxZoom: this.maxZoom,
                        maxNativeZoom: this.maxZoom,
                        reuseTiles: false,
                        updateWhenIdle: true,
                        updateInterval: 200,
                        keepBuffer: 1,
                        noWrap: true
                    });
                    return;
            }
            console.log(layer, 123456);
            if (layer) {
                layer.addTo(this.map);
                if (this.projectCity === 'lianyungang') {
                    this.map.setView([34.5976, 119.2217], 13);
                }
                this.layers.baseLayer = layer;
            }
        },

        // 切换点击事件
        toggleClickEvent(enable) {
            if (enable) {
                this.eventHandlers.click = (e) => {
                    this.$emit('map-click', {
                        lat: e.latlng.lat,
                        lng: e.latlng.lng,
                        latlng: e.latlng
                    });
                };
                this.map.on('click', this.eventHandlers.click);
            } else {
                if (this.eventHandlers.click) {
                    this.map.off('click', this.eventHandlers.click);
                    delete this.eventHandlers.click;
                }
            }
        },

        // 添加标记
        addMarker(latLng, options = {}) {
            const marker = L.marker(latLng, { ...defaultOptions, ...options });
            marker.addTo(this.map);
            this.markers.push(marker);
            return marker;
        },

        // 添加自定义图标标记
        addCustomMarker(latLng, iconUrl, options = {}) {
            const icon = L.icon({
                iconUrl: iconUrl,
                iconSize: options.iconSize || [40, 40],
                iconAnchor: options.iconAnchor || [12.5, 40],
                popupAnchor: options.popupAnchor || [-3, -40]
            });

            const marker = L.marker(latLng, { icon, ...options });
            marker.addTo(this.map);
            this.markers.push(marker);
            return marker;
        },
        // 创建空的折线（用于动画）
        createEmptyPolyline(options = {}) {
            return this.addPolyline([], options);
        },
        setMapView(latlon, zoom) {
            this.map.setView(latlon, zoom);
        },
        // 创建标记组
        createLayerGroup() {
            const layerGroup = L.layerGroup().addTo(this.map);
            this.layers.overlays.push(layerGroup);
            return layerGroup;
        },
        /**
         * 添加起点标记
         * @param {Object} latLng - 经纬度
         * @returns {Promise<Object>} marker对象
         * @example
         * -
         */
        addStartPoint(latLng) {
            return this.addCustomMarker(latLng, require('@/assets/images/startPoint.png'), {
                iconSize: [40, 40],
                iconAnchor: [12.5, 40]
            });
        },

        // 添加终点标记
        addEndPoint(latLng) {
            return this.addCustomMarker(latLng, require('@/assets/images/endPoint.png'), {
                iconSize: [40, 40],
                iconAnchor: [12.5, 40]
            });
        },

        // 添加多边形
        addPolygon(coordinates, options = {}) {
            const defaultOptions = {
                color: '#3388ff',
                fillColor: '#3388ff',
                fillOpacity: 0.2,
                weight: 2
            };

            const polygon = L.polygon(coordinates, { ...defaultOptions, ...options });
            polygon.addTo(this.map);
            this.polygons.push(polygon);
            // 获取多边形的边界框的中心点
            const center = polygon.getBounds().getCenter();
            // 将地图视角移动到多边形的中心位置
            this.map.flyTo(center, 12);
            return polygon;
        },

        // 添加航线（折线）
        addPolyline(coordinates, options = {}) {
            const defaultOptions = {
                color: 'red',
                weight: 3,
                opacity: 0.7
            };

            const polyline = L.polyline(coordinates, { ...defaultOptions, ...options });
            polyline.addTo(this.map);
            this.polylines.push(polyline);
            return polyline;
        },

        // 添加动画标记组
        addAnimationMarkers() {
            const group = L.layerGroup();
            group.addTo(this.map);
            this.layers.animationMarkers = group;
            return group;
        },

        // 清除所有图层
        clearAllLayers() {
            // 清除标记
            this.markers.forEach((marker) => {
                this.map.removeLayer(marker);
            });
            this.markers = [];

            // 清除折线
            this.polylines.forEach((polyline) => {
                this.map.removeLayer(polyline);
            });
            this.polylines = [];

            // 清除多边形
            this.polygons.forEach((polygon) => {
                this.map.removeLayer(polygon);
            });
            this.polygons = [];

            // 清除叠加图层
            this.layers.overlays.forEach((layer) => {
                this.map.removeLayer(layer);
            });
            this.layers.overlays = [];

            // 清除动画标记组
            if (this.layers.animationMarkers) {
                this.map.removeLayer(this.layers.animationMarkers);
                delete this.layers.animationMarkers;
            }
        },

        // 清除特定类型的图层
        clearLayer(type) {
            switch (type) {
                case 'markers':
                    this.markers.forEach((marker) => this.map.removeLayer(marker));
                    this.markers = [];
                    break;
                case 'polylines':
                    this.polylines.forEach((polyline) => this.map.removeLayer(polyline));
                    this.polylines = [];
                    break;
                case 'polygons':
                    this.polygons.forEach((polygon) => this.map.removeLayer(polygon));
                    this.polygons = [];
                    break;
                case 'overlays':
                    this.layers.overlays.forEach((layer) => this.map.removeLayer(layer));
                    this.layers.overlays = [];
                    break;
            }
        },

        // 飞行到指定位置
        flyTo(latLng, zoom = null) {
            if (this.map) {
                if (zoom) {
                    this.map.flyTo(latLng, zoom);
                } else {
                    this.map.flyTo(latLng);
                }
            }
        },

        // 平移到指定位置
        panTo(latLng, options = {}) {
            if (this.map) {
                this.map.panTo(latLng, options);
            }
        },

        // 移除单个图层（供父组件调用）
        removeLayer(layer) {
            if (!this.map || !layer) return;
            this.map.removeLayer(layer);
            this.markers = this.markers.filter((item) => item !== layer);
            this.polylines = this.polylines.filter((item) => item !== layer);
            this.polygons = this.polygons.filter((item) => item !== layer);
            this.layers.overlays = this.layers.overlays.filter((item) => item !== layer);
            if (this.layers.animationMarkers === layer) {
                delete this.layers.animationMarkers;
            }
        },

        // 获取地图边界
        getBounds() {
            return this.map ? this.map.getBounds() : null;
        },

        // 获取地图实例
        getMapInstance() {
            return this.map;
        },

        // 销毁地图
        destroyMap() {
            if (this.map) {
                this.clearAllLayers();

                Object.values(this.eventHandlers).forEach(() => {
                    if (this.map && this.map.off) {
                        this.map.off();
                    }
                });
                this.eventHandlers = {};

                this.map.remove();
                this.map = null;
            }
            this.baseMapLayer = null;
            this.mapFitBounds = null;
        },

        // 重置视图
        resetView() {
            this.map_reset();
        },
        updateView(item, id_num) {
            const defaultIconviolet = L.icon({
                iconUrl: require('@/assets/images/marker-point-orange.png'),
                iconSize: [15, 15], // 图标大小
                iconAnchor: [5, 10], // 图标锚点（中心点）
                popupAnchor: [0, 0] // 弹出窗偏移量
            });
            const marker = L.marker(item, { icon: defaultIconviolet, draggable: true });
            marker.addTo(this.map);
            const markerObj = { id: id_num++, marker: marker, lat: item[0], lon: item[1] };
            this.pointLists.push(markerObj);
            // 添加点击事件
            marker.dragging.enable();
            marker.on('dragend', (e) => {
                var newLatLng = marker.getLatLng(); // 获取marker的新位置
                const newLat = newLatLng.lat;
                const newLon = newLatLng.lng;
                // 更新点的坐标
                this.pointLists.forEach((point) => {
                    if (point.marker === e.target) {
                        point.lat = newLat;
                        point.lon = newLon;
                    }
                });
            });
            marker.on('click', () => {
                const redIcon = L.icon({
                    iconUrl: require('@/assets/images/marker-point-red.png'),
                    iconSize: [15, 15], // 图标大小
                    iconAnchor: [5, 10], // 图标锚点（中心点）
                    popupAnchor: [0, 0] // 弹出窗偏移量
                });
                const defaultIconviolet = L.icon({
                    iconUrl: require('@/assets/images/marker-point-orange.png'),
                    iconSize: [15, 15], // 图标大小
                    iconAnchor: [5, 10], // 图标锚点（中心点）
                    popupAnchor: [0, 0] // 弹出窗偏移量
                });
                if (this.currentClickMarker) {
                    this.currentClickMarker.marker.setIcon(defaultIconviolet);
                }
                this.currentClickMarker = markerObj;
                marker.setIcon(redIcon);
            });
        },
        //处理全景规划查看
        async handleViewPlan(row) {
            if (this.markerGroup.getLayers().length > 0) {
                this.markerGroup.clearLayers();
            }
            if (this.clickRowId != row.id) {
                this.tableData.forEach((item) => {
                    if (item != row) {
                        this.$set(item, 'isViewing', false);
                    }
                });
            }
            this.clickRowId = row.id;
            // 切换当前行的状态
            this.$set(row, 'isViewing', !row.isViewing);
            if (!row.isViewing) {
                this.markerGroup.clearLayers();
                return;
            }
            const res = await viewPlanApi(row.fileId, 'zip');
            if (res.code == 0) {
                const defaultIconviolet = L.icon({
                    iconUrl: require('@/assets/images/marker-point-orange.png'),
                    iconSize: [15, 15], // 图标大小
                    iconAnchor: [5, 10], // 图标锚点（中心点）
                    popupAnchor: [0, 0] // 弹出窗偏移量
                });

                const points = normalizeLatLngList(res.data);
                points.forEach((item) => {
                    const marker = L.marker(item, { icon: defaultIconviolet, draggable: true });
                    // marker.addTo(this.map);
                    marker.addTo(this.markerGroup);
                });
                this.markerGroup.addTo(this.map);
                if (points[0]) {
                    this.map.flyTo(points[0], 10);
                }
            } else {
                this.$message.error(res.msg);
            }
        }
    }
};
</script>

<style scoped>
.se-container,
.map-container {
    width: 100%;
    height: 100%;
    background-color: white;
}

/* 隐藏 SuperMap logo */
:deep(.iclient-leaflet-logo) {
    display: none !important;
}

/* 确保地图容器没有边距 */
:deep(#map),
:deep(.leaflet-container) {
    width: 100%;
    height: 100%;
    margin: 0;
    padding: 0;
}

.zoom-num {
    position: absolute;
    z-index: 999;
    right: 27px;
    bottom: 45px;
    height: 27px;
    width: 27px;
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: bold;
    background: rgba(0, 0, 0, 0.3);
}

.map-reset {
    position: absolute;
    z-index: 999;
    right: 27px;
    bottom: 10px;
    width: 27px;
    height: 27px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}

.map-reset .iconfont {
    text-align: center;
    width: 100%;
    color: #fff;
}

::v-deep .leaflet-bar a.leaflet-disabled {
    background-color: rgba(0, 0, 0, 0.1) !important;
    color: #fff;
    cursor: not-allowed;
}

::v-deep .leaflet-control-zoom-in:hover {
    background: rgba(0, 0, 0, 0.2) !important;
}

::v-deep .leaflet-control-zoom-in,
::v-deep .leaflet-control-zoom-out {
    background: rgba(0, 0, 0, 0.3) !important;
}

::v-deep .leaflet-control-zoom-out:hover {
    background: rgba(0, 0, 0, 0.2) !important;
}

::v-deep .leaflet-bottom .leaflet-control {
    bottom: 80px;
    right: 10px;
    z-index: 998 !important;
    margin-bottom: 0px !important;
}

::v-deep .leaflet-bar a {
    color: #fff;
}

::v-deep .leaflet-touch .leaflet-bar {
    background-clip: padding-box;
    border: none;
}

::v-deep .leaflet-touch .leaflet-bar a {
    width: 27px;
    height: 27px;
}

.toolbar {
    width: 300px;
    height: 35px;
    position: absolute;
    top: 20px;
    right: 20px;
    border: 1px solid #cccccc;
    border-radius: 5px;
    z-index: 999;
    font-weight: bold;
    line-height: 35px;
    background-color: white;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    padding: 0 20px;
}

.toolbar div {
    cursor: pointer;
}

.toolbar div:hover {
    color: #42b4f2;
}
</style>
