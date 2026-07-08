<template>
    <div class="live-monitor">
        <div class="live-monitor__map">
            <div ref="mapContainer" class="live-monitor__map-body"></div>
            <div class="track-panel">
                <div class="track-panel__row">
                    <span class="track-panel__label">轨迹</span>
                    <span :class="['track-panel__status', trackWsConnected ? 'is-online' : 'is-offline']">
                        {{ trackWsStatusText }}
                    </span>
                </div>
                <div class="track-panel__row">航点：{{ trackPoints.length }}</div>
                <div class="track-panel__row" v-if="latestTrackPoint">
                    高度：{{ formatTrackValue(latestTrackPoint.height) }} m
                </div>
                <div class="track-panel__row" v-if="latestTrackPoint">
                    风速：{{ formatTrackValue(latestTrackPoint.wind_speed) }} m/s
                </div>
                <el-button size="mini" type="text" class="track-panel__clear" @click="clearTrack">清空航线</el-button>
            </div>
        </div>

        <div class="live-monitor__video">
            <div class="video-panel">
                <div class="video-panel__header">
                    <el-select
                        v-model="currentNestId"
                        placeholder="请选择机巢"
                        size="small"
                        class="video-panel__nest-select"
                        @change="handleNestChange">
                        <el-option
                            v-for="item in uavList"
                            :key="item.id"
                            :label="item.name"
                            :value="item.id">
                        </el-option>
                    </el-select>

                    <div class="video-panel__actions">
                        <el-button size="mini" @click="pullStream">拉流</el-button>
                        <el-button size="mini" icon="el-icon-full-screen" @click="toggleFullscreen">全屏</el-button>
                    </div>
                </div>
                <div class="video-panel__body" ref="videoWrapper">
                    <div v-if="!streamActive && !streamConnecting" class="video-panel__placeholder">
                        <p class="video-panel__placeholder-text">请点击拉流，获取无人机视频画面</p>
                    </div>
                    <div v-else-if="streamConnecting" class="video-panel__placeholder">
                        <div class="video-panel__connecting">
                            <i class="el-icon-loading video-panel__connecting-icon"></i>
                            <p class="video-panel__connecting-text">网络连接中</p>
                        </div>
                    </div>
                    <video
                        v-else
                        ref="videoElement"
                        class="video-panel__player"
                        :src="localVideoSrc"
                        playsinline
                        preload="auto"
                        @ended="handleVideoEnded">
                    </video>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import '@supermap/iclient-leaflet';
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import { getLiveStreamInfoApi } from '@/api/commonApi';
import { normalizeStaticResourceUrl } from '@/utils/staticResourceUrl';
import { calculateDistance } from '@/utils/utils';
import patchFeature from './patchFeature.json';
import { buildPatchPopupHtml, transformProjectedFeatureToMap } from './patchGeoJson';

const MAX_TRACK_POINTS = 3000;
const TRACK_WS_RECONNECT_MS = 5000;
const STREAM_STEP_SEC = 120;
/** 机巢坐标：经度 120.2888，纬度 31.48485 */
const NEST_POSITION = { lat: 31.48485, lon: 120.2888 };
const FLIGHT_SPEED_MPS = 15;
const PATCH_DWELL_MS = 30000;

export default {
    name: 'LiveMonitor',
    data() {
        const uavList = (window.config && window.config.liveStreamUavList) || [];
        return {
            uavList,
            currentNestId: uavList.length ? uavList[0].id : '',
            map: null,
            baseMapLayer: null,
            markerLayer: null,
            patchLayer: null,
            trackPolyline: null,
            droneMarker: null,
            nestMarker: null,
            flightRouteLine: null,
            routeDroneMarker: null,
            routeAnimationFrame: null,
            routeWaitTimer: null,
            flightPatchCenter: null,
            flightMissionStarted: false,
            trackPoints: [],
            latestTrackPoint: null,
            trackSocket: null,
            trackWsActive: false,
            trackWsConnected: false,
            trackWsStatusText: '未连接',
            trackWsReconnectTimer: null,
            localVideoSrc: normalizeStaticResourceUrl('/static/vedio/1.mp4'),
            streamActive: false,
            streamConnecting: false,
            isFirstPullStream: true,
            playbackPosition: 0,
            videoDuration: 0,
            streamTitle: '',
            projectCity: window.config.projectCity,
            baseMapService: window.config.baseMapService,
            baseMapServiceType: window.config.baseMapServiceType,
            baseMaxNativeZoom: window.config.baseMaxNativeZoom,
            center: window.config.center,
            minZoom: window.config.minZoom,
            maxZoom: window.config.maxZoom,
            zoom: window.config.zoom
        };
    },

    computed: {
        currentNest() {
            return this.uavList.find((item) => item.id === this.currentNestId) || null;
        }
    },

    async mounted() {
        this.trackWsActive = true;
        await this.$nextTick();
        this.initMap();
        this.connectTrackSocket();
        await this.initPlaybackPosition();
        this.initNestInfo();
        this.scheduleInvalidateSize();
    },

    beforeRouteLeave(to, from, next) {
        this.teardownTrackSocket();
        next();
    },

    beforeDestroy() {
        this.teardownTrackSocket();
        this.pauseLocalVideo();
        this.destroyMap();
    },

    methods: {
        initMap() {
            if (!this.$refs.mapContainer) return;
            if (this.map) {
                this.destroyMap();
            }

            const resolutions = [
                1.40625, 0.703125, 0.3515625, 0.17578125, 0.087890625, 0.0439453125, 0.02197265625, 0.010986328125, 0.0054931640625,
                0.00274658203125, 0.001373291015625, 0.0006866455078125, 0.00034332275390625, 0.000171661376953125, 0.0000858306884765625,
                0.00004291534423828125, 0.000021457672119140625, 0.000010728836059570312, 0.000005364418029785156
            ];
            let myCrs = L.CRS.EPSG3857;
            if (this.projectCity !== 'nanjing' && L.Proj && L.Proj.CRS) {
                myCrs = L.Proj.CRS('EPSG:4326', {
                    bounds: L.bounds([-180, -90], [180, 90]),
                    origin: [-180, 90],
                    resolutions
                });
            }

            this.map = L.map(this.$refs.mapContainer, {
                crs: myCrs,
                center: this.center,
                zoom: this.zoom,
                zoomControl: false,
                attributionControl: false,
                minZoom: this.minZoom,
                maxZoom: this.maxZoom,
                zoomSnap: 0.25
            });

            L.control.zoom({ position: 'bottomright' }).addTo(this.map);
            this.markerLayer = L.layerGroup().addTo(this.map);
            this.patchLayer = L.layerGroup().addTo(this.map);
            this.loadBaseLayer();
            this.drawPatchFeature();
        },

        loadBaseLayer() {
            if (!this.baseMapService || !this.map) return;
            if (this.baseMapLayer) {
                this.map.removeLayer(this.baseMapLayer);
            }
            if (this.baseMapServiceType === '1') {
                this.baseMapLayer = new TiledMapLayer(this.baseMapService, {
                    maxZoom: this.maxZoom,
                    maxNativeZoom: this.baseMaxNativeZoom,
                    reuseTiles: false,
                    updateWhenIdle: false,
                    updateWhenZooming: false,
                    keepBuffer: 1000,
                    updateInterval: 0,
                    tileSize: 256,
                    fadeAnimation: false,
                    zoomAnimation: false,
                    preferCanvas: true,
                    noWrap: true
                });
            } else if (this.baseMapServiceType === '2') {
                this.baseMapLayer = L.tileLayer(`${this.baseMapService}/tile/{z}/{y}/{x}`, {
                    maxZoom: this.maxZoom,
                    maxNativeZoom: this.baseMaxNativeZoom,
                    minZoom: this.minZoom,
                    pane: 'tilePane',
                    updateWhenIdle: false,
                    updateWhenZooming: false,
                    keepBuffer: 3,
                    updateInterval: 200,
                    zoomOffset: 0,
                    noWrap: true
                });
            } else {
                this.baseMapLayer = L.tileLayer(this.baseMapService, {
                    maxZoom: this.maxZoom,
                    maxNativeZoom: this.baseMaxNativeZoom,
                    reuseTiles: false,
                    updateWhenIdle: true,
                    updateInterval: 200,
                    keepBuffer: 1,
                    noWrap: true
                });
            }
            this.baseMapLayer.addTo(this.map);
            if (this.baseMapLayer.bringToBack) {
                this.baseMapLayer.bringToBack();
            }
        },

        destroyMap() {
            this.stopRouteAnimation();
            this.clearTrackLayers();
            this.clearFlightRouteLayers();
            if (this.patchLayer && this.map) {
                this.map.removeLayer(this.patchLayer);
            }
            this.patchLayer = null;
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        },

        invalidateMapSize() {
            if (this.map) {
                this.map.invalidateSize();
            }
        },

        scheduleInvalidateSize() {
            this.$nextTick(() => {
                this.invalidateMapSize();
                setTimeout(() => this.invalidateMapSize(), 100);
                setTimeout(() => this.invalidateMapSize(), 300);
            });
        },

        drawPatchFeature() {
            if (!this.map || !this.patchLayer) return;
            this.patchLayer.clearLayers();
            const feature = transformProjectedFeatureToMap(patchFeature);
            const layer = L.geoJSON(feature, {
                style: {
                    color: '#ff4d4f',
                    weight: 2,
                    opacity: 0.95,
                    fillColor: '#ff7875',
                    fillOpacity: 0.35
                },
                onEachFeature: (feat, featLayer) => {
                    const html = buildPatchPopupHtml(feat.properties);
                    if (html) {
                        featLayer.bindPopup(html);
                    }
                }
            });
            layer.addTo(this.patchLayer);
            this.setupNestAndFlightRoute();
            this.refitMapView();
        },

        getPatchCenterLatLng() {
            if (!this.patchLayer) return null;
            const bounds = L.latLngBounds([]);
            this.patchLayer.eachLayer((layer) => {
                if (layer.getBounds) {
                    bounds.extend(layer.getBounds());
                }
            });
            if (!bounds.isValid()) return null;
            const center = bounds.getCenter();
            return [center.lat, center.lng];
        },

        getNestIcon() {
            return L.icon({
                iconUrl: require('@/assets/images/start.png'),
                iconSize: [40, 40],
                iconAnchor: [20, 20],
                popupAnchor: [0, -20]
            });
        },

        getDroneIcon() {
            return L.icon({
                iconUrl: require('@/assets/images/wurenji.png'),
                iconSize: [40, 40],
                iconAnchor: [20, 20],
                popupAnchor: [0, -20]
            });
        },

        setupNestAndFlightRoute() {
            if (!this.map) return;
            this.stopRouteAnimation();
            this.clearFlightRouteLayers();

            const nestLatLng = [NEST_POSITION.lat, NEST_POSITION.lon];
            const patchCenter = this.getPatchCenterLatLng();
            if (!patchCenter) return;

            this.nestMarker = L.marker(nestLatLng, { icon: this.getNestIcon() })
                .bindPopup('<div>机巢</div><div>经度：120.2888</div><div>纬度：31.48485</div>')
                .addTo(this.map);

            this.flightRouteLine = L.polyline([nestLatLng, patchCenter], {
                color: '#faad14',
                weight: 3,
                opacity: 0.9,
                dashArray: '10, 8'
            }).addTo(this.map);

            this.routeDroneMarker = L.marker(nestLatLng, { icon: this.getDroneIcon() })
                .bindPopup('点击拉流后开始飞行')
                .addTo(this.map);

            this.flightPatchCenter = patchCenter;
        },

        startFlightMissionOnPullStream() {
            if (this.flightMissionStarted) return;
            if (!this.routeDroneMarker || !this.flightPatchCenter) return;
            this.flightMissionStarted = true;
            const nestLatLng = [NEST_POSITION.lat, NEST_POSITION.lon];
            this.stopRouteAnimation();
            this.routeDroneMarker.setLatLng(nestLatLng);
            this.startFlightMission(nestLatLng, this.flightPatchCenter);
        },

        resetFlightToNest() {
            this.stopRouteAnimation();
            this.flightMissionStarted = false;
            if (this.routeDroneMarker) {
                this.routeDroneMarker.setLatLng([NEST_POSITION.lat, NEST_POSITION.lon]);
                this.routeDroneMarker.bindPopup('点击拉流后开始飞行');
            }
        },

        startFlightMission(nestLatLng, patchCenter) {
            this.flyAlongRoute(nestLatLng, patchCenter, () => {
                if (!this.routeDroneMarker) return;
                const distance = calculateDistance(
                    nestLatLng[0],
                    nestLatLng[1],
                    patchCenter[0],
                    patchCenter[1]
                );
                this.routeDroneMarker.bindPopup(
                    `<div>已到达图斑，停留 30s</div><div>航程：${distance.toFixed(0)} m</div>`
                );
                this.routeWaitTimer = setTimeout(() => {
                    this.routeWaitTimer = null;
                    this.flyAlongRoute(patchCenter, nestLatLng, () => {
                        if (this.routeDroneMarker) {
                            this.routeDroneMarker.bindPopup('已返回机巢');
                        }
                    });
                }, PATCH_DWELL_MS);
            });
        },

        flyAlongRoute(fromLatLng, toLatLng, onComplete) {
            if (this.routeAnimationFrame) {
                cancelAnimationFrame(this.routeAnimationFrame);
                this.routeAnimationFrame = null;
            }
            const distance = calculateDistance(fromLatLng[0], fromLatLng[1], toLatLng[0], toLatLng[1]);
            if (distance <= 0 || !this.routeDroneMarker) return;

            const durationMs = (distance / FLIGHT_SPEED_MPS) * 1000;
            const startTime = performance.now();

            const animate = (now) => {
                const elapsed = now - startTime;
                const t = Math.min(elapsed / durationMs, 1);
                const lat = fromLatLng[0] + (toLatLng[0] - fromLatLng[0]) * t;
                const lon = fromLatLng[1] + (toLatLng[1] - fromLatLng[1]) * t;
                this.routeDroneMarker.setLatLng([lat, lon]);
                if (t < 1) {
                    this.routeAnimationFrame = requestAnimationFrame(animate);
                } else {
                    this.routeAnimationFrame = null;
                    if (typeof onComplete === 'function') {
                        onComplete();
                    }
                }
            };

            this.routeAnimationFrame = requestAnimationFrame(animate);
        },

        stopRouteAnimation() {
            if (this.routeAnimationFrame) {
                cancelAnimationFrame(this.routeAnimationFrame);
                this.routeAnimationFrame = null;
            }
            if (this.routeWaitTimer) {
                clearTimeout(this.routeWaitTimer);
                this.routeWaitTimer = null;
            }
        },

        clearFlightRouteLayers() {
            if (this.nestMarker && this.map) {
                this.map.removeLayer(this.nestMarker);
            }
            if (this.flightRouteLine && this.map) {
                this.map.removeLayer(this.flightRouteLine);
            }
            if (this.routeDroneMarker && this.map) {
                this.map.removeLayer(this.routeDroneMarker);
            }
            this.nestMarker = null;
            this.flightRouteLine = null;
            this.routeDroneMarker = null;
            this.flightPatchCenter = null;
        },

        refitMapView() {
            if (!this.map) return;
            if (this.trackPoints.length) return;
            const bounds = L.latLngBounds([]);
            if (this.patchLayer) {
                this.patchLayer.eachLayer((layer) => {
                    if (layer.getBounds) {
                        bounds.extend(layer.getBounds());
                    }
                });
            }
            if (this.nestMarker && this.nestMarker.getLatLng) {
                bounds.extend(this.nestMarker.getLatLng());
            }
            if (this.markerLayer) {
                this.markerLayer.eachLayer((layer) => {
                    if (layer.getLatLng) {
                        bounds.extend(layer.getLatLng());
                    }
                });
            }
            if (bounds.isValid()) {
                this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 16 });
            }
        },

        getTrackWsUrl() {
            const cfg = window.config || {};
            if (cfg.droneTrackWsUrl) {
                return cfg.droneTrackWsUrl;
            }
            const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const params = new URLSearchParams();
            if (this.currentNestId) {
                params.set('device_sn', this.currentNestId);
            }
            if (this.currentNest && this.currentNest.uav_id) {
                params.set('uav_id', this.currentNest.uav_id);
            }
            const query = params.toString();
            return `${proto}//${window.location.host}/ws/drone/track/${query ? `?${query}` : ''}`;
        },

        connectTrackSocket() {
            if (!this.trackWsActive) return;
            this.closeTrackSocket(false);
            const url = this.getTrackWsUrl();
            this.trackWsStatusText = '连接中...';
            this.trackWsConnected = false;

            try {
                this.trackSocket = new WebSocket(url);
            } catch (e) {
                console.error('WebSocket 创建失败', e);
                this.trackWsStatusText = '连接失败';
                this.scheduleTrackReconnect();
                return;
            }

            this.trackSocket.onopen = () => {
                if (!this.trackWsActive) {
                    this.closeTrackSocket();
                    return;
                }
                this.trackWsConnected = true;
                this.trackWsStatusText = '已连接';
            };

            this.trackSocket.onmessage = (event) => {
                if (!this.trackWsActive) return;
                this.handleTrackMessage(event.data);
            };

            this.trackSocket.onerror = () => {
                if (!this.trackWsActive) return;
                this.trackWsStatusText = '连接异常';
            };

            this.trackSocket.onclose = () => {
                this.trackWsConnected = false;
                if (!this.trackWsActive) {
                    this.trackWsStatusText = '未连接';
                    return;
                }
                this.trackWsStatusText = '已断开';
                this.scheduleTrackReconnect();
            };
        },

        teardownTrackSocket() {
            this.trackWsActive = false;
            this.closeTrackSocket();
            this.trackWsStatusText = '未连接';
            this.trackWsConnected = false;
        },

        closeTrackSocket(clearTimer = true) {
            if (clearTimer && this.trackWsReconnectTimer) {
                clearTimeout(this.trackWsReconnectTimer);
                this.trackWsReconnectTimer = null;
            }
            if (this.trackSocket) {
                this.trackSocket.onopen = null;
                this.trackSocket.onmessage = null;
                this.trackSocket.onerror = null;
                this.trackSocket.onclose = null;
                if (this.trackSocket.readyState === WebSocket.OPEN || this.trackSocket.readyState === WebSocket.CONNECTING) {
                    this.trackSocket.close();
                }
                this.trackSocket = null;
            }
        },

        scheduleTrackReconnect() {
            if (!this.trackWsActive || this.trackWsReconnectTimer) return;
            this.trackWsReconnectTimer = setTimeout(() => {
                this.trackWsReconnectTimer = null;
                if (!this.trackWsActive) return;
                this.connectTrackSocket();
            }, TRACK_WS_RECONNECT_MS);
        },

        handleTrackMessage(raw) {
            let payload = raw;
            if (typeof raw === 'string') {
                try {
                    payload = JSON.parse(raw);
                } catch (e) {
                    return;
                }
            }
            const point = payload.point_info || payload.data || payload;
            const lat = Number(point.lat);
            const lon = Number(point.lon);
            if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
                return;
            }
            this.appendTrackPoint({
                lat,
                lon,
                height: point.height,
                timestamp: point.timestamp,
                wind_speed: point.wind_speed
            });
        },

        appendTrackPoint(point) {
            const latLng = [point.lat, point.lon];
            const last = this.trackPoints[this.trackPoints.length - 1];
            if (last && last[0] === latLng[0] && last[1] === latLng[1]) {
                return;
            }

            this.trackPoints.push(latLng);
            if (this.trackPoints.length > MAX_TRACK_POINTS) {
                this.trackPoints.shift();
            }
            this.latestTrackPoint = point;

            if (!this.map) return;

            if (this.trackPolyline) {
                this.trackPolyline.setLatLngs(this.trackPoints);
            } else {
                this.trackPolyline = L.polyline(this.trackPoints, {
                    color: '#2bb3f4',
                    weight: 3,
                    opacity: 0.9
                }).addTo(this.map);
            }

            const popupHtml = [
                `<div>经度：${point.lon}</div>`,
                `<div>纬度：${point.lat}</div>`,
                `<div>高度：${this.formatTrackValue(point.height)} m</div>`,
                `<div>风速：${this.formatTrackValue(point.wind_speed)} m/s</div>`,
                point.timestamp ? `<div>时间：${point.timestamp}</div>` : ''
            ].join('');

            if (this.droneMarker) {
                this.droneMarker.setLatLng(latLng);
                this.droneMarker.bindPopup(popupHtml);
            } else {
                this.droneMarker = L.circleMarker(latLng, {
                    radius: 7,
                    color: '#ff4d4f',
                    fillColor: '#ff7875',
                    fillOpacity: 0.95,
                    weight: 2
                })
                    .bindPopup(popupHtml)
                    .addTo(this.map);
            }

            if (this.trackPoints.length === 1) {
                this.map.setView(latLng, 16);
            } else if (this.trackPoints.length % 5 === 0) {
                this.map.panTo(latLng, { animate: true });
            }
        },

        clearTrack() {
            this.trackPoints = [];
            this.latestTrackPoint = null;
            this.clearTrackLayers();
        },

        clearTrackLayers() {
            if (this.trackPolyline && this.map) {
                this.map.removeLayer(this.trackPolyline);
            }
            if (this.droneMarker && this.map) {
                this.map.removeLayer(this.droneMarker);
            }
            this.trackPolyline = null;
            this.droneMarker = null;
        },

        formatTrackValue(value) {
            if (value === null || value === undefined || value === '') {
                return '-';
            }
            const num = Number(value);
            return Number.isFinite(num) ? num.toFixed(1) : value;
        },

        setDeviceMarker(latitude, longitude, title) {
            if (!this.map || latitude == null || longitude == null) return;
            this.markerLayer.clearLayers();
            const marker = L.marker([latitude, longitude]);
            if (title) {
                marker.bindPopup(title);
            }
            marker.addTo(this.markerLayer);
            this.refitMapView();
        },

        async initNestInfo() {
            const routeNestId = this.$route.query.deviceSn || this.$route.query.deviceId;
            if (routeNestId && this.uavList.some((item) => item.id === routeNestId)) {
                this.currentNestId = routeNestId;
            }

            if (this.currentNest) {
                //this.fetchNestInfo(this.currentNest);
            }
        },

        handleNestChange() {
            this.resetVideoPreview();
            this.clearTrack();
            this.connectTrackSocket();
            if (this.currentNest) {
                //this.fetchNestInfo(this.currentNest);
            }
        },

        async fetchNestInfo(nest) {
            if (!nest) return;
            try {
                this.streamTitle = nest.name;
                const res = await getLiveStreamInfoApi({
                    deviceSn: nest.id,
                    tenantId: nest.tenantId,
                    projectId: nest.projectId,
                    uavId: nest.uav_id
                });
                if (res.code === 0 && res.data) {
                    const { latitude, longitude, deviceName } = res.data;
                    if (deviceName) {
                        this.streamTitle = deviceName;
                    }
                    if (latitude != null && longitude != null) {
                        this.setDeviceMarker(latitude, longitude, this.streamTitle);
                    }
                }
            } catch (e) {
                console.error(e);
            }
        },

        resetVideoPreview() {
            this.syncPlaybackPosition();
            this.streamActive = false;
            this.streamConnecting = false;
            this.isFirstPullStream = true;
            this.resetFlightToNest();
        },

        syncPlaybackPosition() {
            const video = this.$refs.videoElement;
            if (this.streamActive && video && Number.isFinite(video.currentTime)) {
                this.playbackPosition = video.currentTime;
            }
        },

        loadVideoDuration() {
            return new Promise((resolve) => {
                const video = document.createElement('video');
                video.preload = 'metadata';
                video.src = this.localVideoSrc;
                video.onloadedmetadata = () => {
                    const duration = Number.isFinite(video.duration) ? video.duration : 0;
                    video.removeAttribute('src');
                    video.load();
                    resolve(duration);
                };
                video.onerror = () => resolve(0);
            });
        },

        async initPlaybackPosition() {
            this.videoDuration = await this.loadVideoDuration();
            this.recalculatePlaybackPosition();
        },

        recalculatePlaybackPosition() {
            const duration = this.videoDuration;
            if (!duration || duration <= 0) {
                this.playbackPosition = 0;
                return;
            }
            const now = new Date();
            const secondsSinceMidnight =
                now.getHours() * 3600 + now.getMinutes() * 60 + now.getSeconds();
            this.playbackPosition = secondsSinceMidnight % duration;
        },

        willExceedDuration(nextPosition) {
            const duration = this.videoDuration;
            return duration > 0 && nextPosition >= duration;
        },

        showStreamConnecting() {
            this.syncPlaybackPosition();
            this.streamActive = false;
            this.streamConnecting = true;
            const video = this.$refs.videoElement;
            if (video) {
                video.pause();
            }
        },

        handleVideoEnded() {
            this.playbackPosition = this.videoDuration;
            this.showStreamConnecting();
        },

        pullStream() {
            let nextPosition;

            if (this.isFirstPullStream) {
                nextPosition = 0;
                this.isFirstPullStream = false;
            } else {
                if (this.streamConnecting) {
                    this.recalculatePlaybackPosition();
                } else {
                    this.syncPlaybackPosition();
                }
                nextPosition = this.playbackPosition + STREAM_STEP_SEC;
            }

            if (this.willExceedDuration(nextPosition)) {
                this.showStreamConnecting();
                return;
            }

            this.streamConnecting = false;
            this.playbackPosition = nextPosition;
            this.streamActive = true;
            this.startFlightMissionOnPullStream();

            this.$nextTick(() => {
                const video = this.$refs.videoElement;
                if (!video) return;

                const seekAndPlay = () => {
                    video.currentTime = this.playbackPosition;
                    video.play();
                };

                if (video.readyState >= 1) {
                    seekAndPlay();
                } else {
                    video.addEventListener('loadedmetadata', seekAndPlay, { once: true });
                }
            });
        },

        pauseLocalVideo() {
            if (!this.streamActive) return;
            const video = this.$refs.videoElement;
            if (video) {
                video.pause();
            }
        },

        toggleFullscreen() {
            const el = this.$refs.videoWrapper;
            if (!el) return;
            if (document.fullscreenElement) {
                document.exitFullscreen();
            } else {
                el.requestFullscreen();
            }
        }
    }
};
</script>

<style scoped lang="scss">
.live-monitor {
    display: flex;
    width: 100%;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    background: #0f1419;
}

.live-monitor__map {
    position: relative;
    width: 50%;
    height: 100%;
    min-height: 0;
    display: flex;
    flex-direction: column;
    background-color: #fff;
}

.live-monitor__map-body {
    flex: 1;
    width: 100%;
    min-height: 0;
}

::v-deep .leaflet-container {
    width: 100%;
    height: 100%;
    z-index: 1;
}

.track-panel {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 500;
    min-width: 150px;
    padding: 10px 12px;
    border-radius: 8px;
    background: rgba(13, 17, 23, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #e6edf3;
    font-size: 12px;
    line-height: 1.7;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.25);
}

.track-panel__row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
}

.track-panel__label {
    font-weight: 600;
}

.track-panel__status.is-online {
    color: #3fb950;
}

.track-panel__status.is-offline {
    color: #8b949e;
}

.track-panel__clear {
    margin-top: 4px;
    padding: 0;
    color: #58a6ff;
}

.live-monitor__video {
    width: 50%;
    height: 100%;
    box-sizing: border-box;
    background: #1a2332;
}

.video-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
    background: #0d1117;
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.video-panel__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.04);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.video-panel__nest-select {
    flex: 1;
    max-width: 400px;
}

::v-deep .video-panel__nest-select .el-input__inner {
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.12);
    color: #e6edf3;
    font-weight: 600;
}

::v-deep .video-panel__nest-select .el-input__inner:hover,
::v-deep .video-panel__nest-select .el-input.is-focus .el-input__inner {
    border-color: rgba(43, 179, 244, 0.6);
}

::v-deep .video-panel__nest-select .el-input__icon {
    color: #8b949e;
}

.video-panel__body {
    flex: 1;
    position: relative;
    background: #000;
    min-height: 0;
}

.video-panel__player {
    width: 100%;
    height: 100%;
    object-fit: contain;
    background: #000;
}

.video-panel__placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    background: #000;
}

.video-panel__placeholder-text {
    margin: 0;
    padding: 0 24px;
    color: #8b949e;
    font-size: 15px;
    line-height: 1.6;
    text-align: center;
}

.video-panel__connecting {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
}

.video-panel__connecting-icon {
    font-size: 36px;
    color: #58a6ff;
}

.video-panel__connecting-text {
    margin: 0;
    color: #8b949e;
    font-size: 15px;
    line-height: 1.6;
}
::v-deep .leaflet-control-rotate-toggle{
    display: none!important;
}
</style>
