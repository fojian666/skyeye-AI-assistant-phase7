<template>
    <div class="vmain">
        <div class="mleft" v-if="showPolygonList && isListVisible && !pointId">
            <div class="list-up">
                <div class="vtitle">项目编号：P32020000{{ taskNumber }}</div>
                <div class="fangkuai">{{ total_todo_count }}</div>
            </div>
            <div class="vcards" v-loading="listLoading" element-loading-background="rgba(0, 0, 0, 0.3)">
                <div
                    v-for="(item, index) in cards"
                    :key="item.id || index"
                    class="vcard"
                    :class="getCardStatusClass(item)"
                    :style="borderStyle(index)"
                    @click="handleCardClick(index, item)"
                >
                    <span class="vcard-status" :class="getCardStatusClass(item)">
                        {{ getFlightStatusText(item.status) }}
                    </span>
                    <div class="card-title">{{ item.polygonType}}{{ item.id }}</div>
                    <div class="card-divider"></div>
                    <div class="card-info">
                        <span>经度: {{ item.longitude }}</span>
                        <span>纬度: {{ item.latitude }}</span>
                        <span>俯视图数量: {{ item.verticalCount }}</span>
                        <span>创建时间: {{ item.createTime }}</span>
                    </div>
                </div>
                <div v-if="!listLoading && cards.length === 0" class="list-empty">暂无图斑数据</div>
            </div>
            <div class="list-pagination">
                <el-pagination
                    small
                    background
                    layout="total, prev, pager, next"
                    :current-page="listPage.page"
                    :page-size="listPage.pageSize"
                    :pager-count="5"
                    :total="listPage.total"
                    @current-change="handleListPageChange" />
            </div>
        </div>
        <div class="rzhixian" v-if="showPolygonList && isListVisible"></div>
        <div class="tright" :class="{ 'is-full-width': !showPolygonList }">
            <div v-if="showPolygonList && !pointId" class="collapse-trigger">
                <div class="shouqi" @click="toggle_list(false)" v-if="isListVisible">
                    <i class="iconfont icon-xiangzuoshouqi"></i>
                </div>
                <div class="shouqi" @click="toggle_list(true)" v-else>
                    <i class="iconfont icon-xiangyouzhankai"></i>
                </div>
            </div>
            <div class="right-content-wrap">
                <div class="small-map-container" v-if="showSmallMap">
                    <small-map
                        class="small-map"
                        ref="smallMap"
                        :task-list="mapTaskList"
                        :current-yaw="currentYaw"
                        :current-task="currentTask"
                        :no_detection_area_list="noDetectionAreaList"
                        :is-auto-rotating="false"
                        :polygon-only-mode="true"
                        :map-view-mode="mapDisplayMode"
                        :site-image-path="siteImagePath"
                        @clickMarker="handleMapMarkerClick"
                    />
                </div>
                <div class="panel-container">
                    <plot-top-view-panel
                        :current-point="currentObj"
                        :task-number="taskNumber"
                        @select-vertical-view="handleVerticalViewSelect"
                        @clear-vertical-view="handleVerticalViewClear"
                        @tab-change="handleTabChange"
                        @select-panorama="handlePanoramaSelect"
                        @sync-map-point="handleSyncMapPoint"
                        @plot-polygon-ready="handlePlotPolygonReady"
                        @panorama-yaw-change="handlePanoramaYawChange"
                        @detail-extra="handleDetailExtra"
                        @back="handleClueReBack('-1')"
                    />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import PlotTopViewPanel from '@/views/taskManagementModule/verifyClue/components/PlotTopViewPanel.vue';
import smallMap from '@/views/taskManagementModule/components/smallMap/index.vue';
import {
  TASK_MGMT_USE_MOCK,
  getSupervisionProjectListApi,
  buildSupervisionProjectListParams,
  getSupervisionPolygonListApi,
  buildSupervisionPolygonListParams,
  TASK_TYPE_DATA_TYPE_MAP,
} from '@/api/taskMgmtApi';
import {
  mockGetSupervisionProjectListApi,
  mockGetSupervisionPolygonListApi,
} from '@/views/taskManagementModule/mock/taskApi';
import {
  adaptProjectDetail,
  adaptPolygonDetail,
  adaptPolygonList,
} from '@/views/taskManagementModule/utils/projectListAdapter';

export default {
    name: 'TaskMgmtVerifyDetail',
    components: { PlotTopViewPanel, smallMap },
    props: {
        taskId: {
            type: String,
            required: true,
        },
    },
    data() {
        return {
            pointId: null,
            isListVisible: true,
            activeIndex: '',
            cards: [],
            currentObj: {},
            currentTask: {},
            taskList: [],
            mapTaskList: [],
            total_todo_count: 0,
            showSmallMap: false,
            taskType:null,
            currentYaw: 0,
            noDetectionAreaList: [],
            routes: [],
            mapDisplayMode: 'panorama',
            mapSyncPlotId: null,
            mapSyncSeq: 0,
            listPage: {
                page: 1,
                pageSize: 5,
                total: 0,
            },
            listLoading: false,
            showPolygonList: false,
            siteImagePath: '',
        };
    },
    computed: {
        taskNumber() {
            return this.taskId;
        },
    },
    methods: {
        normalizeMapTask(item) {
            return {
                ...item,
                latitude: item.latitude != null ? item.latitude : item.lat,
                longitude: item.longitude != null ? item.longitude : item.lon,
                height: item.height != null ? item.height : 100,
            };
        },
        toggle_list(flag) {
            this.isListVisible = flag;
        },
        applyTaskList(cards, options = {}) {
            const { autoSelectFirst = true } = options;
            this.cards = cards;
            this.taskList = cards;
            this.mapTaskList = cards.map((item) => this.normalizeMapTask(item));
            if (autoSelectFirst && cards.length > 0) {
                this.handleCardClick(0, cards[0]);
            }
        },
        async loadProjectSummary() {
            this.taskType = this.$route.query.taskType || 'temp_land_restore';
            const params = buildSupervisionProjectListParams({
                id: this.taskNumber,
                taskType:this.taskType,
                pageIndex: 1,
                pageSize: 1,
            });
            const fetchApi = TASK_MGMT_USE_MOCK
                ? mockGetSupervisionProjectListApi
                : getSupervisionProjectListApi;
            try {
                const res = await fetchApi(params);
                if (res.code === 0 && res.data) {
                    const { routes } = adaptProjectDetail(res.data, this.taskNumber);
                    const detail = Array.isArray(res.data) ? (res.data[0] || {}) : res.data;
                    this.routes = routes;
                    this.total_todo_count = detail.todo_count != null
                        ? detail.todo_count
                        : (detail.count != null ? detail.count : (res.total != null ? res.total : 0));
                    if (this.listPage.total === 0 && res.total != null) {
                        this.listPage.total = res.total;
                    }
                }
            } catch (e) {
                console.warn('项目概要接口请求失败', e);
            }
        },
        async getTaskList(options = {}) {
            const { resetPage = false, autoSelectFirst = true } = options;
            if (resetPage) {
                this.listPage.page = 1;
            }
            this.taskType = this.$route.query.taskType || 'temp_land_restore';
            const dataType = TASK_TYPE_DATA_TYPE_MAP[this.taskType];
            const params = buildSupervisionPolygonListParams({
                pageIndex: this.listPage.page,
                pageSize: this.listPage.pageSize,
                supervisionProjectId: this.taskNumber,
            });
            const fetchApi = TASK_MGMT_USE_MOCK
                ? mockGetSupervisionPolygonListApi
                : getSupervisionPolygonListApi;
            this.listLoading = true;
            try {
                const res = await fetchApi({ ...params, dataType });
                if (res.code === 0 && res.data) {
                    const allCards = adaptPolygonList(res.data, this.taskNumber, dataType);
                    let cards = allCards;
                    let total = res.total != null ? res.total : allCards.length;
                    if (allCards.length > this.listPage.pageSize) {
                        const start = (this.listPage.page - 1) * this.listPage.pageSize;
                        cards = allCards.slice(start, start + this.listPage.pageSize);
                        total = res.total != null ? res.total : allCards.length;
                    }
                    this.listPage.total = total;
                    this.showPolygonList = total > 1;
                    if (!this.showPolygonList) {
                        this.isListVisible = false;
                    }
                    if (cards.length > 0) {
                        this.applyTaskList(cards, { autoSelectFirst });
                        return;
                    }
                    this.cards = [];
                    this.taskList = [];
                    this.mapTaskList = [];
                } else {
                    this.cards = [];
                    this.taskList = [];
                    this.mapTaskList = [];
                    this.listPage.total = 0;
                    this.showPolygonList = false;
                }
            } catch (e) {
                console.warn('图斑列表接口请求失败', e);
                this.cards = [];
                this.taskList = [];
                this.mapTaskList = [];
                this.listPage.total = 0;
                this.showPolygonList = false;
            } finally {
                this.listLoading = false;
            }
        },
        handleListPageChange(page) {
            this.listPage.page = page;
            this.activeIndex = '';
            this.getTaskList({ autoSelectFirst: true });
        },
        applyCurrentPoint(item) {
            this.handleVerticalViewClear();
            const normalized = this.normalizeMapTask(item);
            const samePlot = this.currentTask.id != null && this.currentTask.id === normalized.id;
            const preservedPolygon = normalized.polygon || (samePlot ? this.currentTask.polygon : null);
            this.currentObj = { ...normalized };
            this.currentTask = { ...normalized };
            if (preservedPolygon && !this.currentTask.polygon) {
                this.currentObj.polygon = preservedPolygon;
                this.currentTask.polygon = preservedPolygon;
            }
            this.currentYaw = normalized.yawDegree || 0;
            if (!this.currentObj.point_id && item.pointId) {
                this.currentObj.point_id = item.pointId;
            }
            this.mapSyncPlotId = normalized.id;
            const syncSeq = ++this.mapSyncSeq;
            this.$nextTick(() => {
                if (this.mapSyncSeq !== syncSeq || String(this.currentObj.id) !== String(normalized.id)) {
                    return;
                }
                this.syncMapPlotView(normalized.id);
            });
        },
        buildPlotMapTask(source = this.currentObj) {
            const plotTask = source || {};
            const plotLat = plotTask.latitude != null ? plotTask.latitude : plotTask.lat;
            const plotLon = plotTask.longitude != null ? plotTask.longitude : plotTask.lon;
            return {
                ...plotTask,
                plotLatitude: plotLat,
                plotLongitude: plotLon,
            };
        },
        syncMapPlotView(expectedPlotId) {
            const plotId = expectedPlotId != null ? expectedPlotId : this.currentObj.id;
            if (plotId == null || plotId === '') return;
            if (String(this.mapSyncPlotId) !== String(plotId)) return;
            const smallMapRef = this.$refs.smallMap;
            if (!smallMapRef || !smallMapRef.syncSupervisionPlotView) return;
            const mapTask = this.buildPlotMapTask(this.currentObj);
            smallMapRef.syncSupervisionPlotView(mapTask);
            if (this.mapDisplayMode === 'vertical') return;
            this.$nextTick(() => {
                if (String(this.mapSyncPlotId) !== String(plotId)) return;
                if (smallMapRef.fitMapToSupervisionTask) {
                    smallMapRef.fitMapToSupervisionTask(mapTask);
                }
            });
        },
        handlePlotPolygonReady(payload) {
            if (!payload || !payload.polygon) return;
            const { polygonId, polygon } = payload;
            if (String(this.currentObj.id) !== String(polygonId)) return;
            if (this.currentObj.polygon === polygon) return;
            this.$set(this.currentObj, 'polygon', polygon);
            this.$set(this.currentTask, 'polygon', polygon);
            this.syncMapPlotView(polygonId);
        },
        async handleCardClick(index, item) {
            this.activeIndex = index;
            let pointData = item;
            const params = buildSupervisionPolygonListParams({
                pageIndex: 1,
                pageSize: 1,
                id: item.id,
                supervisionProjectId: item.supervisionProjectId || this.taskNumber,
                polygonType: item.polygonType,
            });
            try {
                const res = await getSupervisionPolygonListApi(params);
                if (res.code === 0 && res.data) {
                    const detail = adaptPolygonDetail(res.data, this.taskNumber);
                    if (detail) {
                        pointData = detail;
                    }
                }
            } catch (e) {
                console.warn('图斑详情接口请求失败', e);
            }
            const selected = this.taskList[this.activeIndex];
            if (!selected || selected.id !== item.id) return;
            this.applyCurrentPoint(pointData);
        },
        handleVerticalViewSelect(view) {
            const smallMapRef = this.$refs.smallMap;
            if (smallMapRef && smallMapRef.showVerticalViewOverlay) {
                smallMapRef.showVerticalViewOverlay(view);
            }
        },
        handleVerticalViewClear() {
            const smallMapRef = this.$refs.smallMap;
            if (smallMapRef && smallMapRef.clearVerticalViewOverlay) {
                smallMapRef.clearVerticalViewOverlay();
            }
        },
        handleDetailExtra(payload) {
            const imagePath = payload && payload.imagePath != null ? payload.imagePath : '';
            if(this.taskType === 'mountain_water') {
                this.siteImagePath = imagePath;
            }
        },
        handleTabChange(mode) {
            this.mapDisplayMode = mode;
            const smallMapRef = this.$refs.smallMap;
            if (mode === 'panorama') {
                this.handleVerticalViewClear();
                this.$nextTick(() => {
                    this.syncMapPlotView(this.currentObj.id);
                });
            } else if (mode === 'vertical') {
                if (smallMapRef && smallMapRef.prepareVerticalViewMode) {
                    smallMapRef.prepareVerticalViewMode();
                }
                this.$nextTick(() => {
                    this.syncMapPlotView(this.currentObj.id);
                });
            }
        },
        handlePanoramaSelect(task) {
            this.syncMapPanoramaPoint(task, { source: 'panorama' });
        },
        handleSyncMapPoint(task) {
            this.syncMapPanoramaPoint(task, { source: 'fallback' });
        },
        syncMapPanoramaPoint(task, meta = {}) {
            const plotTask = this.currentObj || {};
            const polygon = plotTask.polygon;
            const mapTask = {
                ...plotTask,
                ...task,
                polygon,
                id: plotTask.id,
                polygonType: plotTask.polygonType,
            };
            const lat = mapTask.latitude != null ? mapTask.latitude : mapTask.lat;
            const lon = mapTask.longitude != null ? mapTask.longitude : mapTask.lon;

            // console.log('[图斑切换] 全景点', {
            //     source: meta.source || task.source || 'unknown',
            //     pointId: mapTask.pointId || mapTask.point_id,
            //     imageId: mapTask.imageId || '',
            //     latitude: lat,
            //     longitude: lon,
            //     yawDegree: mapTask.yawDegree != null ? mapTask.yawDegree : this.currentYaw,
            // });
            // console.log('[图斑切换] 图斑', {
            //     id: plotTask.id,
            //     polygonType: plotTask.polygonType,
            //     pointId: plotTask.pointId || plotTask.point_id,
            //     hasPolygon,
            // });

            this.currentTask = {
                ...mapTask,
                ...this.buildPlotMapTask(plotTask),
            };

            if (this.mapDisplayMode !== 'panorama') return;
            if (lat == null || lon == null) {
                // console.warn('[图斑切换] 缺少全景点经纬度，跳过全景点图层更新');
                return;
            }
            const smallMapRef = this.$refs.smallMap;
            if (smallMapRef && smallMapRef.updatePanoramaScopeLayers) {
                smallMapRef.updatePanoramaScopeLayers(mapTask);
            } else if (smallMapRef && smallMapRef.showPanoramaScope) {
                smallMapRef.showPanoramaScope(mapTask);
            }
        },
        handlePanoramaYawChange(payload) {
            if (!payload || payload.yaw == null) return;
            this.currentYaw = payload.yaw;
            if (this.mapDisplayMode !== 'panorama') return;
            const smallMapRef = this.$refs.smallMap;
            if (smallMapRef && smallMapRef.updateSector) {
                smallMapRef.updateSector(payload.yaw);
            }
        },
        handleMapMarkerClick(task) {
            const index = this.taskList.findIndex(
                (item) => item.id === task.id || item.imageId === task.imageId || item.pointId === task.pointId
            );
            if (index !== -1) {
                this.handleCardClick(index, this.taskList[index]);
            }
        },
        handleClueReBack(tag) {
            if (tag === '-1') {
                const query = {};
                if (this.$route.query.taskType) {
                    query.taskType = this.$route.query.taskType;
                }
                this.$router.push({ path: '/task-mgmt/verify-clue', query });
            }
        },
        borderStyle(index) {
            return {
                border: this.activeIndex === index ? '2px solid #11A8ED' : '1px solid #0A579E',
            };
        },
        normalizeFlightStatus(status) {
            const n = Number(status);
            return n === 1 ? 1 : 0;
        },
        getFlightStatusText(status) {
            return this.normalizeFlightStatus(status) === 1 ? '数据已飞' : '数据未飞';
        },
        getCardStatusClass(item) {
            return this.normalizeFlightStatus(item && item.status) === 1
                ? 'vcard--flown'
                : 'vcard--pending';
        },
    },
    watch: {
        taskId() {
            this.currentObj = {};
            this.currentTask = {};
            this.listPage.page = 1;
            this.showPolygonList = false;
            this.isListVisible = true;
            this.loadProjectSummary();
            this.getTaskList({ resetPage: true });
        },
        isListVisible() {
            this.$nextTick(() => {
                const smallMapRef = this.$refs.smallMap;
                if (smallMapRef && smallMapRef.map) {
                    smallMapRef.map.invalidateSize();
                }
            });
        },
    },
    mounted() {
        const username = localStorage.getItem('username');
        if (!username) {
            this.$router.push('/login');
            return;
        }
        this.pointId = this.$route.query.pointId;
        this.showSmallMap = true;
        this.loadProjectSummary();
        this.getTaskList({ autoSelectFirst: !this.pointId }).then(() => {
            if (this.pointId) {
                const index = this.taskList.findIndex(
                    (item) => String(item.pointId) === String(this.pointId) || String(item.id) === String(this.pointId)
                );
                if (index !== -1) {
                    this.handleCardClick(index, this.taskList[index]);
                }
            }
        });
    },
};
</script>

<style scoped>
.vmain {
    display: flex;
    height: 100%;
    width: 100%;
}

.mleft {
    width: 320px;
    height: 100%;
    position: relative;
    flex-shrink: 0;
    background-color: #00092d;
    border-right: 1px solid rgba(232, 234, 237, 0.2);
    display: flex;
    flex-direction: column;
}

.tright {
    flex: 1;
    min-width: 0;
    height: 100%;
    position: relative;
}

.right-content-wrap {
    display: flex;
    width: 100%;
    height: 100%;
}

.small-map-container {
    width: 50%;
    height: 100%;
    background-color: #fff;
    flex-shrink: 0;
}

.small-map {
    width: 100%;
    height: 100%;
}

.panel-container {
    width: 50%;
    height: 100%;
    min-width: 0;
    flex-shrink: 0;
}

.tright.is-full-width .small-map-container {
    width: 55%;
}

.tright.is-full-width .panel-container {
    width: 45%;
}

.rzhixian {
    flex: 0 0 1px;
    height: 100%;
    background-color: #E4E7ED;
}

.vtitle {
    font-size: 1rem;
    font-weight: bold;
    margin: 10px;
    color: #fff;
}

.collapse-trigger {
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    z-index: 999;
}

.shouqi {
    width: 16px;
    height: 120px;
    font-size: 1rem;
    justify-content: center;
    display: flex;
    align-items: center;
    background-color: #2db6f4;
    border-bottom-right-radius: 50px;
    border-top-right-radius: 50px;
}

.shouqi:hover {
    cursor: pointer;
}

.vcards {
    margin: 10px 10px 0;
    padding-bottom: 48px;
    flex: 1;
    min-height: 0;
    overflow-y: auto;
}

.vcard {
    position: relative;
    border: 1px solid #0A579E;
    margin-bottom: 8px;
    cursor: pointer;
    background-color: rgba(10, 87, 158, 0.12);
    transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out, background-color 0.3s ease-in-out;
    overflow: hidden;
    padding-left: 6px;
}

.vcard::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    border-radius: 0 2px 2px 0;
}

.vcard--flown::before {
    background: linear-gradient(180deg, #5eead4 0%, #14b8a6 100%);
    box-shadow: 0 0 8px rgba(20, 184, 166, 0.45);
}

.vcard--pending::before {
    background: linear-gradient(180deg, #fcd34d 0%, #f59e0b 100%);
    box-shadow: 0 0 8px rgba(245, 158, 11, 0.35);
}

.vcard--flown {
    background-color: rgba(20, 184, 166, 0.08);
}

.vcard--pending {
    background-color: rgba(245, 158, 11, 0.06);
}

.vcard-status {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 1;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 2px 8px 2px 6px;
    font-size: 11px;
    line-height: 1.4;
    border-radius: 999px;
    font-weight: 500;
    letter-spacing: 0.02em;
}

.vcard-status::before {
    content: '';
    flex-shrink: 0;
    width: 6px;
    height: 6px;
    border-radius: 50%;
}

.vcard-status.vcard--flown {
    color: #5eead4;
    background: rgba(20, 184, 166, 0.18);
    border: 1px solid rgba(94, 234, 212, 0.35);
}

.vcard-status.vcard--flown::before {
    background: #2dd4bf;
    box-shadow: 0 0 6px rgba(45, 212, 191, 0.8);
}

.vcard-status.vcard--pending {
    color: #fcd34d;
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(252, 211, 77, 0.35);
}

.vcard-status.vcard--pending::before {
    background: #fbbf24;
    box-shadow: 0 0 6px rgba(251, 191, 36, 0.7);
    animation: status-pulse 2s ease-in-out infinite;
}

@keyframes status-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.55; transform: scale(0.85); }
}

.list-empty {
    text-align: center;
    color: #999;
    padding: 24px 0;
    font-size: 13px;
}

.list-pagination {
    position: absolute;
    left: 8px;
    right: 8px;
    bottom: 8px;
    display: flex;
    justify-content: center;
    padding: 0;
}

.list-pagination ::v-deep .el-pagination__total {
    color: #ccc;
}

.list-pagination ::v-deep .btn-prev,
.list-pagination ::v-deep .btn-next,
.list-pagination ::v-deep .el-pager li {
    background-color: #001a4d;
    color: #ccc;
}

.list-pagination ::v-deep .el-pager li.active {
    color: #2db6f4;
}

.card-title {
    font-weight: bold;
    margin-bottom: 5px;
    margin-top: 5px;
    margin-left: 10px;
    margin-right: 88px;
    color: #fff;
}

.card-divider {
    height: 1px;
    width: 100%;
    background-color: #0A579E;
}

.card-info {
    font-size: 12px;
    display: flex;
    flex-direction: column;
    padding: 6px 10px ;
    color: #ccc;
}

.card-info span {
    margin-bottom: 8px;
    color: #ccc;
}

.vcard:hover {
    box-shadow: 0 2px 10px rgba(17, 168, 237, 0.25);
}

.vcard--flown:hover {
    background-color: rgba(20, 184, 166, 0.14);
}

.vcard--pending:hover {
    background-color: rgba(245, 158, 11, 0.1);
}

.fangkuai {
    width: 30px;
    height: 30px;
    background-color: #2DB6F4;
    margin-top: 8px;
    display: flex;
    justify-content: center;
    align-items: center;
    font-size: 14px;
    color: white;
}

.list-up {
    height: 40px;
    display: flex;
    flex-direction: row;
    flex-shrink: 0;
}
</style>
