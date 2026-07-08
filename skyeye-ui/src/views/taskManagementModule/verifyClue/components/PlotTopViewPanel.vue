<template>
  <div class="plot-top-view-panel" v-loading="loading">
    <div class="panel-toolbar">
      <el-button type="text" class="back-btn" @click="$emit('back')">
        <i class="el-icon-arrow-left"></i> 返回列表
      </el-button>
      <span class="panel-title">{{ pointTitle }}</span>
      <span class="task-tag">项目号：P32020000{{ taskNumber }}</span>
    </div>

    <div v-if="hasPoint" class="panel-body">
      <div class="panel-top">
        <div class="info-card ai-card">
          <div class="card-header">
            <span class="card-label">AI 判读结果</span>
          </div>
          <div class="ai-content">{{ aiContentText }}</div>
        </div>
        <div class="info-card project-card">
          <div class="card-header">
            <span class="card-label">项目类别</span>
          </div>
          <div class="project-tag-text">{{ projectTag || '暂无' }}</div>
        </div>
      </div>

      <div class="panel-view-tabs">
        <div
          :class="['view-tab', { active: activeTab === 'panorama' }]"
          @click="handleTabChange('panorama')"
        >
          全景图
        </div>
        <div
          :class="['view-tab', { active: activeTab === 'vertical' }]"
          @click="handleTabChange('vertical')"
        >
          俯视图
        </div>
      </div>

      <div class="panel-view-body">
        <template v-if="activeTab === 'vertical'">
          <div class="panel-middle">
            <div v-if="selectedTopView" class="image-wrapper">
              <img
                :src="resolveImageUrl(selectedTopView.path)"
                :alt="selectedTopView.dataName"
                class="main-image"
                @load="onMainImageLoaded"
                @error="onMainImageLoaded"
              />
              <div class="image-name">{{ selectedTopView.dataName }}</div>
            </div>
            <div v-else class="empty-placeholder">暂无俯视图</div>
            <div v-if="imageSwitching" class="image-loading-mask">
              <i class="el-icon-loading image-loading-spinner"></i>
            </div>
          </div>

          <div class="panel-bottom">
            <div class="bottom-label">俯视图列表</div>
            <div class="thumbnail-scroll">
              <div
                v-for="item in topViewList"
                :key="item.id"
                :class="['thumbnail-item', { active: item.id === selectedTopViewId }]"
                @click="handleSelectTopView(item)"
              >
                <img :src="resolveImageUrl(item.path)" :alt="item.dataName" />
                <span class="thumb-name">{{ item.dataName }}</span>
              </div>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="panel-middle panorama-middle">
            <panorama-viewer
              v-if="detailPointId && selectedPanoramaImage && selectedPanoramaImage.imageId"
              :key="detailPointId"
              class="panoramanic-show"
              :point-id="detailPointId"
              :current-point-obj="panoramaPointObj"
              :supervision-polygon-id="polygonId"
              :custom-calculate-panorama="calculatePanoramaFetcher"
              :simple-mode="true"
              @updateSectorYaw="handlePanoramaYawChange"
              @imageSwitch="handlePanoramaImageSwitch"
            />
            <div v-else-if="panoramaLoading" class="empty-placeholder">
              <i class="el-icon-loading image-loading-spinner"></i>
            </div>
            <div v-else class="empty-placeholder">暂无全景图</div>
          </div>
        </template>
      </div>
    </div>

    <div v-else class="empty-panel">
      暂无项目详情
    </div>
  </div>
</template>

<script>
import {
  TASK_MGMT_USE_MOCK,
  getSupervisionPolygonDetailApi,
  buildSupervisionPolygonDetailParams,
} from '@/api/taskMgmtApi';
import { getPanoramaImageApi } from '@/api/commonApi';
import {
  mockGetSupervisionPolygonDetailApi,
  mockGetPanoramaImageApi,
  mockCalculatePanoramaApi,
} from '@/views/taskManagementModule/mock/taskApi';
import PanoramaViewer from '@/components/panoramaViewer';

const DEFAULT_SITE_IMAGE_PATH = '/static/images/aqm.jpg';

export default {
  name: 'PlotTopViewPanel',
  components: { PanoramaViewer },
  props: {
    currentPoint: {
      type: Object,
      default: () => ({}),
    },
    taskNumber: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      activeTab: 'panorama',
      topViewList: [],
      selectedTopViewId: '',
      panoramaList: [],
      selectedPanoramaImage: null,
      detailPointId: '',
      panoramaLoading: false,
      loading: false,
      imageSwitching: false,
      project: null,
      projectTag: '',
      siteImagePath: '',
      constructionDesc: '',
      savedPolygonTask: null,
      loadSeq: 0,
      loadedPlotId: '',
    };
  },
  computed: {
    hasPoint() {
      return !!(this.currentPoint && (this.currentPoint.id || this.currentPoint.polygonId));
    },
    polygonId() {
      return this.currentPoint.id || this.currentPoint.polygonId || '';
    },
    pointTitle() {
      return this.currentPoint.pointName || this.currentPoint.taskName || '未选择图斑';
    },
    aiContentText() {
      return this.constructionDesc || '暂无 AI 判读说明';
    },
    selectedTopView() {
      return this.topViewList.find((item) => item.id === this.selectedTopViewId) || null;
    },
    panoramaPointObj() {
      const cp = this.currentPoint || {};
      const img = this.selectedPanoramaImage || {};
      const pointId = this.detailPointId || cp.pointId || cp.point_id || '';
      return {
        ...cp,
        pointId,
        point_id: pointId,
        pointName: cp.pointName || cp.taskName || '',
        latitude: img.latitude != null ? img.latitude : (cp.latitude != null ? cp.latitude : cp.lat),
        longitude: img.longitude != null ? img.longitude : (cp.longitude != null ? cp.longitude : cp.lon),
        height: img.height != null ? img.height : (cp.height != null ? cp.height : 100),
        imageId: img.imageId || '',
        yawDegree: img.yawDegree != null ? img.yawDegree : (cp.yawDegree != null ? cp.yawDegree : 0),
      };
    },
    calculatePanoramaFetcher() {
      return TASK_MGMT_USE_MOCK ? mockCalculatePanoramaApi : null;
    },
  },
  watch: {
    currentPoint: {
      immediate: true,
      handler(val) {
        const plotId = val && (val.id || val.polygonId);
        if (!plotId) {
          this.loadedPlotId = '';
          this.resetVerticalViews(true);
          return;
        }
        if (String(plotId) === String(this.loadedPlotId)) {
          return;
        }
        this.loadTopViews(plotId);
      },
    },
  },
  methods: {
    resolveImageUrl(path) {
      if (!path) return '';
      if (!/^https?:\/\//i.test(path)) {
        return `/panoramaUrl${path.startsWith('/') ? '' : '/'}${path}`;
      }
      try {
        const { pathname } = new URL(path);
        if (pathname) {
          return `/panoramaUrl${pathname}`;
        }
      } catch (e) {
        // ignore invalid url
      }
      return path;
    },
    resetVerticalViews(emitClear = false) {
      this.activeTab = 'vertical';
      this.topViewList = [];
      this.selectedTopViewId = '';
      this.panoramaList = [];
      this.selectedPanoramaImage = null;
      this.detailPointId = '';
      this.imageSwitching = false;
      this.project = null;
      this.projectTag = '';
      this.siteImagePath = '';
      this.constructionDesc = '';
      this.savedPolygonTask = null;
      this.loadedPlotId = '';
      this.$emit('detail-extra', { tag: '', imagePath: '' });
      if (emitClear) {
        this.$emit('clear-vertical-view');
        this.$emit('tab-change', 'vertical');
      }
    },
    parseTopViewList(data) {
      if (!data) return [];
      if (Array.isArray(data.verticalViews)) return data.verticalViews;
      if (Array.isArray(data)) return data;
      if (Array.isArray(data.topViewList)) return data.topViewList;
      if (Array.isArray(data.topViews)) return data.topViews;
      if (Array.isArray(data.list)) return data.list;
      return [];
    },
    onMainImageLoaded() {
      this.imageSwitching = false;
    },
    startImageSwitching() {
      this.imageSwitching = true;
    },
    handlePanoramaYawChange(payload) {
      this.$emit('panorama-yaw-change', payload);
    },
    buildPanoramaTaskPayload(item) {
      return {
        ...item,
        pointId: item.pointId || this.detailPointId,
        panoramaImageCount: this.panoramaList.length,
      };
    },
    buildMapPointPayload(point, detailPointId) {
      const cp = point || {};
      const pointId = detailPointId || cp.pointId || cp.point_id || '';
      return {
        ...cp,
        pointId,
        point_id: pointId,
        latitude: cp.latitude != null ? cp.latitude : cp.lat,
        longitude: cp.longitude != null ? cp.longitude : cp.lon,
        lat: cp.lat != null ? cp.lat : cp.latitude,
        lon: cp.lon != null ? cp.lon : cp.longitude,
        height: cp.height != null ? cp.height : 100,
        yawDegree: cp.yawDegree != null ? cp.yawDegree : 0,
        source: 'fallback',
      };
    },
    emitSyncMapPoint() {
      this.$emit('sync-map-point', this.buildMapPointPayload(this.currentPoint, this.detailPointId));
    },
    handlePanoramaImageSwitch(image) {
      if (!image || !image.imageId) return;
      this.selectedPanoramaImage = this.buildPanoramaTaskPayload(image);
      this.$emit('select-panorama', this.selectedPanoramaImage);
    },
    handleTabChange(tab) {
      if (this.activeTab === tab) return;
      this.activeTab = tab;
      this.$emit('tab-change', tab);
      if (tab === 'panorama') {
        this.loadPanoramaList();
      } else {
        this.$nextTick(() => this.emitSelectedVerticalView());
      }
    },
    isLoadContextValid(loadSeq, plotId) {
      if (loadSeq != null && loadSeq !== this.loadSeq) return false;
      if (plotId != null && String(this.polygonId) !== String(plotId)) return false;
      return true;
    },
    async loadPanoramaList(loadSeq, plotId) {
      const contextPlotId = plotId != null ? plotId : this.polygonId;
      const pointId = this.detailPointId
        || this.currentPoint.pointId
        || this.currentPoint.point_id;
      if (!pointId) {
        if (!this.isLoadContextValid(loadSeq, contextPlotId)) return;
        this.panoramaList = [];
        this.selectedPanoramaImage = null;
        this.emitSyncMapPoint();
        return;
      }
      this.panoramaLoading = true;
      const fetchApi = TASK_MGMT_USE_MOCK ? mockGetPanoramaImageApi : getPanoramaImageApi;
      try {
        const res = await fetchApi({ pointId });
        if (!this.isLoadContextValid(loadSeq, contextPlotId)) return;
        if (res.code === 0 && Array.isArray(res.data)) {
          this.panoramaList = res.data.map((item) => ({
            ...item,
            pointId: item.pointId || this.detailPointId,
          }));
          if (this.panoramaList.length > 0) {
            this.selectedPanoramaImage = this.buildPanoramaTaskPayload(this.panoramaList[0]);
            this.$emit('select-panorama', this.selectedPanoramaImage);
          } else {
            this.selectedPanoramaImage = null;
            this.emitSyncMapPoint();
          }
        } else {
          this.panoramaList = [];
          this.selectedPanoramaImage = null;
          this.emitSyncMapPoint();
        }
      } catch (e) {
        console.warn('全景图列表接口请求失败', e);
        if (!this.isLoadContextValid(loadSeq, contextPlotId)) return;
        this.panoramaList = [];
        this.selectedPanoramaImage = null;
        this.emitSyncMapPoint();
      } finally {
        this.panoramaLoading = false;
      }
    },
    emitSelectedVerticalView() {
      if (this.activeTab !== 'vertical') return;
      const view = this.selectedTopView;
      if (view) {
        this.$emit('select-vertical-view', view);
      } else {
        this.$emit('clear-vertical-view');
      }
    },
    async loadTopViews(polygonId) {
      if (!polygonId) return;
      const loadSeq = ++this.loadSeq;
      const requestPlotId = polygonId;
      this.loading = true;
      const params = buildSupervisionPolygonDetailParams({ id: polygonId });
      const fetchApi = TASK_MGMT_USE_MOCK
        ? mockGetSupervisionPolygonDetailApi
        : getSupervisionPolygonDetailApi;
      try {
        const res = await fetchApi(params);
        if (!this.isLoadContextValid(loadSeq, requestPlotId)) return;
        if (res.code === 0 && res.data) {
          const list = this.parseTopViewList(res.data);
          this.topViewList = list;
          this.projectTag = res.data.tag || '';
          const rawPath = res.data.imagePath || res.data.image_path || '';
          this.siteImagePath = rawPath
            ? this.resolveImageUrl(rawPath)
            : DEFAULT_SITE_IMAGE_PATH;
          this.$emit('detail-extra', {
            tag: this.projectTag,
            imagePath: this.siteImagePath,
          });
          if (list.length > 0) {
            this.selectedTopViewId = list[0].id;
          } else {
            this.selectedTopViewId = '';
          }
          this.project = res.data.project || null;
          this.constructionDesc = res.data.construction_desc
            || res.data.constructionDesc
            || '';
          this.detailPointId = res.data.pointId || res.data.point_id || '';
          this.savedPolygonTask = { ...this.currentPoint };
          const detailPolygon = res.data.polygon || res.data.geoJson || res.data.geojson;
          if (detailPolygon) {
            this.$emit('plot-polygon-ready', {
              polygonId: requestPlotId,
              polygon: detailPolygon,
            });
          }
          const tabChanged = this.activeTab !== 'panorama';
          this.activeTab = 'panorama';
          if (tabChanged) {
            this.$emit('tab-change', 'panorama');
          }
          this.loadedPlotId = String(requestPlotId);
          await this.loadPanoramaList(loadSeq, requestPlotId);
        } else {
          this.resetVerticalViews(true);
        }
      } catch (e) {
        console.warn('图斑详情接口请求失败', e);
        if (!this.isLoadContextValid(loadSeq, requestPlotId)) return;
        this.resetVerticalViews(true);
      } finally {
        if (loadSeq === this.loadSeq) {
          this.loading = false;
        }
      }
    },
    handleSelectTopView(item) {
      if (item.id === this.selectedTopViewId) return;
      this.startImageSwitching();
      this.selectedTopViewId = item.id;
      this.$emit('select-vertical-view', item);
    },
  },
};
</script>

<style scoped lang="scss">
.plot-top-view-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  width: 100%;
  background-color: #00092d;
  color: #fff;
  box-sizing: border-box;
}

.panel-toolbar {
  flex: 0 0 40px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border-bottom: 1px solid #0A579E;
}

.back-btn {
  color: #42b4f2;
  padding: 0;
  margin-right: 12px;
}

.panel-title {
  font-size: 14px;
  font-weight: bold;
  flex: 1;
}

.task-tag {
  font-size: 12px;
  color: #8c8c8c;
}

.panel-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 10px;
  gap: 10px;
}

.panel-top {
  flex: 0 0 140px;
  display: flex;
  gap: 10px;
}

.panel-view-tabs {
  flex: 0 0 36px;
  display: flex;
  gap: 8px;
}

.view-tab {
  min-width: 88px;
  height: 32px;
  line-height: 32px;
  text-align: center;
  font-size: 13px;
  color: #8c8c8c;
  border: 1px solid #0A579E;
  border-radius: 4px;
  cursor: pointer;
  background: rgba(10, 87, 158, 0.08);
  transition: all 0.2s;
}

.view-tab.active {
  color: #fff;
  border-color: #42b4f2;
  background: rgba(66, 180, 242, 0.25);
}

.panel-view-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.panorama-middle {
  padding: 0;
  align-items: stretch;
}

.panorama-middle ::v-deep .panoramanic-show {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.info-card {
  flex: 1;
  border: 1px solid #0A579E;
  border-radius: 4px;
  padding: 10px 12px;
  background: rgba(10, 87, 158, 0.15);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-label {
  font-size: 13px;
  font-weight: bold;
  color: #42b4f2;
}

.ai-content {
  font-size: 14px;
  color: #e8e8e8;
  line-height: 1.7;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
}

.project-tag-text {
  font-size: 14px;
  color: #e8e8e8;
  line-height: 1.7;
  overflow-y: auto;
  max-height: calc(100% - 28px);
}

.panel-middle {
  flex: 1;
  min-height: 0;
  border: 1px solid #0A579E;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  overflow: hidden;
  position: relative;
}

.image-loading-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 9, 45, 0.72);
}

.image-loading-spinner {
  font-size: 36px;
  color: #42b4f2;
}

.image-wrapper,
.empty-placeholder {
  width: 100%;
  height: 100%;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
}

.main-image {
  max-width: 100%;
  max-height: calc(100% - 28px);
  object-fit: contain;
}

.image-name {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 12px;
  color: #8c8c8c;
  background: rgba(0, 9, 45, 0.7);
  padding: 2px 10px;
  border-radius: 2px;
}

.panel-bottom {
  flex: 0 0 120px;
  border: 1px solid #0A579E;
  border-radius: 4px;
  padding: 8px 10px;
  background: rgba(10, 87, 158, 0.1);
}

.bottom-label {
  font-size: 12px;
  color: #42b4f2;
  margin-bottom: 8px;
}

.thumbnail-scroll {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 4px;
}

.thumbnail-scroll::-webkit-scrollbar {
  height: 4px;
}

.thumbnail-scroll::-webkit-scrollbar-thumb {
  background: #11A8ED;
  border-radius: 2px;
}

.thumbnail-item {
  flex: 0 0 90px;
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 4px;
  padding: 4px;
  transition: border-color 0.2s;
  text-align: center;
}

.thumbnail-item:hover {
  border-color: rgba(23, 125, 228, 0.5);
}

.thumbnail-item.active {
  border-color: #177DE4;
  background: rgba(59, 141, 241, 0.15);
}

.thumbnail-item img {
  width: 80px;
  height: 60px;
  object-fit: cover;
  border-radius: 2px;
  display: block;
  margin: 0 auto;
}

.thumb-name {
  display: block;
  font-size: 11px;
  color: #ccc;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  font-size: 14px;
}

.empty-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
  font-size: 14px;
  height: 100%;
}
</style>
