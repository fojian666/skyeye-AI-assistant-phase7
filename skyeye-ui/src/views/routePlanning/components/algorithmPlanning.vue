<template>
    <div class="box">
        <div class="left" :style="{ width: `${sidebarWidth}px` }">
            <div class="sidebar-resizer" title="拖动调整侧栏宽度" @mousedown.prevent="startSidebarResize">
                <span></span>
            </div>
            <div class="sidebar-header">
                <div class="sidebar-heading">
                    <div>
                        <i class="iconfont icon-baogaoguanli"></i>
                        <span>多机航线规划</span>
                    </div>
                    <small>多起点 · 多航线 · ALNS</small>
                </div>
                <div class="sidebar-tabs">
                    <button :class="{ active: activeSidebarTab === 'config' }" @click="switchSidebarTab('config')">
                        <i class="el-icon-setting"></i>
                        任务配置
                    </button>
                    <button :class="{ active: activeSidebarTab === 'result' }" @click="switchSidebarTab('result')">
                        <i class="el-icon-data-analysis"></i>
                        规划结果
                        <em v-if="planResultRoutes.length">{{ planResultRoutes.length }}</em>
                    </button>
                </div>
            </div>

            <div class="sidebar-scroll">
                <div v-show="activeSidebarTab === 'config'" class="sidebar-pane">
                    <section class="sidebar-card form-card">
                        <div class="card-title">
                            <span><i class="el-icon-edit-outline"></i>基础参数</span>
                            <small>设置任务和飞行参数</small>
                        </div>
                        <el-form ref="ruleForm" :model="ruleForm" :rules="rules" status-icon label-position="top" class="demo-ruleForm">
                            <div class="form-grid">
                                <el-form-item label="任务名称" prop="planname" class="wide-field">
                                    <el-input v-model="ruleForm.planname" clearable class="custom-elinput-height" />
                                </el-form-item>
                                <el-form-item label="相机/镜头（KMZ固定配置）" prop="cameraSize" class="wide-field">
                                    <el-select v-model="ruleForm.cameraSize" disabled class="custom-elinput-height">
                                        <el-option label="大疆可见光镜头，焦距 24mm" value="24" />
                                    </el-select>
                                </el-form-item>
                                <el-form-item label="攀升/巡飞高度 / m" prop="takeOffSecurityHeight">
                                    <el-input-number
                                        v-model="ruleForm.takeOffSecurityHeight"
                                        :min="1"
                                        :step="10"
                                        controls-position="right"
                                        class="custom-elinput-height full-width" />
                                </el-form-item>
                            </div>
                        </el-form>
                    </section>

                    <section class="sidebar-card">
                        <div class="card-title">
                            <span><i class="el-icon-upload2"></i>规划数据</span>
                            <small>上传地块和无人机机巢点位</small>
                        </div>
                        <div class="upload-row">
                            <div>
                                <label>地块数据包</label>
                                <span :class="{ ready: ruleForm.parcelName }">{{ ruleForm.parcelName || '尚未上传 ZIP' }}</span>
                            </div>
                            <el-button type="primary" plain size="mini" icon="el-icon-upload2" @click="openParcelDialog">上传</el-button>
                        </div>
                        <div class="upload-row">
                            <div>
                                <label>机巢点位</label>
                                <span :class="{ ready: ruleForm.aircraftName }">{{ ruleForm.aircraftName || '尚未上传 SHP' }}</span>
                            </div>
                            <el-button type="primary" plain size="mini" icon="el-icon-upload2" @click="openAircraftDialog">上传</el-button>
                        </div>
                    </section>

                    <section v-if="processing.active || processing.progress > 0" class="sidebar-card processing-panel">
                        <div class="processing-title">
                            <span>{{ processing.title }}</span>
                            <span>{{ processing.message }}</span>
                        </div>
                        <el-progress :percentage="processing.progress" :status="processing.status" :stroke-width="14" text-inside />
                    </section>

                    <section v-if="datasetSummary" class="sidebar-card">
                        <div class="card-title">
                            <span><i class="el-icon-circle-check"></i>数据筛选结果</span>
                            <small>{{ parcelRangeKm }} km 服务半径</small>
                        </div>
                        <div class="dataset-summary">
                            <div class="summary-item">
                                <span>有效地块</span>
                                <strong>{{ datasetSummary.parcelCount }}</strong>
                            </div>
                            <div class="summary-item">
                                <span>剔除地块</span>
                                <strong class="excluded-count">{{ datasetSummary.excludedParcelCount || 0 }}</strong>
                            </div>
                            <div class="summary-item">
                                <span>机巢</span>
                                <strong>{{ datasetSummary.aircraftCount }}</strong>
                            </div>
                        </div>
                        <p class="summary-tip">仅保留所有边界点均位于任一机巢 6 km 服务范围内的地块。</p>
                        <div v-if="excludedParcelNames.length" class="excluded-actions">
                            <el-button type="text" size="mini" @click="excludedDialogVisible = true">
                                查看 {{ excludedParcelNames.length }} 个超范围地块
                            </el-button>
                            <el-button type="warning" plain size="mini" icon="el-icon-download" @click="downloadExcludedParcels"> 下载 </el-button>
                        </div>
                    </section>

                    <section v-if="aircraft.length" class="sidebar-card">
                        <div class="card-title">
                            <span><i class="iconfont icon-geoai-list"></i>机巢起降点</span>
                            <small>共 {{ aircraft.length }} 个</small>
                        </div>
                        <el-table :data="aircraft" size="mini" max-height="250" border class="nest-point-table">
                            <el-table-column type="index" label="序号" width="64" align="center" />
                            <el-table-column prop="name" label="机巢名称" width="160" show-overflow-tooltip />
                            <el-table-column label="起降点坐标" min-width="230">
                                <template slot-scope="scope">
                                    <span class="coordinate-value">{{ formatCoordinate(scope.row) }}</span>
                                </template>
                            </el-table-column>
                        </el-table>
                    </section>
                </div>

                <div v-show="activeSidebarTab === 'result'" class="sidebar-pane result-pane">
                    <section v-if="planResultRoutes.length" class="result-overview">
                        <div>
                            <span>{{ resultViewSource === 'history' ? '历史航线' : '本次航线' }}</span>
                            <strong>{{ visiblePlanResultRoutes.length }}</strong>
                        </div>
                        <div>
                            <span>参与飞机</span>
                            <strong>{{ resultAircraftCount }}</strong>
                        </div>
                        <div>
                            <span>总里程 / km</span>
                            <strong>{{ resultTotalDistance }}</strong>
                        </div>
                    </section>

                    <section v-if="planResultRoutes.length" class="sidebar-card">
                        <div class="card-title">
                            <span><i class="el-icon-s-operation"></i>{{ displayedResultTitle }}</span>
                            <small>{{ resultViewSource === 'history' ? '历史任务完整结果' : '按飞机与航线分配' }}</small>
                        </div>
                        <el-table :data="visiblePlanResultRoutes" size="mini" :max-height="resultRouteTableHeight" border class="result-route-table">
                            <el-table-column prop="aircraftName" label="飞机" min-width="90" show-overflow-tooltip />
                            <el-table-column label="航线" width="72" align="center">
                                <template slot-scope="scope">#{{ scope.row.sortieIndex }}</template>
                            </el-table-column>
                            <el-table-column prop="name" label="航线名称" min-width="190" show-overflow-tooltip />
                            <el-table-column label="里程 / km" width="100" align="right">
                                <template slot-scope="scope">
                                    <span class="distance-value">{{ formatDistance(scope.row.distanceKm) }}</span>
                                </template>
                            </el-table-column>
                        </el-table>
                    </section>

                    <div v-else class="result-empty">
                        <i class="el-icon-data-analysis"></i>
                        <strong>暂无规划结果</strong>
                        <span>完成数据上传和筛选后，点击“开始规划”。</span>
                        <el-button type="primary" plain size="small" @click="switchSidebarTab('config')">前往任务配置</el-button>
                    </div>

                    <section class="sidebar-card history-card">
                        <div class="card-title">
                            <span><i class="iconfont icon-geoai-list"></i>历史航线</span>
                            <small>共 {{ tablePage.dataCount }} 条</small>
                        </div>
                        <div class="history-task-select">
                            <label>选择任务</label>
                            <div class="history-task-control">
                                <el-select v-model="selectedHistoryTask" placeholder="请选择任务名称" filterable @change="handleHistoryTaskChange">
                                    <el-option v-for="task in historyTaskOptions" :key="task.key" :label="task.label" :value="task.key" />
                                </el-select>
                                <el-button
                                    type="danger"
                                    plain
                                    size="mini"
                                    icon="el-icon-delete"
                                    :disabled="!selectedHistoryTask"
                                    @click="handleDeleteHistoryTask">
                                    删除任务
                                </el-button>
                            </div>
                        </div>

                        <div v-if="selectedHistoryTask" class="history-capture-select">
                            <label>航线类型</label>
                            <el-radio-group v-model="historyCaptureType" size="mini" @change="handleHistoryCaptureTypeChange">
                                <el-radio-button label="overview">俯视图航线</el-radio-button>
                                <el-radio-button label="panorama">全景图航线</el-radio-button>
                            </el-radio-group>
                        </div>

                        <div v-if="selectedHistoryTask" class="aircraft-card-grid">
                            <button
                                v-for="aircraftItem in selectedTaskAircraft"
                                :key="aircraftItem.name"
                                class="aircraft-history-card"
                                :class="{ active: selectedHistoryAircraft === aircraftItem.name }"
                                @click="handleHistoryAircraftSelect(aircraftItem.name)">
                                <span class="aircraft-card-icon"><i class="el-icon-position"></i></span>
                                <span class="aircraft-card-info">
                                    <strong>{{ aircraftItem.name }}</strong>
                                    <small>{{ aircraftItem.routes.length }} 条航线</small>
                                </span>
                                <i class="el-icon-arrow-right"></i>
                            </button>
                        </div>

                        <div v-if="selectedHistoryAircraft" class="history-route-section">
                            <div class="history-route-heading">
                                <div>
                                    <span>{{ selectedHistoryAircraft }} 航线</span>
                                    <small>点击卡片在地图上高亮显示</small>
                                </div>
                                <div class="history-heading-actions">
                                    <el-button type="primary" plain size="mini" icon="el-icon-view" @click="renderHistoryTaskOverview"
                                        >显示任务全部航线</el-button
                                    >
                                    <el-button type="danger" plain size="mini" icon="el-icon-delete" @click="handleDeleteHistoryAircraft">
                                        删除该飞机全部航线
                                    </el-button>
                                </div>
                            </div>
                            <div class="history-route-list">
                                <article
                                    v-for="route in selectedAircraftRoutes"
                                    :key="route.id"
                                    class="history-route-card"
                                    :class="{ active: selectedHistoryRouteId === route.id }"
                                    @click="handleHistoryRouteSelect(route)">
                                    <div class="route-card-index">#{{ route.sortieIndex }}</div>
                                    <div class="route-card-main">
                                        <strong>{{ route.displayName }}</strong>
                                        <span>{{ route.name }}</span>
                                    </div>
                                    <div class="route-card-actions" @click.stop>
                                        <el-button type="text" icon="el-icon-download" title="下载航线" @click="handleDownload(route)" />
                                        <el-button
                                            type="text"
                                            class="delete-route-button"
                                            icon="el-icon-delete"
                                            title="删除航线"
                                            @click="handleDelete(route)" />
                                    </div>
                                </article>
                            </div>
                        </div>

                        <div v-if="!historyTaskOptions.length" class="history-empty">
                            <i class="el-icon-folder-opened"></i>
                            <span>暂无历史航线</span>
                        </div>
                    </section>
                </div>
            </div>

            <div class="sidebar-footer">
                <div class="footer-status">
                    <i :class="parcelFilterReady ? 'el-icon-circle-check' : 'el-icon-warning-outline'"></i>
                    <span>{{ parcelFilterReady ? '数据已就绪' : '请先完成数据上传' }}</span>
                </div>
                <div>
                    <el-button type="info" size="small" @click="resetForm">重置</el-button>
                    <el-button
                        type="primary"
                        size="small"
                        :loading="processing.active"
                        :disabled="processing.active || !parcelFilterReady"
                        @click="submitForm">
                        开始规划
                    </el-button>
                </div>
            </div>
        </div>

        <div class="right">
            <map-container ref="mapRef" :table-data="tableData" :show-controls="false" />
            <div v-if="activeSidebarTab === 'result' && planResultRoutes.length" class="route-layer-switch">
                <span>地图航线图层</span>
                <el-radio-group v-model="resultCaptureType" size="small" @change="handleResultCaptureTypeChange">
                    <el-radio-button label="overview">俯视图航线</el-radio-button>
                    <el-radio-button label="panorama">全景图航线</el-radio-button>
                </el-radio-group>
            </div>
        </div>

        <el-dialog title="上传地块数据包" :visible.sync="parcelDialogVisible" width="420px" :modal="false">
            <el-alert title="ZIP 内可包含多个地块面 SHP，每个 SHP 请同时带上 .dbf、.shx、.prj 等配套文件。" type="info" :closable="false" show-icon />
            <el-upload
                ref="parcelUpload"
                class="upload-demo"
                drag
                action=""
                accept=".zip"
                :auto-upload="false"
                :limit="1"
                :file-list="parcelFileList"
                :on-change="handleParcelChange"
                :on-remove="handleParcelRemove">
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">将地块 ZIP 拖到此处，或<em>点击选择</em></div>
                <div class="el-upload__tip" slot="tip">仅支持 ZIP，大小不超过 1GB</div>
            </el-upload>
            <div slot="footer">
                <el-button @click="parcelDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="parcelLoading" :disabled="!parcelZip" @click="uploadParcelConfirm"> 解析地块 </el-button>
            </div>
        </el-dialog>

        <el-dialog title="上传机巢点位" :visible.sync="aircraftDialogVisible" width="420px" :modal="false">
            <el-alert
                title="请同时选择 .shp、.dbf、.shx、.prj 等配套文件；支持一个包含多个无人机机巢点位的点 SHP。"
                type="info"
                :closable="false"
                show-icon />
            <el-upload
                ref="aircraftUpload"
                class="upload-demo"
                drag
                action=""
                accept=".shp,.dbf,.shx,.prj,.cpg,.sbn,.sbx"
                multiple
                :auto-upload="false"
                :file-list="aircraftFileList"
                :on-change="handleAircraftChange"
                :on-remove="handleAircraftRemove">
                <i class="el-icon-upload"></i>
                <div class="el-upload__text">将 SHP 及配套文件拖到此处，或<em>点击选择</em></div>
                <div class="el-upload__tip" slot="tip">需包含 .shp 文件，总大小不超过 1GB</div>
            </el-upload>
            <div slot="footer">
                <el-button @click="aircraftDialogVisible = false">取消</el-button>
                <el-button type="primary" :loading="aircraftLoading" :disabled="!hasAircraftShp" @click="uploadAircraftConfirm"> 解析点位 </el-button>
            </div>
        </el-dialog>

        <el-dialog title="超出机巢服务范围的地块" :visible.sync="excludedDialogVisible" width="520px" :modal="false">
            <el-alert
                :title="`共 ${excludedParcelNames.length} 个地块未被 ${parcelRangeKm} km 服务范围完整覆盖`"
                type="warning"
                :closable="false"
                show-icon />
            <el-table :data="excludedParcelRows" size="mini" max-height="420" border style="margin-top: 14px">
                <el-table-column prop="index" label="序号" width="70" />
                <el-table-column prop="name" label="地块名称" show-overflow-tooltip />
            </el-table>
            <div slot="footer">
                <el-button @click="excludedDialogVisible = false">关闭</el-button>
                <el-button type="warning" icon="el-icon-download" @click="downloadExcludedParcels">下载 SHP ZIP</el-button>
            </div>
        </el-dialog>
    </div>
</template>

<script>
import {
    batchDeleteRoutePlansApi,
    deleteKmzfileApi,
    downloadExcludedParcelsApi,
    filterParcelsByRangeApi,
    getDownloadRouteFileApi,
    getRouteMapDetailApi,
    getRouteJobStatusApi,
    getRouteListApi,
    saveMultiAircraftRoutePlanApi,
    upLoadShpApi,
    viewPlanApi
} from '@/api/commonApi';
import MapContainer from '@/components/routeMap.vue';
import { normalizeLatLngList } from '@/utils/utils';
import L from 'leaflet';

const ROUTE_COLORS = ['#ff4d4f', '#40a9ff', '#73d13d', '#9254de', '#faad14', '#13c2c2', '#eb2f96', '#a0d911'];
const PARCEL_RANGE_KM = 6;
const AUTO_FLIGHT_SPEED_MPS = 15;
const MAX_FLIGHT_MINUTES = 20;

export default {
    name: 'algorithmPlanning',
    components: { MapContainer },
    data() {
        return {
            ruleForm: {
                planname: '',
                cameraSize: '24',
                takeOffSecurityHeight: 115,
                parcelName: '',
                aircraftName: ''
            },
            rules: {
                planname: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
                cameraSize: [{ required: true, message: '请选择相机型号', trigger: 'change' }],
                takeOffSecurityHeight: [
                    { required: true, message: '请输入攀升/巡飞高度' },
                    { type: 'number', min: 1, message: '攀升/巡飞高度必须大于 0' }
                ],
                parcelName: [{ required: true, message: '请上传地块 ZIP 数据包', trigger: 'change' }],
                aircraftName: [{ required: true, message: '请上传机巢点位 SHP 文件', trigger: 'change' }]
            },
            parcelDialogVisible: false,
            aircraftDialogVisible: false,
            parcelFileList: [],
            aircraftFileList: [],
            parcelZip: null,
            aircraftLoading: false,
            parcelLoading: false,
            fullGeojson: null,
            geojson: null,
            excludedGeojson: null,
            aircraft: [],
            datasetSummary: null,
            excludedParcelNames: [],
            excludedJobId: '',
            excludedDialogVisible: false,
            parcelFilterReady: false,
            planResultRoutes: [],
            lastPlanResult: null,
            resultViewSource: 'none',
            displayedTaskName: '',
            historyOverviewRequestId: 0,
            resultCaptureType: 'overview',
            historyCaptureType: 'overview',
            parcelRangeKm: PARCEL_RANGE_KM,
            previewLayers: [],
            resultLayers: [],
            historyHighlightLayers: [],
            tableData: [],
            historyRoutes: [],
            tablePage: {
                page: 1,
                limit: 10,
                dataCount: 0
            },
            selectedHistoryTask: '',
            selectedHistoryAircraft: '',
            selectedHistoryRouteId: null,
            activeSidebarTab: 'config',
            clickRowId: '',
            pollTimer: null,
            sidebarWidth: 400,
            sidebarResizeStartX: 0,
            sidebarResizeStartWidth: 400,
            processing: {
                active: false,
                title: '',
                message: '',
                progress: 0,
                status: null
            }
        };
    },
    computed: {
        hasAircraftShp() {
            return this.aircraftFileList.some((file) => file.name.toLowerCase().endsWith('.shp'));
        },
        excludedParcelRows() {
            return this.excludedParcelNames.map((name, index) => ({
                index: index + 1,
                name
            }));
        },
        resultAircraftCount() {
            return new Set(this.visiblePlanResultRoutes.map((route) => route.aircraftName || route.aircraftIndex)).size;
        },
        resultTotalDistance() {
            return this.visiblePlanResultRoutes.reduce((total, route) => total + Number(route.distanceKm || 0), 0).toFixed(2);
        },
        visiblePlanResultRoutes() {
            return this.planResultRoutes.filter((route) => (route.captureType || 'overview') === this.resultCaptureType);
        },
        displayedResultTitle() {
            return this.displayedTaskName ? `${this.displayedTaskName} 航线` : '规划航线';
        },
        resultRouteTableHeight() {
            return Math.max(260, Math.min(430, Math.round(window.innerHeight * 0.38)));
        },
        parsedHistoryRoutes() {
            return this.historyRoutes.map((route) => ({
                ...route,
                ...this.parseHistoryRouteName(route.name)
            }));
        },
        historyTaskOptions() {
            const tasks = new Map();
            this.parsedHistoryRoutes.forEach((route) => {
                if (!tasks.has(route.taskKey)) {
                    tasks.set(route.taskKey, {
                        key: route.taskKey,
                        name: route.taskName,
                        planGeneratedAt: route.planGeneratedAt,
                        routeCount: 0
                    });
                }
                tasks.get(route.taskKey).routeCount += 1;
            });
            return Array.from(tasks.values()).map((task) => ({
                ...task,
                label: `${task.name}${task.planGeneratedAt ? `（${task.planGeneratedAt}）` : ''}（${task.routeCount} 条）`
            }));
        },
        selectedTaskRoutes() {
            return this.parsedHistoryRoutes.filter(
                (route) => route.taskKey === this.selectedHistoryTask && (route.captureType || 'overview') === this.historyCaptureType
            );
        },
        allSelectedTaskRoutes() {
            return this.parsedHistoryRoutes.filter((route) => route.taskKey === this.selectedHistoryTask);
        },
        selectedTaskAircraft() {
            const aircraftMap = new Map();
            this.selectedTaskRoutes.forEach((route) => {
                if (!aircraftMap.has(route.aircraftName)) {
                    aircraftMap.set(route.aircraftName, {
                        name: route.aircraftName,
                        routes: []
                    });
                }
                aircraftMap.get(route.aircraftName).routes.push(route);
            });
            return Array.from(aircraftMap.values()).map((item) => ({
                ...item,
                routes: item.routes.sort((left, right) => right.sortieIndex - left.sortieIndex)
            }));
        },
        selectedAircraftRoutes() {
            const aircraft = this.selectedTaskAircraft.find((item) => item.name === this.selectedHistoryAircraft);
            return aircraft ? aircraft.routes : [];
        }
    },
    methods: {
        setLayerCollectionVisible(layers, visible) {
            const map = this.$refs.mapRef && this.$refs.mapRef.getMapInstance();
            if (!map) return;
            (layers || []).forEach((layer) => {
                if (!layer) return;
                if (visible && !map.hasLayer(layer)) {
                    layer.addTo(map);
                } else if (!visible && map.hasLayer(layer)) {
                    map.removeLayer(layer);
                }
            });
        },
        syncMapLayersForActiveTab() {
            const showConfig = this.activeSidebarTab === 'config';
            this.setLayerCollectionVisible(this.previewLayers, showConfig);
            this.setLayerCollectionVisible(this.resultLayers, !showConfig && this.resultViewSource === 'latest');
            this.setLayerCollectionVisible(this.historyHighlightLayers, !showConfig && this.resultViewSource === 'history');
        },
        switchSidebarTab(tab) {
            this.activeSidebarTab = tab;
            this.$nextTick(() => this.syncMapLayersForActiveTab());
        },
        startSidebarResize(event) {
            this.sidebarResizeStartX = event.clientX;
            this.sidebarResizeStartWidth = this.sidebarWidth;
            document.body.classList.add('route-sidebar-resizing');
            window.addEventListener('mousemove', this.handleSidebarResize);
            window.addEventListener('mouseup', this.stopSidebarResize);
        },
        handleSidebarResize(event) {
            const availableMax = Math.max(420, Math.min(960, window.innerWidth - 360));
            const nextWidth = this.sidebarResizeStartWidth + event.clientX - this.sidebarResizeStartX;
            this.sidebarWidth = Math.min(availableMax, Math.max(420, nextWidth));
        },
        stopSidebarResize() {
            window.removeEventListener('mousemove', this.handleSidebarResize);
            window.removeEventListener('mouseup', this.stopSidebarResize);
            document.body.classList.remove('route-sidebar-resizing');
            localStorage.setItem('routePlanningSidebarWidth', String(this.sidebarWidth));
            this.$nextTick(() => {
                const map = this.$refs.mapRef && this.$refs.mapRef.getMapInstance();
                if (map && map.invalidateSize) map.invalidateSize();
            });
        },
        openParcelDialog() {
            this.parcelDialogVisible = true;
        },
        openAircraftDialog() {
            this.aircraftDialogVisible = true;
        },
        handleParcelChange(file, fileList) {
            if (file.size / 1024 / 1024 / 1024 > 1) {
                this.$message.warning(`${file.name} 文件超出 1GB，不支持上传`);
                this.parcelFileList = [];
                this.parcelZip = null;
                return;
            }
            if (!file.name.toLowerCase().endsWith('.zip')) {
                this.$message.warning('请选择 ZIP 格式的地块数据包');
                this.parcelFileList = [];
                this.parcelZip = null;
                return;
            }
            this.parcelFileList = fileList.slice(-1);
            this.parcelZip = file;
        },
        handleParcelRemove() {
            this.parcelFileList = [];
            this.parcelZip = null;
        },
        handleAircraftChange(file, fileList) {
            const totalSize = fileList.reduce((sum, item) => sum + (item.size || 0), 0);
            if (totalSize / 1024 / 1024 / 1024 > 1) {
                this.$message.warning('文件总大小超出 1GB，不支持上传');
                this.aircraftFileList = fileList.filter((item) => item.uid !== file.uid);
                return;
            }
            this.aircraftFileList = fileList;
        },
        handleAircraftRemove(file, fileList) {
            this.aircraftFileList = fileList;
        },
        async uploadParcelConfirm() {
            if (!this.parcelZip) return;
            const formData = new FormData();
            formData.append('files', this.parcelZip.raw);
            formData.append('uploadType', 'multi-aircraft-parcel');
            this.parcelLoading = true;
            try {
                const res = await upLoadShpApi(formData);
                if (res.code !== 0) {
                    this.$message.error(res.msg || '地块数据包解析失败');
                    return;
                }
                this.fullGeojson = res.data.geojson;
                this.geojson = res.data.geojson;
                this.excludedGeojson = null;
                this.excludedParcelNames = [];
                this.excludedJobId = '';
                this.parcelFilterReady = false;
                this.ruleForm.parcelName = this.parcelZip.name;
                this.updateDatasetSummary({
                    ...res.data.summary,
                    excludedParcelCount: 0,
                    totalParcelCount: res.data.summary.parcelCount
                });
                this.parcelDialogVisible = false;
                if (this.aircraft.length) {
                    this.renderDatasetPreview();
                    await this.applyParcelRangeFilter();
                } else {
                    this.renderDatasetPreview();
                    this.$message.success(`识别到 ${res.data.summary.parcelCount} 个地块`);
                }
                this.$nextTick(() => this.$refs.ruleForm.validateField('parcelName'));
            } catch (error) {
                this.$message.error('地块数据包上传或解析失败');
            } finally {
                this.parcelLoading = false;
            }
        },
        async uploadAircraftConfirm() {
            if (!this.hasAircraftShp) return;
            const formData = new FormData();
            this.aircraftFileList.forEach((file) => {
                formData.append('files', file.raw);
            });
            formData.append('uploadType', 'multi-aircraft-aircraft');
            this.aircraftLoading = true;
            try {
                const res = await upLoadShpApi(formData);
                if (res.code !== 0) {
                    this.$message.error(res.msg || '机巢点位解析失败');
                    return;
                }
                this.aircraft = res.data.aircraft || [];
                this.parcelFilterReady = false;
                const shpFile = this.aircraftFileList.find((file) => file.name.toLowerCase().endsWith('.shp'));
                this.ruleForm.aircraftName = shpFile ? shpFile.name : '机巢点位';
                this.aircraftDialogVisible = false;
                this.updateDatasetSummary(res.data.summary);
                this.renderDatasetPreview();
                if (this.fullGeojson) {
                    await this.applyParcelRangeFilter();
                } else {
                    this.$message.success(`识别到 ${res.data.summary.aircraftCount} 个机巢`);
                }
                this.$nextTick(() => this.$refs.ruleForm.validateField('aircraftName'));
            } catch (error) {
                this.$message.error('机巢点位上传或解析失败');
            } finally {
                this.aircraftLoading = false;
            }
        },
        updateDatasetSummary(summary = {}) {
            this.datasetSummary = {
                totalParcelCount:
                    summary.totalParcelCount != null
                        ? summary.totalParcelCount
                        : (this.datasetSummary && this.datasetSummary.totalParcelCount) || summary.parcelCount || 0,
                parcelCount: summary.parcelCount != null ? summary.parcelCount : (this.datasetSummary && this.datasetSummary.parcelCount) || 0,
                excludedParcelCount:
                    summary.excludedParcelCount != null
                        ? summary.excludedParcelCount
                        : (this.datasetSummary && this.datasetSummary.excludedParcelCount) || 0,
                aircraftCount:
                    summary.aircraftCount != null
                        ? summary.aircraftCount
                        : (this.datasetSummary && this.datasetSummary.aircraftCount) || this.aircraft.length || 0,
                rangeKm: summary.rangeKm || PARCEL_RANGE_KM
            };
        },
        async applyParcelRangeFilter() {
            if (!this.fullGeojson || !this.aircraft.length) return;
            this.parcelFilterReady = false;
            try {
                const res = await filterParcelsByRangeApi({
                    geojson: this.fullGeojson,
                    aircraft: this.aircraft,
                    radiusKm: PARCEL_RANGE_KM
                });
                if (res.code !== 0) {
                    this.$message.error(res.msg || '地块范围筛选失败');
                    return;
                }
                const result = await this.pollJob(res.data.jobId, '地块范围筛选');
                this.geojson = result.geojson;
                this.excludedGeojson = result.excludedGeojson || null;
                this.excludedParcelNames = result.excludedParcelNames || [];
                this.excludedJobId = result.excludedDownloadAvailable ? res.data.jobId : '';
                this.updateDatasetSummary(result.summary);
                this.renderDatasetPreview();
                this.parcelFilterReady = true;
                const { parcelCount, excludedParcelCount, totalParcelCount } = result.summary;
                this.$message.success(
                    `${PARCEL_RANGE_KM} km 筛选完成：保留 ${parcelCount}/${totalParcelCount} 个地块，剔除 ${excludedParcelCount} 个`
                );
            } catch (error) {
                this.parcelFilterReady = false;
                this.$message.error(error.message || '地块范围筛选失败');
            }
        },
        async pollJob(jobId, title) {
            this.stopPolling();
            this.processing = {
                active: true,
                title,
                message: '任务已提交',
                progress: 0,
                status: null
            };
            return new Promise((resolve, reject) => {
                const poll = async () => {
                    try {
                        const response = await getRouteJobStatusApi(jobId);
                        if (response.code !== 0) {
                            throw new Error(response.msg || '任务状态查询失败');
                        }
                        const job = response.data;
                        this.processing.progress = Number(job.progress || 0);
                        this.processing.message = job.message || '';
                        if (job.status === 'completed') {
                            this.processing.active = false;
                            this.processing.status = 'success';
                            this.pollTimer = null;
                            resolve(job.result || {});
                            return;
                        }
                        if (job.status === 'failed') {
                            throw new Error(job.message || '后台任务执行失败');
                        }
                        this.pollTimer = setTimeout(poll, 500);
                    } catch (error) {
                        this.processing.active = false;
                        this.processing.status = 'exception';
                        this.processing.message = error.message || '后台任务失败';
                        this.pollTimer = null;
                        reject(error);
                    }
                };
                poll();
            });
        },
        stopPolling() {
            if (this.pollTimer) {
                clearTimeout(this.pollTimer);
                this.pollTimer = null;
            }
        },
        renderDatasetPreview() {
            this.clearLayers(this.previewLayers);
            const bounds = [];
            const features = (this.geojson && this.geojson.features) || [];
            features.forEach((feature) => {
                this.geometryToLeafletPolygons(feature.geometry).forEach((polygon) => {
                    const layer = this.$refs.mapRef.addPolygon(polygon, {
                        color: '#49b8ff',
                        fillColor: '#49b8ff',
                        fillOpacity: 0.18,
                        weight: 2
                    });
                    this.previewLayers.push(layer);
                    bounds.push(...polygon);
                });
            });
            const excludedFeatures = (this.excludedGeojson && this.excludedGeojson.features) || [];
            excludedFeatures.forEach((feature) => {
                this.geometryToLeafletPolygons(feature.geometry).forEach((polygon) => {
                    const layer = this.$refs.mapRef.addPolygon(polygon, {
                        color: '#ff4d4f',
                        fillColor: '#ff4d4f',
                        fillOpacity: 0.28,
                        weight: 2
                    });
                    const name = this.getParcelFeatureName(feature);
                    layer.bindPopup(`${name}<br><span style="color:#ff4d4f">超出机巢服务范围</span>`);
                    this.previewLayers.push(layer);
                    bounds.push(...polygon);
                });
            });
            this.aircraft.forEach((item, index) => {
                const latLng = [item.latitude, item.longitude];
                const marker = this.$refs.mapRef.addStartPoint(latLng);
                marker.bindPopup(`${item.name || `飞机${index + 1}`}<br>固定起降点`);
                this.previewLayers.push(marker);
                bounds.push(latLng);
            });
            if (bounds.length) {
                this.$refs.mapRef.getMapInstance().fitBounds(bounds, { padding: [30, 30] });
            }
            this.syncMapLayersForActiveTab();
        },
        geometryToLeafletPolygons(geometry) {
            if (!geometry || !geometry.coordinates) return [];
            const toLatLng = (coord) => [coord[1], coord[0]];
            if (geometry.type === 'Polygon') {
                return [geometry.coordinates[0].map(toLatLng)];
            }
            if (geometry.type === 'MultiPolygon') {
                return geometry.coordinates.map((polygon) => polygon[0].map(toLatLng));
            }
            return [];
        },
        getParcelFeatureName(feature) {
            const properties = (feature && feature.properties) || {};
            const keys = ['name', 'NAME', '地块名称', '项目名称', 'project_name', 'parcel_name', 'DKMC', 'BSM', 'id', 'ID'];
            const key = keys.find((item) => properties[item] != null && String(properties[item]).trim());
            return key ? String(properties[key]) : '超范围地块';
        },
        submitForm() {
            if (!this.parcelFilterReady) {
                this.$message.warning('请等待地块范围筛选完成');
                return;
            }
            this.$refs.ruleForm.validate((valid) => {
                if (valid) this.savePlan();
            });
        },
        async savePlan() {
            try {
                const payload = {
                    name: this.ruleForm.planname,
                    cameraSize: this.ruleForm.cameraSize,
                    takeOffSecurityHeight: this.ruleForm.takeOffSecurityHeight,
                    autoFlightSpeed: AUTO_FLIGHT_SPEED_MPS,
                    maxFlightMinutes: MAX_FLIGHT_MINUTES,
                    polygon: this.geojson,
                    aircraft: this.aircraft,
                    rangeKm: PARCEL_RANGE_KM,
                    alreadyFiltered: true
                };
                const res = await saveMultiAircraftRoutePlanApi(payload);
                if (res.code !== 0) {
                    this.$message.error(res.msg || '航线规划失败');
                    return;
                }
                const result = await this.pollJob(res.data.jobId, '多机巢、多航线规划');
                this.planResultRoutes = (result.routes || []).map((route) => ({
                    ...route,
                    aircraftName: route.aircraftName || `飞机${route.aircraftIndex}`
                }));
                this.lastPlanResult = result;
                this.resultViewSource = 'latest';
                this.displayedTaskName = this.ruleForm.planname;
                this.resultCaptureType = 'overview';
                this.historyCaptureType = 'overview';
                this.switchSidebarTab('result');
                this.renderPlanResult(result);
                await this.handelGetKmzFile(true);
                this.selectedHistoryTask = result.planGeneratedAt ? `${this.ruleForm.planname}|${result.planGeneratedAt}` : this.ruleForm.planname;
                this.selectedHistoryAircraft = this.selectedTaskAircraft.length ? this.selectedTaskAircraft[0].name : '';
                const excludedTargetText = result.excludedTargetPointCount
                    ? `，${result.excludedTargetPointCount} 个网格点因超过 ${result.maxDistanceKm || 18}km 往返约束未参与规划`
                    : '';
                this.$message.success(
                    `规划完成：${result.usedAircraftCount}/${result.aircraftCount} 个机巢，` +
                        `${result.totalSorties} 条航线，预计 ${result.estimatedCompletionMinutes} 分钟完成${excludedTargetText}`
                );
            } catch (error) {
                this.$message.error(error.message || '航线规划请求失败');
            }
        },
        async downloadExcludedParcels() {
            if (!this.excludedJobId) {
                this.$message.warning('当前没有可下载的超范围地块');
                return;
            }
            try {
                const blob = await downloadExcludedParcelsApi(this.excludedJobId);
                const url = window.URL.createObjectURL(new Blob([blob]));
                const link = document.createElement('a');
                link.href = url;
                link.download = '超出机巢服务范围地块.zip';
                document.body.appendChild(link);
                link.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                this.$message.error('超范围地块下载失败');
            }
        },
        renderPlanResult(data) {
            this.clearLayers(this.historyHighlightLayers);
            this.selectedHistoryRouteId = null;
            this.clearLayers(this.resultLayers);
            const bounds = [];
            (data.routes || [])
                .filter((route) => (route.captureType || 'overview') === this.resultCaptureType)
                .forEach((route) => {
                    const latLngs = normalizeLatLngList(route.points || []);
                    if (!latLngs.length) return;
                    const color = ROUTE_COLORS[(route.aircraftIndex - 1) % ROUTE_COLORS.length];
                    const aircraftName = route.aircraftName || `飞机${route.aircraftIndex}`;
                    const line = this.$refs.mapRef.addPolyline(latLngs, {
                        color,
                        weight: 4,
                        opacity: 0.85
                    });
                    line.bindPopup(
                        `归属：${aircraftName}<br>` +
                            `第 ${route.sortieIndex} 条航线<br>` +
                            `里程 ${route.distanceKm} km<br>飞行 ${route.flightTimeMinutes} min`
                    );
                    this.resultLayers.push(line);
                    this.addPhotoPointMarkers(latLngs, color, this.resultLayers, {
                        popupPrefix: `${aircraftName} 第 ${route.sortieIndex} 条${
                            route.captureType === 'panorama' ? '全景航线全景点' : '俯视航线拍照点'
                        }`
                    });
                    bounds.push(...latLngs);
                });
            if (bounds.length) {
                this.$refs.mapRef.getMapInstance().fitBounds(bounds, { padding: [30, 30] });
            }
            this.syncMapLayersForActiveTab();
        },
        handleResultCaptureTypeChange() {
            if (this.resultViewSource === 'history') {
                this.historyCaptureType = this.resultCaptureType;
                this.selectedHistoryAircraft = this.selectedTaskAircraft.length ? this.selectedTaskAircraft[0].name : '';
                this.renderHistoryTaskOverview();
            } else if (this.lastPlanResult) {
                this.renderPlanResult(this.lastPlanResult);
            }
        },
        waitForMapReady(timeoutMs = 5000) {
            const startedAt = Date.now();
            return new Promise((resolve) => {
                const check = () => {
                    const map = this.$refs.mapRef && this.$refs.mapRef.getMapInstance();
                    if (map) {
                        resolve(map);
                    } else if (Date.now() - startedAt >= timeoutMs) {
                        resolve(null);
                    } else {
                        window.setTimeout(check, 50);
                    }
                };
                check();
            });
        },
        async renderHistoryTaskOverview() {
            const requestId = ++this.historyOverviewRequestId;
            const routes = this.selectedTaskRoutes.slice();
            this.selectedHistoryRouteId = null;
            this.clearLayers(this.resultLayers);
            this.clearLayers(this.historyHighlightLayers);
            this.syncMapLayersForActiveTab();
            if (!routes.length) return;
            try {
                const responses = await Promise.all(
                    routes.map(async (route) => {
                        try {
                            const response = await getRouteMapDetailApi(route.fileId);
                            return response.code === 0 ? { route, detail: response.data || {} } : null;
                        } catch (error) {
                            console.error('历史任务航线加载失败', route.fileId, error);
                            return null;
                        }
                    })
                );
                if (requestId !== this.historyOverviewRequestId) return;
                const map = await this.waitForMapReady();
                if (!map || requestId !== this.historyOverviewRequestId) return;
                const routeDetails = responses.filter(Boolean);
                const bounds = [];
                const polygonMap = new Map();
                routeDetails.forEach(({ detail }) => {
                    (detail.targetPolygons || []).forEach((item) => {
                        const feature = item.feature || {};
                        const geometry = feature.geometry || feature;
                        const key = item.id != null ? String(item.id) : JSON.stringify(geometry);
                        if (!polygonMap.has(key)) polygonMap.set(key, item);
                    });
                });
                polygonMap.forEach((item) => {
                    const feature = item.feature || {};
                    const geometry = feature.geometry || feature;
                    this.geometryToLeafletPolygons(geometry).forEach((polygon) => {
                        if (!polygon.length) return;
                        const polygonLayer = this.$refs.mapRef.addPolygon(polygon, {
                            color: '#39d98a',
                            fillColor: '#52e39b',
                            fillOpacity: 0.24,
                            weight: 2.5
                        });
                        polygonLayer.bindPopup(`目标地块 #${item.id || '-'}<br>当前任务覆盖区域`);
                        this.historyHighlightLayers.push(polygonLayer);
                        bounds.push(...polygon);
                    });
                });
                const renderedStarts = new Set();
                routeDetails.forEach(({ route, detail }) => {
                    const latLngs = normalizeLatLngList(detail.routePoints || []);
                    if (!latLngs.length) return;
                    const colorIndex = Math.max(
                        0,
                        this.selectedTaskAircraft.findIndex((item) => item.name === route.aircraftName)
                    );
                    const color = ROUTE_COLORS[colorIndex % ROUTE_COLORS.length];
                    const line = this.$refs.mapRef.addPolyline(latLngs, {
                        color,
                        weight: 4,
                        opacity: 0.88
                    });
                    line.bindPopup(
                        `任务：${route.taskName}<br>` +
                            `类型：${route.captureType === 'panorama' ? '全景图航线' : '俯视图航线'}<br>` +
                            `飞机：${route.aircraftName}<br>` +
                            `航线：${route.sortieIndex || '-'}`
                    );
                    this.historyHighlightLayers.push(line);
                    this.addPhotoPointMarkers(latLngs, color, this.historyHighlightLayers, {
                        radius: 4,
                        popupPrefix: `${route.aircraftName} 航线 ${route.sortieIndex || '-'} ${
                            route.captureType === 'panorama' ? '全景点' : '俯拍点'
                        }`
                    });
                    bounds.push(...latLngs);
                    const startPoint = detail.startPoint || [];
                    const startKey = startPoint.length >= 2 ? `${startPoint[0]},${startPoint[1]}` : '';
                    if (startKey && !renderedStarts.has(startKey)) {
                        renderedStarts.add(startKey);
                        const startLatLng = [Number(startPoint[1]), Number(startPoint[0])];
                        const marker = this.$refs.mapRef.addStartPoint(startLatLng);
                        marker.bindPopup(`${route.aircraftName} 起降点`);
                        this.historyHighlightLayers.push(marker);
                        bounds.push(startLatLng);
                    }
                });
                if (bounds.length) {
                    this.$refs.mapRef.getMapInstance().fitBounds(bounds, { padding: [45, 45] });
                }
                this.syncMapLayersForActiveTab();
            } catch (error) {
                console.error('历史任务地图绘制失败', error);
                this.$message.error('历史任务地图加载失败');
            }
        },
        addPhotoPointMarkers(latLngs, color, targetLayers, options = {}) {
            const map = this.$refs.mapRef && this.$refs.mapRef.getMapInstance();
            if (!map || !Array.isArray(latLngs) || latLngs.length <= 2) return;
            latLngs.slice(1, -1).forEach((latLng, index) => {
                const marker = L.circleMarker(latLng, {
                    radius: options.radius || 5,
                    color,
                    weight: options.weight || 2,
                    fillColor: '#06152d',
                    fillOpacity: 0.85,
                    opacity: 1,
                    pane: 'markerPane',
                    interactive: true
                });
                marker.addTo(map);
                marker.bindPopup(`${options.popupPrefix || '拍照点'} #${index + 1}`);
                targetLayers.push(marker);
            });
        },
        clearLayers(layers) {
            layers.forEach((layer) => this.$refs.mapRef && this.$refs.mapRef.removeLayer(layer));
            layers.splice(0, layers.length);
        },
        resetForm() {
            this.stopPolling();
            this.$refs.ruleForm.resetFields();
            this.ruleForm.takeOffSecurityHeight = 115;
            this.parcelFileList = [];
            this.aircraftFileList = [];
            this.parcelZip = null;
            this.fullGeojson = null;
            this.geojson = null;
            this.excludedGeojson = null;
            this.aircraft = [];
            this.datasetSummary = null;
            this.excludedParcelNames = [];
            this.excludedJobId = '';
            this.parcelFilterReady = false;
            this.planResultRoutes = [];
            this.lastPlanResult = null;
            this.resultViewSource = 'none';
            this.displayedTaskName = '';
            this.historyOverviewRequestId += 1;
            this.resultCaptureType = 'overview';
            this.historyCaptureType = 'overview';
            this.activeSidebarTab = 'config';
            this.processing = {
                active: false,
                title: '',
                message: '',
                progress: 0,
                status: null
            };
            this.clearLayers(this.previewLayers);
            this.clearLayers(this.resultLayers);
            this.clearLayers(this.historyHighlightLayers);
        },
        formatCoordinate(row) {
            return `${Number(row.longitude).toFixed(5)}, ${Number(row.latitude).toFixed(5)}`;
        },
        formatDistance(value) {
            const number = Number(value);
            return Number.isFinite(number) ? number.toFixed(3).replace(/\.?0+$/, '') : '-';
        },
        parseHistoryRouteName(name) {
            const value = String(name || '').trim();
            const newMatched = value.match(/^(.*)-(\d{12})-([^-]+)-航线(\d+)$/);
            if (newMatched) {
                return {
                    taskName: newMatched[1],
                    taskKey: `${newMatched[1]}|${newMatched[2]}`,
                    planGeneratedAt: newMatched[2],
                    aircraftName: newMatched[3],
                    sortieIndex: Number(newMatched[4]),
                    displayName: `航线 ${newMatched[4]}`
                };
            }
            const legacyMatched = value.match(/^(.*)-([^-]+)-架次(\d+)$/);
            if (!legacyMatched) {
                return {
                    taskName: value || '未命名任务',
                    taskKey: value || '未命名任务',
                    planGeneratedAt: '',
                    aircraftName: '未分组飞机',
                    sortieIndex: 0,
                    displayName: '航线'
                };
            }
            return {
                taskName: legacyMatched[1],
                taskKey: legacyMatched[1],
                planGeneratedAt: '',
                aircraftName: legacyMatched[2],
                sortieIndex: Number(legacyMatched[3]),
                displayName: `航线 ${legacyMatched[3]}`
            };
        },
        async handleHistoryTaskChange() {
            const task = this.historyTaskOptions.find((item) => item.key === this.selectedHistoryTask);
            this.resultViewSource = 'history';
            this.displayedTaskName = task ? task.name : '';
            this.resultCaptureType = this.historyCaptureType;
            this.lastPlanResult = null;
            this.planResultRoutes = this.allSelectedTaskRoutes.slice();
            this.selectedHistoryAircraft = this.selectedTaskAircraft.length ? this.selectedTaskAircraft[0].name : '';
            this.selectedHistoryRouteId = null;
            await this.renderHistoryTaskOverview();
        },
        async handleHistoryCaptureTypeChange() {
            this.resultCaptureType = this.historyCaptureType;
            this.selectedHistoryAircraft = this.selectedTaskAircraft.length ? this.selectedTaskAircraft[0].name : '';
            this.selectedHistoryRouteId = null;
            await this.renderHistoryTaskOverview();
        },
        handleHistoryAircraftSelect(aircraftName) {
            this.selectedHistoryAircraft = aircraftName;
            this.selectedHistoryRouteId = null;
        },
        selectedHistoryTaskLabel() {
            const task = this.historyTaskOptions.find((item) => item.key === this.selectedHistoryTask);
            return task ? task.label.replace(/（\d+ 条）$/, '') : this.selectedHistoryTask;
        },
        handleDeleteHistoryTask() {
            const routes = this.allSelectedTaskRoutes;
            if (!routes.length) return;
            this.batchDeleteHistoryRoutes(
                routes,
                `确认删除任务“${this.selectedHistoryTaskLabel()}”及其全部 ${routes.length} 条航线吗？`,
                '任务删除后，其监管任务和目标地块数据也将一并删除。'
            );
        },
        handleDeleteHistoryAircraft() {
            const routes = this.selectedAircraftRoutes;
            if (!routes.length) return;
            this.batchDeleteHistoryRoutes(
                routes,
                `确认删除“${this.selectedHistoryAircraft}”的全部 ${routes.length} 条航线吗？`,
                '同一任务下其他飞机的航线数据不会受到影响。'
            );
        },
        batchDeleteHistoryRoutes(routes, message, detail) {
            const fileIds = routes.map((route) => route.fileId);
            this.$confirm(`${message}<br><span class="batch-delete-tip">${detail}</span>`, '批量删除确认', {
                confirmButtonText: '确认删除',
                cancelButtonText: '取消',
                type: 'warning',
                dangerouslyUseHTMLString: true
            })
                .then(async () => {
                    const res = await batchDeleteRoutePlansApi(fileIds);
                    if (res.code !== 0) {
                        this.$message.error(res.msg || '批量删除失败');
                        return;
                    }
                    this.selectedHistoryRouteId = null;
                    this.clearLayers(this.historyHighlightLayers);
                    this.clearLayers(this.resultLayers);
                    await this.handelGetKmzFile();
                    this.$message.success(`已删除 ${res.data.deletedRouteCount} 条航线`);
                })
                .catch(() => {});
        },
        async handleHistoryRouteSelect(route) {
            try {
                this.historyOverviewRequestId += 1;
                const res = await getRouteMapDetailApi(route.fileId);
                if (res.code !== 0) {
                    this.$message.error(res.msg || '航线加载失败');
                    return;
                }
                const detail = res.data || {};
                const latLngs = normalizeLatLngList(detail.routePoints || []);
                if (!latLngs.length) {
                    this.$message.warning('该航线没有可展示的坐标');
                    return;
                }
                this.clearLayers(this.resultLayers);
                this.clearLayers(this.historyHighlightLayers);
                this.syncMapLayersForActiveTab();
                const displayBounds = latLngs.slice();
                const line = this.$refs.mapRef.addPolyline(latLngs, {
                    color: '#ff9f1c',
                    weight: 6,
                    opacity: 0.95
                });
                line.bindPopup(
                    `任务：${route.taskName}<br>` +
                        `类型：${detail.captureType === 'panorama' ? '全景图航线' : '俯视图航线'}<br>` +
                        `飞机：${route.aircraftName}<br>` +
                        `航线：${route.sortieIndex || '-'}<br>` +
                        `目标地块：${(detail.targetPolygons || []).length} 个`
                );
                this.historyHighlightLayers.push(line);
                this.addPhotoPointMarkers(latLngs, '#ff9f1c', this.historyHighlightLayers, {
                    radius: 6,
                    weight: 2.5,
                    popupPrefix: `${route.aircraftName} 航线 ${route.sortieIndex || '-'} ${detail.captureType === 'panorama' ? '全景点' : '俯拍点'}`
                });

                const startPoint = detail.startPoint || [];
                if (startPoint.length >= 2) {
                    const startLatLng = [Number(startPoint[1]), Number(startPoint[0])];
                    const marker = this.$refs.mapRef.addStartPoint(startLatLng);
                    marker.bindPopup(`${route.aircraftName} 起降点`);
                    this.historyHighlightLayers.push(marker);
                    displayBounds.push(startLatLng);
                }

                let renderedPolygonCount = 0;
                (detail.targetPolygons || []).forEach((item) => {
                    const feature = item.feature || {};
                    const geometry = feature.geometry || feature;
                    this.geometryToLeafletPolygons(geometry).forEach((polygon) => {
                        if (!polygon.length) return;
                        const polygonLayer = this.$refs.mapRef.addPolygon(polygon, {
                            color: '#39d98a',
                            fillColor: '#52e39b',
                            fillOpacity: 0.3,
                            weight: 3
                        });
                        polygonLayer.bindPopup(
                            `目标地块 #${item.id}<br>` +
                                `关联飞机：${item.aircraftName || route.aircraftName}<br>` +
                                `关联航线：${item.sortieIndex || route.sortieIndex || '-'}<br>` +
                                `覆盖拍照点：${item.coveredPhotoPointCount || 0} 个`
                        );
                        this.historyHighlightLayers.push(polygonLayer);
                        displayBounds.push(...polygon);
                        renderedPolygonCount += 1;
                    });
                });
                this.selectedHistoryRouteId = route.id;
                this.$refs.mapRef.getMapInstance().fitBounds(displayBounds, { padding: [45, 45] });
                this.syncMapLayersForActiveTab();
                if (!renderedPolygonCount) {
                    this.$message.warning('该航线未匹配到目标地块，仅显示航线和机巢起降点');
                }
            } catch (error) {
                console.error('历史航线地图绘制失败', error);
                this.$message.error('航线加载失败');
            }
        },
        async handelGetKmzFile(keepDisplayedResult = false) {
            const res = await getRouteListApi({
                pageIndex: 1,
                pageSize: 10000,
                routeType: '算法规划,算法规划-多机多架次,算法规划-多机巢多架次,算法规划-多机巢多航线,算法规划-全景图-多机巢多航线',
                orderType: 1,
                orderField: 'createDate'
            });
            if (res.code === 0) {
                this.historyRoutes = res.data || [];
                this.tableData = this.historyRoutes.slice(0, this.tablePage.limit);
                this.tablePage.dataCount = res.total;
                const taskExists = this.historyTaskOptions.some((task) => task.key === this.selectedHistoryTask);
                if (!taskExists) {
                    this.selectedHistoryTask = this.historyTaskOptions.length ? this.historyTaskOptions[0].key : '';
                }
                const aircraftExists = this.selectedTaskAircraft.some((item) => item.name === this.selectedHistoryAircraft);
                if (!aircraftExists) {
                    this.selectedHistoryAircraft = this.selectedTaskAircraft.length ? this.selectedTaskAircraft[0].name : '';
                }
                if (!keepDisplayedResult && this.selectedHistoryTask) {
                    await this.handleHistoryTaskChange();
                }
            } else {
                this.$message.error(res.msg);
            }
        },
        handleCurrentChange(page) {
            this.tablePage.page = page;
            this.handelGetKmzFile();
        },
        async handleDownload(row) {
            try {
                const response = await getDownloadRouteFileApi(row.fileId);
                const url = window.URL.createObjectURL(new Blob([response]));
                const link = document.createElement('a');
                link.href = url;
                const typeLabel = (row.captureType || 'overview') === 'panorama' ? '全景图' : '俯视图';
                const baseName = row.name.toLowerCase().endsWith('.kmz') ? row.name.slice(0, -4) : row.name;
                link.download = `${baseName}-${typeLabel}.kmz`;
                document.body.appendChild(link);
                link.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                this.$message.error('下载文件时发生错误');
            }
        },
        handleDelete(row) {
            this.$confirm('此操作将永久删除该航线，是否继续？', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteKmzfileApi({ route_id: row.fileId });
                    if (res.code === 0) {
                        this.$message.success('删除成功');
                        if (this.selectedHistoryRouteId === row.id) {
                            this.selectedHistoryRouteId = null;
                            this.clearLayers(this.historyHighlightLayers);
                        }
                        this.handelGetKmzFile();
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch(() => {});
        },
        async handleViewPlan(row) {
            if (this.clickRowId !== row.id) {
                this.tableData.forEach((item) => {
                    if (item !== row) this.$set(item, 'isViewing', false);
                });
            }
            this.clickRowId = row.id;
            this.$set(row, 'isViewing', !row.isViewing);
            this.clearLayers(this.resultLayers);
            if (!row.isViewing) return;
            const res = await viewPlanApi(row.fileId, 'kmz');
            if (res.code === 0) {
                const latLngs = normalizeLatLngList(res.data);
                const line = this.$refs.mapRef.addPolyline(latLngs, { color: '#ff4d4f', weight: 4 });
                this.resultLayers.push(line);
                if (latLngs.length) {
                    this.$refs.mapRef.getMapInstance().fitBounds(latLngs, { padding: [30, 30] });
                }
            } else {
                this.$message.error(res.msg);
            }
        }
    },
    mounted() {
        const savedWidth = Number(localStorage.getItem('routePlanningSidebarWidth'));
        if (Number.isFinite(savedWidth) && savedWidth >= 420 && savedWidth <= 960) {
            this.sidebarWidth = savedWidth;
        }
        this.handelGetKmzFile();
    },
    beforeDestroy() {
        this.stopSidebarResize();
        this.stopPolling();
        this.clearLayers(this.previewLayers);
        this.clearLayers(this.resultLayers);
        this.clearLayers(this.historyHighlightLayers);
    }
};
</script>

<style lang="scss" scoped>
.box {
    @import '@/assets/css/table/route-planning';
}

.box {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: row;
    overflow: hidden;
    background: #06152d;
}

.left {
    position: relative;
    flex: 0 0 auto;
    min-width: 420px;
    max-width: 960px;
    height: 100%;
    min-height: 0;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border-right: 1px solid rgba(55, 166, 255, 0.45);
    background: linear-gradient(180deg, #071a36 0%, #061329 100%);
    box-shadow: 8px 0 20px rgba(0, 0, 0, 0.2);
}

.right {
    position: relative;
    flex: 1;
    min-width: 0;
    height: 100%;
}

.route-layer-switch {
    position: absolute;
    z-index: 900;
    top: 18px;
    right: 18px;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    color: #dff5ff;
    border: 1px solid rgba(73, 184, 255, 0.55);
    border-radius: 6px;
    background: rgba(5, 23, 48, 0.92);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
}

.history-capture-select {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin: 12px 0;
}

.history-capture-select label {
    color: #b8d9ed;
    white-space: nowrap;
}

.sidebar-resizer {
    position: absolute;
    top: 0;
    right: -5px;
    z-index: 1000;
    width: 10px;
    height: 100%;
    cursor: col-resize;
    display: flex;
    align-items: center;
    justify-content: center;
}

.sidebar-resizer span {
    width: 2px;
    height: 64px;
    border-radius: 2px;
    background: rgba(73, 184, 255, 0.55);
    box-shadow: 0 0 6px rgba(73, 184, 255, 0.45);
    transition: width 0.15s, background 0.15s;
}

.sidebar-resizer:hover span {
    width: 4px;
    background: #49b8ff;
}

:global(body.route-sidebar-resizing) {
    cursor: col-resize !important;
    user-select: none;
}

.sidebar-header {
    flex: 0 0 auto;
    padding: 14px 14px 0;
    border-bottom: 1px solid rgba(72, 161, 220, 0.2);
    background: rgba(6, 22, 47, 0.96);
}

.sidebar-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-width: 0;
    margin-bottom: 12px;
}

.sidebar-heading > div {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
    color: #f1f8ff;
    font-size: 17px;
    font-weight: 700;
}

.sidebar-heading i {
    color: #49b8ff;
}

.sidebar-heading small {
    color: #78a9c8;
    font-size: 11px;
    font-weight: 400;
    white-space: nowrap;
}

.sidebar-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
}

.sidebar-tabs button {
    position: relative;
    height: 38px;
    color: #8cb5cf;
    border: 0;
    border-bottom: 2px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: color 0.18s, background 0.18s, border-color 0.18s;
}

.sidebar-tabs button:hover {
    color: #dff5ff;
    background: rgba(73, 184, 255, 0.06);
}

.sidebar-tabs button.active {
    color: #49c8ff;
    border-bottom-color: #29b6f6;
    background: linear-gradient(180deg, transparent, rgba(41, 182, 246, 0.12));
}

.sidebar-tabs button i {
    margin-right: 5px;
}

.sidebar-tabs button em {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 18px;
    height: 18px;
    margin-left: 5px;
    padding: 0 5px;
    color: #fff;
    font-size: 10px;
    font-style: normal;
    border-radius: 9px;
    background: #167bc0;
}

.sidebar-scroll {
    flex: 1 1 auto;
    min-height: 0;
    overflow-x: hidden;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: rgba(73, 184, 255, 0.55) rgba(5, 23, 48, 0.5);
}

.sidebar-scroll::-webkit-scrollbar {
    width: 6px;
}

.sidebar-scroll::-webkit-scrollbar-thumb {
    border-radius: 3px;
    background: rgba(73, 184, 255, 0.5);
}

.sidebar-pane {
    padding: 12px;
}

.sidebar-card {
    margin-bottom: 12px;
    padding: 12px;
    border: 1px solid rgba(58, 137, 190, 0.32);
    border-radius: 6px;
    background: rgba(9, 36, 67, 0.72);
    box-shadow: 0 5px 14px rgba(0, 0, 0, 0.12);
}

.card-title {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 12px;
}

.card-title > span {
    display: flex;
    align-items: center;
    gap: 7px;
    color: #e6f6ff;
    font-size: 14px;
    font-weight: 700;
}

.card-title i {
    color: #49b8ff;
}

.card-title small {
    color: #79a6c2;
    font-size: 11px;
    font-weight: 400;
    white-space: nowrap;
}

.form-grid {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: 0 12px;
}

.wide-field {
    grid-column: 1 / -1;
}

.demo-ruleForm ::v-deep .el-form-item {
    margin-bottom: 12px;
}

.demo-ruleForm ::v-deep .el-form-item:last-child {
    margin-bottom: 2px;
}

::v-deep .el-form-item__label {
    width: auto !important;
    height: auto;
    padding: 0 0 5px !important;
    line-height: 18px !important;
    color: #fff !important;
    font-size: 12px;
}

::v-deep .el-form-item__content {
    width: 100%;
    line-height: normal;
    margin-left: 0 !important;
}

.upload-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-height: 52px;
    padding: 8px 0;
    border-top: 1px solid rgba(99, 153, 188, 0.16);
}

.upload-row:first-of-type {
    border-top: 0;
}

.upload-row > div {
    min-width: 0;
}

.upload-row label,
.upload-row span {
    display: block;
}

.upload-row label {
    margin-bottom: 5px;
    color: #dcedf7;
    font-size: 12px;
}

.upload-row span {
    max-width: 100%;
    overflow: hidden;
    color: #789bb2;
    font-size: 12px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.upload-row span.ready {
    color: #72d5ff;
}

.full-width {
    width: 100%;
}

.dataset-summary {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    color: #d8f3ff;
}

.summary-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    min-width: 0;
    min-height: 64px;
    border: 1px solid rgba(73, 184, 255, 0.2);
    border-radius: 5px;
    background: rgba(9, 53, 87, 0.52);
}

.summary-item strong {
    color: #49b8ff;
    font-size: 20px;
}

.excluded-count {
    color: #ff9f7a !important;
}

.summary-tip {
    margin: 10px 0 0;
    color: #9fc7dc;
    font-size: 12px;
    line-height: 18px;
}

.excluded-actions {
    grid-column: 1 / -1;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px 12px;
}

.excluded-actions ::v-deep .el-button {
    max-width: 100%;
    margin-left: 0;
}

.excluded-actions ::v-deep .el-button--text {
    white-space: normal;
    text-align: left;
    line-height: 18px;
}

.processing-panel {
    color: #d8f3ff;
    border-color: rgba(73, 184, 255, 0.55);
    background: rgba(15, 65, 98, 0.5);
}

.processing-title {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 8px;
    font-size: 12px;
}

.processing-title span:last-child {
    min-width: 0;
    overflow: hidden;
    color: #80cfff;
    text-align: right;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.result-overview {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 8px;
    margin-bottom: 12px;
}

.result-overview > div {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-width: 0;
    min-height: 74px;
    padding: 8px;
    border: 1px solid rgba(73, 184, 255, 0.35);
    border-radius: 6px;
    background: linear-gradient(180deg, rgba(22, 96, 142, 0.48), rgba(8, 42, 75, 0.58));
}

.result-overview span {
    margin-bottom: 7px;
    color: #93bcd4;
    font-size: 11px;
}

.result-overview strong {
    max-width: 100%;
    overflow: hidden;
    color: #50c7ff;
    font-size: 20px;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.result-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 260px;
    margin-bottom: 12px;
    padding: 30px;
    color: #779db6;
    text-align: center;
    border: 1px dashed rgba(73, 184, 255, 0.35);
    border-radius: 6px;
    background: rgba(7, 31, 58, 0.52);
}

.result-empty > i {
    margin-bottom: 14px;
    color: #2d8dc7;
    font-size: 42px;
}

.result-empty strong {
    margin-bottom: 8px;
    color: #d9eef9;
}

.result-empty span {
    margin-bottom: 18px;
    font-size: 12px;
    line-height: 20px;
}

.history-card {
    margin-bottom: 0;
}

.history-task-select {
    display: grid;
    grid-template-columns: 72px minmax(0, 1fr);
    align-items: center;
    gap: 10px;
    margin-bottom: 14px;
}

.history-task-select label {
    color: #a9cada;
    font-size: 12px;
}

.history-task-select ::v-deep .el-select {
    width: 100%;
}

.history-task-control {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 8px;
    min-width: 0;
}

.history-task-control ::v-deep .el-button {
    margin-left: 0;
    white-space: nowrap;
}

.aircraft-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 9px;
    margin-bottom: 15px;
}

.aircraft-history-card {
    display: flex;
    align-items: center;
    min-width: 0;
    min-height: 66px;
    padding: 10px;
    color: #a9c9da;
    text-align: left;
    border: 1px solid rgba(62, 137, 186, 0.35);
    border-radius: 6px;
    background: linear-gradient(145deg, rgba(9, 46, 80, 0.88), rgba(6, 31, 61, 0.92));
    cursor: pointer;
    transition: border-color 0.18s, background 0.18s, transform 0.18s;
}

.aircraft-history-card:hover {
    border-color: rgba(73, 184, 255, 0.72);
    transform: translateY(-1px);
}

.aircraft-history-card.active {
    color: #e7f8ff;
    border-color: #26bdf5;
    background: linear-gradient(145deg, rgba(13, 93, 138, 0.86), rgba(8, 54, 92, 0.94));
    box-shadow: inset 0 0 0 1px rgba(65, 207, 255, 0.2), 0 5px 14px rgba(0, 114, 176, 0.18);
}

.aircraft-card-icon {
    display: inline-flex;
    flex: 0 0 auto;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    margin-right: 10px;
    color: #4bc7ff;
    font-size: 18px;
    border-radius: 50%;
    background: rgba(43, 164, 222, 0.14);
}

.aircraft-card-info {
    flex: 1;
    min-width: 0;
}

.aircraft-card-info strong,
.aircraft-card-info small {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.aircraft-card-info strong {
    margin-bottom: 6px;
    color: inherit;
    font-size: 13px;
}

.aircraft-card-info small {
    color: #75a4bf;
    font-size: 11px;
}

.aircraft-history-card > .el-icon-arrow-right {
    flex: 0 0 auto;
    margin-left: 7px;
    color: #5488a6;
}

.history-route-section {
    padding-top: 12px;
    border-top: 1px solid rgba(70, 137, 181, 0.22);
}

.history-route-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    margin-bottom: 9px;
    color: #dff5ff;
    font-size: 13px;
    font-weight: 700;
}

.history-route-heading small {
    display: block;
    margin-top: 4px;
    color: #6995ae;
    font-size: 10px;
    font-weight: 400;
}

.history-route-heading ::v-deep .el-button {
    flex: 0 0 auto;
    margin-left: 0;
    white-space: nowrap;
}

.history-heading-actions {
    display: flex;
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 6px;
}

.history-route-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(245px, 1fr));
    gap: 8px;
    max-height: 390px;
    padding-right: 3px;
    overflow-y: auto;
}

.history-route-card {
    display: flex;
    align-items: center;
    min-width: 0;
    min-height: 58px;
    padding: 8px 9px;
    border: 1px solid rgba(50, 115, 165, 0.35);
    border-radius: 5px;
    background: rgba(4, 27, 56, 0.82);
    cursor: pointer;
    transition: border-color 0.18s, background 0.18s;
}

.history-route-card:hover {
    border-color: rgba(255, 159, 28, 0.65);
    background: rgba(36, 52, 66, 0.9);
}

.history-route-card.active {
    border-color: #ff9f1c;
    background: linear-gradient(90deg, rgba(133, 76, 10, 0.42), rgba(42, 43, 53, 0.85));
    box-shadow: inset 3px 0 0 #ff9f1c;
}

.route-card-index {
    flex: 0 0 auto;
    min-width: 38px;
    color: #ffad3d;
    font-size: 13px;
    font-weight: 700;
}

.route-card-main {
    flex: 1;
    min-width: 0;
}

.route-card-main strong,
.route-card-main span {
    display: block;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.route-card-main strong {
    margin-bottom: 5px;
    color: #e7f5fc;
    font-size: 12px;
}

.route-card-main span {
    color: #719bb3;
    font-size: 10px;
}

.route-card-actions {
    display: flex;
    flex: 0 0 auto;
    align-items: center;
    margin-left: 8px;
}

.route-card-actions ::v-deep .el-button {
    margin: 0 0 0 5px;
    padding: 5px;
    color: #54d0ff;
}

.route-card-actions ::v-deep .delete-route-button {
    color: #ff6262;
}

.history-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 150px;
    color: #668ea6;
    border: 1px dashed rgba(70, 137, 181, 0.28);
    border-radius: 5px;
}

.history-empty i {
    margin-bottom: 9px;
    font-size: 28px;
}

.plantable {
    max-height: 470px;
    margin-top: 0;
    overflow-y: auto;
}

.result-route-table ::v-deep th .cell,
.result-route-table ::v-deep td .cell,
.distance-value {
    white-space: nowrap;
    word-break: keep-all;
}

.result-route-table ::v-deep td .cell {
    line-height: 20px;
}

.nest-point-table ::v-deep .el-table__header th,
.nest-point-table ::v-deep .el-table__body td {
    height: 42px;
    padding: 0;
}

.nest-point-table ::v-deep .cell {
    overflow: hidden;
    padding: 0 12px;
    line-height: 42px;
    text-overflow: ellipsis;
    white-space: nowrap;
    word-break: keep-all;
}

.nest-point-table .coordinate-value {
    display: block;
    overflow: hidden;
    font-variant-numeric: tabular-nums;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.page-left {
    display: flex;
    justify-content: flex-end;
    padding-top: 10px;
    overflow-x: auto;
}

.action-list {
    justify-content: center;
    gap: 3px;
}

.action-item {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    border-radius: 4px;
    transition: background 0.18s;
}

.action-item:hover {
    background: rgba(73, 184, 255, 0.12);
}

.sidebar-footer {
    flex: 0 0 auto;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    min-height: 62px;
    padding: 10px 14px;
    border-top: 1px solid rgba(72, 161, 220, 0.25);
    background: rgba(5, 20, 43, 0.98);
    box-shadow: 0 -8px 18px rgba(0, 0, 0, 0.16);
}

.footer-status {
    display: flex;
    align-items: center;
    min-width: 0;
    color: #7da5bd;
    font-size: 11px;
}

.footer-status i {
    margin-right: 6px;
    color: #edb64b;
}

.footer-status .el-icon-circle-check {
    color: #49d49d;
}

.footer-status span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.upload-demo {
    margin-top: 16px;
}

.upload-demo ::v-deep .el-upload,
.upload-demo ::v-deep .el-upload-dragger {
    width: 100%;
}

::v-deep .el-pagination__total {
    margin-left: 10px;
}

:global(.batch-delete-tip) {
    color: #9aa9b5;
    font-size: 12px;
}

::v-deep .el-table {
    background: transparent;
}

::v-deep .el-table th,
::v-deep .el-table tr {
    background: rgba(5, 28, 59, 0.72);
}

::v-deep .el-table td,
::v-deep .el-table th.is-leaf {
    border-color: rgba(55, 125, 177, 0.3);
}

::v-deep .el-table--border,
::v-deep .el-table--group {
    border-color: rgba(55, 125, 177, 0.35);
}

@media (max-width: 1440px) {
    .left {
        min-width: 420px;
    }

    .sidebar-heading small {
        display: none;
    }

    .sidebar-pane {
        padding: 10px;
    }

    .sidebar-card {
        padding: 10px;
    }
}

@media (max-height: 760px) {
    .sidebar-header {
        padding-top: 10px;
    }

    .sidebar-heading {
        margin-bottom: 7px;
    }

    .sidebar-tabs button {
        height: 34px;
    }

    .sidebar-pane {
        padding-top: 8px;
    }

    .sidebar-card {
        margin-bottom: 8px;
    }

    .sidebar-footer {
        min-height: 54px;
        padding-top: 7px;
        padding-bottom: 7px;
    }
}

::v-deep .iclient-leaflet-logo {
    display: none !important;
}
</style>
<style lang="scss">
/* ======== 亮色主题：左侧栏全部子元素 ======== */
html[data-theme='light'] .left {
    border-right: 1px solid #e2e8f0 !important;
    background: linear-gradient(180deg, #f8fafc 0%, #eef1f5 100%) !important;
    box-shadow: 4px 0 14px rgba(0, 0, 0, 0.06) !important;
}
html[data-theme='light'] .sidebar-header,
html[data-theme='light'] .sidebar-footer {
    background: #f1f5f9 !important;
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .sidebar-heading > div,
html[data-theme='light'] .sidebar-heading i,
html[data-theme='light'] .card-title > span,
html[data-theme='light'] .card-title i,
html[data-theme='light'] .summary-item strong,
html[data-theme='light'] .upload-row label,
html[data-theme='light'] .result-overview strong,
html[data-theme='light'] .footer-status,
html[data-theme='light'] .route-card-main strong,
html[data-theme='light'] .aircraft-card-info,
html[data-theme='light'] .dataset-summary,
html[data-theme='light'] .processing-title {
    color: #1e293b !important;
}
html[data-theme='light'] .sidebar-heading small,
html[data-theme='light'] .card-title small,
html[data-theme='light'] .upload-row span,
html[data-theme='light'] .summary-tip,
html[data-theme='light'] .result-overview span,
html[data-theme='light'] .result-empty,
html[data-theme='light'] .history-empty,
html[data-theme='light'] .route-card-main span,
html[data-theme='light'] .aircraft-history-card small,
html[data-theme='light'] .footer-status span {
    color: #64748b !important;
}
html[data-theme='light'] .sidebar-card,
html[data-theme='light'] .summary-item,
html[data-theme='light'] .aircraft-history-card,
html[data-theme='light'] .history-route-card {
    background: #ffffff !important;
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .aircraft-history-card.active {
    border-color: #2563eb !important;
}
html[data-theme='light'] .sidebar-tabs button {
    color: #64748b !important;
}
html[data-theme='light'] .sidebar-tabs button:hover {
    color: #1e293b !important;
    background: rgba(37, 99, 235, 0.05) !important;
}
html[data-theme='light'] .sidebar-tabs button.active {
    color: #2563eb !important;
    border-bottom-color: #2563eb !important;
    background: linear-gradient(180deg, transparent, rgba(37, 99, 235, 0.08)) !important;
}
html[data-theme='light'] .sidebar-tabs button em {
    background: #2563eb !important;
}
html[data-theme='light'] .upload-row {
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .processing-panel {
    background: #f8fafc !important;
    border-color: #e2e8f0 !important;
    color: #1e293b !important;
}
html[data-theme='light'] .result-overview > div {
    background: linear-gradient(180deg, rgba(37, 99, 235, 0.06), rgba(37, 99, 235, 0.02)) !important;
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .result-empty {
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .history-empty {
    border-color: #e2e8f0 !important;
}
html[data-theme='light'] .route-layer-switch {
    background: #ffffff !important;
    border-color: #e2e8f0 !important;
    color: #1e293b !important;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08) !important;
}
html[data-theme='light'] .sidebar-resizer span {
    background: rgba(37, 99, 235, 0.35) !important;
    box-shadow: 0 0 6px rgba(37, 99, 235, 0.25) !important;
}
html[data-theme='light'] .sidebar-scroll {
    scrollbar-color: rgba(37, 99, 235, 0.25) rgba(0, 0, 0, 0.05) !important;
}
html[data-theme='light'] .sidebar-scroll::-webkit-scrollbar-thumb {
    background: rgba(37, 99, 235, 0.25) !important;
}
html[data-theme='light'] .history-capture-select label {
    color: #475569 !important;
}
html[data-theme='light'] .route-card-index,
html[data-theme='light'] .route-card-actions ::v-deep .el-button {
    color: #2563eb !important;
}
</style>
