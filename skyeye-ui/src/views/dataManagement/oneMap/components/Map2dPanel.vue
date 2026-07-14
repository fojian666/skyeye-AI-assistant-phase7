<template>
  <div class="map-2d-panel">
<!--    <div class="time-axis">-->
<!--      <timeAxis @handleDateChange="handleDateChange"></timeAxis>-->
<!--    </div>-->
    <div ref="mapContainer" id="mapContainer" style="height: 100%" @click="drawPointActive" @dblclick="measureActive"></div>
    <div class="toolbar" :style="targetDivStyle">
      <div @click="drawPoint" :class="{ baractive: activeToolBarIndex === 2 }">
        <span class="icon iconfont icon-position icon-toolbar"></span><span>查经纬度</span>
      </div>
      <span style="color: #cccccc">|</span>
      <div @click="measureLength" :class="{ baractive: activeToolBarIndex === 3 }">
        <span class="icon iconfont icon-icon-line-graph icon-toolbar"></span><span>测距</span>
      </div>
      <span style="color: #cccccc">|</span>
      <div @click="startDrawPolygon" :class="{ baractive: activeToolBarIndex === 4 }">
        <span class="icon iconfont icon-duobianxing icon-toolbar"></span><span>测面积</span>
      </div>
      <span style="color: #cccccc">|</span>
      <div @click="clearDraw"><span class="icon iconfont icon-qingchu icon-toolbar"></span><span>清除</span>
      </div>
    </div>
    <div class="clue-image" v-if="activeMarker">
      <div class="gt-header">
        <el-descriptions title="线索详情" style="padding-left: 6px"></el-descriptions>
        <div @click="activeMarker = null" style="cursor: pointer"><i class="el-icon-close"></i></div>
      </div>
      <el-descriptions class="margin-top" :column="2" border>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-monitor"></i>
            全景点位ID
          </template>
          {{ activeMarker.point_id }}
        </el-descriptions-item>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-location-outline"></i>
            所属区域
          </template>
          {{ activeMarker.address }}
        </el-descriptions-item>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-document"></i>
            线索名称
          </template>
          {{ activeMarker.clue_name }}
        </el-descriptions-item>
        <el-descriptions-item>
          <template slot="label">
            <i class="el-icon-position"></i>
            线索编号
          </template>
          <el-tag size="small">{{ activeMarker.clue_id }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>
      <div class="gt-image">
        <img :src="activeMarker.image_path" alt=""/>
      </div>
    </div>
    <div class="detectlist" v-if="activePanoramaPoint">
      <div class="title">
        <span>当前点位：{{ activePanoramaPoint.pointName }}</span>
        <el-tooltip class="item" effect="dark" content="多期对比" placement="bottom-end">
          <el-button icon="el-icon-position" circle @click="openMulti"></el-button>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="关闭" placement="bottom-end">
          <el-button icon="el-icon-close" circle @click="closeDrawer"></el-button>
        </el-tooltip>
      </div>
      <el-table :data="listData" style="background-color: white">
        <el-table-column type="index" label="序号"></el-table-column>
        <el-table-column property="batchName" label="批次名称" width="150"></el-table-column>
        <el-table-column property="operation" label="操作">
          <template slot-scope="scope">
            <el-button
              type="text"
              size="small"
              @click="
                singleObj = scope.row;
                isShowSingleDiv = true;
              "
            >查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="view-multi-comparision" v-if="isShowMultiDiv">
      <multiComparision :listData="listData" @closeMultiDiv="closeMultiDiv"></multiComparision>
    </div>
    <div class="view-single" v-if="isShowSingleDiv">
      <viewSingle
        :singleObj="singleObj"
        @closeDiv="
          isShowSingleDiv = false;
          singleObj = null;
        "
        @skipMulti="skipMulti"
      ></viewSingle>
    </div>
    <div class="detectlist" v-if="activeAirline">
      <div class="title">
        <span>当前航线：1</span>
        <el-tooltip class="item" effect="dark" content="关闭" placement="bottom-end">
          <el-button icon="el-icon-close" circle @click="activeAirline=false"></el-button>
        </el-tooltip>
      </div>
      <el-table :data="videoListData" style="background-color: white">
        <el-table-column type="index" label="序号"></el-table-column>
        <el-table-column property="videoName" label="视频名称"></el-table-column>
        <el-table-column property="operation" label="操作">
          <template slot-scope="scope">
            <el-button
              type="text"
              size="small"
              @click="showVideo(scope.row)"
            >查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div
      class="detect-list"
      v-show="dialogTableVisible">
      <div class="title">
        <el-tooltip class="item" effect="dark" content="添加至地图" placement="top">
          <el-button icon="iconfont icon-xiangjiaofenxi" circle @click="addToMap">
          </el-button>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="全屏" placement="top">
          <el-button icon=" iconfont icon-quantu1" circle @click="toggleFullScreen"></el-button>
        </el-tooltip>
        <span style="padding:0 10px">拍摄时间：{{ currentTopViewImageTime }}</span>
        <el-tooltip class="item" effect="dark" content="关闭" placement="top"
                    style="position:absolute;right:8px">
          <el-button icon="el-icon-close" circle @click="closeDetectDialog"></el-button>
        </el-tooltip>
      </div>
      <div class="collapsible-content">
        <div class="gt-query">
          <img ref="image" :src="currentImagePath" style="width:100%;height:100%"/>
        </div>
        <div class="block">
          <el-slider
            @input="handleInput"
            v-model="value"
            show-input>
          </el-slider>
        </div>
      </div>
    </div>

    <div v-show="videoDialogVisible" title="视频播放" class="video">
      <div class="close-btn">
        <el-tooltip class="item" effect="dark" content="关闭" placement="top"
                    style="position:absolute;right:8px">
          <el-button icon="el-icon-close" circle @click="videoDialogVisible=false"></el-button>
        </el-tooltip>
      </div>
      <video
        v-if="currentVideoUrl"
        :src="currentVideoUrl"
        controls
        autoplay
        style="width: 100%"
      ></video>
    </div>

    <div v-if="isFullScreen" class="fullscreen-container" ref="fullscreenContainer">
      <img :src="currentImagePath" class="fullscreen-image">
      <button @click="closeFullScreen" class="close-fullscreen-btn">×</button>
    </div>
  </div>
</template>

<script>
import {TiledMapLayer, GetFeaturesBySQLParameters, FeatureService, ImageTileLayer} from '@supermap/iclient-leaflet';
import '@supermap/iclient-leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import {
  getClueData,
  getPanoramaImageApi,
  getTimeAxisDataApi
} from '@/api/commonApi';
import {clearGraphical, drawPoint, measureArea, measureDistance} from '@/utils/utils';
import multiComparision from '@/views/dataManagement/oneMap/multiView/index.vue';
import viewSingle from '@/views/panoramicDetection/mapView/singlePeriodView/viewSingle.vue';
import timeAxis from '@/views/dataManagement/oneMap/timeAxis/index.vue';
import axios from 'axios';
import L from 'leaflet';
import { getLeafletVectorStyle } from '@/utils/vectorStyle';
import { create4528LeafletMap, createGeoCrs, createGeoBaseLayer } from '@/utils/map4528Loader';
import proj4 from 'proj4';
import { isWgs84LatLng, toMapLatLng } from '@/views/dataManagement/oneMap/oneMapCoords';

export default {
  name: 'Map2dPanel',
  components: {viewSingle, multiComparision, timeAxis},
  props: {
    treeData: {
      type: Array,
      default: () => []
    },
    initialCenter: {
      type: Array,
      default: () => window.config.center
    },
    initialZoom: {
      type: Number,
      default: () => window.config.zoom
    },
    /** 父组件同步的已勾选树节点，供时间轴切换时使用 */
    selectedNodes: {
      type: Array,
      default: () => []
    },
    mapReady: {
      type: Boolean,
      default: false
    },
    panoramaPointList: {
      type: Array,
      default: () => []
    },
    tempPointList: {
      type: Array,
      default: () => []
    },
    topViewList: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      isFullScreen: false,
      dialogTableVisible: false,
      currentImagePath: '',
      currentTopViewImageTime: '',
      currentImageBounds: [],
      overlay: null,
      value: 70,
      uniquekey: 1,
      isShowMultiDiv: false,
      leftObj: null,
      rightObj: null,
      isShowSingleDiv: false,
      singleObj: null,
      listData: [],
      activePanoramaPoint: null,
      activeMarker: null,
      targetDivPosition: {x: 0},
      activeToolBarIndex: 0,
      map: null,
      formInfo: {
        keyword: '',
      },
      tabName: 'first',
      clusterLayer: L.markerClusterGroup(),
      panoramaPointLayer: L.layerGroup(),
      tempPanoramaPointLayer: L.layerGroup(),
      nestLayer: L.layerGroup(),
      neatBufferLayer: L.layerGroup(),
      bufferLayer: L.layerGroup(),
      tempbufferLayer: L.layerGroup(),
      topViewLayer: L.layerGroup(),
      clueList: [],
      nestList: [],
      currentHighlightedLayer: null,
      hxOrWg: '',
      activeAirline: false,
      videoListData: [],
      videoDialogVisible: false,
      currentVideoUrl: '',
      aerialPhotoLayer: L.markerClusterGroup(),
      timeAxisData: [],
      selectTime: '',
      selectNodes: [],
      mapBounds: [],
      center: window.config.center,
      circleRadius: window.config.circleRadius,
      PhotoDataList: [],
      topViewMarker: [],
      singleToMultiTag: false,
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMapUse4528: window.config.baseMapUse4528 === true,
      baseMap4528Epsg: window.config.baseMap4528Epsg || 'EPSG:4528',
      baseMap4528Proj: window.config.baseMap4528Proj,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      _crsMaxZoom: null,
      _serviceFitBounds: null,
      _mapInitPromise: null,
      layerRandList: [],
      minZoom: window.config.minZoom,
      maxZoom: window.config.maxZoom,
      zoom: window.config.zoom,
      projectCity: window.config.projectCity,
      currentShowZoom: window.config.zoom,
      _pendingViewState: null,
      baseMapLayer: null,
      _resizeObserver: null,
      _resizeDebounceTimer: null,
      _onWindowResize: null
    };
  },
  created() {
    /** 图层实例与树节点解耦，避免 Leaflet 对象进入 Vue 响应式导致栈溢出 */
    this.layerByLabel = new Map();
    this._pendingPanoramaRefresh = false;
  },
  computed: {
    targetDivStyle() {
      return {
        transform: `translateX(${this.targetDivPosition.x}px)`
      };
    }
  },
  watch: {
    initialCenter: {
      handler(val) {
        if (Array.isArray(val) && val.length === 2) {
          this.center = [val[0], val[1]];
          if (this.map) {
            this.applyApiCenterView();
          }
        }
      },
      deep: true,
      immediate: true
    },
    mapReady(val) {
      if (val) {
        this.tryInitMap();
      }
    },
    activeMarker(newValue, oldValue) {
      const defaultIconRed = L.icon({
        iconUrl: require('@/assets/images/marker-icon-red.png'),
        iconSize: [25, 40],
        iconAnchor: [12.5, 40],
        popupAnchor: [-3, -40]
      });
      const defaultIconBlue = L.icon({
        iconUrl: require('@/assets/images/marker-icon-blue.png'),
        iconSize: [25, 40],
        iconAnchor: [12.5, 40],
        popupAnchor: [-3, -40]
      });
      if (newValue) {
        const newMarker = this.clusterLayer.getLayers().filter((item) => item.options.clue_id === newValue.clue_id)[0];
        if (newMarker) {
          newMarker.setIcon(defaultIconRed);
          newMarker.setZIndexOffset(10);
        }
      }
      if (oldValue) {
        const oldMarker = this.clusterLayer.getLayers().filter((item) => item.options.clue_id === oldValue.clue_id)[0];
        if (oldMarker) {
          oldMarker.setIcon(defaultIconBlue);
          oldMarker.setZIndexOffset(1);
        }
      }
      this.clusterLayer.refreshClusters();
    },
    activePanoramaPoint(newValue, oldValue) {
      if (newValue) {
        const newCircle = this.panoramaPointLayer.getLayers().filter((item) => item.options.pointID === newValue.pointId)[0];
        if (newCircle) {
          newCircle.setStyle({
            color: 'red',
            fillColor: 'red',
            fillOpacity: 0.4,
            opacity: 0.4,
            weight: 2,
            pointID: newValue.pointId
          });
          newCircle.setRadius(150);
        }
      }
      if (oldValue) {
        const oldCircle = this.panoramaPointLayer.getLayers().filter((item) => item.options.pointID === oldValue.pointId)[0];
        if (oldCircle) {
          oldCircle.setStyle({
            color: 'orange',
            fillColor: 'orange',
            fillOpacity: 0.1,
            opacity: 0.4,
            weight: 2,
            pointID: oldValue.pointId
          });
          oldCircle.setRadius(80);
        }
      }
    },
    activeAirline(newValue) {
      if (!newValue) {
        if (this.currentHighlightedLayer != null) {
          this.currentHighlightedLayer.setStyle({
            color: 'red',
            weight: 2,
            fillOpacity: 0.3
          });
        }
      }
    },
    panoramaPointList(newValue) {
      if (!newValue || !newValue.length) {

        return;
      }

      if (!this.map) {

        this._pendingPanoramaRefresh = true;
        return;
      }
      this.refreshBusinessLayersIfChecked(['panorama', 'panorama_coverage']);
    },
    topViewList(newValue) {
      if (!newValue) return;

      if (!this.map) return;
      this.topViewLayer.clearLayers();
      this.getTopViewLayerData();
    },
    tempPointList(newValue) {
      if (!newValue || !newValue.length) {

        return;
      }

      if (!this.map) {

        return;
      }
      this.refreshBusinessLayersIfChecked(['temp_panorama', 'temp_panorama_coverage']);
    },
    treeData: {
      handler(data) {
        this.syncBusinessDataFromTree(data);
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    syncBusinessDataFromTree(data) {
      if (!data || !data.length) return;
      data.forEach((item) => {
        if (item.label === '低空业务数据' && item.children) {
          const nestNode = item.children.find((i) => i.data_type === 'nest_location');
          if (nestNode) {
            this.nestList = nestNode.data ? nestNode.data : [];
            if (!nestNode.data || !nestNode.data.length) {

            }
          }
          const clueNode = item.children.find((i) => i.data_type === 'clue');
          if (clueNode) {
            this.clueList = clueNode.data ? clueNode.data : [];
          }
        }
      });

    },

    resolveLayerType(node) {
      if (!node) return null;
      const t = (node.data_type || '').toLowerCase();
      const label = node.label || '';
      if (t === 'panorama' || label === '全景点') return 'panorama';
      if (t === 'panorama_coverage' || label.includes('全景覆盖')) return 'panorama_coverage';
      if (t === 'temp_panorama_coverage' || (label.includes('临时') && label.includes('覆盖'))) {
        return 'temp_panorama_coverage';
      }
      if (t === 'temp_panorama' || label.includes('临时全景点')) return 'temp_panorama';
      if (t === 'nest_location' || (label.includes('机巢') && !label.includes('覆盖'))) {
        return 'nest_location';
      }
      if (t === 'nest_coverage' || label.includes('机巢覆盖')) return 'nest_coverage';
      if (t === 'clue' || label === '线索') return 'clue';
      if (t === 'top_view' || label.includes('俯视')) return 'top_view';
      if (label === '航片') return 'aerial_photo';
      return t || null;
    },

    buildLayerForNode(node) {
      const layerType = this.resolveLayerType(node);
      switch (layerType) {
        case 'clue':
          return this.getClueData(node);
        case 'panorama':
          return this.getPanoramaPointData(node);
        case 'panorama_coverage':
          return this.getBufferData(node);
        case 'temp_panorama_coverage':
          return this.getTempBufferData(node);
        case 'temp_panorama':
          return this.getTempPointData(node);
        case 'nest_location':
          return this.getNestData(node);
        case 'nest_coverage':
          return this.getNestBufferData(node);
        case 'top_view':
          return this.getTopViewLayerData();
        case 'aerial_photo':
          return null;
        default:
          return undefined;
      }
    },

    refreshBusinessLayersIfChecked(layerTypes) {
      if (!this.map) return;
      const typeSet = new Set(layerTypes);
      (this.selectedNodes || []).forEach((node) => {
        const layerType = this.resolveLayerType(node);
        if (!layerType || !typeSet.has(layerType)) return;
        const layer = this.buildLayerForNode(node);
        if (!layer) return;
        if (!this.map.hasLayer(layer)) {
          this.map.addLayer(layer);
        }
        this.setNodeLayer(node, layer);

      });
    },

    countLayerChildren(layer) {
      if (!layer) return 0;
      return layer.getLayers ? layer.getLayers().length : 0;
    },

    collectPointsForLayerType(layerType) {
      switch (layerType) {
        case 'panorama':
        case 'panorama_coverage':
          return this.panoramaPointList || [];
        case 'temp_panorama':
        case 'temp_panorama_coverage':
          return this.tempPointList || [];
        case 'nest_location':
        case 'nest_coverage':
          return this.nestList || [];
        default:
          return [];
      }
    },

    dedupePointsByLatLng(points) {
      const seen = new Set();
      return (points || []).filter((p) => {
        if (!p || p.latitude == null || p.longitude == null) return false;
        const key = `${p.latitude},${p.longitude}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      });
    },

    /** 地图是否已设置 center/zoom（Leaflet 未设置时会抛错） */
    isMapViewReady() {
      if (!this.map) return false;
      try {
        this.map.getZoom();
        return true;
      } catch (e) {
        return false;
      }
    },

    /** 确保地图有初始视野，避免 "Set map center and zoom first" */
    ensureMapHasView(reason) {
      if (!this.map) return false;
      if (this.isMapViewReady()) return true;
      return this.applyApiCenterView();
    },

    /** 定位到 getOneMapApi 返回的项目中心点 */
    applyApiCenterView() {
      if (!this.map) return false;
      const center = this.resolveMapCenter();
      const zoom = this._crsMaxZoom != null ? Math.min(this.zoom, this._crsMaxZoom) : this.zoom;
      this.map.setView(center, zoom);
      this.syncZoomDisplay();
      return true;
    },

    /** 定位到点位范围，并在控制台输出 flyTo 日志 */
    flyToPointList(points, reason) {
      if (!this.map) {

        return false;
      }
      this.ensureMapHasView(reason);
      const valid = this.dedupePointsByLatLng(points);
      if (!valid.length) {

        return false;
      }
      const latLngs = valid.map((p) => toMapLatLng(p.latitude, p.longitude));
      const before = this.getViewState();
      const mapMax = this.map.getMaxZoom();
      const mapMin = this.map.getMinZoom();
      const minFlyZoom = Math.min(mapMax, Math.max(14, mapMin));

      if (latLngs.length === 1) {
        this.map.setView(latLngs[0], minFlyZoom);
        this.syncZoomDisplay();

      } else {
        const bounds = L.latLngBounds(latLngs);
        this.map.fitBounds(bounds, { padding: [50, 50], maxZoom: minFlyZoom });
        let finalZoom = this.map.getZoom();
        const center = bounds.getCenter();
        if (finalZoom < minFlyZoom) {
          this.map.setView(center, minFlyZoom);
          finalZoom = minFlyZoom;

        }
        this.syncZoomDisplay();

      }
      return true;
    },

    syncZoomDisplay() {
      if (!this.map || !this.isMapViewReady()) return;
      this.currentShowZoom = Math.floor(this.map.getZoom());
      this.$emit('zoom-change', this.currentShowZoom);
    },

    flyToCheckedBusinessPoints(reason, layerTypes, checkedNodes) {
      const types = layerTypes || [
        'panorama',
        'panorama_coverage',
        'temp_panorama',
        'temp_panorama_coverage',
        'nest_location',
        'nest_coverage'
      ];
      const typeSet = new Set(types);
      const nodes = checkedNodes || this.selectedNodes || [];
      const points = [];
      nodes.forEach((node) => {
        const layerType = this.resolveLayerType(node);
        if (layerType && typeSet.has(layerType)) {
          points.push(...this.collectPointsForLayerType(layerType));
        }
      });
      const unique = this.dedupePointsByLatLng(points);

      return this.flyToPointList(unique, reason);
    },

    /** 供父组件 ref 调用：初始化地图并应用待恢复的视图状态 */
    async initMap2d() {
      await this.initMap();
      if (this._pendingViewState) {
        this.setViewState(this._pendingViewState);
        this._pendingViewState = null;
      }
      await this.applyPendingPanoramaRefresh();
      await this.$nextTick();
      this.scheduleInvalidateSize();
    },

    /** 等待异步地图初始化完成（供父组件在 applyTreeCheck 前调用） */
    async waitForMapReady() {
      if (this.map) return;
      if (!this._mapInitPromise && this.mapReady) {
        this.tryInitMap();
      }
      if (this._mapInitPromise) {
        await this._mapInitPromise;
      }
    },

    tryInitMap() {
      if (this.map || !this.mapReady) return;
      if (this._mapInitPromise) return;
      this._mapInitPromise = this._doTryInitMap();
    },

    async _doTryInitMap() {

      try {
        await this.initMap();
        this.getTimePhotoData({ time: '' });
        await this.$nextTick();
        this.scheduleInvalidateSize();
        await this.applyPendingPanoramaRefresh();

      } catch (err) {

      } finally {
        this._mapInitPromise = null;
      }
    },

    getMapContainerEl() {
      return this.$refs.mapContainer || document.getElementById('mapContainer');
    },

    /** 地图就绪后补绘全景点（解决数据先于 map 到达的竞态） */
    async applyPendingPanoramaRefresh() {
      if (!this.map) return;
      if (!this._pendingPanoramaRefresh) return;
      if (!this.panoramaPointList || !this.panoramaPointList.length) {
        this._pendingPanoramaRefresh = false;
        return;
      }
      this.drawPanoramaLayersOnMap();
      this._pendingPanoramaRefresh = false;
    },

    /** 绘制全景点/覆盖范围并挂到 map（样式对齐 mapView） */
    drawPanoramaLayersOnMap() {
      if (!this.map || !this.panoramaPointList || !this.panoramaPointList.length) {
        return;
      }
      this.ensureMapHasView('drawPanoramaLayersOnMap');
      this.getPanoramaPointData(null);
      this.getBufferData(null);
      if (!this.map.hasLayer(this.panoramaPointLayer)) {
        this.map.addLayer(this.panoramaPointLayer);
      }
      if (!this.map.hasLayer(this.bufferLayer)) {
        this.map.addLayer(this.bufferLayer);
        this.bufferLayer.eachLayer((layer) => {
          if (layer.bringToBack) layer.bringToBack();
        });
      }

    },

    scheduleInvalidateSize() {
      if (this._resizeDebounceTimer) {
        clearTimeout(this._resizeDebounceTimer);
      }
      this._resizeDebounceTimer = setTimeout(() => {
        this._resizeDebounceTimer = null;
        this.invalidateMapSize();
      }, 100);
    },

    invalidateMapSize() {
      if (this.map) {
        this.map.invalidateSize();

      }
    },

    bindMapResizeListeners() {
      this.unbindMapResizeListeners();
      if (!this.map) return;
      const el = this.getMapContainerEl();
      if (!el) return;
      this._onWindowResize = () => this.scheduleInvalidateSize();
      window.addEventListener('resize', this._onWindowResize);
      if (typeof ResizeObserver !== 'undefined') {
        this._resizeObserver = new ResizeObserver(() => this.scheduleInvalidateSize());
        this._resizeObserver.observe(el);
      }
    },

    unbindMapResizeListeners() {
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

    destroyMap() {
      this.unbindMapResizeListeners();
      if (this.map) {
        this.map.off();
        this.map.remove();
        this.map = null;
      }
      if (this.layerByLabel) {
        this.layerByLabel.clear();
      }
    },

    /** 切换 2D/3D 前重置弹窗与选中态，避免 v-show 隐藏后面板仍保留 UI */
    resetPanelUi() {
      this.activePanoramaPoint = null;
      this.activeMarker = null;
      this.activeAirline = false;
      this.isShowMultiDiv = false;
      this.isShowSingleDiv = false;
      this.singleObj = null;
      this.leftObj = null;
      this.rightObj = null;
      this.singleToMultiTag = false;
      this.dialogTableVisible = false;
      this.videoDialogVisible = false;
      this.currentVideoUrl = '';
      this.isFullScreen = false;
      this.targetDivPosition = { x: 0 };
      if (this.map && this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.overlay = null;
    },

    getLayerKey(node) {
      return node && node.label;
    },

    setNodeLayer(node, layer) {
      const key = this.getLayerKey(node);
      if (key != null && layer) {
        layer._treeLabel = key;
        this.layerByLabel.set(key, layer);
      }
    },

    getNodeLayer(node) {
      const key = this.getLayerKey(node);
      return key != null ? this.layerByLabel.get(key) : null;
    },

    detachNodeLayer(node) {
      const key = this.getLayerKey(node);
      const layer = key != null ? this.layerByLabel.get(key) : null;
      if (!layer || !this.map) {
        if (key != null) {
          this.layerByLabel.delete(key);
        }
        return;
      }
      this.map.removeLayer(layer);
      if (layer._zoomHandler) {
        this.map.off('zoomend', layer._zoomHandler);
      }
      if (layer._imageLayers) {
        Object.values(layer._imageLayers).forEach((childLayer) => {
          this.map.removeLayer(childLayer);
        });
      }
      this.layerByLabel.delete(key);
      if (Object.prototype.hasOwnProperty.call(node, 'layer')) {
        delete node.layer;
      }
    },

    /** 以树勾选为准同步图层，避免 prev 差集与异步加载竞态导致无法移除 */
    async syncLayers(checkedLeafNodes) {
      if (!this.map) {

        return;
      }
      this.ensureMapHasView('syncLayers');
      const checkedLabels = new Set(
        checkedLeafNodes.map((node) => this.getLayerKey(node)).filter((key) => key != null)
      );
      const existingKeys = [...this.layerByLabel.keys()];



      for (const label of existingKeys) {
        if (!checkedLabels.has(label)) {
          this.detachNodeLayer({ label });
        }
      }

      this.map.eachLayer((layer) => {
        const label = layer._treeLabel;
        if (label && !checkedLabels.has(label) && this.map.hasLayer(layer)) {
          this.map.removeLayer(layer);
          this.layerByLabel.delete(label);
        }
      });

      const toAdd = checkedLeafNodes.filter((node) => !this.layerByLabel.has(this.getLayerKey(node)));
      if (toAdd.length) {
        await this.addLayers(toAdd);
      }
    },

    getViewState() {
      if (!this.map || !this.isMapViewReady()) return null;
      const c = this.map.getCenter();
      return {
        center: { lat: c.lat, lng: c.lng },
        zoom: this.map.getZoom()
      };
    },

    setViewState({center, zoom}) {
      if (!this.map) {
        this._pendingViewState = {center, zoom};
        return;
      }
      if (center && zoom != null) {
        this.map.setView([center.lat, center.lng], zoom);
      }
    },

    flyToHome() {
      this.applyApiCenterView();
    },

    flyTo(lat, lng, zoom = 16) {
      if (!this.map) return
      this.map.flyTo([lat, lng], zoom, { duration: 1.5 })
    },

    flyToRegion(lat, lng, polygon) {
      if (!this.map) return
      if (polygon && polygon.length > 0) {
        // 用 polygon 构建 bounds，自适应缩放确保一次看到所有轮廓
        const rings = polygon.map(ring => ring.map(p => [p.lat, p.lng]))
        const tempLayer = L.polygon(rings)
        const bounds = tempLayer.getBounds()
        tempLayer.remove()
        const mapMax = this.map.getMaxZoom()
        this.map.flyToBounds(bounds, { padding: [30, 30], maxZoom: mapMax, duration: 1.5 })
      } else {
        // 无 polygon 回退到点定位
        this.map.flyTo([lat, lng], 16, { duration: 1.5 })
      }
    },

    drawRegion(polygon, name, lat, lng, subRegions) {
      if (!this.map) return
      // 清除上一个区域
      if (this._regionLayers) { this._regionLayers.forEach(l => this.map.removeLayer(l)); this._regionLayers = null }
      if (!polygon || !polygon.length) return

      this._regionLayers = []
      const rings = polygon.map(ring => ring.map(p => [p.lat, p.lng]))

      // 主区域半透明
      const mainLayer = L.polygon(rings, {
        color: '#ccc', weight: 1.5, fillColor: '#ccc', fillOpacity: 0.05,
      }).addTo(this.map)
      this._regionLayers.push(mainLayer)

      // 子区域用不同颜色
      if (subRegions && subRegions.length) {
        subRegions.forEach(region => {
          if (!region.polygon || !region.polygon.length) return
          const rRings = region.polygon.map(ring => ring.map(p => [p.lat, p.lng]))
          const layer = L.polygon(rRings, {
            color: region.color || '#f56c6c', weight: 2,
            fillColor: region.color || '#f56c6c', fillOpacity: 0.2,
          }).addTo(this.map)
          if (region.name) layer.bindTooltip(region.name, { permanent: false, direction: 'center' })
          this._regionLayers.push(layer)
        })
      } else {
        // 无子区域：红色
        mainLayer.setStyle({ color: '#f56c6c', weight: 2, fillColor: '#f56c6c', fillOpacity: 0.15 })
      }

      // 飞到区域中心
      if (lat != null && lng != null) this.map.flyTo([lat, lng], 14, { duration: 1.2 })
      else if (rings[0] && rings[0].length) this.map.fitBounds(mainLayer.getBounds(), { padding: [30, 30], maxZoom: 16 })
    },

    getZoom() {
      return this.currentShowZoom;
    },

    toggleFullScreen() {
      this.isFullScreen = true;
      this.$nextTick(() => {
        const elem = this.$refs.fullscreenContainer;
        if (elem.requestFullscreen) {
          elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
          elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
          elem.msRequestFullscreen();
        }
      });
    },
    closeFullScreen() {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      this.isFullScreen = false;
    },
    handleInput(val) {
      const value = val / 100;
      if (this.overlay) {
        this.overlay.setOpacity(value);
      }
    },
    addToMap() {
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.overlay = L.imageOverlay(this.currentImagePath, this.currentImageBounds, {
        opacity: 0.5,
        interactive: true
      }).addTo(this.map);
    },
    closeMultiDiv() {
      this.isShowMultiDiv = false;
      if (this.singleToMultiTag) {
        this.isShowSingleDiv = true;
      }
    },
    skipMulti() {
      this.isShowMultiDiv = true;
      this.isShowSingleDiv = false;
      this.singleToMultiTag = true;
    },
    closeDetectDialog() {
      this.dialogTableVisible = false;
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.topViewMarker.forEach((mData) => {
        mData.marker.setIcon(mData.customIcon);
      });
    },
    drawPointActive() {
      if (this.activeToolBarIndex === 2) {
        this.activeToolBarIndex = 0;
      }
    },
    measureActive() {
      if (this.activeToolBarIndex > 2) {
        this.activeToolBarIndex = 0;
      }
    },
    drawPoint() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.map.off('contextmenu');
      this.activeToolBarIndex = 2;
      drawPoint(this.map, 5);
    },
    measureLength() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.map.off('contextmenu');
      this.activeToolBarIndex = 3;
      measureDistance(this.map);
    },
    startDrawPolygon() {
      this.map.off('mousedown');
      this.map.off('mousemove');
      this.map.off('dblclick');
      this.map.off('contextmenu');
      this.activeToolBarIndex = 4;
      measureArea(this.map);
    },
    clearDraw() {
      this.activeToolBarIndex = 0;
      clearGraphical(this.map);
    },

    resolveMapCenter() {
      const c = this.center;
      if (!c || c.length !== 2) {

        return window.config.center;
      }
      const lat = Number(c[0]);
      const lng = Number(c[1]);
      if (this.baseMapUse4528 && !isWgs84LatLng(lat, lng)) {
        const converted = toMapLatLng(lat, lng);

        return converted;
      }

      return [lat, lng];
    },

    addBaseLayerToList(name) {
      this.layerRandList.unshift({
        name,
        layer: this.baseMapLayer,
        shapeOption: {
          opacity: 1,
          brightness: 1,
          contrast: 1,
          saturation: 1
        },
        show: true,
        expanded: false,
        source_type: '底图'
      });
    },

    finishMapSetup() {
      if (!this.map) return;
      L.control.zoom({ position: 'bottomright' }).addTo(this.map);
      const zoomHandler = () => {
        this.syncZoomDisplay();
      };
      zoomHandler();
      this.map.on('zoomend', zoomHandler);
      this.bindMapResizeListeners();
    },

    async initMap() {
      if (this.map) {
        this.map.remove();
        this.map = null;
      }

      try {
        if (this.baseMapUse4528 && this.baseMapService) {
          await this.init4528Map();
        } else {
          this.initLegacyMap();
        }
      } catch (err) {

        this.$message.error('底图加载失败：' + (err.message || '请检查服务地址'));
        throw err;
      }
    },

    async init4528Map() {
      const container = this.getMapContainerEl();
      if (!container) {
        throw new Error('mapContainer 元素未找到');
      }
      const hasPanoramaPoints = this.panoramaPointList && this.panoramaPointList.length > 0;
      const result = await create4528LeafletMap(container, {
        serviceUrl: this.baseMapService,
        serviceType: this.baseMapServiceType,
        epsgCode: this.baseMap4528Epsg,
        projDef: this.baseMap4528Proj,
        initialZoom: this.zoom,
        center: this.resolveMapCenter(),
        mapBounds: this.mapBounds.length > 0 ? this.mapBounds : null,
        initialView: 'none'
      });

      this.map = result.map;
      this.baseMapLayer = result.baseMapLayer;
      this._crsMaxZoom = result.maxZoom;
      this._serviceFitBounds = result.fitBounds;



      if (this.mapBounds.length > 0) {

      } else if (result.fitBounds && result.fitBounds.isValid()) {

      }

      this.addBaseLayerToList('底图(4528)');
      this.finishMapSetup();
      this.applyApiCenterView();

      if (hasPanoramaPoints) {
        this.drawPanoramaLayersOnMap();
      }

      await this.$nextTick();
      if (this.map) {
        this.map.invalidateSize();
      }

    },

    initLegacyMap() {

      let myCrs = null;
      if (this.projectCity === 'nanjing') {
        myCrs = L.CRS.EPSG3857;
      } else if (this.projectCity === 'jiangyin') {
        const crsResolutions = [];
        let res = 78183.89453125001;
        for (let i = 0; i < 20; i++) {
          crsResolutions.push(res);
          res /= 2;
        }
        proj4.defs('EPSG:4528', '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs');
        myCrs = new L.Proj.CRS('EPSG:4528', {
          resolutions: crsResolutions
        });
        this._crsMaxZoom = crsResolutions.length - 1;
      } else {
        myCrs = createGeoCrs(this.projectCity);
      }
      const mapCenter = this.resolveMapCenter();
      const mapZoom = this.zoom;
      const mapMaxZoom = this._crsMaxZoom != null
        ? Math.min(this.maxZoom, this._crsMaxZoom)
        : this.maxZoom;
      this.map = L.map(this.getMapContainerEl() || 'mapContainer', {
        crs: myCrs,
        zoom: mapZoom,
        zoomControl: false,
        center: mapCenter,
        attributionControl: false,
        preferCanvas: true,
        maxZoom: mapMaxZoom,
        minZoom: this.minZoom
      });
      if (this.mapBounds.length > 0) {
        this.map.fitBounds(this.mapBounds);
      }

      if (this.baseMapService) {
        if (this.projectCity !== 'jiangyin' && this.projectCity !== 'nanjing') {
          this.baseMapLayer = createGeoBaseLayer(this.baseMapService, this.baseMapServiceType, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            minZoom: this.minZoom
          });
        } else if (this.baseMapServiceType === '1') {
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
        if (this.baseMapLayer) {
          this.baseMapLayer.addTo(this.map);
          this.baseMapLayer.bringToBack();
          this.addBaseLayerToList('底图');
        }
      }
      this.finishMapSetup();

    },

    getTopViewLayerData() {
      const customIcon = L.icon({
        iconUrl: require('@/assets/images/topBlue.png'),
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      const redIcon = L.icon({
        iconUrl: require('@/assets/images/topRed.png'),
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      if (this.topViewList.length > 0) {
        this.topViewList.map(item => {
          const bounds = JSON.parse(item.bounds);
          const marker = L.marker(bounds[0], {icon: customIcon});
          const markerData = {
            marker,
            customIcon: customIcon,
            redIcon: redIcon
          };
          this.topViewMarker.push(markerData);
          this.topViewLayer.addLayer(marker);
          marker.on('click', () => {
            this.dialogTableVisible = true;
            this.currentImagePath = '/panoramaUrl' + item.path;
            this.currentImageBounds = bounds;
            this.currentTopViewImageTime = item.collect_time;
            this.topViewMarker.forEach((mData) => {
              mData.marker.setIcon(mData.customIcon);
            });
            marker.setIcon(redIcon);
            this.map.setView(bounds[0], 16);
          });
        });
      }
      return this.topViewLayer;
    },

    async addLayers(addLeafNodes) {
      if (!this.map) {

        return;
      }
      for (const node of addLeafNodes) {
        const key = this.getLayerKey(node);
        if (key != null && this.layerByLabel.has(key)) {
          continue;
        }
        const layerType = this.resolveLayerType(node);
        let layer;
        if (node.source_type === '业务矢量数据服务' && node.datasets_name) {
          layer = await this.getVectorData(node);
        } else if (layerType === 'aerial_photo') {
          layer = await this.getAerialPhotoLayer();
        } else {
          const businessLayer = this.buildLayerForNode(node);
          if (businessLayer !== undefined) {
            layer = businessLayer;
          } else if (node.label !== '航片') {

            if (node.gis_service_type === '1') {
              layer = new TiledMapLayer(node.service, {
                maxZoom: this.maxZoom,
                maxNativeZoom: this.maxZoom,
                reuseTiles: false,
                updateWhenIdle: true,
                updateInterval: 200,
                keepBuffer: 1,
                noWrap: true
              });
            } else if (node.gis_service_type === '2') {
              layer = L.tileLayer(`${node.service}/tile/{z}/{y}/{x}`, {
                maxZoom: this.maxZoom,
                minZoom: this.minZoom,
                pane: 'tilePane',
                updateWhenIdle: false,
                updateWhenZooming: false,
                keepBuffer: 3,
                updateInterval: 200,
                noWrap: true
              }).addTo(this.map);
            } else if (node.gis_service_type === '3') {
              layer = L.tileLayer(node.service, {}).addTo(this.map);
            } else {
              layer = L.tileLayer.wms(node.service, {
                layers: `${node.datasource_name}:${node.datasets_name}`,
                format: 'image/png',
                transparent: true,
                attribution: 'Your Attribution'
              });
            }
          } else {
            layer = await this.getAerialPhotoLayer();
          }
        }

        if (layer && this.map) {
          if (!this.map.hasLayer(layer)) {
            this.map.addLayer(layer);
          }
          this.setNodeLayer(node, layer);

        } else {

        }
      }
    },

    removeLayers(deleteLeafNodes) {
      if (!this.map) return;
      deleteLeafNodes.forEach((node) => {
        this.detachNodeLayer(node);
      });
    },

    async getAerialPhotoLayer() {
      if (this.aerialPhotoLayer) {
        this.aerialPhotoLayer.clearLayers();
        if (this.map && this.map.hasLayer(this.aerialPhotoLayer)) {
          this.map.removeLayer(this.aerialPhotoLayer);
        }
      }

      const layerGroup = await this.createAggregateMarker();
      const imageLayers = {};
      let isShowingImagery = false;
      layerGroup._imageLayers = imageLayers;

      const zoomHandler = () => {
        const zoom = this.map.getZoom();
        if (zoom >= 14) {
          if (!isShowingImagery) {
            layerGroup.eachLayer(marker => {
              const bbox = marker._bbox;
              const bboxBounds = L.latLngBounds(
                L.latLng(bbox[1], bbox[0]),
                L.latLng(bbox[3], bbox[2])
              );
              if (this.map.getBounds().intersects(bboxBounds)) {
                if (marker._imageService && !imageLayers[marker._imageService + `+${marker._timeName}`]) {
                  const imageLayer = new ImageTileLayer(marker._imageService, {
                    collectionId: marker._tiffServiceCollection,
                    names: [marker._timeName],
                    maxZoom: this.maxZoom
                  });
                  imageLayers[marker._imageService + `+${marker._timeName}`] = imageLayer;
                  this.map.addLayer(imageLayer);
                }
              }
            });
            isShowingImagery = true;
          }
        } else {
          if (isShowingImagery) {
            Object.values(imageLayers).forEach(layer => {
              this.map.removeLayer(layer);
            });
            for (const key in imageLayers) {
              delete imageLayers[key];
            }
            isShowingImagery = false;
          }
        }
      };

      this.map.on('zoomend', zoomHandler);
      layerGroup._zoomHandler = zoomHandler;
      this.aerialPhotoLayer = layerGroup;
      return this.aerialPhotoLayer;
    },

    async createAggregateMarker() {
      const layerGroup = L.markerClusterGroup({
        disableClusteringAtZoom: 14,
        spiderfyOnMaxZoom: false,
        showCoverageOnHover: false,
        singleMarkerMode: true,
        iconCreateFunction: function (cluster) {
          const count = cluster.getChildCount();
          return L.divIcon({
            html: '<div><span>' + count + '个</span></div>',
            className: 'marker-cluster marker-cluster-' +
              (count < 10 ? 'small' : count < 100 ? 'medium' : 'large'),
            iconSize: new L.Point(40, 40)
          });
        }
      });
      for (const item of this.PhotoDataList) {
        if (item.tiffCenter !== '') {
          const center = item.tiffCenter.split(',').map(item => parseFloat(item));
          const defaultIconBlue = L.icon({
            iconUrl: require('@/assets/images/marker-icon-blue.png'),
            iconSize: [25, 40],
            iconAnchor: [12.5, 40],
            popupAnchor: [-3, -40]
          });
          const marker = L.marker(center, {icon: defaultIconBlue});
          marker._imageService = window.config.iserverAdress;
          marker._imageCenter = center;
          marker._tiffServiceCollection = item.tiffServiceCollection;
          marker._timeName = item.timeName;
          const bbox = await this.cacuBounds(item.tiffId, item.tiffServiceCollection);
          marker._bbox = bbox;
          layerGroup.addLayer(marker);
        }
      }
      return layerGroup;
    },

    async cacuBounds(tiffId, tiffServiceCollection) {
      if (tiffId == '' || tiffServiceCollection == '') {
        this.$message.error('航片数据不全，无法计算边界，导致无法显示影像');
      }
      try {
        const res = await axios.get(
          `${window.config.iserverAdress}collections/${tiffServiceCollection}/items/${tiffId}.json`,
          {withCredentials: false}
        );
        return res.data.properties['proj:bbox'];
      } catch (err) {
        console.error(err);
        return null;
      }
    },

    getFeaturesBySQLAsync(featureService, params) {
      return new Promise((resolve, reject) => {
        featureService.getFeaturesBySQL(params, (serviceResult) => {
          if (serviceResult && serviceResult.result) {
            resolve(serviceResult.result);
          } else {
            reject(new Error('No features found or invalid response'));
          }
        });
      });
    },

    async getVectorData(node) {
      const vectorStyle = getLeafletVectorStyle(node);
      if (node.gis_service_type === '1') {
        try {
          this.hxOrWg = (node.label && node.label.includes('航线')) ? 'hx' : 'wg';
          var sqlParam = new GetFeaturesBySQLParameters({
            queryParameter: {
              name: `${node.datasets_name}@${node.datasource_name}`,
              attributeFilter: '1=1'
            },
            datasetNames: [`${node.datasource_name}:${node.datasets_name}`]
          });
          const vectorData = [];
          const featureService = await new FeatureService(node.service);
          const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
          serviceResult.features.features.forEach((item) => {
            vectorData.push(item);
          });
          if (vectorData.length > 0) {
            const geojsonFeature = {
              type: 'FeatureCollection',
              features: vectorData
            };
            return L.geoJSON(geojsonFeature, {
              style: vectorStyle,
              onEachFeature: (feature, layer) => this.onEachFeature(feature, layer)
            });
          }
        } catch (error) {
          this.$message.error('加载矢量数据错误！');
        }
      } else {
        var urlString = node.service + '/' + node.datasource_name;
        var param = {
          service: 'WFS',
          version: '1.1.0',
          request: 'GetFeature',
          typeName: node.datasets_name,
          outputFormat: 'application/json',
          maxFeatures: 20000,
          srsName: 'EPSG:4326'
        };
        var u = urlString + L.Util.getParamString(param, urlString);
        const response = await axios.get(u);
        return L.geoJson(response.data, {
          style: vectorStyle
        });
      }
    },

    onEachFeature(feature, layer) {
      if (this.hxOrWg == 'hx') {
        layer.on({
          click: (e) => {
            if (this.currentHighlightedLayer) {
              this.currentHighlightedLayer.setStyle({
                color: 'red',
                weight: 2,
                fillOpacity: 0.3
              });
            }
            layer.setStyle({
              color: 'yellow',
              weight: 4,
              fillOpacity: 0.7
            });
            this.currentHighlightedLayer = layer;
            this.activePanoramaPoint = false;
            this.activeAirline = true;
            this.getVideoData();
            e.originalEvent.preventDefault();
          }
        });
      }
    },

    getClueData(node) {
      this.clusterLayer.clearLayers();
      const defaultIconBlue = L.icon({
        iconUrl: require('@/assets/images/marker-icon-blue.png'),
        iconSize: [25, 40],
        iconAnchor: [12.5, 40],
        popupAnchor: [-3, -40]
      });
      this.clueList.forEach((item) => {
        const marker = L.marker(toMapLatLng(item.latitude, item.longitude), {
          icon: defaultIconBlue,
          clue_id: item.clue_id
        });
        marker.bindPopup(item.clue_name);
        marker.on('click', () => {
          this.activeMarker = item;
        });
        this.clusterLayer.addLayer(marker);
      });
      return this.clusterLayer;
    },

    getPanoramaPointData(node) {
      if (!this.map) {

        return this.panoramaPointLayer;
      }
      const numberLabels = [];
      this.panoramaPointLayer.clearLayers();
      let drawnCount = 0;
      if (this.panoramaPointList.length > 0) {
        if (node) {
          node.center = JSON.stringify(
            toMapLatLng(this.panoramaPointList[0].latitude, this.panoramaPointList[0].longitude)
          );
        }
        this.panoramaPointList.forEach((item) => {
          if (item.latitude == null || item.longitude == null) {
            return;
          }
          const latLng = toMapLatLng(item.latitude, item.longitude);
          drawnCount += 1;
          const circle = L.circle(latLng, 80, {
            color: 'orange',
            fillColor: 'orange',
            fillOpacity: 1,
            opacity: 1,
            weight: 2,
            pointID: item.pointId
          }).addTo(this.panoramaPointLayer);
          const pointNum = item.panoramaImageCount ? item.panoramaImageCount : 0;
          const numberLabel = L.marker(latLng, {
            icon: L.divIcon({
              className: 'circle-number',
              html: `<div style="
                border-radius: 50%;
                width: 20px;
                height: 20px;
                line-height: 20px;
                text-align: center;
                font-size: 20px;
                position: relative;
                color: #fff;">` + pointNum + `</div>`,
              iconSize: [20, 20]
            }),
            opacity: 0
          }).addTo(this.panoramaPointLayer);
          const currentZoom = this.map.getZoom();
          if (currentZoom >= 14 && currentZoom < 22) {
            numberLabel.setOpacity(1);
          }
          numberLabels.push(numberLabel);
          let clickTimer = null;
          numberLabel.on('click', () => {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
              return;
            }
            clickTimer = setTimeout(() => {
              if (!this.activePanoramaPoint) {
                this.targetDivPosition.x -= 360;
              }
              this.activePanoramaPoint = item;
              this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
              clickTimer = null;
            }, 1000);
          });
          numberLabel.on('dblclick', async () => {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
            }
            await this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
            this.singleObj = this.listData[0];
            this.isShowSingleDiv = true;
          });
          numberLabel.on('mouseover', () => {
            if (this.map.getZoom() >= 14) {
              circle.bindPopup(
                '<div style="font-family: Arial; font-size: 14px; color: #555;">' +
                '<strong style="color: black;font-weight: bold;font-size: 19px">点位名称: ' + item.pointName + '</strong><br>' +
                '<strong style="color: black;font-weight: bold;font-size: 19px">批次数量:' + item.panoramaImageCount + '</strong> <br>' +
                '<strong style="color: black;font-weight: bold;font-size: 19px">最近拍摄时间:' + item.latestTime + '</strong> <br>' +
                '<strong style="color: black;font-weight: bold;font-size: 19px">飞行员信息:' + item.gridOperator + '</strong>' +
                '</div>'
              ).openPopup();
            }
          });
          numberLabel.on('mouseout', () => {
            circle.closePopup();
          });
        });
      } else {

      }

      this.map.on('zoomend', () => {
        const currentZoom = this.map.getZoom();
        if (currentZoom >= 14) {
          numberLabels.forEach((label) => {
            label.setOpacity(1);
          });
        } else {
          numberLabels.forEach((label) => {
            label.setOpacity(0);
          });
        }
      });
      return this.panoramaPointLayer;
    },

    getTempPointData(node) {
      if (!this.map) {

        return this.tempPanoramaPointLayer;
      }
      const numberLabels = [];
      this.tempPanoramaPointLayer.clearLayers();
      if (this.tempPointList.length > 0) {
        if (node) {
          node.center = JSON.stringify(
            toMapLatLng(this.tempPointList[0].latitude, this.tempPointList[0].longitude)
          );
        }
        this.tempPointList.forEach((item) => {
          const latLng = toMapLatLng(item.latitude, item.longitude);
          const circle = L.circle(latLng, 90, {
            color: '#9c27b0',
            fillColor: 'orange',
            fillOpacity: 0.1,
            weight: 1,
            pointID: item.pointId
          }).addTo(this.tempPanoramaPointLayer);
          const pointNum = item.panoramaImageCount ? item.panoramaImageCount : 0;
          const numberLabel = L.marker(latLng, {
            icon: L.divIcon({
              className: 'circle-number',
              html: `<div style="
                border-radius: 50%;
                width: 20px;
                height: 20px;
                line-height: 20px;
                text-align: center;
                font-size: 20px;
                position: relative;
                color: #9c27b0;">` + pointNum + `</div>`,
              iconSize: [20, 20]
            }),
            opacity: 0
          }).addTo(this.tempPanoramaPointLayer);
          const currentZoom = this.map.getZoom();
          if (currentZoom >= 14 && currentZoom < 22) {
            numberLabel.setOpacity(1);
          }
          numberLabels.push(numberLabel);
          let clickTimer = null;
          numberLabel.on('click', () => {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
              return;
            }
            clickTimer = setTimeout(() => {
              if (!this.activePanoramaPoint) {
                this.targetDivPosition.x -= 360;
              }
              this.activePanoramaPoint = item;
              this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
              clickTimer = null;
            }, 1000);
          });
          numberLabel.on('dblclick', async () => {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
            }
            await this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
            this.singleObj = this.listData[0];
            this.isShowSingleDiv = true;
          });
          numberLabel.on('mouseover', () => {
            if (this.map.getZoom() >= 14) {
              circle.bindPopup(
                '点位名称:' + item.pointName +
                '<br>批次数量:' + item.panoramaImageCount +
                '<br>最近拍摄时间:' + item.latestTime +
                '<br>飞行员信息:' + item.gridOperator
              ).openPopup();
            }
          });
          numberLabel.on('mouseout', () => {
            circle.closePopup();
          });
        });
      }
      this.map.on('zoomend', () => {
        const currentZoom = this.map.getZoom();
        if (currentZoom >= 14) {
          numberLabels.forEach((label) => {
            label.setOpacity(1);
          });
        } else {
          numberLabels.forEach((label) => {
            label.setOpacity(0);
          });
        }
      });
      return this.tempPanoramaPointLayer;
    },

    getNestData(node) {
      if (!this.map) {

        return this.nestLayer;
      }
      this.nestLayer.clearLayers();
      const nestIcon = L.icon({
        iconUrl: require('@/assets/images/nest2.png'),
        iconSize: [40, 40],
        iconAnchor: [20, 20],
        popupAnchor: [-3, -40]
      });
      this.nestList.forEach((item) => {
        const marker = L.marker(toMapLatLng(item.latitude, item.longitude), {icon: nestIcon, nest_id: item.id});
        const popupContent = `
          <div>
            <strong>名称：</strong>${item.name}<br>
            <strong>飞机型号：</strong>${item.plane_model}<br>
            <strong>机巢SN：</strong>${item.nest_sn}<br>
            <strong>飞机SN：</strong>${item.plane_sn}<br>
            <strong>经纬度：</strong>${item.latitude},${item.longitude}<br>
            <strong>位置：</strong>${item.location}
          </div>
        `;
        marker.bindPopup(popupContent);
        this.nestLayer.addLayer(marker);
      });

      return this.nestLayer;
    },

    getNestBufferData(node) {
      if (!this.map) {

        return this.neatBufferLayer;
      }
      this.neatBufferLayer.clearLayers();
      if (!this.nestList.length) {

        return this.neatBufferLayer;
      }
      this.nestList.forEach((item) => {
        L.circle(toMapLatLng(item.latitude, item.longitude), 6000, {
          color: 'red',
          fillColor: 'transparent',
          fillOpacity: 0,
          opacity: 1,
          weight: 1
        }).addTo(this.neatBufferLayer);
      });

      return this.neatBufferLayer;
    },

    getBufferData(node) {
      if (!this.map) {

        return this.bufferLayer;
      }
      this.bufferLayer.clearLayers();
      this.panoramaPointList.forEach((item) => {
        L.circle(toMapLatLng(item.latitude, item.longitude), this.circleRadius, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        }).addTo(this.bufferLayer);
      });

      return this.bufferLayer;
    },

    getTempBufferData(node) {
      this.tempbufferLayer.clearLayers();
      this.tempPointList.forEach((item) => {
        L.circle(toMapLatLng(item.latitude, item.longitude), this.circleRadius, {
          color: '#800080',
          fillOpacity: 0,
          weight: 2
        }).addTo(this.tempbufferLayer);
      });
      return this.tempbufferLayer;
    },

    async getMultiInfo(para) {
      const multiObjres = await getPanoramaImageApi(para);
      if (multiObjres.code === 0) {
        this.listData = multiObjres.data;
        this.listData.forEach((item) => {
          item.pointId = para.pointId;
        });
      } else {
        this.$message.error(multiObjres.msg);
      }
    },

    openMulti() {
      if (this.listData.length <= 1) {
        this.$message.warning('当前该全景点没有多期图片，暂不可进行多期对比查看!!!!');
      } else {
        this.leftObj = this.listData[0];
        this.rightObj = this.listData[1];
        this.isShowMultiDiv = true;
      }
    },

    hanldeViewMultiRight(row) {
      if (this.isShowMultiDiv) {
        if (this.leftObj !== row) {
          if (this.rightObj != row) {
            this.rightObj = row;
            this.uniquekey += 1;
          }
        } else {
          this.$message.warning('左右两期图片不能相同，请重新选择！！！！');
        }
      } else {
        this.$message.warning('请先点击右上角多期对比，在进行查看！！！！');
      }
    },

    hanldeViewMultiLeft(row) {
      if (this.isShowMultiDiv) {
        if (this.rightObj !== row) {
          if (this.leftObj != row) {
            this.leftObj = row;
            this.uniquekey += 1;
          }
        } else {
          this.$message.warning('左右两期图片不能相同，请重新选择！！！！');
        }
      } else {
        this.$message.warning('请先点击右上角多期对比，在进行查看！！！！');
      }
    },

    closeDrawer() {
      this.activePanoramaPoint = null;
      this.targetDivPosition.x += 360;
      this.rightObj = null;
      this.leftObj = null;
      this.singleObj = null;
      this.isShowMultiDiv = false;
      this.isShowSingleDiv = false;
    },

    async getClue() {
      this.formInfo.limit = 10000;
      this.formInfo.page = 1;
      const res = await getClueData(this.formInfo);
      if (res.code === 0) {
        this.clueList = res.data;
      } else {
        this.$message.error(res.msg);
      }
    },

    async getVideoData() {
      this.videoListData = [
        {videoName: '2025-06-03', videoUrl: '/static/video/uav1.mp4'},
        {videoName: '2025-06-04', videoUrl: '/static/video/uav1.mp4'},
      ];
    },

    showVideo(row) {
      this.currentVideoUrl = row.videoUrl;
      this.videoDialogVisible = true;
    },

    async getTimeAxisData() {
      const res = await getTimeAxisDataApi();
      if (res.code === 0) {
        this.timeAxisData = res.data.rawTimelineItems;
      } else {
        this.$message.error(res.msg);
      }
    },

    async handleDateChange(datevalue) {
      this.selectTime = datevalue;
      this.activePanoramaPoint = null;
      await this.getTimePhotoData({time: datevalue});
      const selectedLabels = this.selectedNodes;
      const aerialNode = selectedLabels.find(node => node.label === '航片');
      if (aerialNode && this.map) {
        if (this.aerialPhotoLayer && this.map.hasLayer(this.aerialPhotoLayer)) {
          this.map.removeLayer(this.aerialPhotoLayer);
        }
        this.aerialPhotoLayer = await this.getAerialPhotoLayer();
        this.map.addLayer(this.aerialPhotoLayer);
        this.setNodeLayer(aerialNode, this.aerialPhotoLayer);
      }
      this.$emit('date-change', datevalue);
    },

    async getTimePhotoData(para) {
      this.aerialPhotoLayer.clearLayers();
    }
  },

  beforeDestroy() {
    this.destroyMap();
  }
};
</script>

<style lang="scss" scoped>
.map-2d-panel {
  width: 100%;
  height: 100%;
  position: relative;
}

.toolbar {
  width: 600px;
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
  color: black;
}

.toolbar .el-date-editor {
  width: 250px;
  height: 33px;
  background-color: transparent;
  border: none !important;
}

.toolbar ::v-deep(.el-date-editor) {
  .el-range-separator {
    width: 25px;
  }

  .el-range-input {
    background-color: rgba(255, 255, 255, 0.2);
    color: #666;

    &::placeholder {
      color: #666;
    }
  }

  .el-input__icon {
    color: #666;
  }
}

.toolbar div {
  cursor: pointer;
}

.toolbar div:hover {
  color: #42b4f2;
}

.baractive {
  color: #42b4f2;
}

.icon-toolbar {
  margin: 0 6px;
  font-size: 18px;
}

.clue-image {
  position: absolute;
  width: 400px;
  height: 400px;
  right: 0;
  bottom: 0;
  z-index: 1000;
  overflow: auto;
  display: flex;
  flex-direction: column;
  padding: 6px;
  background-color: #fff;

  img {
    width: 100%;
    height: 100%;
    object-fit: fill;
    border: 2px solid #cccccc;
  }

  .gt-header {
    display: flex;
    padding-left: 6px;
    height: 32px;
    line-height: 32px;
  }

  .gt-image {
    height: 240px;
  }
}

.detectlist {
  color: black;
  top: 0px;
  box-shadow: none;
  z-index: 999;
  position: absolute;
  right: 0;
  width: 360px;
  height: 100%;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  border-left: 1px solid #cccccc;
  background-color: #e4e7ed;
}

.detectlist ::v-deep(.el-table) {
  color: black;
  background-color: transparent;
}

.detectlist ::v-deep(.el-table tr) {
  background-color: rgba(255, 255, 255, 0.2);
  color: black;
}

.detectlist ::v-deep(.el-table th) {
  background-color: rgba(255, 255, 255, 0.4);
  color: black;
}

.detectlist ::v-deep(.el-table--enable-row-hover .el-table__body tr:hover > td.el-table__cell) {
  background-color: rgba(255, 255, 255, 0.4);
  color: black;
}

.detectlist .title {
  display: flex;
  text-align: center;
  border-bottom: 1px solid #fff;
  padding-bottom: 10px;
  font-size: 14px;
}

.detectlist .title span {
  text-align: left;
  width: 98%;
}

.detectlist .title .el-tooltip {
  background-color: transparent;
  height: 25px;
  width: 25px;
  text-align: center;
  display: flex;
  align-items: center;
  justify-content: center;
  color: black;
}

.view-multi-comparision,
.view-single {
  top: 0;
  background-color: white;
  box-shadow: none;
  z-index: 999;
  color: black;
  position: absolute;
  right: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.video {
  width: 500px;
  height: 500px;
  z-index: 999;
  position: absolute;
  top: 60px;
  right: 360px;
  display: flex;
  flex-direction: column;
}

.video div {
  background: rgba(0, 0, 0, 0.4);
  text-align: right;
  color: white;
  font-size: 15px;
  height: 32px;
}

.detect-list {
  background-color: rgba(0, 0, 0, 0.4);
  box-shadow: none;
  z-index: 999;
  color: #fff;
  position: absolute;
  width: 400px;
  height: auto;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  min-height: 40px;
  cursor: grab;
  right: 10px;
  top: 80px;
}

.fullscreen-container {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.9);
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.fullscreen-container:fullscreen {
  display: flex;
}

.fullscreen-container:-webkit-full-screen {
  display: flex;
}

.fullscreen-container:-ms-fullscreen {
  display: flex;
}

.fullscreen-image {
  max-width: 90%;
  max-height: 90%;
  object-fit: contain;
}

.close-fullscreen-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  font-size: 30px;
  color: white;
  background: transparent;
  border: none;
  cursor: pointer;
  z-index: 10000;
}

.close-btn span {
  margin-right: 10px;
  cursor: pointer;
}

.time-axis {
  position: absolute;
  height: 40px;
  z-index: 999;
  width: 30%;
  height: 46px;
  left: 335px;
  top: 15px;
  background: #515c72ad;
  border-radius: 5px;
}

#mapContainer {
  background-color: white;
}

::v-deep .el-input__inner {
  color: #fff;
}

::v-deep .iclient-leaflet-logo {
  display: none !important;
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
  right: 0;
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
</style>
