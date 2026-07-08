<template>
  <div style="position: relative">
    <div class="map-container" ref="mapContainer">
      <div id="map" class="map-container-body"></div>
    </div>
    <div class="tree-container" ref="ctrllayer">
      <!-- 控制按钮 -->
      <div class="show-control" >
        <div @click="handleExpandAll" class="button-expand" v-if="isShowTree">
          <i class="iconfont icon-sys-minus-square" style="font-size: 16px"></i>服务目录
        </div>
        <div @click="handleCollapseAll" class="button-expand" v-else>
          <i class="iconfont icon-shouqizhankai" style="font-size: 16px"></i>服务目录
        </div>
      </div>
      <el-tree
        v-if="isShowTree"
        :data="businessData"
        :show-checkbox="true"
        :default-expand-all="true"
        @check-change="loadOrDeleteMap"
        ref="tree"
        node-key="label"
        :highlight-current="false"
        :render-content="renderContent"></el-tree>
    </div>
    <div v-if="isWuxiProject" class="vector-table-panel" :class="{ collapsed: geoPanelCollapsed }">
      <div class="panel-header">
        <span>监测范围</span>
        <span class="panel-toggle" @click="geoPanelCollapsed = !geoPanelCollapsed">
          {{ geoPanelCollapsed ? '展开' : '收起' }}
        </span>
      </div>
      <el-table
        v-show="!geoPanelCollapsed"
        :data="geoTableData"
        :row-key="row => row.id"
        @row-click="onGeoTableRowClick"
        highlight-current-row
        :current-row-key="currentGeoRowId"
        max-height="280"
        size="small"
        border>
        <el-table-column prop="XZQMC" label="行政区名称" width="120"></el-table-column>
        <el-table-column prop="SSXZ" label="所属街道" width="120"></el-table-column>
        <el-table-column prop="SHAPE_Area" label="区域面积" width="140"></el-table-column>
        <el-table-column prop="TDYT" label="土地用途" width="140"></el-table-column>
        <el-table-column prop="XZQDM" label="行政区编码" width="120"></el-table-column>
      </el-table>
    </div>
    <div class="detect-list" v-show="dialogTableVisible">
      <div class="title">
        <!-- 新增收起/展开按钮 -->
        <el-tooltip class="item" effect="dark" content="添加至地图" placement="top">
          <el-button icon="iconfont icon-xiangjiaofenxi" circle @click="addToMap"></el-button>
        </el-tooltip>
        <el-tooltip class="item" effect="dark" content="全屏" placement="top">
          <el-button icon=" iconfont icon-quantu1" circle @click="toggleFullScreen"></el-button>
        </el-tooltip>
        <span style="padding: 0 10px">拍摄时间：{{ currentTopViewImageTime }}</span>
        <el-tooltip class="item" effect="dark" content="关闭" placement="top" style="position: absolute; right: 8px">
          <el-button icon="el-icon-close" circle @click="closeDetectDialog"></el-button>
        </el-tooltip>
      </div>
      <!-- 可收起的内容区域 -->
      <div class="collapsible-content">
        <div class="gt-query">
          <img ref="image" :src="currentImagePath" style="width: 100%; height: 100%"/>
        </div>
        <div class="block">
          <el-slider @input="handleInput" v-model="value" show-input></el-slider>
        </div>
      </div>
    </div>
    <div v-if="isFullScreen" class="fullscreen-container" ref="fullscreenContainer">
      <img :src="currentImagePath" class="fullscreen-image"/>
      <button @click="closeFullScreen" class="close-fullscreen-btn">×</button>
    </div>
    <tooBar :map="map" :currentTask="currentTask" v-if="isShowBar" :oneMapSingle="oneMapSingle" ref="tooBar"></tooBar>
    <div class="se-map-tool">
      <div class="zoom-num">{{ currentShowZoom }}</div>
      <div class="map-reset" @click="map_reset" title="地图复位"><i class="iconfont icon-quantu"></i></div>
    </div>
  </div>
</template>

<script>
import 'leaflet.markercluster'; // 引入插件
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet-rotate';

import {FeatureService, GetFeaturesBySQLParameters, ImageTileLayer, TiledMapLayer} from '@supermap/iclient-leaflet';
import {
  getClueData,
  getOneMapApi,
  getPanoramaPointByCountryApi,
  getTopViewDataApi,
  submitCorrectPointApi
} from '@/api/commonApi';
import axios from 'axios';
import { getLeafletVectorStyle } from '@/utils/vectorStyle';
import tooBar from './tooBar.vue';
import L from 'leaflet';
import { create4528LeafletMap, createGeoCrs, createGeoBaseLayer, isFiniteLatLngPair } from '@/utils/map4528Loader';
import { toMapLatLng } from '@/views/dataManagement/oneMap/oneMapCoords';

export default {
  name: 'smallMapView',
  //接收父组件传递的数据
  props: {
    taskList: Array,
    currentYaw: Number,
    currentTask: Object,
    currentViewPoint: L.Marker, //当前查看的全景点
    currentAddMarker: L.Marker, //新增点位当前打点操作的marker
    currentLocationMarker: L.Marker,
    isMapChange: Boolean,
    rectFrameAreaList: Array,
    currentLocationMarker1: {
      type: Object,
      default: null
    },
    no_detection_area_list: Array,
    oneMapSingle: {Boolean, default: false}
  },
  components: {tooBar},
  computed: {
    isWuxiProject() {
      return this.projectCity !== 'wuxi';
    }
  },
  data() {
    return {
      isShowBar: false,
      sectorLocationList: [],
      map: null,
      baseMapLayer: null,
      baseMapUse4528: window.config.baseMapUse4528 === true,
      baseMap4528Epsg: window.config.baseMap4528Epsg || 'EPSG:4528',
      baseMap4528Proj:
        window.config.baseMap4528Proj ||
        '+proj=tmerc +lat_0=0 +lon_0=120 +k=1 +x_0=40500000 +y_0=0 +ellps=GRS80 +units=m +no_defs +type=crs',
      mapResetCenter: window.config.center,
      mapResetZoom: window.config.zoom,
      mapFitBounds: null,
      serviceMaxZoom: null,
      serviceMinZoom: null,
      needAddService:null,
      datasetsName:'',
      datasourceName:'',
      projectCity: window.config.projectCity,
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      layerRandList: [],
      activeNames: ['1'], // 控制折叠面板的展开和折叠
      layerVisibility: {
        gengdivector: false,
        monitorcircle: true
      },
      markers: [], //全景点点集合
      currentMarker: null,
      circleLayerList: [],
      circleLayers: {}, //700m缓冲区图层
      currentLonLat: [],
      imageName: '',
      pointName: '',
      noDetectionLayer: L.layerGroup(),
      mapService: '',
      gengdiService: '',
      center: window.config.center,
      businessData: [
        {label: '基础地理数据', children: []},
        {label: '资源调查数据', children: []},
        {label: '低空业务数据', children: []}
      ], //业务数据列表
      currentLeafNodes: [], //当前选中的叶节点
      clusterLayer: L.markerClusterGroup(), //线索点聚合图层
      panoramaPointLayer: L.layerGroup(), //全景点位图层
      bufferLayer: L.layerGroup(), //缓冲区图层
      clueList: [], //线索集合
      customIcon: L.icon({
        iconUrl: '../../static/iconblue.png',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      }),
      redIcon: L.icon({
        iconUrl: '../../static/iconred.png',
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      }),
      topViewList: [],
      nestList: [], //机巢点列表
      nestLayer: L.layerGroup(), //机巢点图层
      neatBufferLayer: L.layerGroup(), //机巢缓冲区图层
      topViewLayer: L.layerGroup(), //俯视图图层
      frameAreaLayer: L.layerGroup(), //不检测区域
      isClickCompass: true, //是否点击了指北针
      changeYaw: 0,
      circleRadius: window.config.circleRadius,
      minZoom: window.config.minZoom,
      maxZoom: window.config.maxZoom,
      zoom: window.config.zoom, //初始层级
      currentShowZoom: window.config.zoom, //当前层级
      tempBufferLayer: L.layerGroup(), //临时全景点缓冲区图层
      tempPanoramaPointLayer: L.layerGroup(),
      tempPointList: [], //临时全景点列表
      topViewMarker: [],
      dialogTableVisible: false,
      overlay: null,
      value: 70,
      isFullScreen: false,
      currentImagePath: '',
      currentTopViewImageTime: '',
      currentImageBounds: [],
      isShowTree: false,
      defaultCheckedNodes: [],
      geoTableData: [],
      geoFeatures: [],
      currentGeoRowId: null,
      geoPanelCollapsed: false,
      selectedGeoFeatureLayer: L.layerGroup(),
      geoServerLoading: false
    };
  },
  watch: {
    taskList() {
      if (!this.map) return;
      // 清除地图上所有图层, 保留底图
      this.map.eachLayer((layer) => {
        if (!(layer.options && layer.options.source === 'baseMapLayer')) {
          this.map.removeLayer(layer);
        }
      });
      this.currentLeafNodes = [];
      this.loadOrDeleteMap();
      if (this.taskList && this.taskList.length > 0) {
        this.renderTaskListMarkers();
      }
    },
    // 监听矩形框区域，绘制目标检测
    rectFrameAreaList() {
      if (!this.map) return;
      if (this.noDetectionLayer.getLayers().length > 0) {
        this.noDetectionLayer.clearLayers();
      }
      const targetPolygonLatLonList = this.rectFrameAreaList.map((item) => ({
        id: item.id,
        points: item.xy,
        name: item.name
      }));
      targetPolygonLatLonList.forEach((item) => {
        L.polygon(item.points, {
          color: '#56f501',
          fillColor: 'transparent',
          fillOpacity: 0
        }).addTo(this.noDetectionLayer);
      });
      this.map.addLayer(this.noDetectionLayer);
    },
    // 监听打点操作
    isMapChange(val) {
      if (val) {
        // if (this.map) this.map.remove();
        // this.initMap();
        //this.addMarker();
        //this.updateSector(this.currentYaw);
        //this.map.on('click', this.mapClick);
      } else {
        // if (this.map) this.map.remove();
        // this.initMap();
        //this.addMarker();
        //this.map.off('click', this.mapClick);
      }
    },
    // 监听当前yaw值，实时更新扇形
    currentYaw(newVal, oldVal) {
      if (newVal) {
        this.updateSector(newVal);
      }
    },
    // 监听当前任务，在当前全景更新样式
    currentTask: {
      handler(val) {
        if (!val || !this.map) return;
        this.isClickCompass = true;
        if (this.currentViewPoint) {
          this.currentViewPoint.remove();
        }
        let lat;
        let lon;
        let marker;
        let markerData;
        this.markers.forEach((mData) => {
          if (mData.sector) {
            this.map.removeLayer(mData.sector);
          }
          mData.marker.setIcon(mData.customIcon);
        });
        this.markers.forEach((item) => {
          if (item.imageId === val.imageId) {
            lat = item.lat;
            lon = item.lon;
            marker = item.marker;
            markerData = item;
          }
        });
        if (lat == null || lon == null) {
          lat = val.latitude != null ? val.latitude : val.lat;
          lon = val.longitude != null ? val.longitude : val.lon;
        }
        if (lat != null && lon != null) {
          if (marker && markerData) {
            this.drawSector(lat, lon, markerData, marker);
          }
          this.focusOnTask(val, 16);
        }
      },
      deep: true
    },
    // 在小地图绘制线索marker
    currentViewPoint(newVal, oldVal) {
      if (oldVal) {
        oldVal.remove();
      }
      if (!newVal) return;
      this.bindCurrentViewPoint(newVal);
    },
    // 打点操作增加的线索点
    currentAddMarker(newVal, oldVal) {
      if (oldVal) {
        oldVal.remove();
      }
      if (newVal) this.addLayerWhenReady(newVal);
    },
    currentLocationMarker(newVal, oldVal) {
      if (oldVal) {
        oldVal.remove();
      }
      if (newVal) this.addLayerWhenReady(newVal);
    },
    currentLocationMarker1(newVal, oldVal) {
      if (oldVal && oldVal.currentLocationMarker) {
        oldVal.currentLocationMarker.remove();
      }
      if (newVal && newVal.currentLocationMarker) {
        this.addLayerWhenReady(newVal.currentLocationMarker);
      }
    },
    isShowTree(val) {
      if (val && this.defaultCheckedNodes.length) {
        this.$nextTick(() => {
          if (this.$refs.tree) {
            this.$refs.tree.setCheckedNodes(this.defaultCheckedNodes);
          }
        });
      }
    }
  },
  methods: {
    // 一键展开所有节点
    handleExpandAll() {
      this.isShowTree = false;
    },
    // 一键收起所有节点
    handleCollapseAll() {
      this.isShowTree = true;
    },
    async loadGeoserverVectorData() {
      const workspace = this.datasourceName || 'wx';
      const layerName = this.datasetsName || 'jcfw';
      const geoserverBase = 'http://2.24.15.55:8080/geoserver';
      const urlString = this.needAddService
        ? `${this.needAddService}/${workspace}`
        : `${geoserverBase}/${workspace}`;
      try {
        this.geoServerLoading = true;
        const typeName = `${workspace}:${layerName}`;
        const param = {
          service: 'WFS',
          version: '1.1.0',
          request: 'GetFeature',
          typeName,
          outputFormat: 'application/json',
          format_options: 'charset:UTF-8',
          maxFeatures: 20000,
          srsName: 'EPSG:4326'
        };
        const url = urlString + L.Util.getParamString(param, urlString);
        console.log('GeoServer WFS url:', url);
        const res = await axios.get(url);
        const data = res.data || {};
        const features = (data && data.features) || [];
        this.geoFeatures = features;
        this.geoTableData = features.map((feature, index) => {
          const props = feature.properties || {};
          return {
            id: index,
            XZQMC: props.XZQMC || props.xzqmc || props.XZQMC || '',
            SSXZ: props.SSXZ || props.ssxz || props.SSXZ || props.ssxz || '',
            SHAPE_Area: props.SHAPE_Area || props.SHAPE_Area || props.SHAPE_Area || '',
            TDYT: (props.TDYT || props.tdyt || props.TDYT || '').substring(0, 7),
            XZQDM: props.XZQDM || props.xzqdm || props.XZQDM || '',
            _feature: feature
          };
        });
      } catch (error) {
        console.error('加载GeoServer矢量数据失败', error);
      } finally {
        this.geoServerLoading = false;
      }
    },
    onGeoTableRowClick(row) {
      if (!row || !row._feature) return;
      this.currentGeoRowId = row.id;
      this.highlightGeoFeature(row._feature);
    },
    highlightGeoFeature(feature) {
      if (!feature || !feature.geometry) return;
      this.selectedGeoFeatureLayer.clearLayers();
      const layer = L.geoJSON(feature, {
        style: {
          color: '#ff5722',
          weight: 3,
          opacity: 0.9,
          fillOpacity: 0.2
        }
      });
      layer.addTo(this.selectedGeoFeatureLayer);
      if (layer.getBounds && layer.getBounds().isValid()) {
        this.map.fitBounds(layer.getBounds(), { maxZoom: 18 });
      } else if (feature.geometry.type === 'Point') {
        const coord = feature.geometry.coordinates;
        this.safeSetView(coord[1], coord[0], 13);
      }
    },
    createMapCircle(lat, lon, radius, options = {}) {
      const coords = this.normalizeCoord(lat, lon);
      if (!coords) return null;
      return L.circle(coords, radius, options);
    },
    normalizeCoord(lat, lng) {
      if (!isFiniteLatLngPair(lat, lng)) return null;
      const [la, lo] = toMapLatLng(lat, lng);
      if (!isFiniteLatLngPair(la, lo)) return null;
      return [la, lo];
    },
    safeSetView(lat, lng, zoom) {
      if (!this.map) return;
      const coords = this.normalizeCoord(lat, lng);
      if (coords) {
        this.map.setView(coords, zoom);
      }
    },
    parseNodeCenter(center) {
      if (!center) return null;
      try {
        const parsed = typeof center === 'string' ? JSON.parse(center) : center;
        if (!Array.isArray(parsed) || parsed.length < 2) return null;
        return this.normalizeCoord(parsed[0], parsed[1]);
      } catch (e) {
        return null;
      }
    },
    getMapFallbackCenter() {
      if (!Array.isArray(this.center) || this.center.length < 2) return null;
      return this.normalizeCoord(this.center[0], this.center[1]);
    },
    finalize4528ViewState(loaded) {
      if (!this.map || !loaded) return;
      const maxZ = loaded.maxZoom;
      const minZ = loaded.minZoom;
      this.serviceMaxZoom = maxZ;
      this.serviceMinZoom = minZ;
      this.maxZoom = maxZ;
      this.minZoom = minZ;
      this.map.setMaxZoom(maxZ);
      this.map.setMinZoom(minZ);

      let z = this.map.getZoom();
      const preferZoom = Number(window.config.zoom);
      if (Number.isFinite(preferZoom)) {
        z = Math.min(maxZ, Math.max(minZ, preferZoom));
      } else if (!Number.isFinite(z)) {
        z = loaded.initialZoom != null ? loaded.initialZoom : minZ;
        z = Math.min(maxZ, Math.max(minZ, z));
      } else {
        z = Math.min(maxZ, Math.max(minZ, z));
      }
      const center = this.getMapFallbackCenter();
      if (center) {
        this.map.setView(center, z);
      } else if (this.map.getZoom() !== z) {
        this.map.setZoom(z);
      }
      this.zoom = z;
      this.currentShowZoom = Math.floor(z);
    },
    addLayerWhenReady(layer) {
      if (!layer) return;
      const apply = () => {
        if (!this.map || this.map.hasLayer(layer)) return;
        this.map.addLayer(layer);
      };
      if (this.map) {
        apply();
      } else {
        this.$nextTick(apply);
      }
    },
    bindCurrentViewPoint(marker) {
      if (!marker) return;
      this.addLayerWhenReady(marker);
      if (!this.map) return;
      const latLng = marker.getLatLng();
      if (latLng && Number.isFinite(latLng.lat) && Number.isFinite(latLng.lng)) {
        this.map.setView(latLng, 13);
      }
      if (this.$refs.tooBar) {
        this.$refs.tooBar.updataCurrentViewPoint(marker);
      }
      const that = this;
      marker.off('dragend');
      marker.on('dragend', async function (e) {
        L.DomEvent.stopPropagation(e);
        const newLatLng = e.target.getLatLng();
        const newLat = newLatLng.lat;
        const newLng = newLatLng.lng;
        const parm = {
          clue_id: marker.options.clueId,
          longitude: newLng,
          latitude: newLat
        };
        const res = await submitCorrectPointApi(parm);
        if (res.code === 0) {
          that.$message.success('地址修改成功');
          that.correctLabelVisible = false;
          that.$set(that.currentRow, 'status', 2);
          if (that.currentViewPoint !== null) {
            that.currentViewPoint = null;
          }
        } else {
          that.$message.error(res.msg);
        }
      });
    },
    syncPropMarkersToMap() {
      if (!this.map) return;
      if (this.currentLocationMarker) {
        this.addLayerWhenReady(this.currentLocationMarker);
      }
      if (this.currentAddMarker) {
        this.addLayerWhenReady(this.currentAddMarker);
      }
      if (this.currentLocationMarker1 && this.currentLocationMarker1.currentLocationMarker) {
        this.addLayerWhenReady(this.currentLocationMarker1.currentLocationMarker);
      }
      if (this.currentViewPoint) {
        this.bindCurrentViewPoint(this.currentViewPoint);
      }
    },
    async initMap() {
      try {
        if (this.baseMapUse4528 && this.baseMapService) {
          await this.init4528Map();
        } else {
          this.initGeoMap();
        }
      } catch (err) {
        console.error('[smallMap] 4528 底图加载失败', err);
        this.$message.error('地图加载失败：' + (err.message || '请检查底图服务'));
        return;
      }
      this.setupMapAfterInit();
    },
    async init4528Map() {
      const fallbackCenter =
        Array.isArray(this.center) && isFiniteLatLngPair(this.center[0], this.center[1])
          ? [Number(this.center[0]), Number(this.center[1])]
          : null;
      const loaded = await create4528LeafletMap('map', {
        serviceUrl: this.baseMapService,
        serviceType: this.baseMapServiceType,
        epsgCode: this.baseMap4528Epsg,
        projDef: this.baseMap4528Proj,
        initialZoom: this.zoom,
        center: fallbackCenter || undefined,
        initialView: 'none',
        mapOptions: {
          zoomSnap: 1,
          zoomDelta: 1,
          rotate: true,
          rotateControl: {
            closeOnZeroBearing: false,
            position: 'topright'
          },
          compassBearing: true,
          touchRotate: true
        }
      });
      this.map = loaded.map;
      this.baseMapLayer = loaded.baseMapLayer;
      this.finalize4528ViewState(loaded);
      this.mapFitBounds = loaded.fitBounds && loaded.fitBounds.isValid() ? loaded.fitBounds : null;
      if (this.mapFitBounds) {
        this.mapResetCenter = this.mapFitBounds.getCenter();
        this.mapResetZoom = this.map.getZoom();
      } else if (fallbackCenter) {
        this.mapResetCenter = L.latLng(fallbackCenter[0], fallbackCenter[1]);
        this.mapResetZoom = this.map.getZoom();
      } else {
        this.mapResetCenter = null;
        this.mapResetZoom = this.map.getZoom();
      }
      if (this.baseMapLayer && this.baseMapLayer.options) {
        this.baseMapLayer.options.source = 'baseMapLayer';
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
      let myCrs = null;
      if (this.projectCity === 'nanjing') {
        myCrs = L.CRS.EPSG3857;
      } else if (this.projectCity === 'jiangyin') {
        const jyResolutions = [];
        let res = 78183.89453125001;
        for (let i = 0; i < 20; i++) {
          jyResolutions.push(res);
          res /= 2;
        }
        myCrs = L.Proj.CRS('EPSG:4528', {
          resolutions: jyResolutions
        });
      } else {
        myCrs = createGeoCrs(this.projectCity);
      }
      this.map = L.map('map', {
        crs: myCrs,
        center: this.center,
        zoom: this.zoom,
        zoomControl: false,
        attributionControl: false,
        rotate: true,
        rotateControl: {
          closeOnZeroBearing: false,
          position: 'topright'
        },
        zoomSnap: 0.25,
        compassBearing: true,
        touchRotate: true,
        maxZoom: this.maxZoom,
        minZoom: this.minZoom
      });
      this.mapResetCenter = this.center;
      this.mapResetZoom = this.zoom;
      this.mapFitBounds = null;

      if (this.baseMapService) {
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
          this.baseMapLayer = createGeoBaseLayer(this.baseMapService, this.baseMapServiceType, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            minZoom: this.minZoom
          });
        } else {
          this.baseMapLayer = createGeoBaseLayer(this.baseMapService, this.baseMapServiceType, {
            maxZoom: this.maxZoom,
            maxNativeZoom: this.baseMaxNativeZoom,
            minZoom: this.minZoom
          });
        }
        if (this.baseMapLayer) {
          if (this.baseMapLayer.options) {
            this.baseMapLayer.options.source = 'baseMapLayer';
          }
          this.baseMapLayer.addTo(this.map);
          this.baseMapLayer.bringToBack();
          this.layerRandList.unshift({
            name: '底图',
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
        }
      }
    },
    setupMapAfterInit() {
      if (!this.map) return;
      this.selectedGeoFeatureLayer.addTo(this.map);
      // 为按钮添加点击事件,默认事件不生效
      if (document.getElementsByClassName('leaflet-control-rotate-toggle')) {
        var elements = document.getElementsByClassName('leaflet-control-rotate-toggle');
        var that = this;
        for (var i = 0; i < elements.length; i++) {
          elements[i].onclick = (e) => {
            // that.rotateMap(0);
            e.stopPropagation();
            this.isClickCompass = !this.isClickCompass;
            if (this.isClickCompass) {
              // 第一次点击：启用跟随模式
              this.map.setBearing(this.changeYaw);
            } else {
              // 第二次点击：重置到正北
              that.rotateMap(0);
            }
          };
        }
      }
      this.map.on('zoomend', () => {
        if (!this.map) return;
        this.currentShowZoom = Math.floor(this.map.getZoom());
      });
      // 监听鼠标移入地图事件
      this.map.on('mousemove', (e) => {
        const latlng = e.latlng;
        if (!latlng || !Number.isFinite(latlng.lat) || !Number.isFinite(latlng.lng)) return;
        const isInside = this.isPointInSectorPolygon([latlng.lat.toFixed(6), latlng.lng.toFixed(6)], this.sectorLocationList);
        if (isInside) {
          this.$emit('synchronousPosition', latlng);
        } else {
          this.$emit('synchronousPosition', []);
        }
      });
      this.isShowBar = true;
      this.syncPropMarkersToMap();
    },
    //计算距离
    calculateDistance(lat1, lon1, lat2, lon2) {
      const R = 6371e3; // 地球半径（单位：米）
      const φ1 = (lat1 * Math.PI) / 180; // 纬度1转弧度
      const φ2 = (lat2 * Math.PI) / 180; // 纬度2转弧度
      const Δφ = ((lat2 - lat1) * Math.PI) / 180; // 纬度差转弧度
      const Δλ = ((lon2 - lon1) * Math.PI) / 180; // 经度差转弧度

      const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      return R * c <= 700; // 返回距离（米）
    },
    /**
     * 判断点是否在扇形坐标数组内
     * @param {Array} point - 待判断点 [纬度, 经度]
     * @param {Array} sectorCoordinates - 扇形坐标数组 [[lat1,lng1], [lat2,lng2], ...]
     * @returns {boolean} 是否在扇形内
     */
    isPointInSectorPolygon(point, sectorCoordinates) {
      // 验证输入
      if (!point || !sectorCoordinates || sectorCoordinates.length < 3) {
        return false;
      }
      // 最终多边形判断
      return this.pointInPolygon(point, sectorCoordinates);
    },

    /**
     * 射线法判断点是否在多边形内
     */
    pointInPolygon(point, polygon) {
      const [lat, lng] = point;
      let inside = false;

      // 遍历多边形所有边
      for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++) {
        const [latI, lngI] = polygon[i];
        const [latJ, lngJ] = polygon[j];

        // 检查点是否在边上
        if (this.isPointOnEdge(point, [polygon[i], polygon[j]])) {
          return true;
        }

        // 射线法核心判断
        const intersect =
          // 点的纬度在边的两个端点纬度之间
          latI > lat !== latJ > lat &&
          // 计算交点经度并判断是否在点的经度右侧
          lng < ((lngJ - lngI) * (lat - latI)) / (latJ - latI) + lngI;

        if (intersect) {
          inside = !inside;
        }
      }

      return inside;
    },
    /**
     * 判断点是否在边上
     * @param {Array} point - [lat, lng]
     * @param {Array} edge - [[lat1, lng1], [lat2, lng2]]
     * @returns {boolean}
     */
    isPointOnEdge(point, edge) {
      const [lat, lng] = point;
      const [p1, p2] = edge;
      const [lat1, lng1] = p1;
      const [lat2, lng2] = p2;

      // 1. 检查点是否在边的经纬度范围内
      const inLatRange = lat >= Math.min(lat1, lat2) - 1e-8 && lat <= Math.max(lat1, lat2) + 1e-8;
      const inLngRange = lng >= Math.min(lng1, lng2) - 1e-8 && lng <= Math.max(lng1, lng2) + 1e-8;
      if (!inLatRange || !inLngRange) {
        return false;
      }

      // 2. 检查点是否在直线上（使用面积法判断共线）
      // 计算三角形面积的2倍（避免除法，提高精度）
      const area = Math.abs((lat2 - lat1) * (lng - lng1) - (lng2 - lng1) * (lat - lat1));
      // 面积接近0视为共线（允许微小误差）
      return area < 1e-8;
    },
    //在地图上添加点
    clearTaskMarkers() {
      this.markers.forEach((mData) => {
        if (mData.sector) {
          this.map.removeLayer(mData.sector);
        }
        if (mData.marker) {
          this.map.removeLayer(mData.marker);
        }
      });
      this.markers = [];
      if (this.circleLayers) {
        this.map.removeLayer(this.circleLayers);
        this.circleLayers = null;
      }
      this.circleLayerList = [];
    },
    renderTaskListMarkers() {
      if (!this.map || !this.taskList || !this.taskList.length) return;
      this.clearTaskMarkers();
      this.taskList.forEach((task) => {
        const lat = task.latitude != null ? task.latitude : task.lat;
        const lon = task.longitude != null ? task.longitude : task.lon;
        if (lat == null || lon == null) return;
        const customIcon = L.icon({
          iconUrl: '../../static/iconblue.png',
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32]
        });
        this.redIcon = L.icon({
          iconUrl: '../../static/iconred.png',
          iconSize: [32, 32],
          iconAnchor: [16, 32],
          popupAnchor: [0, -32]
        });
        const coords = this.normalizeCoord(lat, lon);
        if (!coords) return;
        const marker = L.marker(coords, { icon: customIcon }).addTo(this.map).bindPopup(task.pointName);
        const markerData = {
          marker,
          sector: null,
          lat,
          lon,
          customIcon,
          redIcon: this.redIcon,
          imageId: task.imageId
        };
        const circle = this.createMapCircle(lat, lon, this.circleRadius, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        });
        if (!circle) return;
        this.circleLayerList.push(circle);
        this.markers.push(markerData);
        if (this.currentTask && this.currentTask.imageId === task.imageId) {
          this.drawSector(lat, lon, markerData, marker);
        }
        marker.on('click', () => {
          this.markers.forEach((mData) => {
            if (mData.sector) {
              this.map.removeLayer(mData.sector);
            }
            mData.marker.setIcon(mData.customIcon);
          });
          this.drawSector(lat, lon, markerData, marker);
          this.$emit('clickMarker', task, lat, lon, markerData, marker);
        });
      });
      if (this.circleLayerList.length > 0) {
        this.circleLayers = L.layerGroup(this.circleLayerList);
        this.circleLayers.addTo(this.map);
      }
    },
    addMarker() {
      this.renderTaskListMarkers();
    },
    focusOnTask(task, zoom = 16) {
      if (!this.map || !task) return;
      const lat = task.latitude != null ? task.latitude : task.lat;
      const lon = task.longitude != null ? task.longitude : task.lon;
      this.safeSetView(lat, lon, zoom);
    },
    drawSector(lat, lon, markerData, marker) {
      // 绘制当前标记的扇形
      const radius = this.circleRadius;
      const startAngle = -30;
      const endAngle = 30;
      const numberOfPoints = 50;

      this.sectorLocationList = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
      const center = this.normalizeCoord(lat, lon);
      if (center) {
        this.sectorLocationList.push(center);
      }
      const sector = L.polygon(this.sectorLocationList, {
        color: 'blue',
        fillColor: 'transparent',
        fillOpacity: 0
      }).addTo(this.map);

      // 设置当前点击的标记图标为红色
      marker.setIcon(this.redIcon);
      this.currentMarker = {marker, sector, lat, lon};
      // 更新当前标记的扇形数据
      markerData.sector = sector;
    },
    //绘制扇形
    getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints) {
      const geo = this.normalizeCoord(lat, lon);
      if (!geo) return [];
      const [baseLat, baseLon] = geo;
      const latlngs = [];
      const angleStep = (endAngle - startAngle) / numberOfPoints;
      for (let i = 0; i <= numberOfPoints; i++) {
        const angle = ((startAngle + i * angleStep) * Math.PI) / 180;
        const pointLat = baseLat + (radius / 111320) * Math.cos(angle);
        const pointLon = baseLon + (radius / (111320 * Math.cos((baseLat * Math.PI) / 180))) * Math.sin(angle);
        latlngs.push([pointLat, pointLon]);
      }
      return latlngs;
    },
    //更新扇形
    updateSector(yaw) {
      if (!this.currentMarker) return;
      // 旋转底图
      this.changeYaw = 0 - yaw - this.currentTask.yawDegree;
      const {marker, sector, lat, lon} = this.currentMarker;
      if (this.changeYaw && this.isClickCompass) {
        this.safeSetView(lat, lon);
        this.map.setBearing(this.changeYaw);
      }
      const radius = this.circleRadius;
      // 扇形固定，底图转动
      const startAngle = yaw + this.currentTask.yawDegree - 30;
      const endAngle = yaw + this.currentTask.yawDegree + 30;
      const numberOfPoints = 50;
      // 更新扇形坐标
      this.sectorLocationList = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
      const center = this.normalizeCoord(lat, lon);
      if (center) {
        this.sectorLocationList.push(center);
      }
      // 更新地图上的扇形
      sector.setLatLngs(this.sectorLocationList);
      sector.addTo(this.map);
    },
    // 旋转底图
    rotateMap(yaw) {
      if (!yaw) {
        yaw = 0;
      }
      this.map.setBearing(yaw);
    },
    mapClick(e) {
      //this.$emit('clickMap', e.latlng.lat, e.latlng.lng);
    },
    //获取全景点坐标
    async getPanoramaPoint() {
      this.tempPointList = [];
      this.panoramaPointList = [];
      const params = {time: ''};
      const res = await getPanoramaPointByCountryApi(params);
      if (res.code === 0) {
        res.data.forEach((item) => {
          if (item.pointType === '1') {
            this.tempPointList.push(item);
          } else {
            this.panoramaPointList.push(item);
          }
        });
      } else {
        this.$message.error(res.msg);
      }
    },
    setTreeCheckedNodes(nodes) {
      const validNodes = (nodes || []).filter(Boolean);
      this.defaultCheckedNodes = validNodes;
      if (!validNodes.length) return;
      if (this.$refs.tree) {
        this.$refs.tree.setCheckedNodes(validNodes);
        return;
      }
      const leafNodes = validNodes.filter((node) => !node.children || node.children.length === 0);
      this.currentLeafNodes = [];
      if (leafNodes.length) {
        this.addLayers(leafNodes);
      }
    },
    loadOrDeleteMap() {
      if (!this.$refs.tree) return;
      const nodes = this.$refs.tree.getCheckedNodes();
      // 叶节点
      const leafNodes = nodes.filter((node) => !node.children || node.children.length === 0);
      // 新增叶节点
      if (leafNodes.length > this.currentLeafNodes.length) {
        const addLeafNodes = leafNodes.filter((node) => !this.currentLeafNodes.some((currentNode) => currentNode.label === node.label));
        this.addLayers(addLeafNodes);
      } else if (leafNodes.length < this.currentLeafNodes.length) {
        // 删除叶节点
        const deleteLeafNodes = this.currentLeafNodes.filter((node) => !leafNodes.some((currentNode) => currentNode.label === node.label));
        this.removeLayers(deleteLeafNodes);
      }
    },
    //设置树子节点样式
    renderContent(h, {node}) {
      // 获取子节点数量
      return (
        <span class="custom-tree-node" style="display:flex;align-items:center">
                    {node.isLeaf
                      ? [
                        <span
                          key="label"
                          title={node.label}
                          style="font-weight:700;font-size:14px;color:#000000a6;display:inline-block;width:120px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;">
                                  {node.label}
                              </span>
                      ]
                      : [
                        <span key="label" style="font-weight:bold;font-size:14px;color:#000000a6;">
                                  {node.label}
                              </span>
                      ]}
                </span>
      );
    },
    //添加地图图层
    async addLayers(addLeafNodes) {
      addLeafNodes.forEach(async (node) => {
        let layer;
        if (node.source_type === '业务矢量数据服务' && node.datasets_name) {
          layer = await this.getVectorData(node); //矢量服务
        } else if (node.data_type && node.data_type === 'clue') {
          layer = this.getClueData(); //线索点位
        } else if (node.data_type && node.data_type === 'panorama') {
          layer = this.getPanoramaPointData(); //全景点位
        } else if (node.data_type && node.data_type === 'panorama_coverage') {
          layer = this.getBufferData(); //全景覆盖范围
        } else if (node.data_type && node.data_type === 'temp_panorama_coverage') {
          layer = this.getTempBufferData(node);
        } else if (node.data_type && node.data_type === 'temp_panorama') {
          layer = this.getTempPointData(node);
        } else if (node.data_type && node.data_type === 'nest_location') {
          layer = this.getNestData(node); //机巢点位
        } else if (node.data_type && node.data_type === 'nest_coverage') {
          layer = this.getNestBufferData(node); //机巢覆盖范围
        } else if (node.data_type && node.data_type === 'top_view') {
          layer = this.getTopViewLayerData(); //俯视图范围
        } else if (node.data_type && node.data_type === 'frame_area') {
          layer = this.getFrameArea();
        } else {
          if (node.label !== '航片') {
            if (node.gis_service_type === '1') {
              layer = new TiledMapLayer(node.service, {
                maxZoom: this.maxZoom, // 允许地图缩放到 22 级
                maxNativeZoom: this.maxZoom, // 瓦片服务实际支持的最高级别
                reuseTiles: false, // 关键参数：禁止复用旧瓦片
                updateWhenIdle: true,
                updateInterval: 200,
                keepBuffer: 1, // 仅保留1屏缓冲
                noWrap: true // 禁止瓦片重复
              });
              console.log(JSON.parse(node.center))
              const nodeCenter = this.parseNodeCenter(node.center);
              if (nodeCenter) this.map.setView(nodeCenter, 13);
            } else if (node.gis_service_type === '2') {
              layer = L.tileLayer(`${node.service}/tile/{z}/{y}/{x}`, {
                maxZoom: this.maxZoom,
                minZoom: this.minZoom,
                pane: 'tilePane',
                updateWhenIdle: false, // 拖动时也更新瓦片
                updateWhenZooming: false, // 缩放时也更新
                keepBuffer: 3, // 仅保留1屏缓冲
                updateInterval: 200,
                noWrap: true // 禁止瓦片重复
              })
            } else if (node.gis_service_type === '3') {
              console.log('加载天地图服务');
              //天地图服务
              // 矩阵集id, 决定了在每一级该去请求哪一个identifier对应的切片，如果只有个别几级需要处理minZoom， maxZoom
              let identifier = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
              let matrixIds = [];
              for (var i = 0; i < identifier.length; i++) {
                matrixIds.push({
                  identifier: identifier[i]
                });
              }
              //new L.supermap.WMTSLayer
              console.log("加载内网天地图")
              layer = L.tileLayer(node.service, {
                crs: 'EPSG:3857',
                // layer: 'img',
                // style: 'default',
                // tilematrixSet: 'c',
                // format: 'tiles',
                // matrixIds: matrixIds,
                // maxZoom: identifier.length - 1
              }).addTo(this.map);
              console.log(node.center);
              const nodeCenter = this.parseNodeCenter(node.center);
              if (nodeCenter) this.map.setView(nodeCenter, 13);
            } else {
              //geoserver服务
              layer = L.tileLayer.wms(node.service, {
                layers: `${node.datasource_name}:${node.datasets_name}`, // 图层名称
                format: 'image/png',
                transparent: true,
                attribution: 'Your Attribution'
              });
            }
          } else {
            layer = await this.getAerialPhotoLayer(node);
          }
        }
        this.map.addLayer(layer);
        // if (node.data_type && node.data_type === '地图服务' && node.service) {
        //     layer.bringToBack(); //地图服务图层置底
        // }
        if (node.center && node.source_type === '影像服务') {
          if (this.currentTask && this.currentTask.latitude && this.currentTask.longitude) {
            this.safeSetView(this.currentTask.latitude, this.currentTask.longitude, 13);
          }
        }
        node.layer = layer;
      });
      this.currentLeafNodes = this.currentLeafNodes.concat(addLeafNodes);
    },
    //删除地图图层
    removeLayers(deleteLeafNodes) {
      deleteLeafNodes.forEach((node) => {
        this.map.removeLayer(node.layer);
        if (node.data_type === 'panorama') {
          this.markers.forEach((mData) => {
            if (mData.sector) {
              this.map.removeLayer(mData.sector); // 移除扇形
            }
          });
        }
        // 新增：移除关联的影像图层和事件监听
        if (node.layer._zoomHandler) {
          this.map.off('zoomend', node.layer._zoomHandler); // 移除事件监听
        }
        if (node.layer._imageLayers) {
          // 假设将imageLayers挂载到layerGroup上
          Object.values(node.layer._imageLayers).forEach((layer) => {
            this.map.removeLayer(layer);
          });
        }
      });
      this.currentLeafNodes = this.currentLeafNodes.filter((node) => !deleteLeafNodes.some((currentNode) => currentNode.label === node.label));
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
    //获取地图服务矢量数据图层
    async getVectorData(node) {
      const vectorStyle = getLeafletVectorStyle(node);
      if (node.gis_service_type === '1') {
        try {
          //获取网格数据多边形坐标
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
              style: vectorStyle
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
        // 关键：用await等待axios请求完成，确保数据返回后再继续
        const response = await axios.get(u);

        // 基于返回数据创建图层
        const layer = L.geoJson(response.data, {
          style: vectorStyle
        });
        return layer;
      }
    },
    //获取线索数据图层
    getClueData() {
      this.clusterLayer.clearLayers();
      const defaultIconBlue = L.icon({
        iconUrl: require('@/assets/images/marker-icon-blue.png'),
        iconSize: [25, 40], // 图标大小
        iconAnchor: [12.5, 40], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      });
      this.clueList.forEach((item) => {
        const marker = L.marker([item.latitude, item.longitude], {
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
    //获取全景点数据图层
    getPanoramaPointData() {
      //加载全景点
      this.panoramaPointLayer.clearLayers();
      this.taskList.forEach((item) => {
        const coords = this.normalizeCoord(item.latitude, item.longitude);
        if (!coords) return;
        const marker = L.marker(coords, {icon: this.customIcon})
          .addTo(this.panoramaPointLayer)
          .bindPopup(item.pointName);
        const markerData = {
          marker: marker,
          sector: null,
          lat: item.latitude,
          lon: item.longitude,
          customIcon: this.customIcon,
          redIcon: this.redIcon,
          imageId: item.imageId
        };
        this.markers.push(markerData);
        // 检查是否初始化时要显示这个任务的全景图和扇形
        if (this.currentTask.imageId === item.imageId) {
          // 重置所有标记为默认状态
          this.markers.forEach((mData) => {
            if (mData.sector) {
              this.map.removeLayer(mData.sector); // 移除扇形
            }
            mData.marker.setIcon(mData.customIcon); // 重置图标为默认
          });
          // 绘制当前标记的扇形
          this.drawSector(item.latitude, item.longitude, markerData, marker);
        }
        marker.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          console.log("点击全景点事件")
          // 重置所有标记为默认状态
          this.markers.forEach((mData) => {
            if (mData.sector) {
              this.map.removeLayer(mData.sector); // 移除扇形
            }
            mData.marker.setIcon(mData.customIcon); // 重置图标为默认
          });
          this.drawSector(item.latitude, item.longitude, markerData, marker);
          this.$emit('clickMarker', item, item.latitude, item.longitude, markerData, marker);
        });
      });
      return this.panoramaPointLayer;
    },
    getTempPointData(node) {
      //加载全景点
      const numberLabels = [];
      this.tempPanoramaPointLayer.clearLayers();
      if (this.tempPointList.length > 0) {
        if (node) {
          node.center = JSON.stringify([this.tempPointList[0].latitude, this.tempPointList[0].longitude]);
        }
        this.tempPointList.forEach((item) => {
          const coords = this.normalizeCoord(item.latitude, item.longitude);
          if (!coords) return;
          const circle = this.createMapCircle(item.latitude, item.longitude, 80, {
            color: 'orange',
            fillColor: 'orange',
            fillOpacity: 0.1,
            opacity: 0.4,
            weight: 2,
            pointID: item.pointId
          });
          if (!circle) return;
          circle.addTo(this.tempPanoramaPointLayer);
          // 定义数字标签
          const pointNum = item.panoramaImageCount ? item.panoramaImageCount : 0;
          const numberLabel = L.marker(coords, {
            icon: L.divIcon({
              className: 'circle-number', // 自定义样式类名
              html:
                `<div style="
                           border-radius: 50%;
                           width: 20px;
                           height: 20px;
                           line-height: 20px;
                           text-align: center;
                           font-size: 20px;

                           position: relative;
                           color: #fff;">` +
                pointNum +
                `</div>`, // 替换为你的数字
              iconSize: [20, 20] // 设置图标大小
            }),
            opacity: 0 // 默认隐藏
          }).addTo(this.tempPanoramaPointLayer);
          // 根据地图缩放级别调整圆圈半径和数字标签的透明度
          const currentZoom = this.map.getZoom();
          if (currentZoom >= 14 && currentZoom < 22) {
            numberLabel.setOpacity(1);
          }
          numberLabels.push(numberLabel);
          let clickTimer = null; // 计时器 用于记录单击事件的计时器
          numberLabel.on('click', () => {
            if (clickTimer) {
              // 如果计时器存在，说明可能是双击，清除单击事件
              clearTimeout(clickTimer);
              clickTimer = null;
              return;
            }
            clickTimer = setTimeout(() => {
              if (!this.activePanoramaPoint) {
                this.targetDivPosition.x -= 360; // 向左移动 360px
              }
              this.activePanoramaPoint = item;
              this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
              clickTimer = null; // 清空计时器
            }, 1000); // 延迟时间可根据需要调整
          });
          numberLabel.on('dblclick', async (e) => {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
            }
            await this.getMultiInfo({pointId: item.pointId, time: this.selectTime});
            this.singleObj = this.listData[0];
            this.isShowSingleDiv = true;
          });
          // 绑定鼠标悬停事件
          numberLabel.on('mouseover', (e) => {
            // 绑定并打开弹窗
            if (this.map.getZoom() >= 14) {
              circle
                .bindPopup(
                  '点位名称:' +
                  item.pointName +
                  '<br>' +
                  '批次数量:' +
                  item.panoramaImageCount +
                  '<br>' +
                  '最近拍摄时间:' +
                  item.latestTime +
                  '<br>' +
                  '飞行员信息:' +
                  item.gridOperator
                )
                .openPopup();
            }
          });
          numberLabel.on('mouseout', (e) => {
            // 关闭弹窗
            circle.closePopup();
          });
        });
      }
      // //监听影像缩放层级，控制批次显隐
      // this.map.on('zoomend', (e) => {
      //   console.log(currentZoom,1111)
      //   const currentZoom = this.map.getZoom();
      //
      //   this.currentShowZoom = Math.floor(currentZoom);
      //   this.tempPanoramaPointLayer.getLayers().forEach((layer) => {
      //     if (layer.options.pointID && currentZoom < 22) {
      //     }
      //   });
      //   if (currentZoom >= 14) {
      //     numberLabels.forEach((label) => {
      //       label.setOpacity(1);
      //     });
      //   } else {
      //     numberLabels.forEach((label) => {
      //       label.setOpacity(0);
      //     });
      //   }
      // });
      return this.tempPanoramaPointLayer;
    },
    //获取700m缓冲区数据图层
    getBufferData() {
      this.bufferLayer.clearLayers();
      this.taskList.forEach((item) => {
        const coords = this.normalizeCoord(item.latitude, item.longitude);
        if (!coords) return;
        // 由于投影问题，L.circle绘制的圆圈会变形
        const circle = this.createMapCircle(item.latitude, item.longitude, this.circleRadius, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        });
        if (circle) circle.addTo(this.bufferLayer);

        // 绘制圆圈范围，由于动态调整投影问题，导致和全景图拍摄范围不匹配
        //const radiusNew = 700;
        //const startAngleNew = 0;
        //const endAngleNew = 360;
        //const numberOfPointsNew = 360;
        //const latlngsNew = [];
        //const angleStep = (endAngleNew - startAngleNew) / numberOfPointsNew;
        //for (let i = 0; i <= numberOfPointsNew; i++) {
        //    const angle = ((startAngleNew + i * angleStep) * Math.PI) / 180; // 转换为弧度
        //    const pointLat = item.latitude + (radiusNew / 111320) * Math.cos(angle); // 111320是大约的米/纬度度转换系数
        //    const pointLon = item.longitude + (radiusNew / 111320) * Math.sin(angle);
        //
        //    latlngsNew.push([pointLat, pointLon]);
        //}
        //const circle = L.polygon(latlngsNew, {
        //    color: 'yellow',
        //    fillColor: 'transparent',
        //    fillOpacity: 0,
        //    weight: 1
        //}).addTo(this.bufferLayer);
      });
      return this.bufferLayer;
    },
    getTempBufferData(node) {
      this.tempBufferLayer.clearLayers();

      this.tempPointList.forEach((item) => {
        const coords = this.normalizeCoord(item.latitude, item.longitude);
        if (!coords) return;
        const bufferCircle = this.createMapCircle(item.latitude, item.longitude, this.circleRadius, {
          color: 'yellow',
          fillColor: 'red',
          fillOpacity: 0,
          weight: 1
        });
        if (bufferCircle) bufferCircle.addTo(this.tempBufferLayer);
      });
      return this.tempBufferLayer;
    },
    //获取线索数据
    async getClue() {
      const res = await getClueData({keyword: ''});
      if (res.code === 0) {
        this.clueList = res.data;
      } else {
        this.$message.error(res.msg);
      }
    },
    setMapZoom(zoom) {
      if (!this.map) return;
      if (this.currentTask && (this.currentTask.latitude != null || this.currentTask.lat != null)) {
        this.focusOnTask(this.currentTask, zoom);
      } else {
        this.map.setZoom(zoom);
      }
    },
    resetMapZoom() {
      this.focusOnTask(this.currentTask, 13);
    },
    addClueMarker(coord, clue_id, label) {
      L.marker(coord, {icon: this.customIcon})
        .bindPopup(clue_id + ' ' + label)
        .openPopup();
    },
    async getAerialPhotoLayer(node) {
      // 创建图层组
      const layerGroup = await this.createAggregateMarker(node);
      // 存储影像图层引用
      const imageLayers = {};
      // 记录当前是否已放大到显示影像的级别
      let isShowingImagery = false;
      // 将imageLayers挂载到layerGroup上便于后续清理
      layerGroup._imageLayers = imageLayers;
      // 监听地图缩放事件
      const zoomHandler = () => {
        const zoom = this.map.getZoom();
        console.log('当前缩放级别：', zoom);
        // 当放大到指定级别(如14级)时显示影像
        if (zoom >= 14) {
          if (!isShowingImagery) {
            layerGroup.eachLayer((marker) => {
              const bbox = marker._bbox;
              if (!bbox || bbox.length < 4) return;
              const sw = this.normalizeCoord(bbox[1], bbox[0]);
              const ne = this.normalizeCoord(bbox[3], bbox[2]);
              if (!sw || !ne) return;
              const bboxBounds = L.latLngBounds(sw, ne);
              // if (this.map.getBounds().contains(marker._imageCenter)) {
              if (this.map.getBounds().intersects(bboxBounds)) {
                if (marker._imageService && !imageLayers[marker._imageService + `+${marker._timeName}`]) {
                  //区分开来
                  const imageLayer = new ImageTileLayer(marker._imageService, {
                    collectionId: marker._tiffServiceCollection,
                    names: [marker._timeName],
                    maxZoom: this.maxZoom //设置最大级别
                  });
                  // 存储图层引用
                  imageLayers[marker._imageService + `+${marker._timeName}`] = imageLayer;
                  // 将影像图层添加到地图
                  this.map.addLayer(imageLayer);
                }
              }
            });
            isShowingImagery = true;
          }
        } else {
          // 当缩小到指定级别以下时移除影像图层
          if (isShowingImagery) {
            Object.values(imageLayers).forEach((layer) => {
              this.map.removeLayer(layer);
            });
            // 清空对象
            for (const key in imageLayers) {
              delete imageLayers[key];
            }
            isShowingImagery = false;
          }
        }
      };

      // 添加事件监听
      //this.map.on('zoomend', zoomHandler);
      // 存储zoomHandler以便后续可以移除
      layerGroup._zoomHandler = zoomHandler;
      return layerGroup;
    },
    // 创建聚合标记
    async createAggregateMarker(node) {
      const layerGroup = L.markerClusterGroup({
        disableClusteringAtZoom: 14, // 在16级停止聚合
        spiderfyOnMaxZoom: false, // 禁用最后一级的蜘蛛展开
        showCoverageOnHover: false, // 禁用悬停显示覆盖区域
        singleMarkerMode: true,
        // 自定义图标创建函数，使单个点也显示为聚合样式
        iconCreateFunction: function (cluster) {
          const count = cluster.getChildCount();
          // 即使是单个标记，也强制使用聚合样式
          return L.divIcon({
            html: '<div><span>' + count + '个</span></div>',
            className: 'marker-cluster marker-cluster-' + (count < 10 ? 'small' : count < 100 ? 'medium' : 'large'),
            iconSize: new L.Point(40, 40) // 确保尺寸正确
          });
        }
      });
      // 为每个航片添加标记
      for (const item of node.list) {
        if (item.tiffCenter !== '') {
          const rawCenter = item.tiffCenter.split(',').map((v) => parseFloat(v));
          const center = this.normalizeCoord(rawCenter[0], rawCenter[1]);
          if (!center) continue;
          const defaultIconBlue = L.icon({
            iconUrl: require('@/assets/images/marker-icon-blue.png'),
            iconSize: [25, 40], // 图标大小
            iconAnchor: [12.5, 40], // 图标锚点（中心点）
            popupAnchor: [-3, -40] // 弹出窗偏移量
          });
          const marker = L.marker(center, {icon: defaultIconBlue});
          // 存储影像服务URL到标记上
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
    //计算航片边界
    async cacuBounds(tiffId, tiffServiceCollection) {
      if (tiffId == '' || tiffServiceCollection == '') {
        this.$message.error('航片数据不全，无法计算边界，导致无法显示影像');
      }
      try {
        const res = await this.axios.get(`${window.config.iserverAdress}collections/${tiffServiceCollection}/items/${tiffId}.json`, {
          withCredentials: false
        });
        const bbox = res.data.properties['proj:bbox'];
        return bbox;
      } catch (err) {
        console.error(err);
        return null; // 或者抛出错误 throw err;
      }
    },

    async getTopViewData(para) {
      const res = await getTopViewDataApi(para);
      if (res.code === 0) {
        this.topViewList = res.data;
      }
    },
    getTopViewLayerData() {
      //换成红色图标
      const customIcon = L.icon({
        iconUrl: require('@/assets/images/topBlue.png'), // 替换为红色图标的路径
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      const redIcon = L.icon({
        iconUrl: require('@/assets/images/topRed.png'), // 替换为红色图标的路径
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32]
      });
      const data = [];
      this.topViewList.map((item) => {
        const bounds = JSON.parse(item.bounds);
        data.push({
          path: '/panoramaUrl' + item.path,
          imageBounds: bounds
        });
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
            mData.marker.setIcon(mData.customIcon); // 重置图标为默认
          });
          marker.setIcon(redIcon); // 设置为红色图标
          this.map.setView(bounds[0], 16);
        });
      });
      return this.topViewLayer;
    },
    swapLonLat(coords) {
      // 如果是最内层坐标数组（长度为2，且都是数字），则交换经纬度
      if (Array.isArray(coords) && coords.length === 2 && typeof coords[0] === 'number' && typeof coords[1] === 'number') {
        return [coords[1], coords[0]]; // [纬度, 经度]
      }
      // 如果是嵌套数组（多边形或多边形集合），则递归处理每个元素
      if (Array.isArray(coords)) {
        return coords.map((item) => this.swapLonLat(item));
      }
      // 非数组类型直接返回（防止意外数据）
      return coords;
    },
    //获取不检测区域数据
    getFrameArea() {
      this.no_detection_area_list.forEach((item) => {
        // 创建多边形并添加到地图
        L.polygon(JSON.parse(item.pixel), {
          color: 'red',       // 边框颜色
          weight: 4,          // 边框宽度
          opacity: 0.7,       // 边框透明度
          fillColor: 'transport',  // 填充颜色
          fillOpacity: 0    // 填充透明度
        }).addTo(this.frameAreaLayer);
      })
      return this.frameAreaLayer;
    },
    //获取机巢数据图层
    getNestData(node) {
      const nestIcon = L.icon({
        iconUrl: require('@/assets/images/nest.png'),
        iconSize: [40, 40], // 图标大小
        iconAnchor: [20, 20], // 图标锚点（中心点）
        popupAnchor: [-3, -40] // 弹出窗偏移量
      });
      this.nestList.forEach((item) => {
        const coords = this.normalizeCoord(item.latitude, item.longitude);
        if (!coords) return;
        const marker = L.marker(coords, {icon: nestIcon, nest_id: item.id});
        // 拼接多个信息为 HTML 字符串
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
    //获取机巢5000m缓冲区数据图层
    getNestBufferData(node) {
      this.neatBufferLayer.clearLayers();
      this.nestList.forEach((item) => {
        const coords = this.normalizeCoord(item.latitude, item.longitude);
        if (!coords) return;
        const nestCircle = this.createMapCircle(item.latitude, item.longitude, 5000, {
          color: 'red',
          fillColor: 'transport',
          fillOpacity: 0,
          opacity: 1,
          weight: 1
        });
        if (nestCircle) nestCircle.addTo(this.neatBufferLayer);
      });

      return this.neatBufferLayer;
    },

    //获取地图服务数据，构造树节点
    async getOneMapServerInfo(para) {
      const res = await getOneMapApi(para);
      if (res.code === 0) {
        if (isFiniteLatLngPair(res.data.latitude, res.data.longitude)) {
          this.center = [res.data.latitude, res.data.longitude];
        }
        this.businessData.forEach((item) => {
          if (item.label === '基础地理数据') {
            item.children = res.data['基础地理数据'].children;
          } else if (item.label === '资源调查数据') {
            item.children = res.data['资源调查数据'].children;
            item.children.forEach((item1) => {
              if(item1.label === '监测图斑'){
                this.needAddService = item1.service;
                this.datasetsName= item1.datasets_name;
                this.datasourceName = item1.datasource_name;
              }
            })
          } else if (item.label === '低空业务数据') {
            const allowShow = [
              'panorama',
              'panorama_coverage',
              'nest_location',
              'nest_coverage',
              '航片',
              'top_view',
                '其他服务',
                '禁飞区'
            ];
            res.data['低空业务数据'].children.forEach((i) => {
              if (i.data_type === 'nest_location' && i.data) {
                this.nestList = i.data;
              }
              if (allowShow.indexOf(i.data_type) !== -1 || allowShow.indexOf(i.label) !== -1) {
                item.children.push(i);
              }
            });
            item.children.push({
              service: '',
              center: '',
              data_type: 'frame_area',
              county: '320100',
              orderIndex: 10,
              datasource_name: '',
              datasets_name: '',
              label: '不检测区域'
            });
          }
        });
        const targetIndex = this.businessData[0].children.findIndex((item) => item.source_type === '影像服务');
        if (targetIndex !== -1) {
          // 从原位置移除
          const targetTask = this.businessData[0].children.splice(targetIndex, 1)[0];
          // 添加到首位
          this.businessData[0].children.unshift(targetTask);
        }
        //设置初始选中的地图服务
        this.$nextTick(() => {
          if (para.time === '') {
            const defaultDisplayDataList = [];
            const lowAltitudeChildren = this.businessData[2].children;
            const panorama = lowAltitudeChildren.find((item) => item.data_type === 'panorama');
            const panoramaCoverage = lowAltitudeChildren.find((item) => item.data_type === 'panorama_coverage');
            const nestLocation = lowAltitudeChildren.find((item) => item.data_type === 'nest_location');
            const nestCoverage = lowAltitudeChildren.find((item) => item.data_type === 'nest_coverage');
            const aerialPhoto = lowAltitudeChildren.find((item) => item.label === '航片');
            defaultDisplayDataList.push(
              panorama,
              panoramaCoverage,
              nestLocation,
              nestCoverage,
              aerialPhoto
            );
            this.businessData.forEach((i) => {
              i.children.forEach((item) => {
                if (item.isShow && item.isShow == 1) {
                  defaultDisplayDataList.push(item);
                }
              });
            });
            this.setTreeCheckedNodes(defaultDisplayDataList);
          } else if (this.selectNodes && this.selectNodes.length) {
            this.setTreeCheckedNodes(this.selectNodes);
          }
        });
      } else {
        this.$message.error('获取地图服务数据失败！');
      }

    },
    closeDetectDialog() {
      this.dialogTableVisible = false;
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.topViewMarker.forEach((mData) => {
        mData.marker.setIcon(mData.customIcon); // 重置图标为默认
      });
    },
    addToMap() {
      if (this.overlay) {
        this.map.removeLayer(this.overlay);
      }
      this.overlay = L.imageOverlay(this.currentImagePath, this.currentImageBounds, {
        opacity: 0.5, // 透明度（0-1）
        interactive: true // 允许交互（如点击事件）
      }).addTo(this.map);
    },
    handleInput(val) {
      const value = val / 100;
      if (this.overlay) {
        this.overlay.setOpacity(value);
      }
    },
    toggleFullScreen() {
      this.isFullScreen = true;
      this.$nextTick(() => {
        const elem = this.$refs.fullscreenContainer;
        if (elem.requestFullscreen) {
          elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
          /* Safari */
          elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
          /* IE11 */
          elem.msRequestFullscreen();
        }
      });
    },
    closeFullScreen() {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        /* Safari */
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        /* IE11 */
        document.msExitFullscreen();
      }
      this.isFullScreen = false;
    },
    // 地图重置
    map_reset() {
      if (!this.map) return;
      if (this.mapFitBounds && this.mapFitBounds.isValid()) {
        this.map.fitBounds(this.mapFitBounds);
        return;
      }
      if (this.mapResetCenter && Number.isFinite(this.mapResetCenter.lat) && Number.isFinite(this.mapResetCenter.lng)) {
        this.map.setView(this.mapResetCenter, this.mapResetZoom || this.zoom);
        return;
      }
      const fallback = this.getMapFallbackCenter();
      if (fallback) {
        this.map.setView(fallback, this.mapResetZoom || this.zoom);
      }
    },
  },
  async mounted() {
    try {
      await this.initMap();
      await this.getTopViewData({time: ''});
      await this.getOneMapServerInfo({time: ''});
      await this.getClue();
      if (this.isWuxiProject) {
        try {
          this.loadGeoserverVectorData();
        } catch (e) {
          console.log(e);
        }
      }
      if (this.taskList && this.taskList.length > 0) {
        this.renderTaskListMarkers();
        if (this.currentTask && this.currentTask.imageId) {
          this.focusOnTask(this.currentTask, 16);
        }
      }
      this.getPanoramaPoint();
    } catch (e) {
      console.log(e);
    }
  }
};
</script>

<style>
div#mapContainer .leaflet-control-container .leaflet-left {
  display: none !important;
}
</style>

<style scoped>
@import '@/css/pannellum.css';

::v-deep .map-container {
  width: 100%;
  height: 100%;
  background-color: white;
}

::v-deep .leaflet-control-attribution {
  display: none !important;
}

.layer-checkbox {
  margin-right: 8px;
}

::v-deep .el-collapse-item__content {
  font-size: 12px;
  color: #303133;
  line-height: 1.769230769230769;
  margin-left: 5px;
  padding-bottom: 0;
}

::v-deep .el-collapse-item__header {
  display: flex;
  align-items: center;
  height: 24px;
  line-height: 24px;
  background-color: #fff;
  color: #303133;
  cursor: pointer;
  border-bottom: 1px solid #ebeef5;
  font-size: 12px;
  font-weight: 500;
  transition: border-bottom-color 0.3s;
  outline: 0;
  margin-left: 10px;
}

::v-deep .el-form-item--small .el-form-item__content,
.el-form-item--small .el-form-item__label {
  line-height: 32px;
  width: 205px;
}

.arrow-right {
  position: absolute;
  bottom: 100px;
  left: 4px;
  width: 26px;
  height: 26px;
  z-index: 9999;
  border: 1px solid #999;
  background-color: #fff;
  border-radius: 3px;
}

.arrow-right i {
  width: 26px;
  height: 26px;
  font-size: 14px;
  color: black;
  font-weight: bold;
  text-align: center;
  display: flex;
  justify-content: center;
  align-items: center;
}

.tree-container {
  left: 10px;
  bottom: 10px;
  z-index: 9999999;
  width: 160px;
  height: auto;
  position: absolute;
  display: flex; /* 使用flex布局 */
  flex-direction: column; /* 子元素按列排列 */
  background: #fff;
  border-radius: 5px;
  overflow-y: auto;
}

.tree-container label {
  display: flex;
  align-items: center; /* 垂直居中对齐子元素 */
  padding: 5px; /* 移除默认的外边距 */
  font-size: 12px;
}

.map-container-body {
  width: 100%;
  height: 100%;
  flex: 1;
}

.map-container-header {
  height: 20px;
  line-height: 20px;
  color: #666;
  font-size: 12px;
  display: flex;
}

.map-container-header div:first-child {
  width: 96%;
  background-color: white;
}

.map-container-header div:last-child {
  flex: 1;
  background-color: white;
}

.map-container-header .el-icon-arrow-left {
  cursor: pointer;
}

.tree-container {
  background-color: rgba(255, 255, 255, 0.4);
}

.tree-container ::v-deep(.el-checkbox) {
  position: absolute;
  right: 0;
}

.tree-container ::v-deep(.el-tree) {
  background-color: rgba(255, 255, 255, 0);
}

.tree-container ::v-deep(.is-leaf) {
  display: none;
}

.tree-container ::v-deep(.el-tree-node) {
  padding: 4px 0;
}

.tree-container ::v-deep(.el-tree-node__content):hover,
.tree-container ::v-deep(.el-tree-node.is-current > .el-tree-node__content) {
  background-color: rgba(255, 255, 255, 0.3) !important;
}

.tree-container ::v-deep(.el-tree-node__expand-icon) {
  color: black;
}

.tree-container ::v-deep(.el-tree-node__children) {
  padding-top: 2px;
}

/* 强制固定旋转控制按钮样式
    ::v-deep .leaflet-control-rotate-toggle {
        background-color: #fff !important;
    }  */

/*::v-deep .leaflet-control-rotate-toggle:hover {
        background-color: #b3d4fc !important;
    }*/

::v-deep .leaflet-container {
  background: #fff;
  outline-offset: 1px;
}

.detect-list {
  background-color: rgba(0, 0, 0, 0.4);
  box-shadow: none;
  z-index: 999;
  color: #fff;
  position: absolute;
  width: 330px;
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

::v-deep .el-button--small.is-circle {
  padding: 5px;
}

::v-deep .button-expand {
  color: rgba(0, 0, 0, 0.65);
  font-weight: bold;
  font-size: 15px !important;
  cursor: pointer;
}

::v-deep .button-expand i {
  font-size: 18px !important;
  padding-right: 6px;
  font-weight: bold;
}

.show-control {
  padding: 4px;
  background-color: rgba(255, 255, 255, 0.4);
}

::v-deep .iclient-leaflet-logo {
  display: none !important;
}

.zoom-num {
  position: absolute;
  z-index: 999;
  right: 10px;
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
  right: 10px;
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

::v-deep .leaflet-control-zoom-in, ::v-deep .leaflet-control-zoom-out {
  background: rgba(0, 0, 0, 0.3) !important;
}

::v-deep .leaflet-control-zoom-out:hover {
  background: rgba(0, 0, 0, 0.2) !important;
}

.vector-table-panel {
  position: absolute;
  left: 10px;
  top: 23%;
  transform: translateY(-50%);
  z-index: 9999999;
  width: 380px;
  max-height: 320px;
  border-radius: 6px;
  overflow: hidden;
}

.vector-table-panel.collapsed {
  width: 220px;
  max-height: 40px;
}

.vector-table-panel .panel-header {
  padding: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  background-color: rgba(255, 255, 255, 0.4);
  font-weight: 600;
  color: #1f2d3d;
}

.vector-table-panel .panel-header .panel-toggle {
  cursor: pointer;
  font-size: 12px;
  color: #1f2d3d;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.3);
}

.vector-table-panel.collapsed .panel-header {
  margin-bottom: 0;
}

.vector-table-panel ::v-deep .el-table,
.vector-table-panel ::v-deep .el-table__expanded-cell {
  background-color: rgba(255, 255, 255, 0.3) !important;
  color: #333 !important;
}

.vector-table-panel ::v-deep .el-table th.el-table__cell,
.vector-table-panel ::v-deep .el-table td.el-table__cell {
  color: #333 !important;
  background: transparent !important;
}

.vector-table-panel ::v-deep .el-table th.el-table__cell > .cell,
.vector-table-panel ::v-deep .el-table td.el-table__cell > .cell {
  color: #333 !important;
}

.vector-table-panel ::v-deep .el-table tbody tr {
  background-color: transparent !important;
  cursor: pointer;;
}

.vector-table-panel ::v-deep .el-table::before {
  display: none !important;
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
::v-deep .vector-table-panel .el-table th.el-table__cell > .cell{
  background-color: rgba(255, 255, 255, 0.3) !important;
}
::v-deep .el-table--small .el-table__cell{
  padding: 2px 0!important;
}
</style>
