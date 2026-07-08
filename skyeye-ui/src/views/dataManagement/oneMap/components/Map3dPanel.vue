<template>
  <div class="map-3d-panel">
    <div
      id="cesiumContainer"
      :class="{ 'cesium-split-left': isShowSingleDiv }"
      style="height: 100%"
    ></div>
    <SceneLayerManager
      ref="sceneLayerManager"
      map-id="cesiumContainer"
      :load-resources="false"
    />
    <div
      v-show="cesiumTooltipVisible"
      class="cesium-tooltip"
      :style="cesiumTooltipStyle"
      v-html="cesiumTooltipContent"
    ></div>
    <div
      class="detectlist"
      v-if="activePanoramaPoint && !isShowSingleDiv"
    >
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
              @click="openSingleView3D(scope.row)"
            >查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div class="view-multi-comparision" v-if="isShowMultiDiv">
      <multiComparision :listData="listData" @closeMultiDiv="closeMultiDiv"></multiComparision>
    </div>
    <div
      class="view-single view-single-3d"
      v-if="isShowSingleDiv"
    >
      <template v-if="singleObj && singleObj.pointId">
        <div class="view-single-3d-close" @click="closeSingleView3D">
          <span class="el-icon-close"></span>
        </div>
        <panorama-viewer
          class="panorama-viewer-3d"
          :pointId="singleObj.pointId"
          :currentPointObj="singleObj"
          :key="singleViewKey"
          @updateSectorYaw="updateSingleSectorYaw3D"
          @panorama-mousemove="handleSinglePanoramaMove3D"
          @skipMulti="skipMulti"
        />
      </template>
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
import { GetFeaturesBySQLParameters, FeatureService } from '@supermap/iclient-leaflet';
import {
  getPanoramaImageApi
} from '@/api/commonApi';
import multiComparision from '@/views/dataManagement/oneMap/multiView/index.vue';
import SceneLayerManager from '@/components/sceneLayer/SceneLayerManager.vue';
import panoramaViewer from '@/components/panoramaViewer';
import axios from 'axios';
import * as Cesium from 'cesium';
import { getCesiumVectorStyle } from '@/utils/vectorStyle';
import { toCesiumLonLat, toMapLatLng } from '@/views/dataManagement/oneMap/oneMapCoords';
import { isTempPanoramaPoint } from '@/views/dataManagement/oneMap/oneMapDebug';

const CESIUM_TREE_LAYER_TYPES = ['panorama', 'panorama_coverage', '3dtiles'];
const PANORAMA_POINT_BATCH_SIZE = 50;
const PANORAMA_POINT_MIN_ZOOM = 9;
const PANORAMA_POINT_MAX_ZOOM = 22;
const PANORAMA_COLOR_DEFAULT = 'rgba(255, 165, 0, 0.6)';
const PANORAMA_COLOR_HOVER = 'rgba(255, 165, 0, 0.85)';
const PANORAMA_COLOR_ACTIVE = 'rgba(255, 0, 0, 0.6)';
const PANORAMA_SIZE_DEFAULT = 40;
const PANORAMA_SIZE_EMPHASIS = 44;

function buildQueryString(params) {
  return Object.keys(params)
    .map((k) => encodeURIComponent(k) + '=' + encodeURIComponent(params[k]))
    .join('&');
}

export default {
  name: 'Map3dPanel',
  components: { multiComparision, SceneLayerManager, panoramaViewer },
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
      currentImagePath: '',
      isShowMultiDiv: false,
      leftObj: null,
      rightObj: null,
      isShowSingleDiv: false,
      singleObj: null,
      singleViewKey: 0,
      cesiumSingleViewDataSource: null,
      cesiumSectorEntity: null,
      cesiumCursorEntity: null,
      listData: [],
      activePanoramaPoint: null,
      currentLeafNodes: [],
      clueList: [],
      nestList: [],
      videoListData: [],
      videoDialogVisible: false,
      currentVideoUrl: '',
      selectTime: '',
      circleRadius: window.config.circleRadius,
      PhotoDataList: [],
      baseMapService: window.config.baseMapService,
      baseMapServiceType: window.config.baseMapServiceType,
      baseMaxNativeZoom: window.config.baseMaxNativeZoom,
      minZoom: window.config.minZoom,
      maxZoom: window.config.maxZoom,
      zoom: window.config.zoom,
      currentShowZoom: window.config.zoom,
      singleToMultiTag: false,

      viewer: null,
      cesiumLoaded: false,
      cesiumLayerMap: {},
      Cesium: null,
      cesiumPanoramaEntityMap: {},
      cesiumPanoramaEntityList: [],
      cesiumPanoramaBuildToken: 0,
      cesiumPanoramaCoverageBuildToken: 0,
      billboardImageCache: {},
      hoveredPanoramaPointId: null,
      selectedPanoramaPointId: null,
      cesiumBaseMapUrl: '',
      cesiumBaseMapLayer: null,
      _cesiumClickHandler: null,
      _cesiumMoveHandler: null,
      _cesiumCameraChangedRemover: null,
      _pendingViewCenter: null,
      _pendingViewZoom: null,
      cesiumTooltipVisible: false,
      cesiumTooltipContent: '',
      cesiumTooltipStyle: { left: '0px', top: '0px' },
      _cesiumHoverPickTimer: null,
      _cesiumCameraThrottleTimer: null
    };
  },
  created() {
    this._tilesetLoadPromises = new Map();
  },
  watch: {
    initialCenter: {
      handler(val) {
        if (Array.isArray(val) && val.length === 2 && this.viewer && this.$refs.sceneLayerManager) {
          this.$refs.sceneLayerManager.flyToView(
            { lat: val[0], lng: val[1] },
            this.initialZoom
          );
        }
      },
      deep: true
    },
    treeData: {
      handler(val) {
        this.syncListsFromTreeData(val);
      },
      deep: true,
      immediate: true
    },
    activePanoramaPoint(newValue, oldValue) {
      this.updatePanoramaHighlight3D(newValue, oldValue);
    },
    panoramaPointList() {
      this.refreshPanoramaIfNeeded();
    },
    tempPointList() {
      this.refreshTempPanoramaIfNeeded();
    },
    topViewList() {
      this.refreshTopViewIfNeeded();
    }
  },
  mounted() {
    this.preloadCesium();
  },
  beforeDestroy() {
    this.destroyMap();
  },
  methods: {
    syncListsFromTreeData(treeData) {
      if (!treeData || !treeData.length) return;
      const lowAltitude = treeData.find((item) => item.label === '低空业务数据');
      if (!lowAltitude || !lowAltitude.children) return;
      const nestNode = lowAltitude.children.find((i) => i.data_type === 'nest_location');
      if (nestNode) {
        this.nestList = nestNode.data ? nestNode.data : [];
      }
      const clueNode = lowAltitude.children.find((i) => i.data_type === 'clue');
      if (clueNode) {
        this.clueList = clueNode.data ? clueNode.data : [];
      }
    },

    async initMap3D() {
      this.preloadCesium();
      await this.create3DMap();
    },

    getViewState() {
      if (this.viewer && this.Cesium) {
        const Cesium = this.Cesium;
        const carto = this.viewer.camera.positionCartographic;
        if (carto) {
          return {
            center: {
              lat: Cesium.Math.toDegrees(carto.latitude),
              lng: Cesium.Math.toDegrees(carto.longitude)
            },
            zoom: Math.floor(this.heightToZoom(carto.height))
          };
        }
      }
      return {
        center: { lat: this.initialCenter[0], lng: this.initialCenter[1] },
        zoom: this.currentShowZoom
      };
    },

    setViewState({ center, zoom }) {
      this._pendingViewCenter = center;
      this._pendingViewZoom = zoom;
    },

    flyToHome() {
      if (this.$refs.sceneLayerManager) {
        this.$refs.sceneLayerManager.flyToView(
          { lat: this.initialCenter[0], lng: this.initialCenter[1] },
          this.initialZoom
        );
        return;
      }
      if (this.viewer && this.Cesium) {
        this.flyTo3D(this.initialCenter[0], this.initialCenter[1], this.initialZoom);
      }
    },

    syncZoomDisplay() {
      this.$emit('zoom-change', this.currentShowZoom);
    },

    getZoom() {
      return this.currentShowZoom;
    },

    refreshPanoramaIfNeeded() {
      const hasPanoramaLayer = this.currentLeafNodes.some(
        (n) => n.data_type === 'panorama' || n.data_type === 'panorama_coverage'
      );
      if (hasPanoramaLayer) {
        this.refreshPanoramaLayers3D();
      }
    },

    refreshTempPanoramaIfNeeded() {
      const hasLayer = this.currentLeafNodes.some(
        (n) => n.data_type === 'temp_panorama' || n.data_type === 'temp_panorama_coverage'
      );
      if (hasLayer) {
        this.refreshTempPanoramaLayers3D();
      }
    },

    refreshTopViewIfNeeded() {
      const hasLayer = this.currentLeafNodes.some((n) => n.data_type === 'top_view');
      if (hasLayer) {
        this.refreshTopViewLayers3D();
      }
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

    async addLayers3D(addLeafNodes) {
      if (!this.viewer) return;
      const loadableNodes = addLeafNodes.filter((node) =>
        CESIUM_TREE_LAYER_TYPES.includes(node.data_type)
      );
      for (const node of loadableNodes) {
        const existing = this.cesiumLayerMap[node.label];
        if (existing && existing.type === 'tileset' && existing.tileset) {
          if (this.$refs.sceneLayerManager) {
            this.$refs.sceneLayerManager.showTileset(existing.tileset);
            await this.flyTo3dtilesNode(existing.tileset, node);
          }
          node.layer = existing.tileset;
          continue;
        }
        node.layer = await this.addLayer3D(node);
      }
      this.currentLeafNodes = this.currentLeafNodes.concat(addLeafNodes);
    },

    removeLayers3D(deleteLeafNodes) {
      deleteLeafNodes
        .filter((node) => CESIUM_TREE_LAYER_TYPES.includes(node.data_type))
        .forEach((node) => {
          this.removeLayer3D(node);
          node.layer = null;
        });
      this.currentLeafNodes = this.currentLeafNodes.filter(
        (node) => !deleteLeafNodes.some((currentNode) => currentNode.label === node.label)
      );
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

    closeDrawer() {
      this.activePanoramaPoint = null;
      this.closeSingleView3D();
      this.rightObj = null;
      this.leftObj = null;
      this.isShowMultiDiv = false;
    },

    async getPanoramaPoint(para) {
      const res = await getPanoramaPointByCountryApi(para);
      if (res.code === 0) {
        res.data.forEach((item) => {
          if (isTempPanoramaPoint(item)) {
            this.tempPointList.push(item);
          } else {
            this.panoramaPointList.push(item);
          }
        });
      } else {
        this.$message.error(res.msg);
      }
    },

    async getVideoData() {
      this.videoListData = [
        { videoName: '2025-06-03', videoUrl: '/static/video/uav1.mp4' },
        { videoName: '2025-06-04', videoUrl: '/static/video/uav1.mp4' }
      ];
    },

    showVideo(row) {
      this.currentVideoUrl = row.videoUrl;
      this.videoDialogVisible = true;
    },

    async getTimePhotoData(para) {
      // const res = await getTimePhotoApi(para);
      // if (res.code == 0) {
      //   this.PhotoDataList = res.data;
      // }
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

    getBasemapUrl(type, url) {
      if (String(type) === '2') {
        return `${url}/tile/{z}/{y}/{x}`;
      }
      return url;
    },

    findCesiumImageryNode() {
      const basicGeo = this.treeData && this.treeData.find((item) => item.label === '基础地理数据');
      const children = basicGeo && basicGeo.children ? basicGeo.children : [];
      const imageryNodes = children.filter(
        (item) =>
          item.source_type === '影像服务' &&
          String(item.gis_service_type) !== '3' &&
          item.service
      );
      if (imageryNodes.length === 0) return null;
      const defaultNode = imageryNodes.find(
        (item) => item.isShow === 1 || item.isShow === '1'
      );
      return defaultNode || imageryNodes[0];
    },

    resolveCesiumBasemapSource() {
      const minZoom = this.minZoom;
      const maxZoom = this.maxZoom;
      const maxNativeZoom = this.baseMaxNativeZoom;

      const node = this.findCesiumImageryNode();
      if (node) {
        return {
          source: 'api',
          node,
          minZoom,
          maxZoom,
          maxNativeZoom
        };
      }

      const cfgType = String(this.baseMapServiceType || '');
      if (this.baseMapService && (cfgType === '1' || cfgType === '2')) {
        return {
          source: 'config',
          type: cfgType,
          url: this.getBasemapUrl(cfgType, this.baseMapService),
          minZoom,
          maxZoom,
          maxNativeZoom
        };
      }

      if (this.baseMapService && cfgType === '3') {
        console.warn(
          '三维底图：config 为 MBTiles(type=3)，仅用于二维；请确保「基础地理数据」存在 gis_service_type≠3 的影像服务节点'
        );
      }
      return null;
    },

    async load3DBasemap() {
      /** @type {import('@/components/sceneLayer/SceneLayerManager').SceneLayerManagerInstance | undefined} */
      const manager = this.$refs.sceneLayerManager;
      if (!manager || !this.viewer) return null;

      const basemap = this.resolveCesiumBasemapSource();
      if (!basemap) {
        return null;
      }

      let layer = null;
      if (basemap.source === 'api') {
        const node = basemap.node;
        const serverType = String(node.gis_service_type);
        if (serverType === '2') {
          layer = await manager.openImageryService(node, { frameView: false });
          this.cesiumBaseMapUrl = node.service;
        } else if (serverType === '1') {
          layer = manager.loadBaseMap({
            type: '1',
            url: node.service,
            minZoom: basemap.minZoom,
            maxZoom: basemap.maxZoom,
            maxNativeZoom: basemap.maxNativeZoom
          });
          this.cesiumBaseMapUrl = node.service;
        } else {
          console.warn(`三维底图：暂不支持的影像类型 gis_service_type=${serverType}`);
        }
      } else if (basemap.source === 'config') {
        layer = manager.loadBaseMap(basemap);
        this.cesiumBaseMapUrl = basemap.url;
      }

      this.cesiumBaseMapLayer = layer;
      this.requestCesiumRender();
      return layer;
    },

    buildFlatEllipse3D(Cesium, options) {
      return {
        semiMajorAxis: options.radius,
        semiMinorAxis: options.radius,
        height: 0,
        material: options.fillColor || Cesium.Color.TRANSPARENT,
        outline: options.outline !== false,
        outlineColor: options.outlineColor || Cesium.Color.YELLOW,
        outlineWidth: options.outlineWidth != null ? options.outlineWidth : 2
      };
    },

    requestCesiumRender() {
      if (this.viewer && !this.viewer.isDestroyed()) {
        this.viewer.scene.requestRender();
      }
    },

    preloadCesium() {
      this.Cesium = Cesium;
      this.cesiumLoaded = true;
    },

    destroyMap() {
      if (this._cesiumClickHandler) {
        this._cesiumClickHandler.destroy();
        this._cesiumClickHandler = null;
      }
      if (this._cesiumMoveHandler) {
        this._cesiumMoveHandler.destroy();
        this._cesiumMoveHandler = null;
      }
      if (this._cesiumCameraChangedRemover) {
        this._cesiumCameraChangedRemover();
        this._cesiumCameraChangedRemover = null;
      }
      if (this._cesiumCameraThrottleTimer) {
        clearTimeout(this._cesiumCameraThrottleTimer);
        this._cesiumCameraThrottleTimer = null;
      }
      if (this._cesiumHoverPickTimer) {
        clearTimeout(this._cesiumHoverPickTimer);
        this._cesiumHoverPickTimer = null;
      }
      this.cesiumTooltipVisible = false;
      this.clearSingleView3DLayers();

      Object.values(this.cesiumLayerMap).forEach((ref) => {
        if (ref && ref.type === 'tileset' && ref.tileset && this.$refs.sceneLayerManager) {
          this.$refs.sceneLayerManager.removeTileset(ref.tileset);
        }
      });

      if (this.$refs.sceneLayerManager) {
        this.$refs.sceneLayerManager.removeBaseMap();
        this.$refs.sceneLayerManager.destroyScene();
      }
      this.viewer = null;
      this.Cesium = Cesium;
      this.cesiumLayerMap = {};
      this.cesiumPanoramaEntityMap = {};
      this.cesiumPanoramaEntityList = [];
      this.cesiumPanoramaBuildToken += 1;
      this.cesiumPanoramaCoverageBuildToken += 1;
      this.billboardImageCache = {};
      this.hoveredPanoramaPointId = null;
      this.selectedPanoramaPointId = null;
      this.cesiumBaseMapLayer = null;
      this.cesiumBaseMapUrl = '';
      this.currentLeafNodes = [];
      if (this._tilesetLoadPromises) {
        this._tilesetLoadPromises.clear();
      }
    },

    /** 切换 2D/3D 前重置弹窗与选中态，避免 v-show 隐藏后面板仍保留 UI */
    resetPanelUi() {
      this.closeDrawer();
      this.videoDialogVisible = false;
      this.currentVideoUrl = '';
      this.cesiumTooltipVisible = false;
      this.cesiumTooltipContent = '';
      this.isFullScreen = false;
    },

    create3DMap() {
      /** @type {import('@/components/sceneLayer/SceneLayerManager').SceneLayerManagerInstance | undefined} */
      const manager = this.$refs.sceneLayerManager;
      if (!manager) return;

      if (!Cesium) {
        this.$message.error('Cesium 未加载');
        return;
      }

      const center = this._pendingViewCenter
        ? { lat: this._pendingViewCenter.lat, lng: this._pendingViewCenter.lng }
        : { lat: this.initialCenter[0], lng: this.initialCenter[1] };
      const zoom = this._pendingViewZoom != null ? this._pendingViewZoom : this.initialZoom;

      this.viewer = manager.initScene({ center, zoom });
      this.Cesium = Cesium;
      this.cesiumLoaded = true;
      this.currentShowZoom = Math.floor(zoom);
      this.syncZoomDisplay();

      this.$nextTick(() => {
        requestAnimationFrame(() => {
          if (this.viewer) {
            this.load3DBasemap()
              .catch((e) => {
                console.error('三维底图加载失败:', e);
              })
              .finally(() => {
                if (this.viewer && !this.viewer.isDestroyed()) {
                  this.initCesiumInteractionHandlers();
                  this.setupCesiumCameraListener();
                  this.updatePanoramaPointVisibility3D();
                }
              });
          }
        });
      });
    },

    setupCesiumCameraListener() {
      if (!this.viewer || !this.Cesium) return;
      if (this._cesiumCameraChangedRemover) {
        this._cesiumCameraChangedRemover();
        this._cesiumCameraChangedRemover = null;
      }
      this._cesiumCameraChangedRemover = this.viewer.camera.changed.addEventListener(() => {
        this.onCesiumCameraIdle();
      });
    },

    onCesiumCameraIdle() {
      if (!this.viewer || this.viewer.isDestroyed()) return;
      if (this._cesiumCameraThrottleTimer) {
        clearTimeout(this._cesiumCameraThrottleTimer);
      }
      this._cesiumCameraThrottleTimer = setTimeout(async () => {
        const cartographic = this.viewer.camera.positionCartographic;
        const h = cartographic ? cartographic.height : 0;
        this.currentShowZoom = Math.floor(this.heightToZoom(h));
        this.syncZoomDisplay();
        this.updatePanoramaPointVisibility3D();
        const hasAerial = this.currentLeafNodes.some((n) => n.label === '航片');
        if (hasAerial) {
          await this.updateAerialImagery3D();
        }
        this.requestCesiumRender();
      }, 200);
    },

    initCesiumInteractionHandlers() {
      const Cesium = this.Cesium;
      if (!this._cesiumClickHandler) {
        this._cesiumClickHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
        let clickTimer = null;
        this._cesiumClickHandler.setInputAction((click) => {
          const picked = this.viewer.scene.pick(click.position);
          if (Cesium.defined(picked) && picked.id && picked.id._panoramaData) {
            const item = picked.id._panoramaData;
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
            }
            clickTimer = setTimeout(() => {
              this.activePanoramaPoint = item;
              this.getMultiInfo({ pointId: item.pointId, time: this.selectTime });
              clickTimer = null;
            }, 300);
          }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        this._cesiumClickHandler.setInputAction(async (click) => {
          const picked = this.viewer.scene.pick(click.position);
          if (Cesium.defined(picked) && picked.id && picked.id._panoramaData) {
            if (clickTimer) {
              clearTimeout(clickTimer);
              clickTimer = null;
            }
            const item = picked.id._panoramaData;
            await this.getMultiInfo({ pointId: item.pointId, time: this.selectTime });
            if (this.listData && this.listData.length > 0) {
              this.openSingleView3D(this.listData[0]);
            }
          }
        }, Cesium.ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
      }

      if (!this._cesiumMoveHandler) {
        this._cesiumMoveHandler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);
        this._cesiumMoveHandler.setInputAction((movement) => {
          if (this._cesiumHoverPickTimer) {
            clearTimeout(this._cesiumHoverPickTimer);
          }
          this._cesiumHoverPickTimer = setTimeout(() => {
            if (!this.viewer || this.viewer.isDestroyed()) return;
            const cartographic = this.viewer.camera.positionCartographic;
            const height = cartographic ? cartographic.height : 0;
            if (!this.isPanoramaPointVisibleByHeight(height)) {
              if (this.hoveredPanoramaPointId) {
                this.resetPanoramaBillboard3D(this.hoveredPanoramaPointId);
                this.hoveredPanoramaPointId = null;
              }
              this.cesiumTooltipVisible = false;
              this.requestCesiumRender();
              return;
            }
            const picked = this.viewer.scene.pick(movement.endPosition);
            if (Cesium.defined(picked) && picked.id && picked.id._panoramaData) {
              const item = picked.id._panoramaData;
              const pointId = item.pointId;
              if (pointId !== this.hoveredPanoramaPointId) {
                if (this.hoveredPanoramaPointId) {
                  this.resetPanoramaBillboard3D(this.hoveredPanoramaPointId);
                }
                this.hoveredPanoramaPointId = pointId;
                if (pointId !== this.selectedPanoramaPointId) {
                  const entity = this.cesiumPanoramaEntityMap[pointId];
                  if (entity) {
                    this.updatePanoramaBillboard3D(entity, PANORAMA_SIZE_EMPHASIS, PANORAMA_COLOR_HOVER);
                  }
                }
              }
              this.cesiumTooltipContent =
                '<strong>点位名称: ' + (item.pointName || '') + '</strong><br>' +
                '<strong>批次数量: ' + (item.panoramaImageCount || 0) + '</strong><br>' +
                '<strong>最近拍摄时间: ' + (item.latestTime || '') + '</strong><br>' +
                '<strong>飞行员信息: ' + (item.gridOperator || '') + '</strong>';
              this.cesiumTooltipStyle = {
                left: movement.endPosition.x + 12 + 'px',
                top: movement.endPosition.y + 12 + 'px'
              };
              this.cesiumTooltipVisible = true;
            } else {
              if (this.hoveredPanoramaPointId) {
                this.resetPanoramaBillboard3D(this.hoveredPanoramaPointId);
                this.hoveredPanoramaPointId = null;
              }
              this.cesiumTooltipVisible = false;
            }
            this.requestCesiumRender();
          }, 120);
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
      }
    },

    flyTo3D(lat, lng, zoom) {
      if (!this.viewer || !this.Cesium) return;
      const Cesium = this.Cesium;
      const { lat: mapLat, lon: mapLng } = toCesiumLonLat(lat, lng);
      const height = this.zoomToHeight(zoom || this.currentShowZoom);
      this.viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(mapLng, mapLat, height),
        orientation: {
          heading: Cesium.Math.toRadians(0),
          pitch: Cesium.Math.toRadians(-90),
          roll: 0
        },
        duration: 0.5
      });
    },

    drawRegion(polygon, name, lat, lng) {
      if (!this.viewer || !this.Cesium) return
      const Cesium = this.Cesium
      // 清除上一个区域
      if (this._regionEntity) { this.viewer.entities.remove(this._regionEntity); this._regionEntity = null }
      if (!polygon || !polygon.length) return
      const positions = polygon[0].map(p => Cesium.Cartesian3.fromDegrees(p.lng, p.lat))
      this._regionEntity = this.viewer.entities.add({
        name: name || '区域',
        polygon: {
          hierarchy: new Cesium.PolygonHierarchy(positions),
          material: Cesium.Color.RED.withAlpha(0.15),
          outline: true,
          outlineColor: Cesium.Color.RED,
          outlineWidth: 2,
        },
      })
      if (lat != null && lng != null) this.flyTo3D(lat, lng, 12)
      else this.viewer.flyTo(this._regionEntity, { duration: 1.2 })
    },

    resizeCesiumAfterLayout() {
      this.$nextTick(() => {
        requestAnimationFrame(() => {
          if (this.$refs.sceneLayerManager) {
            this.$refs.sceneLayerManager.resizeScene();
          }
          this.requestCesiumRender();
        });
      });
    },

    openSingleView3D(row) {
      if (!row) return;
      const merged = { ...row };
      if (this.activePanoramaPoint) {
        if (merged.latitude == null) merged.latitude = this.activePanoramaPoint.latitude;
        if (merged.longitude == null) merged.longitude = this.activePanoramaPoint.longitude;
        if (merged.pointName == null) merged.pointName = this.activePanoramaPoint.pointName;
      }
      this.singleObj = merged;
      this.singleViewKey += 1;
      this.isShowSingleDiv = true;
      this.initSingleViewSector3D();
      const lat = merged.latitude;
      const lon = merged.longitude;
      if (lat != null && lon != null) {
        const { lat: mapLat, lon: mapLng } = toCesiumLonLat(lat, lon);
        this.flyTo3D(mapLat, mapLng, 15);
      }
      this.resizeCesiumAfterLayout();
    },

    closeSingleView3D() {
      this.isShowSingleDiv = false;
      this.singleObj = null;
      this.clearSingleView3DLayers();
      this.resizeCesiumAfterLayout();
    },

    clearSingleView3DLayers() {
      if (this.viewer && !this.viewer.isDestroyed() && this.cesiumSingleViewDataSource) {
        this.viewer.dataSources.remove(this.cesiumSingleViewDataSource, true);
      }
      this.cesiumSingleViewDataSource = null;
      this.cesiumSectorEntity = null;
      this.cesiumCursorEntity = null;
    },

    initSingleViewSector3D() {
      this.clearSingleView3DLayers();
      const Cesium = this.Cesium;
      if (!this.viewer || !Cesium || this.viewer.isDestroyed()) return;
      const dataSource = new Cesium.CustomDataSource('singleViewSync');
      this.viewer.dataSources.add(dataSource);
      this.cesiumSingleViewDataSource = dataSource;
    },

    getSectorLatLngs(lat, lon, radius, startAngle, endAngle, numberOfPoints = 50) {
      const latlngs = [];
      const angleStep = (endAngle - startAngle) / numberOfPoints;
      for (let i = 0; i <= numberOfPoints; i++) {
        const angle = ((startAngle + i * angleStep) * Math.PI) / 180;
        const pointLat = lat + (radius / 111320) * Math.cos(angle);
        const pointLon = lon + (radius / (111320 * Math.cos((lat * Math.PI) / 180))) * Math.sin(angle);
        latlngs.push([pointLat, pointLon]);
      }
      latlngs.push([lat, lon]);
      return latlngs;
    },

    buildSectorPositions3D(lat, lon, radius, startAngle, endAngle, numberOfPoints = 50) {
      const Cesium = this.Cesium;
      const latlngs = this.getSectorLatLngs(lat, lon, radius, startAngle, endAngle, numberOfPoints);
      return latlngs.map(([pLat, pLon]) => Cesium.Cartesian3.fromDegrees(pLon, pLat));
    },

    updateSingleSectorYaw3D({ yaw, originYaw }) {
      if (!this.viewer || this.viewer.isDestroyed() || !this.singleObj) return;
      const Cesium = this.Cesium;
      if (!Cesium || !this.cesiumSingleViewDataSource) return;

      const lat = this.singleObj.latitude;
      const lon = this.singleObj.longitude;
      if (lat == null || lon == null) return;

      const { lat: mapLat, lon: mapLng } = toCesiumLonLat(lat, lon);
      const yawDegree = this.singleObj.yawDegree != null ? this.singleObj.yawDegree : (originYaw || 0);
      const geoYaw = Number(yaw) + Number(yawDegree);
      const radius = this.circleRadius || 800;
      const positions = this.buildSectorPositions3D(mapLat, mapLng, radius, geoYaw - 30, geoYaw + 30);

      if (!this.cesiumSectorEntity) {
        this.cesiumSectorEntity = this.cesiumSingleViewDataSource.entities.add({
          polygon: {
            hierarchy: new Cesium.PolygonHierarchy(positions),
            material: Cesium.Color.BLUE.withAlpha(0.15),
            outline: true,
            outlineColor: Cesium.Color.BLUE,
            outlineWidth: 2,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
          }
        });
      } else {
        this.cesiumSectorEntity.polygon.hierarchy = new Cesium.PolygonHierarchy(positions);
      }

      const cartographic = this.viewer.camera.positionCartographic;
      const height = cartographic ? cartographic.height : this.zoomToHeight(15);
      this.viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(mapLng, mapLat, height),
        orientation: {
          heading: Cesium.Math.toRadians(-geoYaw),
          pitch: Cesium.Math.toRadians(-90),
          roll: 0
        }
      });
      this.requestCesiumRender();
    },

    handleSinglePanoramaMove3D(data) {
      if (!this.viewer || this.viewer.isDestroyed() || !this.cesiumSingleViewDataSource) return;
      const Cesium = this.Cesium;
      const marker = data && data.currentLocationMarker;
      if (!marker || typeof marker.getLatLng !== 'function') {
        if (this.cesiumCursorEntity) {
          this.cesiumCursorEntity.show = false;
        }
        this.requestCesiumRender();
        return;
      }
      const latlng = marker.getLatLng();
      if (!latlng || (latlng.lat === 0 && latlng.lng === 0)) {
        if (this.cesiumCursorEntity) {
          this.cesiumCursorEntity.show = false;
        }
        this.requestCesiumRender();
        return;
      }
      const position = Cesium.Cartesian3.fromDegrees(latlng.lng, latlng.lat);
      if (!this.cesiumCursorEntity) {
        this.cesiumCursorEntity = this.cesiumSingleViewDataSource.entities.add({
          position,
          point: {
            pixelSize: 10,
            color: Cesium.Color.CYAN,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 1,
            disableDepthTestDistance: Number.POSITIVE_INFINITY,
            heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
          }
        });
      } else {
        this.cesiumCursorEntity.position = position;
        this.cesiumCursorEntity.show = true;
      }
      this.requestCesiumRender();
    },

    zoomToHeight(zoom) {
      const equatorCircumference = 40075016.686;
      return equatorCircumference / (2 * Math.PI * Math.pow(2, zoom));
    },

    heightToZoom(height) {
      const equatorCircumference = 40075016.686;
      return Math.log2(equatorCircumference / (2 * Math.PI * Math.max(height, 1)));
    },

    async addLayer3D(node) {
      if (!this.viewer) return null;
      if (node.source_type === '业务矢量数据服务' && node.datasets_name) {
        return await this.getVectorData3D(node);
      }
      if (node.data_type === 'clue') {
        return this.getClueData3D(node);
      }
      if (node.data_type === 'panorama') {
        return this.getPanoramaPointData3D(node);
      }
      if (node.data_type === 'panorama_coverage') {
        return this.getBufferData3D(node);
      }
      if (node.data_type === 'temp_panorama_coverage') {
        return this.getTempBufferData3D(node);
      }
      if (node.data_type === 'temp_panorama') {
        return this.getTempPointData3D(node);
      }
      if (node.data_type === 'nest_location') {
        return this.getNestData3D(node);
      }
      if (node.data_type === 'nest_coverage') {
        return this.getNestBufferData3D(node);
      }
      if (node.data_type === 'top_view') {
        return this.getTopViewLayerData3D(node);
      }
      if (node.data_type === '3dtiles') {
        return await this.load3dtilesLayer3D(node);
      }
      if (node.label === '航片') {
        return await this.getAerialPhotoLayer3D(node);
      }
      if (node.label !== '航片') {
        return this.addTreeImageryLayer3D(node);
      }
      return null;
    },

    removeLayer3D(node) {
      const ref = this.cesiumLayerMap[node.label];
      if (!ref || !this.viewer) return;
      if (Array.isArray(ref)) {
        ref.forEach((entity) => this.viewer.entities.remove(entity));
      } else if (ref.type === 'imagery' && ref.layer) {
        this.viewer.imageryLayers.remove(ref.layer, true);
      } else if (ref.type === 'datasource' && ref.source) {
        this.viewer.dataSources.remove(ref.source, true);
      } else if (ref.type === 'aerial') {
        if (ref.entities) {
          ref.entities.forEach((entity) => this.viewer.entities.remove(entity));
        }
        if (ref.imageryLayers) {
          ref.imageryLayers.forEach((layer) => this.viewer.imageryLayers.remove(layer, true));
        }
      } else if (ref.type === 'tileset' && ref.tileset && this.$refs.sceneLayerManager) {
        this.$refs.sceneLayerManager.removeTileset(ref.tileset);
      }
      if (node.data_type === 'panorama') {
        this.cesiumPanoramaBuildToken += 1;
        this.cesiumPanoramaEntityMap = {};
        this.cesiumPanoramaEntityList = [];
        this.hoveredPanoramaPointId = null;
        this.selectedPanoramaPointId = null;
        this.cesiumTooltipVisible = false;
      }
      if (node.data_type === 'panorama_coverage') {
        this.cesiumPanoramaCoverageBuildToken += 1;
      }
      delete this.cesiumLayerMap[node.label];
    },

    parse3dtilesNodeCenter(node) {
      if (!node.center) return {};
      try {
        const c = JSON.parse(node.center);
        return { latitude: c[0], longitude: c[1] };
      } catch (e) {
        console.warn('3DTiles 节点 center 解析失败', node.label, e);
        return {};
      }
    },

    async flyTo3dtilesNode(tileset, node) {
      const manager = this.$refs.sceneLayerManager;
      if (!manager || !tileset) return;
      const { latitude, longitude } = this.parse3dtilesNodeCenter(node);
      await manager.flyToTileset(tileset, {
        longitude,
        latitude,
        flyDuration: 1.5
      });
    },

    async load3dtilesLayer3D(node) {
      /** @type {import('@/components/sceneLayer/SceneLayerManager').SceneLayerManagerInstance | undefined} */
      const manager = this.$refs.sceneLayerManager;
      if (!manager || !this.viewer || !node.service) return null;

      const existing = this.cesiumLayerMap[node.label];
      if (existing && existing.type === 'tileset' && existing.tileset) {
        manager.showTileset(existing.tileset);
        await this.flyTo3dtilesNode(existing.tileset, node);
        return { type: '3d', tileset: existing.tileset };
      }

      if (this._tilesetLoadPromises.has(node.label)) {
        return this._tilesetLoadPromises.get(node.label);
      }

      const { latitude, longitude } = this.parse3dtilesNodeCenter(node);
      const loadPromise = (async () => {
        const tileset = await manager.loadTileset({
          url: node.service,
          longitude,
          latitude,
          height: node.height,
          maximumScreenSpaceError: node.maximumScreenSpaceError,
          flyTo: true,
          flyDuration: 1.5
        });
        if (!tileset) return null;
        this.cesiumLayerMap[node.label] = { type: 'tileset', tileset };
        this.requestCesiumRender();
        return { type: '3d', tileset };
      })();

      this._tilesetLoadPromises.set(node.label, loadPromise);
      try {
        return await loadPromise;
      } finally {
        this._tilesetLoadPromises.delete(node.label);
      }
    },

    addTreeImageryLayer3D(node) {
      const Cesium = this.Cesium;
      let url = node.service;
      if (node.gis_service_type === '2') {
        url = `${node.service}/tile/{z}/{y}/{x}`;
      }
      if (node.gis_service_type !== '1' && node.gis_service_type !== '2' && node.gis_service_type !== '3' && node.datasource_name) {
        const imageryLayer = this.viewer.imageryLayers.addImageryProvider(
          new Cesium.WebMapServiceImageryProvider({
            url: node.service,
            layers: `${node.datasource_name}:${node.datasets_name}`,
            parameters: { transparent: true, format: 'image/png' }
          })
        );
        this.cesiumLayerMap[node.label] = { type: 'imagery', layer: imageryLayer };
        return { type: '3d', imagery: imageryLayer };
      }
      const normalizedUrl = this.getBasemapUrl(String(node.gis_service_type), node.service);
      if (normalizedUrl === this.cesiumBaseMapUrl) {
        return { type: '3d', skip: true };
      }
      const imageryLayer = this.viewer.imageryLayers.addImageryProvider(
        new Cesium.UrlTemplateImageryProvider({
          url: normalizedUrl,
          maximumLevel: this.maxZoom,
          minimumLevel: this.minZoom
        })
      );
      if (node.center && node.source_type === '影像服务') {
        const c = JSON.parse(node.center);
        this.flyTo3D(c[0], c[1], 12);
      }
      this.cesiumLayerMap[node.label] = { type: 'imagery', layer: imageryLayer };
      return { type: '3d', imagery: imageryLayer };
    },

    async getVectorData3D(node) {
      const Cesium = this.Cesium;
      let geojsonFeature = null;
      if (node.gis_service_type === '1') {
        try {
          const sqlParam = new GetFeaturesBySQLParameters({
            queryParameter: {
              name: `${node.datasets_name}@${node.datasource_name}`,
              attributeFilter: '1=1'
            },
            datasetNames: [`${node.datasource_name}:${node.datasets_name}`]
          });
          const featureService = await new FeatureService(node.service);
          const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
          geojsonFeature = {
            type: 'FeatureCollection',
            features: serviceResult.features.features
          };
        } catch (error) {
          this.$message.error('加载矢量数据错误！');
          return null;
        }
      } else {
        const urlString = node.service + '/' + node.datasource_name;
        const param = {
          service: 'WFS',
          version: '1.1.0',
          request: 'GetFeature',
          typeName: node.datasets_name,
          outputFormat: 'application/json',
          maxFeatures: 20000,
          srsName: 'EPSG:4326'
        };
        const u = urlString + '?' + buildQueryString(param);
        const response = await axios.get(u);
        geojsonFeature = response.data;
      }
      if (!geojsonFeature) return null;
      const { strokeColorHex, strokeWidth, strokeAlpha } = getCesiumVectorStyle(node);
      const stroke = Cesium.Color.fromCssColorString(strokeColorHex).withAlpha(strokeAlpha);
      const dataSource = await Cesium.GeoJsonDataSource.load(geojsonFeature, {
        stroke,
        fill: Cesium.Color.TRANSPARENT.withAlpha(0),
        strokeWidth
      });
      await this.viewer.dataSources.add(dataSource);
      this.cesiumLayerMap[node.label] = { type: 'datasource', source: dataSource };
      return { type: '3d', source: dataSource };
    },

    getClueData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.clueList.forEach((item) => {
        const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
          billboard: {
            image: require('@/assets/images/marker-icon-blue.png'),
            width: 25,
            height: 40,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM
          },
          label: {
            text: item.clue_name || '',
            font: '12px sans-serif',
            fillColor: Cesium.Color.WHITE,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 1,
            verticalOrigin: Cesium.VerticalOrigin.TOP,
            pixelOffset: new Cesium.Cartesian2(0, 8),
            show: false
          },
          _clueData: item
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    getNestData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.nestList.forEach((item) => {
        const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
          billboard: {
            image: require('@/assets/images/nest.png'),
            width: 40,
            height: 40,
            verticalOrigin: Cesium.VerticalOrigin.CENTER
          },
          description: `<div><strong>名称：</strong>${item.name}<br><strong>位置：</strong>${item.location}</div>`
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    getNestBufferData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.nestList.forEach((item) => {
        const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
          ellipse: this.buildFlatEllipse3D(Cesium, {
            radius: 5000,
            fillColor: Cesium.Color.TRANSPARENT,
            outlineColor: Cesium.Color.RED,
            outlineWidth: 1
          })
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    getTopViewLayerData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.topViewList.forEach((item) => {
        const bounds = JSON.parse(item.bounds);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(bounds[0][1], bounds[0][0], 0),
          billboard: {
            image: require('@/assets/images/topBlue.png'),
            width: 32,
            height: 32,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM
          },
          _topViewData: item
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    getTempPointData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.tempPointList.forEach((item) => {
        const pointNum = item.panoramaImageCount ? item.panoramaImageCount : 0;
        const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
          point: {
            pixelSize: 8,
            color: Cesium.Color.fromCssColorString('#9c27b0')
          },
          label: {
            text: String(pointNum),
            font: '14px sans-serif',
            fillColor: Cesium.Color.WHITE,
            show: this.currentShowZoom >= 14
          },
          _panoramaData: item
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    getTempBufferData3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      this.tempPointList.forEach((item) => {
        const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
        const entity = this.viewer.entities.add({
          position: Cesium.Cartesian3.fromDegrees(lon, lat, 0),
          ellipse: this.buildFlatEllipse3D(Cesium, {
            radius: this.circleRadius,
            fillColor: Cesium.Color.TRANSPARENT,
            outlineColor: Cesium.Color.fromCssColorString('#800080'),
            outlineWidth: 2
          })
        });
        entities.push(entity);
      });
      this.cesiumLayerMap[node.label] = entities;
      return { type: '3d', entities };
    },

    async cacuBounds(tiffId, tiffServiceCollection) {
      if (tiffId === '' || tiffServiceCollection === '') {
        this.$message.error('航片数据不全，无法计算边界，导致无法显示影像');
      }
      try {
        const res = await axios.get(
          `${window.config.iserverAdress}collections/${tiffServiceCollection}/items/${tiffId}.json`,
          { withCredentials: false }
        );
        return res.data.properties['proj:bbox'];
      } catch (err) {
        console.error(err);
        return null;
      }
    },

    async getAerialPhotoLayer3D(node) {
      const Cesium = this.Cesium;
      const entities = [];
      const imageryLayers = [];
      const markerMetaList = [];

      for (const item of this.PhotoDataList) {
        if (item.tiffCenter !== '') {
          const center = item.tiffCenter.split(',').map((v) => parseFloat(v));
          const entity = this.viewer.entities.add({
            position: Cesium.Cartesian3.fromDegrees(center[1], center[0], 0),
            point: {
              pixelSize: 10,
              color: Cesium.Color.BLUE
            }
          });
          entities.push(entity);
          markerMetaList.push({
            entity,
            _imageService: window.config.iserverAdress,
            _tiffServiceCollection: item.tiffServiceCollection,
            _timeName: item.timeName,
            _tiffId: item.tiffId,
            _bbox: null,
            _imageCenter: center
          });
        }
      }

      const layerRef = {
        type: 'aerial',
        entities,
        imageryLayers,
        markerMetaList,
        _imageLayers: {}
      };
      this.cesiumLayerMap[node.label] = layerRef;
      this.updateAerialImagery3D(layerRef);
      return { type: '3d', aerial: layerRef };
    },

    async updateAerialImagery3D(layerRef) {
      if (!this.viewer || !this.Cesium) return;
      const aerialRef = layerRef || Object.values(this.cesiumLayerMap).find((r) => r && r.type === 'aerial');
      if (!aerialRef || !aerialRef.markerMetaList) return;

      const Cesium = this.Cesium;
      const zoom = this.currentShowZoom;
      const showImagery = zoom >= 14;

      if (!showImagery) {
        Object.values(aerialRef._imageLayers).forEach((layer) => {
          this.viewer.imageryLayers.remove(layer, true);
        });
        aerialRef._imageLayers = {};
        aerialRef.imageryLayers = [];
        this.requestCesiumRender();
        return;
      }

      for (const marker of aerialRef.markerMetaList) {
        const key = marker._imageService + '+' + marker._timeName;
        if (aerialRef._imageLayers[key]) continue;
        if (!marker._bbox && marker._tiffId) {
          marker._bbox = await this.cacuBounds(marker._tiffId, marker._tiffServiceCollection);
        }
        if (!marker._bbox) continue;

        const bbox = marker._bbox;
        const rectangle = Cesium.Rectangle.fromDegrees(bbox[0], bbox[1], bbox[2], bbox[3]);
        const tileUrl = `${marker._imageService}collections/${marker._tiffServiceCollection}/tile/{z}/{x}/{y}?name=${marker._timeName}`;
        try {
          const imageryLayer = this.viewer.imageryLayers.addImageryProvider(
            new Cesium.UrlTemplateImageryProvider({
              url: tileUrl,
              maximumLevel: this.maxZoom,
              rectangle
            })
          );
          aerialRef._imageLayers[key] = imageryLayer;
          aerialRef.imageryLayers.push(imageryLayer);
        } catch (e) {
          console.warn('航片三维影像加载失败', e);
        }
      }
      this.requestCesiumRender();
    },

    refreshPanoramaLayers3D() {
      if (!this.viewer) return;
      this.currentLeafNodes.forEach((node) => {
        if (node.data_type === 'panorama') {
          this.removeLayer3D(node);
          node.layer = this.getPanoramaPointData3D(node);
        } else if (node.data_type === 'panorama_coverage') {
          this.removeLayer3D(node);
          node.layer = this.getBufferData3D(node);
        }
      });
    },

    refreshTempPanoramaLayers3D() {
      if (!this.viewer) return;
      this.currentLeafNodes.forEach((node) => {
        if (node.data_type === 'temp_panorama') {
          this.removeLayer3D(node);
          node.layer = this.getTempPointData3D(node);
        } else if (node.data_type === 'temp_panorama_coverage') {
          this.removeLayer3D(node);
          node.layer = this.getTempBufferData3D(node);
        }
      });
    },

    refreshTopViewLayers3D() {
      if (!this.viewer) return;
      this.currentLeafNodes.forEach((node) => {
        if (node.data_type === 'top_view') {
          this.removeLayer3D(node);
          node.layer = this.getTopViewLayerData3D(node);
        }
      });
    },

    createNumberedCanvas(number, bgColor, size) {
      const canvas = document.createElement('canvas');
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext('2d');
      const r = size / 2;
      ctx.beginPath();
      ctx.arc(r, r, r - 2, 0, 2 * Math.PI);
      ctx.fillStyle = bgColor;
      ctx.fill();
      ctx.lineWidth = 2;
      ctx.strokeStyle = '#fff';
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = 'bold ' + Math.floor(size * 0.4) + 'px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(String(number), r, r);
      return canvas.toDataURL();
    },

    getBillboardImage(pointNum, color, size) {
      const key = `${pointNum}_${color}_${size}`;
      if (!this.billboardImageCache[key]) {
        this.billboardImageCache[key] = this.createNumberedCanvas(pointNum, color, size);
      }
      return this.billboardImageCache[key];
    },

    getPanoramaPointMaxHeight() {
      return 40075000 / Math.pow(2, PANORAMA_POINT_MIN_ZOOM + 1);
    },

    getPanoramaPointMinHeight() {
      return 40075000 / Math.pow(2, PANORAMA_POINT_MAX_ZOOM + 1);
    },

    isPanoramaPointVisibleByHeight(height) {
      const maxHeight = this.getPanoramaPointMaxHeight();
      const minHeight = this.getPanoramaPointMinHeight();
      return height <= maxHeight && height > minHeight;
    },

    updatePanoramaBillboard3D(entity, size, color) {
      if (!entity || !entity.billboard) return;
      const item = entity._panoramaData;
      const num = item && item.panoramaImageCount != null ? item.panoramaImageCount : 0;
      entity.billboard.width = size;
      entity.billboard.height = size;
      entity.billboard.image = this.getBillboardImage(num, color, size);
    },

    resetPanoramaBillboard3D(pointId) {
      if (pointId === this.selectedPanoramaPointId) return;
      const entity = this.cesiumPanoramaEntityMap[pointId];
      if (entity) {
        this.updatePanoramaBillboard3D(entity, PANORAMA_SIZE_DEFAULT, PANORAMA_COLOR_DEFAULT);
      }
    },

    updatePanoramaPointVisibility3D() {
      if (!this.viewer || this.viewer.isDestroyed()) return;
      const cartographic = this.viewer.camera.positionCartographic;
      const height = cartographic ? cartographic.height : 0;
      const shouldShow = this.isPanoramaPointVisibleByHeight(height);
      Object.values(this.cesiumLayerMap).forEach((ref) => {
        if (ref && ref.layerKind === 'panorama' && ref.source) {
          ref.source.show = shouldShow;
        }
      });
      if (!shouldShow) {
        this.cesiumTooltipVisible = false;
      }
      this.requestCesiumRender();
    },

    updatePanoramaHighlight3D(newValue, oldValue) {
      if (oldValue && oldValue.pointId && (!newValue || oldValue.pointId !== newValue.pointId)) {
        const oldEntity = this.cesiumPanoramaEntityMap[oldValue.pointId];
        if (oldEntity) {
          this.updatePanoramaBillboard3D(oldEntity, PANORAMA_SIZE_DEFAULT, PANORAMA_COLOR_DEFAULT);
        }
      }
      if (newValue && newValue.pointId) {
        this.selectedPanoramaPointId = newValue.pointId;
        const entity = this.cesiumPanoramaEntityMap[newValue.pointId];
        if (entity) {
          this.updatePanoramaBillboard3D(entity, PANORAMA_SIZE_EMPHASIS, PANORAMA_COLOR_ACTIVE);
        }
      } else {
        this.selectedPanoramaPointId = null;
      }
      this.requestCesiumRender();
    },

    computeGroundCirclePositions(longitude, latitude, radiusMeters, segments = 64) {
      const Cesium = this.Cesium;
      const positions = [];
      const latRad = Cesium.Math.toRadians(latitude);
      const metersPerDegLat = 111320;
      const metersPerDegLon = 111320 * Math.cos(latRad);
      for (let i = 0; i <= segments; i++) {
        const angle = (i / segments) * 2 * Math.PI;
        const dLat = (radiusMeters / metersPerDegLat) * Math.cos(angle);
        const dLon = (radiusMeters / metersPerDegLon) * Math.sin(angle);
        positions.push(Cesium.Cartesian3.fromDegrees(longitude + dLon, latitude + dLat));
      }
      return positions;
    },

    getPanoramaPointData3D(node) {
      const Cesium = this.Cesium;
      const viewer = this.viewer;
      if (!viewer || !Cesium || !node) return null;

      this.cesiumPanoramaBuildToken += 1;
      const token = this.cesiumPanoramaBuildToken;
      this.cesiumPanoramaEntityMap = {};
      this.cesiumPanoramaEntityList = [];
      this.hoveredPanoramaPointId = null;
      this.selectedPanoramaPointId = null;

      const dataSource = new Cesium.CustomDataSource('panoramaPoints');
      viewer.dataSources.add(dataSource);

      const list = this.panoramaPointList || [];
      if (list.length > 0) {
        const first = toMapLatLng(list[0].latitude, list[0].longitude);
        node.center = JSON.stringify(first);
      }

      const layerRef = {
        type: 'datasource',
        source: dataSource,
        entityCache: [],
        layerKind: 'panorama',
        buildToken: token
      };
      this.cesiumLayerMap[node.label] = layerRef;

      const scheduleBatch = (startIndex) => {
        if (token !== this.cesiumPanoramaBuildToken) return;
        const endIndex = Math.min(startIndex + PANORAMA_POINT_BATCH_SIZE, list.length);
        for (let i = startIndex; i < endIndex; i++) {
          const item = list[i];
          const pointNum = item.panoramaImageCount ? item.panoramaImageCount : 0;
          const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
          const entity = dataSource.entities.add({
            position: Cesium.Cartesian3.fromDegrees(lon, lat),
            billboard: {
              image: this.getBillboardImage(pointNum, PANORAMA_COLOR_DEFAULT, PANORAMA_SIZE_DEFAULT),
              width: PANORAMA_SIZE_DEFAULT,
              height: PANORAMA_SIZE_DEFAULT,
              heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
              scaleByDistance: new Cesium.NearFarScalar(1000, 1.0, 50000, 0.4),
              disableDepthTestDistance: Number.POSITIVE_INFINITY
            },
            _panoramaData: item
          });
          this.cesiumPanoramaEntityMap[item.pointId] = entity;
          this.cesiumPanoramaEntityList.push(entity);
          layerRef.entityCache.push(entity);
        }
        if (endIndex < list.length) {
          requestAnimationFrame(() => scheduleBatch(endIndex));
        } else if (token === this.cesiumPanoramaBuildToken) {
          this.updatePanoramaPointVisibility3D();
        }
      };

      if (list.length > 0) {
        requestAnimationFrame(() => scheduleBatch(0));
      } else {
        this.updatePanoramaPointVisibility3D();
      }

      return { type: '3d', source: dataSource };
    },

    getBufferData3D(node) {
      const Cesium = this.Cesium;
      const viewer = this.viewer;
      if (!viewer || !Cesium || !node) return null;

      const radiusInMeters = this.circleRadius || 800;
      const list = this.panoramaPointList || [];
      const batchSize = 200;

      this.cesiumPanoramaCoverageBuildToken += 1;
      const token = this.cesiumPanoramaCoverageBuildToken;

      const dataSource = new Cesium.CustomDataSource('panoramaCoverage');
      viewer.dataSources.add(dataSource);

      const layerRef = {
        type: 'datasource',
        source: dataSource,
        layerKind: 'panorama_coverage',
        buildToken: token
      };
      this.cesiumLayerMap[node.label] = layerRef;

      const scheduleBatch = (startIndex) => {
        if (token !== this.cesiumPanoramaCoverageBuildToken) return;
        const endIndex = Math.min(startIndex + batchSize, list.length);
        for (let i = startIndex; i < endIndex; i++) {
          const item = list[i];
          const { lat, lon } = toCesiumLonLat(item.latitude, item.longitude);
          const circlePositions = this.computeGroundCirclePositions(
            lon,
            lat,
            radiusInMeters
          );
          dataSource.entities.add({
            polyline: {
              positions: circlePositions,
              width: 1,
              material: Cesium.Color.YELLOW,
              clampToGround: true,
              disableDepthTestDistance: Number.POSITIVE_INFINITY
            }
          });
        }
        if (endIndex < list.length) {
          requestAnimationFrame(() => scheduleBatch(endIndex));
        } else if (token === this.cesiumPanoramaCoverageBuildToken) {
          this.requestCesiumRender();
        }
      };

      if (list.length > 0) {
        requestAnimationFrame(() => scheduleBatch(0));
      }

      return { type: '3d', source: dataSource };
    }
  }
};
</script>

<style lang="scss" scoped>
.map-3d-panel {
  height: 100%;
  position: relative;
  overflow: hidden;
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

.view-single.view-single-3d {
  width: 50%;
}

#cesiumContainer.cesium-split-left {
  width: 50%;
  position: absolute;
  left: 0;
  top: 0;
}

.panorama-viewer-3d {
  width: 100%;
  height: 100%;
}

.view-single-3d-close {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1000;
  cursor: pointer;
  font-size: 20px;
  color: #333;
  background: rgba(255, 255, 255, 0.85);
  border-radius: 50%;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
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

#cesiumContainer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  overflow: hidden;
}

::v-deep .cesium-viewer-bottom,
::v-deep .cesium-viewer-zoomIndicatorContainer {
  display: none;
}

.cesium-tooltip {
  position: absolute;
  z-index: 1001;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 8px 10px;
  font-size: 13px;
  color: #555;
  pointer-events: none;
  max-width: 280px;
  line-height: 1.6;
}
</style>
