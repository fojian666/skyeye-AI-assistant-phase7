<template>
    <div style="width: 100%; height: 100%; display: flex">
        <div class="small-map-container" ref="smallMapContainer" v-if="showSmallMap">
            <small-map
                    class="small-map"
                    ref="smallMap"
                    :temp-point-list="tempPointList"
                    :task-list="taskList"
                    :currentYaw="currentYaw"
                    :current-task="currentTask"
                    :current-view-point="currentViewPoint"
                    :isMapChange="isMapChange"
                    :currentAddMarker="currentAddMaker"
                    @synchronousPosition="synchronousPosition"
                    :currentLocationMarker="currentLocationMarker"
                    :no_detection_area_list="no_detection_area_list"
                    :isAutoRotating="isAutoRotating"
                    @clickMarker="handleMarkerClick"
                    @clickMap="modifyTakePoint">
            </small-map>
        </div>
        <div id="panoramaContainer" style="position: relative; height: 100%; width: 50%"   @mousemove="mouseMoveFunction" @mouseleave="MouseLeaveFunction">
            <div class="pannellum-layer" v-if="afterLoadPannellum"></div>
            <canvas id="overlay" ref="canvas"></canvas>
            <div class="select-gd">
                <el-collapse >
                    <el-collapse-item title="业务图层" name="allLayers">
                        <div v-for="(item, index) in allLayers" :key="item.id" class="gd-item">
                            <el-checkbox v-model="item.check" @change="handleGdChange">{{ item.name }}</el-checkbox>
                        </div>
                    </el-collapse-item>
                </el-collapse>
            </div>
            <div class="show_jiaodu">
                <div class="gongju_left">{{ formattedShotTime}}</div>

            </div>
            <div class="close-chahao"><el-button icon="el-icon-close" @click="handlebtnclick" class="close-chahao-btn"></el-button></div>

            <div class="gt-toolbar-right">
                <div v-if="!pointId" class="gt-alarms-list" title="返回" @click="handlebtnclick">
                    <img src="@/assets/images/back.png" />
                </div>
                <div v-if="isAutoRotating" class="gt-alarms-list" title="暂停自动播放" @click="autoPlay">
                    <img src="@/assets/images/stop.png" />
                </div>
                <div v-else class="gt-alarms-list" title="自动播放" @click="autoPlay">
                    <img src="@/assets/images/play.png" />
                </div>
                <div class="gt-alarms-list" title="检测列表" @click="fetchList">
                    <img src="@/assets/images/list.png" />
                </div>
                <div class="gt-alarms-list" title="提交复核" @click="handleSubmitReview">
                    <img src="@/assets/images/save.png" />
                </div>
                <div class="gt-alarms-list" title="添加目标" @click="openDialog">
                    <img src="@/assets/images/add.png" />
                </div>
                <div class="gt-alarms-list gt-alarms-text" title="分析结果" @click="openAnalysisResultDialog">
                  <img src="@/assets/images/plan1.png" />
                </div>
<!--                <div class="gt-alarms-list" title="不检测区域" @click="handleNoDevelopFun">-->
<!--                    <img src="@/assets/images/nodetection.png" />-->
<!--                </div>-->
                <div class="gt-alarms-list" title="多期对比" @click="handleMultiComparision">
                    <img src="@/assets/images/change.png" />
                </div>
                <div class="gt-alarms-list" @click="handleThreeComparison" title="三屏对比">
                    <img src="@/assets/images/sanping.png" />
                </div>
                <div class="gt-alarms-list" @click="handleResetViewYaw" title="一键归位">
                    <img src="@/assets/images/guiwei.png" />
                </div>
            </div>

            <div id="hotspot-buttons" style="display: none; position: absolute">
                <el-button id="confirm-button">确认</el-button>
                <el-button id="misjudgment-button">无效</el-button>
            </div>
            <!-- 速度控制条 -->
            <div v-if="isAutoRotating" class="speed-control">
                <el-radio-group v-model="angleRadio" size="mini" class="angleRadio" @change="handleAngleChange">
                    <el-radio-button label="近"></el-radio-button>
                    <el-radio-button label="远"></el-radio-button>
                </el-radio-group>
                <span style="margin-top: 5px;color:black">速度</span>
                <div class="speed-btn-group">
                    <ul>
                        <li @click="handleSpeedChange(1)" :class="{ activate: rotationSpeed === 1 }">1x</li>
                        <li @click="handleSpeedChange(2)" :class="{ activate: rotationSpeed === 2 }">2x</li>
                        <li @click="handleSpeedChange(3)" :class="{ activate: rotationSpeed === 3 }">3x</li>
                        <li @click="handleSpeedChange(4)" :class="{ activate: rotationSpeed === 4 }">4x</li>
                        <li @click="handleSpeedChange(5)" :class="{ activate: rotationSpeed === 5 }">5x</li>
                        <li @click="handleSpeedChange(6)" :class="{ activate: rotationSpeed === 6 }">6x</li>
                        <li @click="handleSpeedChange(7)" :class="{ activate: rotationSpeed === 7 }">7x</li>
                        <li @click="handleSpeedChange(8)" :class="{ activate: rotationSpeed === 8 }">8x</li>
                        <li @click="handleSpeedChange(9)" :class="{ activate: rotationSpeed === 9 }">9x</li>
                        <li @click="handleSpeedChange(10)" :class="{ activate: rotationSpeed === 10 }">10x</li>
                    </ul>
                </div>
            </div>

            <el-dialog :title="currentTitle" :visible.sync="dialogVisible" :modal="false" class="transparent-dialog">
                <div>这是采用大疆无人机在龙潭街道拍摄的全景图</div>
                <div>{{ currentObj.imageName }}</div>
            </el-dialog>
            <el-dialog
                title="分析结果"
                :visible.sync="analysisResultDialogVisible"
                :modal="false"
                class="label-dialog analysis-result-dialog"
                :close-on-click-modal="false"
                width="480px">
                <div class="analysis-result-content" v-if="currentObj.desc">{{ currentObj.desc }}</div>
                <div class="analysis-result-empty" v-else>暂无分析结果</div>
            </el-dialog>
<!--            <panoramaList-->
<!--                    v-if="isShowPanoramaList"-->
<!--                    class="panoramaList"-->
<!--                    :currentTask="currentTask"-->
<!--                    @changeScene="changeScene"-->
<!--                    @isThumbnailCollapsed="handleIsThumbnailCollapsed"-->
<!--                    ref="panoramaList">-->
<!--            </panoramaList>-->
        </div>
        <div
                class="detectlist"
                v-show="dialogTableVisible"
                :style="{
                right: position.right + 'px',
                top: position.top + 'px',
                height: isCollapsed ? 'auto' : '500px'
            }"
                @mousedown="startDrag">
            <div class="title">
                <!--            <div class="tablenum">{{calculateTableNum}}</div>-->
                <span>检测列表（{{ calculateTableNum }}）</span>
                <!-- 新增收起/展开按钮 -->
                <el-tooltip class="item" effect="dark" content="收起" placement="top">
                    <el-button icon="el-icon-arrow-up" circle @click="toggleCollapse" :icon="isCollapsed ? 'el-icon-arrow-down' : 'el-icon-arrow-up'">
                    </el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="刷新" placement="top">
                    <el-button icon="el-icon-refresh" circle @click="refresh"></el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="关闭" placement="top">
                    <el-button icon="el-icon-close" circle @click="closeDetectdialog"></el-button>
                </el-tooltip>
            </div>
            <!-- 可收起的内容区域 -->
            <div class="collapsible-content" :class="{ collapsed: isCollapsed }">
                <div class="gt-query">
                    <el-input v-model="queryClueClass" placeholder="请输入标签类别"></el-input>
                    <el-select v-model="queryClueStatus" placeholder="请选择" clearable style="margin-right: 2px; z-index: 9999999">
                        <el-option v-for="item in cluesOptions" :key="item.value" :label="item.label" :value="item.value"> </el-option>
                    </el-select>
                  <el-select v-model="queryClueSource" placeholder="请选择线索来源" clearable style="margin-right: 2px; z-index: 9999999">
                    <el-option key="1" label="目标检测" value="1"> </el-option>
                    <el-option key="2" label="变化检测" value="2"> </el-option>
                  </el-select>
                    <el-button icon="el-icon-search" type="primary" @click="filterData" style="width: 50px"></el-button>
                </div>
                <!-- 表格容器添加固定高度和滚动控制 -->
                <div class="table-container">
                    <el-table :data="filteredData" :row-class-name="rowClassName">
<!--                        <el-table-column property="clue_id" label="id" width="50"></el-table-column>-->
                        <el-table-column type="index" ></el-table-column>
                        <el-table-column property="label" label="标签" width="70"></el-table-column>
                        <el-table-column property="szdl" label="地类" width="70"></el-table-column>
                        <el-table-column property="operation" label="操作" width="180">
                            <template slot-scope="scope">
                                <el-button type="text" size="small" @click="handleView(scope.row.clue_id)" :disabled="isMarked(scope.row.status)[0]"
                                >查看</el-button
                                >
                                <el-button
                                        type="text"
                                        size="small"
                                        @click="handleConfirmAndMistake(scope.row, 1)"
                                        :disabled="isMarked(scope.row.status)[1]"
                                        class="btn"
                                >无效</el-button
                                >
                                <el-button
                                        type="text"
                                        size="small"
                                        @click="handleConfirmAndMistake(scope.row, 2)"
                                        :disabled="isMarked(scope.row.status)[2]"
                                        class="btn"
                                >确认</el-button
                                >
                                <el-button
                                        type="text"
                                        size="small"
                                        @click="startTakeMap(scope.row)"
                                        :disabled="isMarked(scope.row.status)[3]"
                                        class="btn"
                                >纠偏</el-button
                                >
                                <!--                            <el-button type="text" size="small" :disabled="judeLuRuButton(scope.row.status)" @click="handleWriteResult(scope.row)">录入</el-button>-->
                                <el-button
                                        type="text"
                                        size="small"
                                        :disabled="isMarked(scope.row.status)[4]"
                                        @click="handleWriteResult(scope.row)"
                                        class="btn"
                                >录入</el-button
                                >
                            </template>
                        </el-table-column>
                        <el-table-column property="status" label="状态" >
                            <template slot-scope="scope">
                                <span :style="{ color: getClueStatus(scope.row.status)[0] }" style="font-weight: bold">
                                    {{ getClueStatus(scope.row.status)[1] }}
                                </span>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>
        <div
                class="undetected-region-list"
                v-show="drawPolygonVisible"
                :style="{
                right: position.right + 'px',
                top: position.top + 'px',
                height: isCollapsed ? 'auto' : '500px'
            }"
                @mousedown="startDrag">
            <div class="title">
                <span>不检测区域列表（{{ frameAreaList.length }}）</span>
                <el-tooltip class="item" effect="dark" content="收起" placement="top">
                    <el-button icon="el-icon-arrow-up" circle @click="toggleCollapse" :icon="isCollapsed ? 'el-icon-arrow-down' : 'el-icon-arrow-up'">
                    </el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="开始绘制" placement="top">
                    <el-button
                            icon="el-icon-edit"
                            circle
                            @click="
                            editFlag = false;
                            drawPolygonFlag = true;
                        "></el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="关闭" placement="top">
                    <el-button
                            icon="el-icon-close"
                            circle
                            @click="
                            drawPolygonFlag = false;
                            drawPolygonVisible = false;
                            isCollapsed = false;
                        "></el-button>
                </el-tooltip>
            </div>
            <div class="collapsible-content" :class="{ collapsed: isCollapsed }">
                <div class="table-container-frame">
                    <el-table :data="frameAreaList">
<!--                        <el-table-column property="id" label="id" width="70"></el-table-column>-->
                        <el-table-column type="index"></el-table-column>
                        <el-table-column property="name" label="名称" width="200"></el-table-column>
                        <el-table-column property="operation" label="操作">
                            <template slot-scope="scope">
                                <el-button type="text" size="small" @click="deleteFrameArea(scope.row.id)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>
        <div
                class="undetected-region-list"
                v-show="drawRectPolygonVisible"
                :style="{
                right: position.right + 'px',
                top: position.top + 'px',
                height: isCollapsed ? 'auto' : '500px'
            }"
                @mousedown="startDrag">
            <div class="title">
                <span>目标区域列表（{{ rectFrameAreaList.length }}）</span>
                <el-tooltip class="item" effect="dark" content="收起" placement="top">
                    <el-button icon="el-icon-arrow-up" circle @click="toggleCollapse" :icon="isCollapsed ? 'el-icon-arrow-down' : 'el-icon-arrow-up'">
                    </el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="开始绘制" placement="top">
                    <el-button
                            icon="el-icon-edit"
                            circle
                            @click="
                            editFlag = false;
                            drawRectPolygonFlag = true;
                        "></el-button>
                </el-tooltip>
                <el-tooltip class="item" effect="dark" content="关闭" placement="top">
                    <el-button
                            icon="el-icon-close"
                            circle
                            @click="
                            drawRectPolygonFlag = false;
                            drawRectPolygonVisible = false;
                            isCollapsed = false;
                        "></el-button>
                </el-tooltip>
            </div>
            <div class="collapsible-content" :class="{ collapsed: isCollapsed }">
                <div class="table-container-frame">
                    <el-table :data="rectFrameAreaList">
                        <el-table-column property="id" label="id" width="70"></el-table-column>
                        <el-table-column property="label" label="名称" width="200"></el-table-column>
                        <el-table-column property="operation" label="操作">
                            <template slot-scope="scope">
                                <el-button type="text" size="small" @click="deleteTargetAreaClue(scope.row.id)">删除</el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
            </div>
        </div>
        <el-dialog
                title="修改点位信息"
                :visible.sync="correctLabelVisible"
                :modal="false"
                class="label-dialog"
                :close-on-click-modal="false"
                @close="">
            <el-form class="form_class">
                <el-form-item label="经度坐标:" style="display: flex">
                    <el-input v-model="currentClickObj.clickLongitude" class="select-item"> </el-input>
                </el-form-item>
                <el-form-item label="纬度坐标:" style="display: flex">
                    <el-input v-model="currentClickObj.clickLatitude" class="select-item"></el-input>
                </el-form-item>
                <el-form-item label="线索ID:" style="display: flex">
                    <el-input v-model="currentClickObj.clickcorrentClueId" class="select-item"></el-input>
                </el-form-item>
                <div class="btn-uploading">
                    <el-button style="margin-right: 20px" type="primary" size="medium" @click="modifyPointCoord">确认 </el-button>
                    <el-button style="margin-left: 20px" size="medium" @click="cancelCorrectVisible">取消</el-button>
                </div>
            </el-form>
        </el-dialog>
        <el-dialog
                title="添加目标点"
                :visible.sync="labelVisible"
                :modal="false"
                class="label-dialog"
                :close-on-click-modal="false"
                @close="handleClose">
            <el-form class="form_class">
                <el-form-item label="点位像素x:" style="display: flex">
                    <el-input v-model="pixel_x"> </el-input>
                </el-form-item>
                <el-form-item label="点位像素y:" style="display: flex">
                    <el-input v-model="pixel_y"></el-input>
                </el-form-item>
                <el-form-item label="目标类型:" style="display: flex">
                    <el-select v-model="currentClass" filterable  placeholder="请选择" style="width: 205px">
                        <el-option v-for="item in classList" :key="item" :label="item" :value="item"> </el-option>
                    </el-select>
                </el-form-item>
                <div class="btn-uploading">
                    <el-button style="margin-right: 20px" type="primary" size="medium" @click="addOdLabel">添加 </el-button>
                    <el-button style="margin-left: 20px" size="medium" @click="handleClose">取消</el-button>
                </div>
            </el-form>
        </el-dialog>
        <div class="result-dialog" v-if="writeResultDialogVisible">
            <div class="verify-title">
                <span>核查结论录入</span>
                <el-button icon="el-icon-close" circle @click="writeResultDialogVisible = false"></el-button>
            </div>
            <el-form ref="form" :model="form" label-width="100px" class="result-form">
                <el-form-item label="线索ID" class="gt-form-item">
                    <el-input v-model="form.clue_id" :disabled="true"></el-input>
                </el-form-item>
                <el-form-item label="线索是否有效" class="gt-form-item">
                    <el-radio v-model="form.clue_valid_judge" label="5">是</el-radio>
                    <el-radio v-model="form.clue_valid_judge" label="4">否</el-radio>
                </el-form-item>
                <el-form-item label="核查结论" class="gt-form-item">
                    <el-input type="textarea" v-model="form.clue_verify_result"></el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="submitWriteResult" style="margin-right: 50px">提交</el-button>
                    <el-button @click="writeResultDialogVisible = false">取消</el-button>
                </el-form-item>
            </el-form>
        </div>

        <div class="pannellum-toolbar">
            <div @click="handleMeasure('measureDistance')" :class="{ baractive: activeToolBarType === 'measureDistance' }" title="测距">
                <span class="icon iconfont icon-icon-line-graph icon-toolbar"></span>
            </div>
            <span style="color: #cccccc; margin-left: 5px">|</span>
            <div @click="handleMeasure('measureArea')" :class="{ baractive: activeToolBarType === 'measureArea' }" title="测面积">
                <span class="icon iconfont icon-duobianxing icon-toolbar"></span>
            </div>
            <span style="color: #cccccc; margin-left: 5px" title="清除">|</span>
            <div @click="handleClear"><span class="icon iconfont icon-qingchu icon-toolbar"></span></div>
        </div>
    </div>
</template>

<script>
    import screenfull from 'screenfull';
    import {
      changeClueByIdApi,
      getOneQuanjingPointClueInfoApi,
      queryCluesDataApi,
      postClueInfoApi,
      submitReviewApi,
      submitCorrectPointApi,
      postFrameAreaApi,
      getFrameAreaListApi,
      deleteFrameAreaApi,
      clueEntryApi,
      getOnePointMultiComInfoApi,
      getBufferLayerApi,
      getPointBufferLayerApi,
      getTargetAreaListApi,
      deleteTargetClueApi,
      getFrameAreaByPointIdApi, getEnumOptionApi
    } from '@/api/commonApi';
    import smallMap from '@/components/smallMap/index.vue';
    import {calculateTotalArea, calculateTotalDistance, imageToLatLon,latLonToYawPitch} from "@/utils/utils";
    import {sphericalToScreen, isPointInView, updateZoomButtonsState} from "@/utils/panoramaTools";
    export default {
        name: 'verifypannelViewer',
        //接收父组件传递的数据
        props: {
            currentObj: Object,
            taskList: {
                type: Array,
                required: true
            },
            batchNumber: ''
        },
        components: {
            smallMap
        },
        data() {
            return {
              selectedGdPolygon: null, // 单个选中（仅顶层），
              highlightColor: 'red',
              gdPolygonDrawStack: [], // 绘制栈：记录当前可见的图斑（后绘制的在栈顶）
              isMouseMoved: false,
                pointId: null, // 新增 loading 状态
                isLoading: false, // 新增 loading 状态
                isShowPanoramaList:false,
                angleRadio:'',
                showSmallMap: false, //小地图显示
                currentPointId: null,
                frameAreaList: [], //不检测区域列表
                drawPolygonVisible: false,
                polygons: [], //需要绘制的多边形集合,坐标为pitch，yaw
                drawPoints: [], //当前绘制的多边形顶点集合,坐标为pitch,yaw
                ctx: null,
                drawPolygonFlag: false,
                // 图层显示
                afterLoadPannellum: false,
                yawDegree: 0,
                // 全景对象
                viewer: undefined,
                currentHfov: 0,
                //是否全屏
                isScreenFull: false,
                currentScene: '',
                lastIndex: 1,
                dialogVisible: false,
                analysisResultDialogVisible: false,
                currentTitle: '全景图简介',
                labelVisible: false,
                editFlag: false,
                isMapChange: false, //是否按下打点
                pixel_x: 0,
                pixel_y: 0,
                mouseDownPitch: 0,
                mouseDownYaw: 0,
                lastHighView: {
                    id: 0,
                    yaw: 0,
                    pitch: 0,
                    label: ''
                },
                currentClass: '',
                classList: [],
                currentIndex: 1,
                dialogTableVisible: false,
                clueList: [],
                currentMarker: null,
                markers: [],
                totalTaskList: [],
                mapService: '',
                gengdiService: '',
                center: '',
                redIcon: null,
                activeNames: ['1'], // 控制折叠面板的展开和折叠
                gengdilayer: {},
                circlelayerList: [],
                layerVisibility: {
                    gengdivector: false,
                    monitorcircle: true
                },
                circleLayers: {},
                currentYaw: 0,
                currentPitch: 0,
                imageName: '',
                pointName: '',
                bufferPitch: 0,
                rowStatus: {}, // 保存每行状态的对象
                currentTask: {},
                isAutoRotating: false,
                rotationSpeed: 5, // 默认速度（1-10）
                map: {},
                correctLabelVisible: false,
                currentClickObj: {
                    clickcorrentClueId: '-1',
                    clickLongitude: 0,
                    clickLatitude: 0,
                },
                tempPointList: [],
                currentAddMaker: null,
                currentLocationMarker:null,
                cluePointsDic: {},
                customIcon: L.icon({
                    iconUrl: '../../static/marker-icon-red.png',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                }),
                currentViewPoint: null,
                currentRow: {},
                points: [],
                isDrawing: false,
                polygon: null,
                cluesOptions: [
                    {
                        value: 1,
                        label: '无效'
                    },
                    {
                        value: 2,
                        label: '已确认'
                    },
                    {
                        value: 0,
                        label: '待复核'
                    },
                    {
                        value: 5,
                        label: '已核实'
                    }
                ],
                queryClueStatus: '',
                queryClueClass: '',
              queryClueSource:'',
                filteredData: [],
                current_static: {
                    total_count: 0,
                    done_clue_count: 0,
                    undone_clue_count: 0
                },
                showMap: true,
                writeResultDialogVisible: false,
                form: {
                    clue_valid_judge: '',
                    clue_verify_result: '',
                    clue_id: ''
                },
                drawRectPolygonVisible: false,
                rectFrameAreaList: [],
                drawRectPolygonFlag: false,
                drawRectPoints: [],
                targetPolygons: [], //需要绘制的目标多边形集合,坐标为pitch，yaw
                noDetectionLayer: L.layerGroup(),
                canvas: null, //全景图上的画布
                initYawDegree: 0, //初始Yaw值
                isCollapsed: false, // 控制是否收起
                position: {
                    right: 60, // 初始right值（px）
                    top: window.innerHeight * 0.15 // 15vh换算值
                },
                dragStartPos: { x: 0, y: 0 },
                isDragging: false,
                gdPolygons:[],
                targetLabelVisible:false,
                circleRadius: window.config.circleRadius,
                innerCircleRadius: window.config.innerCircleRadius,
                activeToolBarType:'',
                measureDistancePoints:[],
                measureAreaPoints:[],
                isMeasureDistance:false,
                isMeasureArea:false,
                minHfov:10,
                maxHfov:120,
                //全部图层
                allLayers:[],
                disableMouseMove: false,
                no_detection_area_list:[],
                lastHov: 120,
            };
        },
        beforeDestroy() {
            if (this.viewer) {
                this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
            }
        },
        methods: {
            //业务图层选择变化监听
            handleGdChange() {
                this.drawGdPolygons();
            },
            //监听
            mouseMoveFunction(event){
                // 如果处于禁用状态，直接返回
                if (this.disableMouseMove) return;
                if(!this.viewer) return;
                var coords = this.viewer.mouseEventToCoords(event);
                const lat_lon =  imageToLatLon(this.currentTask.latitude, this.currentTask.longitude, this.currentTask.height, coords[1], coords[0], this.currentTask.yawDegree)
                var customIcon = L.icon({
                    iconUrl: '../../static/guangbiao.png',
                    iconSize: [32, 32], // 图标的尺寸
                    // 可选的其他图标样式选项
                });
                const r = this.isPointInBuffer( coords[1], coords[0])
                if(r){
                    this.currentLocationMarker= L.marker(lat_lon, {
                        icon: customIcon,
                        className: 'custom-cursor'
                    })
                }else{
                    // 创建一个完全透明的自定义图标
                    const emptyIcon = L.divIcon({
                        className: 'empty-marker',
                        html: '', // 空内容
                        iconSize: [0, 0] // 零尺寸
                    });

                    this.currentLocationMarker =  L.marker(lat_lon, {
                        icon: emptyIcon,
                        interactive: true // 保持可交互性
                    });
                }
            },
            MouseLeaveFunction(event){
                // 创建一个完全透明的自定义图标
                const emptyIcon = L.divIcon({
                    className: 'empty-marker',
                    html: '', // 空内容
                    iconSize: [0, 0] // 零尺寸
                });
                this.currentLocationMarker =  L.marker([0,0], {
                    icon: emptyIcon,
                    interactive: true // 保持可交互性
                });
            },
            // 修改打点的位置
            modifyTakePoint(lat, lng) {
                this.currentClickObj.clickLatitude = lat;
                this.currentClickObj.clickLongitude = lng;
                const customIcon = L.icon({
                    iconUrl: '../../static/video_mark_model.png',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32]
                });
                if (this.dialogTableVisible) {
                  this.currentAddMaker = L.marker([lat, lng], { icon: customIcon });
                    this.correctLabelVisible = true;
                }
            },
            //开始打点
            startTakeMap(row) {
                this.handleView(row.clue_id);
                this.currentClickObj.clickcorrentClueId = row.clue_id;
                this.isMapChange = true;
                this.$refs.smallMap.updateSector(this.currentYaw)
            },
            openDialog() {
                if(this.currentTask.status === 2){
                    this.$message.warning('当前全景图已判读完毕，无法新增目标点！')
                }else {
                    this.drawPolygonFlag = false;
                    this.drawRectPolygonFlag = false;
                    this.editFlag = true;
                }
            },
            openAnalysisResultDialog() {
                this.analysisResultDialogVisible = true;
            },
            //关闭添加线索点
            handleClose() {
                this.editFlag = false;
                this.labelVisible = false;
            },
            //移除所有线索点
            removeAllHotspots() {
              if(this.viewer) {
                // 获取所有热点
                this.clueList.forEach((item) => {
                  this.viewer.removeHotSpot(item.clue_id);
                });
              }
            },
            //从全景图中移除所有全景点
            removeAllQuanjingHotspots() {
              if(this.viewer) {
                this.taskList.forEach((item) => {
                  this.viewer.removeHotSpot(item.imageId);
                });
              }
            },
            //保存目标点
            async addOdLabel() {
                if (this.currentClass === '') {
                    this.$message.warning('请选择标签类别！');
                    return;
                }
                const params = {
                    pixelX: this.pixel_x,
                    pixelY: this.pixel_y,
                    panoramaImageId: this.currentTask.imageId,
                    className: this.currentClass,
                    yaw: this.mouseDownYaw,
                    pitch: this.mouseDownPitch,
                };

                const res = await postClueInfoApi(params);
                if (res.code === 0) {
                  this.$message.success("添加成功！");
                } else {
                    this.viewer.removeHotSpot(this.currentIndex);
                    this.$message.error('添加失败，请查看后台日志！', res.msg);
                }
                this.editFlag = false;
                this.labelVisible = false;
                this.pixel_y = 0;
                this.pixel_y = 0;
                this.removeAllHotspots();
                await this.fetchData(this.currentTask.imageId);
                this.$emit('update-data', { value: true });
            },
            handleMouseDown(event) {
                if (this.isAutoRotating) {
                    this.viewer.stopAutoRotate();
                    this.isAutoRotating = false;
                    this.angleRadio = '';
                }
                var coords = this.viewer.mouseEventToCoords(event);
                this.mouseDownPitch = coords[0];
                this.mouseDownYaw = coords[1];
                if (this.editFlag) {
                    this.drawMarker(coords);
                    // 将 pitch 和 yaw 转换为 x 和 y 像素坐标
                    this.pixel_x = (((coords[1] * Math.PI) / 180 + Math.PI) / (2 * Math.PI)) * this.width;
                    this.pixel_y = ((Math.PI / 2 - (coords[0] * Math.PI) / 180) / Math.PI) * this.height;
                    this.labelVisible = true;
                } else if (this.drawPolygonFlag) {
                    if (event.button === 2) {
                        //表示右击结束面绘制
                        this.drawPolygonFlag = false;
                        return;
                    }
                    this.drawPoints.push(coords);
                    this.drawPolygons();
                } else if (this.drawRectPolygonFlag) {
                    if (event.button === 2) {
                        //表示右击结束面绘制
                        this.drawRectPolygonFlag = false;
                        return;
                    }

                    this.pixel_x = (((coords[1] * Math.PI) / 180 + Math.PI) / (2 * Math.PI)) * this.width;
                    this.pixel_y = ((Math.PI / 2 - (coords[0] * Math.PI) / 180) / Math.PI) * this.height;
                    this.drawRectPoints.push(coords);
                    this.drawTargetPolygons();
                } else if(this.isMeasureDistance){
                    if (event.button === 2) {
                        //表示右击结束面绘制
                        this.isMeasureDistance = false;
                        return;
                    }
                    this.measureDistancePoints.push(coords);
                    this.drawMeasureLine()
                }else if(this.isMeasureArea){
                    if (event.button === 2) {
                        //表示右击结束面绘制
                        this.isMeasureArea = false;
                        return;
                    }
                    this.measureAreaPoints.push(coords);
                    this.drawMeasureArea()
                }
            },
            //绘制Marker点
            drawMarker(coords) {
                this.mouseDownPitch = coords[0];
                this.mouseDownYaw = coords[1];
                this.currentIndex = this.filteredData.length + 1
                this.viewer.addHotSpot({
                    id: this.currentIndex,
                    pitch: this.mouseDownPitch,
                    yaw: this.mouseDownYaw,
                    text: this.currentClass,
                    type: 'info',
                    cssClass: 'custom-hotspot',
                    // clickHandlerFunc: (event) => {
                    //     this.clickHandlerFunc(event, this.currentIndex, '0');
                    // }
                });
            },

            /*
             * 获取全景任务信息
             * @param {task_id} task_id - 任务的ID
             */
            async fetchData(imageId) {
                if (imageId) {
                    const res = await getOneQuanjingPointClueInfoApi(imageId);
                    if (res.code === 0) {
                        this.width = res.data.image_width;
                        this.height = res.data.image_height;
                        this.clueList = res.data.clue_list;
                        this.currentPointId = res.data.point_id;
                        this.clueList.forEach((item) => {
                            // 将像素坐标转换为弧度
                            var yawRad = (item.center_x / this.width) * 2 * Math.PI - Math.PI;
                            var pitchRad = Math.PI / 2 - (item.center_y / this.height) * Math.PI;
                            // 将弧度转换为角度
                            var yaw = (yawRad * 180) / Math.PI;
                            var pitch = (pitchRad * 180) / Math.PI;
                            // 创建热点对象
                            var hotSpot = {
                                id: item.clue_id,
                                pitch: pitch,
                                yaw: yaw,
                                text: item.label,
                                type: 'info',
                                cssClass: 'custom-hotspot',
                                clickHandlerFunc: (event) => {
                                    this.clickHandlerFunc(event, item.clue_id, '0');
                                }
                            };
                            if (item.status !== 1) {
                                //1是无效 添加热点到viewer
                                this.viewer.addHotSpot(hotSpot);
                                this.cluePointsDic[item.clue_id] = [item.latitude, item.longitude];
                            }
                        });
                    } else {
                        this.$message.error(res.msg);
                    }
                }
            },
            //处理线索的点击事件，可处理线索状态，也可点击全景点跳转：tag为0表明是线索点点击事件，为1表明是全景点点击事件
            clickHandlerFunc(event, item_or_id, tag) {
                if (tag === '0') {
                    this.disableMouseMove = true;
                    // 获取热点的坐标,若为线索点点击传入的是id，若为全景点点击传入的是对象
                    var hotspotCoords = this.viewer.mouseEventToCoords(event);
                    // 设置按钮的位置
                    var buttons = document.getElementById('hotspot-buttons');
                    buttons.style.display = 'flex';
                    var viewportWidth = window.innerWidth;
                    // 计算 panoramaContainer 的宽度
                    var panoramaContainerWidth = (viewportWidth - 415) / 2;
                    buttons.style.left = event.clientX - panoramaContainerWidth - 415 + 10 + 'px';
                    buttons.style.top = event.clientY -60 + 'px';
                    // 为按钮添加点击事件
                    document.getElementById('confirm-button').onclick = () => {
                        this.confirmHotspot(item_or_id);
                        this.disableMouseMove = false;
                    };
                    document.getElementById('misjudgment-button').onclick = () => {
                        this.misjudgmentHotspot(item_or_id);
                        this.disableMouseMove = false;
                    };
                } else if (tag === '1') {
                    //说明点击的是全景点，这个时候id是整个全景对象
                    // 获取热点的坐标
                    this.currentTask = item_or_id;
                    this.removeAllHotspots();
                    this.removeAllQuanjingHotspots();
                    this.pointName = this.currentTask.pointName;
                    this.imageName = this.currentTask.imageName;
                    this.showPanorama();
                    this.$emit('markerclick', this.pointName);
                }
            },
            //将线索改为确认
            confirmHotspot(id) {
                // 处理确认操作
                this.handleClickConfirmAndMistake(id, 2);
            },
            //将线索改为判读
            misjudgmentHotspot(id) {
                // 处理判读操作
                this.handleClickConfirmAndMistake(id, 1);
            },
            hideButtons() {
                document.getElementById('hotspot-buttons').style.display = 'none';
            },
            autoPlay() {
                this.currentHfov = this.viewer.getHfov(); // 当前水平视场角
                if (this.isAutoRotating) {
                    // 如果已经在自动旋转，禁用自动旋转
                    this.viewer.stopAutoRotate();
                    this.isAutoRotating = false;
                    this.angleRadio = '';
                } else {
                    this.rotationSpeed = 1;
                    // 否则，启用自动旋转
                    this.viewer.setHfov(this.currentHfov);
                    this.viewer.startAutoRotate(-1, this.currentPitch);
                    this.isAutoRotating = true;
                }
            },
            updateRotateSpeed() {
                this.viewer.setHfov(this.currentHfov);
                this.viewer.startAutoRotate(-this.rotationSpeed, this.currentPitch);
            },

            async fetchList() {
                this.drawPolygonVisible = false;
                this.dialogVisible = false;
                this.drawRectPolygonVisible = false;
                this.dialogTableVisible = true;
            },
            async getFrameArea(){
                const params1 = {
                    pointId:this.currentTask.pointId
                }
                const res1 = await getFrameAreaByPointIdApi(params1);
                if(res1.code === 0) {
                    this.no_detection_area_list = res1.data.no_detection_area_list;
                }

            },
            destroyExistingWebGLContext() {
                const canvases = document.querySelectorAll('canvas');
                canvases.forEach(canvas => {
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    if (gl && gl.getExtension('WEBGL_lose_context')) {
                        gl.getExtension('WEBGL_lose_context').loseContext();
                    }
                });
                // 4. 清除画布
                if (this.ctx) {
                    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                }
            },
            //点击检测列表，点击查看点位
            async handleView(id) {
                const res = await queryCluesDataApi(id);
                if (res.code === 0) {
                    const result = res.data;
                    var yawRad = (result.center_x / this.width) * 2 * Math.PI - Math.PI;
                    var pitchRad = Math.PI / 2 - (result.center_y / this.height) * Math.PI;
                    // 将弧度转换为角度
                    var yaw = (yawRad * 180) / Math.PI;
                    var pitch = (pitchRad * 180) / Math.PI;
                    this.viewer.setHfov(20);
                  this.viewer.lookAt(pitch, yaw);

                  this.viewer.removeHotSpot(id);
                    if (this.lastHighView.id !== 0) {
                        this.viewer.removeHotSpot(this.lastHighView.id);
                        this.viewer.addHotSpot({
                            id: id,
                            pitch: pitch,
                            yaw: yaw,
                            text: result.label,
                            type: 'info',
                            cssClass: 'custom-hotspot2',
                            clickHandlerFunc: (event) => {
                                this.clickHandlerFunc(event, id, '0');
                            }
                        });
                    } else {
                        this.viewer.addHotSpot({
                            id: id,
                            pitch: pitch,
                            yaw: yaw,
                            text: result.label,
                            type: 'info',
                            cssClass: 'custom-hotspot2',
                            clickHandlerFunc: (event) => {
                                this.clickHandlerFunc(event, id, '0');
                            }
                        });
                    }
                    this.lastHighView = {
                        id: id,
                        MouseDownPitch: pitch,
                        mouseDownYaw: yaw,
                        label: result.label
                    };
                    if (this.cluePointsDic[id]) {
                        this.currentViewPoint = L.marker(this.cluePointsDic[id],
                            {   icon: this.customIcon,
                                clueId: id,
                                clueName: result.label,
                                imageId:this.currentTask.imageId,
                                pointName: this.currentTask.pointName,
                                pointId: this.currentTask.pointId,
                                clueStatus: result.status,
                              draggable: true,
                            }
                        )
                            .bindPopup(result.clue_id + ' ' + result.label)
                            .openPopup();
                    }
                } else {
                    this.$message.error(res.msg);
                }
            },
            //更改行的样式
            rowClassName({ row }) {
                const status = this.rowStatus[row.clue_id];
                if (status === 'confirmed' || status === 'mistake') {
                    return 'highlight-row'; // 确认行的样式
                }
                return '';
            },
            removePolygon(id) {
                if (!this.drawnPolygons || !this.drawnPolygons[id]) return;

                // 1. 清除整个画布
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);


            },
            //线索列表中处理线索状态
            async handleConfirmAndMistake(row, tag) {
                //1为误判，2为确认
                const id = row.clue_id;
                this.$set(this.rowStatus, id, tag === 2 ? 'confirmed' : 'mistake');
                const params = {
                    id: id,
                    status: tag
                };
                // this.currentIndex = id;
                const res = await changeClueByIdApi(params);
                if (res.code === 0) {
                    this.$message.success("截图成功！")
                    this.$set(row, 'status', tag === 2 ? 2 : 1);
                    this.$emit('handleTotalTodoCount', res.data);
                    if (tag === 1) {
                        this.viewer.removeHotSpot(id);
                        this.currentViewPoint = null;
                    }
                } else {
                    this.$message.error("截图失败！");
                }
            },
            //处理点击热点的弹框点击事件
            async handleClickConfirmAndMistake(clue_id, tag) {
                //与上一个handleConfirmAndMistake函数不同之处在于，一个是地图上直接点击，一个是列表中点击，地图上直接更改状态的，需要去找列表中对应的数据进行修订，无法直接定位到行
                //2为确认，1为误判
                const id = clue_id;
                this.$set(this.rowStatus, id, tag === 2 ? 'confirmed' : 'mistake');
                const params = {
                    id: id,
                    status: tag
                };
                // this.currentIndex = id;
                const res = await changeClueByIdApi(params);
                if (res.code === 0) {
                    const targetRow = this.clueList.find((row) => row.clue_id === id);
                    if (targetRow) {
                        // 更新行的 status 属性
                        this.$set(targetRow, 'status', tag === 2 ? 2 : 1);
                        if (tag === 1) {
                            this.viewer.removeHotSpot(id);
                            this.currentViewPoint = null;
                        }
                    }
                }else {
                    this.$message.error(res.msg);
                }
            },
            //根据全景图路径切换全景图
            async showPanorama() {
                this.initYawDegree = this.currentTask.yawDegree;
                this.yawDegree = this.currentTask.yawDegree;
                this.destroyExistingWebGLContext();
                this.handleViewerLoad();
            },
            //返回按钮的处理
            handlebtnclick() {
                this.$emit('reback', '-1');
            },
            //处理marker的点击事件
            async handleMarkerClick(task, lat, lon, markerData, marker) {
              this.allLayers.forEach((layer) => {
                if (layer.hasOwnProperty('gdPolygons')) {
                  delete layer.gdPolygons;
                }
              });
              if (this.viewer) {
                this.viewer.allRemoveHotSpot();
              }
                //this.removeAllQuanjingHotspots();
                if (this.currentTask !== task) {
                    this.currentTask = task;
                }
                //更换地图内容
                this.pointName = task.pointName;
                this.imageName = task.imageName;

                // 显示全景图
                await this.showPanorama();
                this.$emit('markerclick', this.pointName);
            },
            synchronousPosition(latlng) {
                if (latlng.length === 0) {
                    this.viewer.removeHotSpot('123456');
                } else {
                    const lat = latlng.lat.toFixed(6);
                    const lon = latlng.lng.toFixed(6);

                    const yaw_pitch = latLonToYawPitch(
                        lat,
                        lon,
                        0,
                        this.currentTask.latitude,
                        this.currentTask.longitude,
                        this.currentTask.height,
                        this.currentTask.yawDegree
                    );
                    this.viewer.removeHotSpot('123456');
                    this.viewer.addHotSpot({
                        id: '123456',
                        pitch: yaw_pitch[1],
                        yaw: yaw_pitch[0],
                        text: '',
                        type: 'info',
                        cssClass: 'crosshair'
                    });
                }
            },
            //跳转多期对比
            async handleMultiComparision() {
                const multiObjres = await getOnePointMultiComInfoApi(this.currentTask.imageId);
                if (multiObjres.code === 0) {
                    this.images = multiObjres.data;
                    if (this.images.length >= 2) {
                        this.$emit('backToMultiPanoramic', this.currentTask,this.mouseDownYaw,this.mouseDownPitch,this.currentHfov);
                    } else {
                        this.$message.warning('该线索没有多期对比数据');
                    }
                }else{
                    this.$message.error(multiObjres.msg);
                }
            },
            //三屏对比
            async handleThreeComparison() {
                const multiObjres = await getOnePointMultiComInfoApi(this.currentTask.imageId);
                if (multiObjres.code === 0) {
                    this.images = multiObjres.data;
                    if (this.images.length >= 2) {
                        this.$emit('backToThreeScreen', this.currentTask, this.mouseDownYaw, this.mouseDownPitch, this.currentHfov);
                    } else {
                        this.$message.warning('该线索没有多期对比数据');
                    }
                } else {
                    this.$message.error(multiObjres.msg);
                }
            },
            //处理提交复核
            async handleSubmitReview() {
                if (this.currentTask.status === 2){
                    this.$message.warning('该全景已提交复核，请勿重复提交')
                }else{
                    const hasStatusZero = this.filteredData.some(item => item.status === 0);
                    if (hasStatusZero) {
                        this.$message.warning('该全景存在待复核的线索，请先确认');
                    }else{
                        const params = {
                            panoramaImageId: this.currentTask.imageId
                        };
                        const res = await submitReviewApi(params);
                        if (res.code === 0) {
                            this.$message.success('提交复核成功');
                            this.$emit('refreshpage');
                        } else {
                            this.$message.error(res.msg);
                        }
                    }
                }

            },
            //关闭线索列表框
            closeDetectdialog() {
                this.dialogTableVisible = false;
                this.currentAddMaker = null;
                this.isCollapsed = false;
            },
            //刷新
            refresh() {
                this.fetchData(this.currentTask.imageId);
            },
            async modifyPointCoord() {
                const parm = {
                    id: this.currentClickObj.clickcorrentClueId,
                    longitude: this.currentClickObj.clickLongitude,
                    latitude: this.currentClickObj.clickLatitude,
                };
                const res = await submitCorrectPointApi(parm);
                if (res.code === 0) {
                    this.$message.success('地址修改成功');
                    this.correctLabelVisible = false;
                    //更新状态值
                    // this.$set(this.currentRow, 'status', 3);原来打点（纠偏）是3
                    this.$set(this.currentRow, 'status', 2);
                    if (this.currentViewPoint !== null) {
                        this.currentViewPoint = null;
                    }
                } else {
                    this.$message.error(res.msg);
                }
            },
            cancelCorrectVisible() {
                this.correctLabelVisible = false;
                this.currentAddMaker = null;
            },
            getClueStatus(status) {
                switch (status) {
                    case 1:
                        return ['#c0c4cc', '无效'];
                    case 2:
                        return ['#f5222d', '已确认'];
                    case 3:
                        // return ['#56f501', '已纠偏'];
                        return ['#f5222d', '已确认'];
                    case 0:
                        return ['#f8d22e', '待复核'];
                    default:
                        return ['#38c81a', '已核实'];
                }
            },
            isMarked(status) {
                // // 判断状态是否为 "已打点"
                // return tag === '已打点';
                //依次顺序为[查看、无效、确认、打点、录入]  控制按钮的可用状态，true为禁用,false为开启
                // 1是已判读（无效） 2是已确认 3是已打点 0是待复核
                if (status === 1) {
                    return [false, true, true, true, true];
                } else if (status === 2) {
                    return [false, true, true, false, false];
                } else if (status === 3) {
                    return [false, true, true, false, false];
                } else if (status === 5 || status === 4) {
                    return [false, true, true, true, true];
                } else {
                    //待复核
                    return [false, false, false, true, true];
                }
            },
            handleNoDevelopFun() {
                this.dialogTableVisible = false;
                this.drawRectPolygonVisible = false;
                this.dialogVisible = false;
                this.drawPolygonVisible = true;
            },

            //检测列表框条件查询
            filterData() {
                // 根据查询条件筛选数据
                let filtered = this.clueList;
                // 如果 queryClueClass 有值，则筛选 label 包含 queryClueClass 的项
                if (this.queryClueClass !== '') {
                    filtered = filtered.filter((item) => item.label === this.queryClueClass);
                    if (filtered.length === 0) {
                        this.filteredData = filtered;
                        return;
                    }
                    // 如果 queryClueStatus 有值，则筛选 status 等于 queryClueStatus 的项
                    if (this.queryClueStatus !== '') {
                        if (this.queryClueStatus == 2) {
                            filtered = filtered.filter((item) => item.status === 2 || item.status === 3);
                        } else if (this.queryClueStatus == 5) {
                            filtered = filtered.filter((item) => item.status === 5 || item.status === 4);
                        } else {
                            filtered = filtered.filter((item) => item.status === this.queryClueStatus);
                        }
                    }
                    if(this.queryClueSource!==''){
                      filtered = filtered.filter((item) => item.clue_source === 2 || item.status === 3);
                    }
                    this.filteredData = filtered;
                } else {
                    if (this.queryClueStatus !== '') {
                        if (this.queryClueStatus == 2) {
                          filtered = filtered.filter((item) => item.status === 2 || item.status === 3);
                        } else {
                          filtered = filtered.filter((item) => item.status === this.queryClueStatus);
                        }
                    }
                  if(this.queryClueSource!==''){
                    filtered = filtered.filter((item) => item.clue_source === 2 || item.status === 3);
                  }
                  this.filteredData = filtered;
                }
            },
            // Haversine公式计算两点之间的相对方位角
            calculateBearing(lat1, lon1, lat2, lon2) {
                // 将度转换为弧度
                function toRadians(degrees) {
                    return (degrees * Math.PI) / 180;
                }
                lat1 = toRadians(lat1);
                lon1 = toRadians(lon1);
                lat2 = toRadians(lat2);
                lon2 = toRadians(lon2);
                var dLon = lon2 - lon1;
                var y = Math.sin(dLon) * Math.cos(lat2);
                var x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
                var bearing = Math.atan2(y, x);
                return (bearing * 180) / Math.PI; // 转换为度
            },
            //添加全景点至全景
            addQuanjingPoint() {
                this.totalTaskList.forEach((item) => {
                    // var yaw = this.calculateBearing(item.latitude, item.longitude, this.currentTask.latitude, this.currentTask.longitude);
                    var yaw = this.calculateBearing( this.currentTask.latitude, this.currentTask.longitude,item.latitude, item.longitude);
                    // 根据需要调整yaw角度，例如，如果需要相对于point1的yawDegree调整
                    var yawDegree = this.currentTask.yawDegree || 0; // 假设point1有yawDegree属性
                    var relativeYaw = (yaw - yawDegree + 360) % 360; // 确保yaw角度在0-
                    if (relativeYaw > 360) {
                        relativeYaw = relativeYaw - 360;
                    }
                    // 为热点分配一个基础的pitch值
                    var basePitch = 0; // 可以根据需要调整
                    // 检查热点是否与其他热点的yaw值相近
                    var isCloseToOtherHotspots = this.totalTaskList.some((otherItem) => {
                        return (
                            otherItem !== item &&
                            Math.abs(this.calculateBearing(otherItem.latitude, otherItem.longitude, item.latitude, item.longitude) - relativeYaw) < 2
                        ); // 假设如果yaw相差小于2度，则认为相近
                    });

                    // 如果热点相近，动态调整pitch
                    var pitch = isCloseToOtherHotspots ? basePitch - 3 : basePitch; // 根据需要调整
                    // 创建热点对象
                    var hotSpot = {
                        id: item.imageId,
                        yaw: relativeYaw, // 使用已知的yaw
                        pitch: pitch, // 计算得到的pitch
                        text: item.pointName.match(/\d+/g),
                        type: 'scene',
                        clickHandlerFunc: (event) => {
                            this.clickHandlerFunc(event, item, '1');
                        }
                    };

                    if (this.currentTask.imageId !== item.imageId) {
                        // 添加热点到viewer
                        this.viewer.addHotSpot(hotSpot);
                    }
                });
            },
            //绘制目标多边形
            drawTargetPolygons() {
                const color = ['red', 'rgba(190, 0, 0, 0.3)'];
                this.drawPolygon(this.drawRectPoints, '', color);

            },
            //绘制所有多边形
            drawPolygons() {
                this.polygons.map((item) => {
                    if (item.id === 0) {
                        item.points = this.drawPoints;
                    }
                });
                if (this.ctx) {
                    this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                  this.drawBuffer(this.circleRadius,'yellow');
                  //this.drawBuffer(this.innerCircleRadius,'#d417d4');
                  this.drawPointCircleLocation();
                }
                this.polygons.forEach((item) => {
                    const color = ['#f7423e', 'rgba(86,245,1, 0.1)'];
                    this.drawPolygon(item.points, item.name, color);
                });
            },
            drawClues() {
                this.clueList.forEach((item) => {
                    const color = ['red', 'rgba(190, 0, 0, 0.3)'];
                    if (item.position) {
                        this.drawClue(item.position.slice(), item.label, color);
                    }
                });
            },

            drawTargetClues(){
                this.rectFrameAreaList.forEach((item) => {
                    const color = ['red', 'rgba(190, 0, 0, 0.3)'];
                    if (item.position) {
                        this.drawClue(item.position.slice(), item.label, color);
                    }
                });
            },

            //根据顶点绘制单个多边形
            drawPolygon(points, name, color) {
                const screenPoints = [];
                const isInViews = [];
                points.forEach((coord) => {
                    //将全景图坐标pitch，yaw转为屏幕坐标
                    const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                    screenPoints.push(point);
                    const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                    isInViews.push(isInView);
                });
                if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
                if (screenPoints.length === 0) return;
                this.ctx.beginPath();
                this.ctx.strokeStyle = color[0];
                this.ctx.lineWidth = 3;
                if (screenPoints.length === 1) {
                    // 绘制点
                    const [x, y] = screenPoints[0];
                    this.ctx.arc(x, y, 3, 0, Math.PI * 2); // 小圆表示点
                    this.ctx.fillStyle = 'red';
                    this.ctx.fill();
                } else if (screenPoints.length === 2) {
                    // 绘制线段
                    this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                    this.ctx.lineTo(screenPoints[1][0], screenPoints[1][1]);
                    this.ctx.stroke();
                } else {
                    // 绘制多边形
                    this.ctx.fillStyle = color[1];
                    this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                    for (let i = 1; i < screenPoints.length; i++) {
                        this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                    }
                    this.ctx.closePath(); // 闭合路径以形成多边形
                    this.ctx.stroke(); // 描边
                    this.ctx.fill(); //填充多边形
                    this.ctx.font = '16px Arial';
                    this.ctx.fillStyle = 'white';
                    const center = this.getPolygonCenterXY(screenPoints);
                    this.ctx.fillText(name, center[0] - 60, center[1]);
                }
            },
            drawClue(points, name, color) {
                const screenPoints = [];
                const isInViews = [];
                points.forEach((coord) => {
                    //将全景图坐标pitch，yaw转为屏幕坐标
                    const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                    screenPoints.push(point);
                    const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                    isInViews.push(isInView);
                });
                if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
                if (screenPoints.length === 0) return;

                if (screenPoints.length === 0) return;
                this.ctx.beginPath();
                this.ctx.strokeStyle = color[0];
                this.ctx.lineWidth = 3;

                // 绘制多边形
                this.ctx.fillStyle = color[1];
                this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                for (let i = 1; i < screenPoints.length; i++) {
                    this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                }
                this.ctx.closePath(); // 闭合路径以形成多边形
                this.ctx.stroke(); // 描边
                this.ctx.fill(); //填充多边形
                this.ctx.font = '16px Arial';
                this.ctx.fillStyle = 'white';
                const center = this.getPolygonCenterXY(screenPoints);
                this.ctx.fillText(name, center[0] - 60, center[1]);
            },
            //获取多边形的中心坐标
            getPolygonCenterXY(polygon) {
                let sumX = 0;
                let sumY = 0;
                polygon.forEach((point) => {
                    sumX += point[0];
                    sumY += point[1];
                });
                return [sumX / polygon.length, sumY / polygon.length];
            },
            // //将全景图坐标转为屏幕坐标
            // sphericalToScreen(viewer, pitch, yaw, canvas) {
            //     const currentPitch = viewer.getPitch();
            //     const currentYaw = viewer.getYaw();
            //     const currentHfov = viewer.getHfov();
            //     const currentRoll = 0;
            //     var hsPitchSin = Math.sin((pitch * Math.PI) / 180),
            //         hsPitchCos = Math.cos((pitch * Math.PI) / 180),
            //         configPitchSin = Math.sin((currentPitch * Math.PI) / 180),
            //         configPitchCos = Math.cos((currentPitch * Math.PI) / 180),
            //         yawCos = Math.cos(((-yaw + currentYaw) * Math.PI) / 180);
            //     var z = hsPitchSin * configPitchSin + hsPitchCos * yawCos * configPitchCos;
            //     if (z <= 0) {
            //         z = -z;
            //     }
            //     var yawSin = Math.sin(((-yaw + currentYaw) * Math.PI) / 180),
            //         hfovTan = Math.tan((currentHfov * Math.PI) / 360);
            //     var canvasWidth = canvas.clientWidth,
            //         canvasHeight = canvas.clientHeight;
            //     var coord = [
            //         ((-canvasWidth / hfovTan) * yawSin * hsPitchCos) / z / 2,
            //         ((-canvasWidth / hfovTan) * (hsPitchSin * configPitchCos - hsPitchCos * yawCos * configPitchSin)) / z / 2
            //     ];
            //     // Apply roll
            //     var rollSin = Math.sin((currentRoll * Math.PI) / 180),
            //         rollCos = Math.cos((currentRoll * Math.PI) / 180);
            //     coord = [coord[0] * rollCos - coord[1] * rollSin, coord[0] * rollSin + coord[1] * rollCos];
            //     // Apply transform
            //     coord[0] += canvasWidth / 2;
            //     coord[1] += canvasHeight / 2;
            //     return coord;
            // },
            // //判断点是否在当前视角范围内
            // isPointInView(viewer, pitch, yaw, canvas) {
            //     // 获取当前视角参数
            //     var currentPitch = this.viewer.getPitch(); // 当前俯仰角
            //     var currentYaw = this.viewer.getYaw(); // 当前偏航角
            //     var currentHfov = this.viewer.getHfov(); // 当前水平视场角
            //     var canvasWidth = canvas.clientWidth,
            //         canvasHeight = canvas.clientHeight;
            //
            //     var yawDiff = Math.abs(yaw - currentYaw);
            //     if (yawDiff > 180) {
            //         yawDiff = 360 - yawDiff;
            //     }
            //     var halfYaw = currentHfov / 2;
            //     if (yawDiff > halfYaw) {
            //         return false;
            //     }
            //
            //     // 计算当前pitch边界
            //     var halfVfov = (currentHfov * canvasHeight) / canvasWidth;
            //     var minPitch = currentPitch - halfVfov;
            //     var maxPitch = currentPitch + halfVfov;
            //
            //     // 判断目标点的俯仰角是否在当前视角范围内
            //     if (pitch < minPitch || pitch > maxPitch) {
            //         return false;
            //     }
            //     return true;
            // },
            //新增不检测区域
            handlePostFrameArea() {
                let indexArray = this.polygons.map((item) => Number(item.name.split('_').pop()));
                indexArray = indexArray.filter((item) => Number.isFinite(item));
                if (indexArray.length === 0) indexArray = [0];
                const index = Math.max(...indexArray) + 1;
                const planePoints = this.getPlaneCoordinate(this.drawPoints);
                const para = {
                    polygon: this.drawPoints,
                    pointId: this.currentPointId,
                    name: this.currentTask.pointName + '_' + index,
                    pixel: planePoints,
                    areaType: 0
                };
                postFrameAreaApi(para)
                    .then((res) => {
                        if (res.code === 0) {
                            this.$message.success('新增成功');
                            this.drawPoints = [];
                            this.getFrameAreaList();
                        } else {
                            this.$message.error(res.msg);
                        }
                    })
                    .catch((err) => {
                        this.$message.error(err);
                    });
            },
            //获取不检测区域列表
            getFrameAreaList() {
                getFrameAreaListApi({ pointId: this.currentPointId, imageId: this.currentTask.imageId })
                    .then((res) => {
                        if (res.code === 0) {
                            //更新不检测区域
                            this.frameAreaList = res.data.no_detection_area_list;
                            this.polygons = this.frameAreaList.map((item) => ({
                                id: item.id,
                                points: JSON.parse(item.polygon),
                                name: item.name
                            }));
                            this.polygons.push({ id: 0, points: [], name: '' });
                            this.drawPolygons();
                            // //更新目标区域
                            // this.rectFrameAreaList = res.data.polygon_list;
                            // this.targetPolygons = this.rectFrameAreaList.map((item) => ({
                            //     id: item.id,
                            //     points: JSON.parse(item.polygon),
                            //     name: item.name
                            // }));
                            // this.targetPolygons.push({ id: 0, points: [], name: '' });
                            // this.drawTargetPolygons();

                            // this.getTargetArea() //获取以前的人工添加的目标区域
                        } else {
                            this.$message.error(res.msg);
                        }
                    })
                    .catch((err) => {
                        this.$message.error(err);
                    });

            },
            getTargetArea(){
                getTargetAreaListApi({ imageId: this.currentTask.imageId })
                    .then((res) => {
                        if (res.code === 0) {
                            //更新目标区域
                            this.rectFrameAreaList = res.data.map((item) => (
                                {
                                    id: item.id,
                                    position: item.polygon,
                                    label: item.name
                                }
                            ));;
                            this.drawTargetClues();
                        } else {
                            this.$message.error(res.msg);
                        }
                    })
                    .catch((err) => {
                        this.$message.error(err);
                    });
            },

            //删除不检测区域
            deleteFrameArea(id) {
                this.$confirm('此操作将永久删除该区域, 是否继续?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                })
                    .then(() => {
                        deleteFrameAreaApi({ id: id })
                            .then((res) => {
                                if (res.code === 0) {
                                    if (this.ctx) {
                                        this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                                    }
                                    this.$message.success('删除成功');
                                    this.getFrameAreaList();
                                } else {
                                    this.$message.error(res.msg);
                                }
                            })
                            .catch((err) => {
                                this.$message.error(err);
                            });
                    })
                    .catch(() => {
                        this.$message({ type: 'info', message: '已取消删除' });
                    });
            },
            deleteTargetAreaClue(id) {
                this.$confirm('此操作将永久删除该区域, 是否继续?', '提示', {
                    confirmButtonText: '确定',
                    cancelButtonText: '取消',
                    type: 'warning'
                })
                    .then(() => {
                        deleteTargetClueApi({ clue_id: id })
                            .then((res) => {
                                if (res.code === 0) {
                                    if (this.ctx) {
                                        this.ctx.clearRect(0, 0, this.ctx.canvas.width, this.ctx.canvas.height);
                                    }
                                    this.$message.success('删除成功');
                                    //this.getTargetArea();
                                } else {
                                    this.$message.error(res.msg);
                                }
                            })
                            .catch((err) => {
                                this.$message.error(err);
                            });
                    })
                    .catch(() => {
                        this.$message({ type: 'info', message: '已取消删除' });
                    });
            },

            //将pitch，yaw坐标转为平面坐标
            getPlaneCoordinate(coords) {
                const planeCoords = [];
                coords.forEach((point) => {
                    const x = (((point[1] * Math.PI) / 180 + Math.PI) / (2 * Math.PI)) * this.width;
                    const y = ((Math.PI / 2 - (point[0] * Math.PI) / 180) / Math.PI) * this.height;
                    const tupleString = [];
                    tupleString.push(parseFloat(x.toFixed(2)));
                    tupleString.push(parseFloat(y.toFixed(2)));
                    planeCoords.push(tupleString);
                });
                planeCoords.push(planeCoords[0]);
                return planeCoords;
            },
            isPointInBuffer(targetYaw, targetPitch) {
                // 将目标yaw/pitch转换为屏幕坐标
                const targetPoint = sphericalToScreen(
                    this.viewer,
                    targetPitch,
                    targetYaw,
                    this.canvas
                );

                // 使用Canvas的isPointInPath方法判断点是否在路径内
                this.ctx.beginPath();

                // 重新构建缓冲区路径
                const bufferPoints = [];
                this.bufferPitch = Math.atan(112 / (this.circleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);

                for (let i = -90; i <= 90; i++) {
                    const point = sphericalToScreen(this.viewer, -this.bufferPitch, this.currentYaw + i, this.canvas);
                    bufferPoints.push(point);
                }

                this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
                for (let i = 1; i < bufferPoints.length; i++) {
                    this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
                }

                // 闭合路径以确保isPointInPath正确工作
                this.ctx.closePath();

                // 判断目标点是否在路径内
                return this.ctx.isPointInPath(targetPoint[0], targetPoint[1]);
            },
            //绘制700m缓冲区
            drawBuffer(circleRadius,color) {
                this.ctx.beginPath();
                this.ctx.strokeStyle = color;
                this.ctx.lineWidth = 3;
                const bufferPoints = [];
                this.bufferPitch = Math.atan(112 / (circleRadius * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
                for (let i = -90; i <= 90; i++) {
                    const point = sphericalToScreen(this.viewer, -this.bufferPitch, this.currentYaw + i, this.canvas);
                    bufferPoints.push(point);
                }
                this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
                for (let i = 1; i < bufferPoints.length; i++) {
                    this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
                }
                this.ctx.stroke();
            },
            judeLuRuButton(status) {
                return !(status == 2 || status == 3);
            },
            handleWriteResult(row) {
                this.form.clue_id = row.clue_id;
                this.writeResultDialogVisible = true;
            },
            //点击提交按钮
            async submitWriteResult() {
                const para = {
                    id: this.form.clue_id,
                    status: parseInt(this.form.clue_valid_judge),
                    verification_conclusion: this.form.clue_verify_result
                };
                const res = await clueEntryApi(para);
                if (res.code === 0) {
                    this.$message.success(res.msg);
                    this.writeResultDialogVisible = false;
                    this.form.clue_id = '';
                    this.form.clue_valid_judge = '';
                    this.form.clue_verify_result = '';
                } else {
                    this.$message.error(res.msg);
                }
            },
            //一键归位
            handleResetViewYaw() {
                this.viewer.setYaw(-this.initYawDegree);
                this.viewer.setPitch(0);
                this.viewer.setHfov(120);
                this.$refs.smallMap.resetMapZoom();
            },
            //处理自动播放远近功能
            handleAngleChange() {
                if (this.angleRadio === '远') {
                    this.viewer.setHfov(12);
                    this.viewer.setPitch(-14);
                    this.handleSpeedChange(2);
                } else if (this.angleRadio === '近') {
                    this.viewer.setHfov(70);
                    this.viewer.setPitch(-60);
                    this.handleSpeedChange(5);
                } else {
                    this.viewer.setHfov(120);
                }
            },
            handleSpeedChange(speed) {
                this.rotationSpeed = Number(speed);
                this.updateRotateSpeed();
            },
            //控制列表的收起
            toggleCollapse() {
                this.isCollapsed = !this.isCollapsed;
            },

            startDrag(e) {
                if (e.target.closest('.title')) {
                    this.isDragging = true;
                    this.dragStartPos = {
                        x: e.clientX,
                        y: e.clientY
                    };
                    document.addEventListener('mousemove', this.handleDrag);
                    document.addEventListener('mouseup', this.stopDrag);
                }
            },

            handleDrag(e) {
                if (!this.isDragging) return;
                const dx = e.clientX - this.dragStartPos.x;
                const dy = e.clientY - this.dragStartPos.y;
                this.position = {
                    right: Math.max(10, this.position.right - dx), // 最小保留10px右边距
                    top: Math.max(10, this.position.top + dy) // 最小保留10px上边距
                };
                this.dragStartPos = {
                    x: e.clientX,
                    y: e.clientY
                };
            },

            stopDrag() {
                this.isDragging = false;
                document.removeEventListener('mousemove', this.handleDrag);
                document.removeEventListener('mouseup', this.stopDrag);
            },
          drawPointCircleLocation() {
            if (this.currentPitch < 0) {
              this.ctx.beginPath();
              this.ctx.strokeStyle = 'yellow';
              this.ctx.lineWidth = 3;
              const bufferPoints = [];
              const bufferPitch = Math.atan(112 / (5 * Math.cos((Math.abs(0) * Math.PI) / 180))) * (180 / Math.PI);
              for (let i = -180; i <= 180; i++) {
                const point = sphericalToScreen(this.viewer, -bufferPitch, this.currentYaw + i, this.canvas);
                bufferPoints.push(point);
              }
              this.ctx.moveTo(bufferPoints[0][0], bufferPoints[0][1]);
              for (let i = 1; i < bufferPoints.length; i++) {
                this.ctx.lineTo(bufferPoints[i][0], bufferPoints[i][1]);
              }
              this.ctx.stroke();
            }

          },
            async handleViewerLoad() {
              var specificElement = document.getElementById('panoramaContainer');
              specificElement.addEventListener('contextmenu', function (e) {
                e.preventDefault();
              });
              const oldCompass = specificElement.querySelector('.pnlm-compass');
              if (oldCompass) {
                const parent = oldCompass.parentElement;
                if (parent) {
                  parent.removeChild(oldCompass);
                }
              }
                this.viewer = pannellum.viewer('panoramaContainer', {
                    type: 'multires',
                    sceneFadeDuration: 1000,
                    autoLoad: true,
                    hfov: 300, // 初始的水平视场角
                    minHfov: this.minHfov, // 最小水平视场角
                    vOffset: 0, // 垂直偏移，可按需调整
                    yaw: -this.yawDegree,
                    pitch: 0,
                    maxHfov: this.maxHfov, // 最大水平视场角
                    multiRes: {
                        basePath: '/panoramaUrl/static/layers/' + this.batchNumber + '/' + this.currentTask.imageId,
                        path: '/%l/%s%y_%x',
                        fallbackPath: '/fallback/%s',
                        extension: 'png',
                        tileResolution: this.currentTask.tileResolution? this.currentTask.tileResolution : 512,
                        maxLevel: this.currentTask.maxLevel ? this.currentTask.maxLevel:5,
                        cubeResolution: this.currentTask.cubeResolution?this.currentTask.cubeResolution : 4576
                    },
                    autoRotate: 0,
                    autoRotateInactivityDelay: 0
                });

                // 设置初始的正北方向
                this.viewer.on('mousedown', this.handleMouseDown);
                // 场景加载完成时添加图层选择节点
                this.viewer.on('load', () => {
                    this.afterLoadPannellum = true;
                });
                //全程监听yaw的值,等待加载完成
                this.viewer.on('animatefinished', (event) => {
                    localStorage.setItem('initYaw', this.currentYaw);
                    localStorage.setItem('initPitch', this.currentPitch);
                    localStorage.setItem('initHfov', this.currentHfov);
                    this.drawMeasureLine();
                    this.drawMeasureArea();

                });
                //全程监听yaw的值
                this.viewer.on('rendercanvas', (event) => {
                    this.currentYaw = this.viewer.getYaw();
                    this.currentPitch = this.viewer.getPitch();
                    this.hideButtons();
                    this.drawPolygons();
                  this.allLayers.forEach((child) => {
                    if (child.check) {
                      this.drawGdPolygons();
                    }
                  });
                    if (this.currentHfov !== 100 && this.currentHfov !== 0 && this.isAutoRotating) {
                        this.viewer.setHfov(this.currentHfov);
                    }
                    updateZoomButtonsState(this.viewer, this.minHfov, this.maxHfov)
                    this.disableMouseMove = false;
                });
                this.canvas = this.$refs.canvas;
                this.canvas.width = this.viewer.getContainer().clientWidth;
                this.canvas.height = this.viewer.getContainer().clientHeight;
                this.ctx = this.canvas.getContext('2d');
                this.handleResize = () => {
                  this.isScreenFull = screenfull.isFullscreen;
                  if (this.canvas) {
                    this.canvas.width = this.viewer.getContainer().clientWidth;
                    this.canvas.height = this.viewer.getContainer().clientHeight;
                    // 可选：重新绘制canvas内容（如之前的线条、多边形）

                  }

              };
              window.addEventListener('resize', this.handleResize);
              // 关键：监听全景图容器的 click 事件（事件会穿透 Canvas）
              specificElement.addEventListener('mousedown', () => {
                this.isMouseMoved = false; // 鼠标按下时，标记为未移动
                this.selectedGdPolygon = null;
              });
              // 2. 监听 mousemove：如果鼠标移动，标记为拖动
              specificElement.addEventListener('mousemove', (e) => {
                // 只有鼠标按下时（buttons === 1 表示左键按住）移动，才视为拖动
                if (e.buttons === 1) {
                  this.isMouseMoved = true;
                }
                this.selectedGdPolygon = null;
              });
              // 3. 监听 click：仅当鼠标未移动时，才判断图斑点击
              specificElement.addEventListener('click', (e) => {
                if (this.isMouseMoved) {
                  this.isMouseMoved = false; // 重置状态
                  return;
                }
                // 纯点击（无拖动），执行图斑命中判断
                this.handleContainerClick(e);
              });

              // this.addQuanjingPoint();
                await this.fetchData(this.currentTask.imageId);
                this.getFrameAreaList();


            },
          // 全景图容器点击事件：判断是否命中图斑
          handleContainerClick(e) {
            const container = this.viewer.getContainer();
            const rect = this.canvas.getBoundingClientRect(); // 获取 Canvas 坐标范围
            // 计算点击坐标（相对 Canvas 的坐标，和图斑绘制坐标一致）
            const clickX = e.clientX - rect.left;
            const clickY = e.clientY - rect.top;
            // 校验坐标是否在 Canvas 内（避免点击容器边缘无效区域）
            if (clickX < 0 || clickX > this.canvas.width || clickY < 0 || clickY > this.canvas.height) {
              return;
            }
            let selected = null;
            // 从绘制栈顶向下遍历（优先选中顶层图斑）
            for (let i = this.gdPolygonDrawStack.length - 1; i >= 0; i--) {
              const polygon = this.gdPolygonDrawStack[i];
              // 复用预存的路径，判断点击是否命中
              polygon.path(); // 生成图斑路径（仅用于检测，不重新绘制）
              if (this.ctx.isPointInPath(clickX, clickY)) {
                selected = polygon;
                break; // 找到顶层命中图斑，退出遍历
              }
            }
            // 更新选中状态并重新绘制高亮
            this.selectedGdPolygon = selected;
            this.drawGdPolygons(); // 重新绘制图斑（应用高亮样式）
          },
          // 绘制业务图层
            async drawGdPolygons() {
              this.gdPolygonDrawStack = [];
              for (let i = 0; i < this.allLayers.length; i++){
                  const child = this.allLayers[i]
                  if( child.check ){
                      // 1. 若正在请求，等待后跳过
                      if (child.isLoading) {
                          await new Promise(resolve => {
                              const timer = setInterval(() => {
                                  if (!child.isLoading) {
                                      clearInterval(timer);
                                      resolve();
                                  }
                              }, 100);
                          });
                          continue;
                      }
                    if (!child.gdPolygons) {
                      child.isLoading = true; // 2. 标记为请求中
                      try {
                        const res = await this.getLayerBuffer(child);
                        child.gdPolygons = res.points; // 3. 赋值后清除标记
                      } catch (error) {
                        console.error('请求失败：', error);
                      } finally {
                        child.isLoading = false;
                      }
                    }

                      child.gdPolygons.forEach((item) => {
                          const color = child.color;
                          const points = item.points
                          const screenPoints = [];
                          const isInViews = [];
                          points.forEach((coord) => {
                              //将全景图坐标pitch，yaw转为屏幕坐标
                              const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                              screenPoints.push(point);
                              const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                              isInViews.push(isInView);
                          });
                          if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
                          if (screenPoints.length === 0) return;
                          // 关键：记录当前图斑到绘制栈（后绘制的在栈顶，视觉上层）
                          this.gdPolygonDrawStack.push({
                          layerId: child.id,
                          polygonItem: item,
                          screenPoints: screenPoints,
                          // 预存路径信息（避免点击时重复计算）
                          path: () => {
                            this.ctx.beginPath();
                            this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                            for (let i = 1; i < screenPoints.length; i++) {
                              this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                            }
                            this.ctx.closePath();
                          }
                        });
                          this.ctx.beginPath();
                          this.ctx.strokeStyle = 'red';
                          this.ctx.lineWidth = 2;
                          // 绘制多边形
                          this.ctx.fillStyle = 'transparent';
                          this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                          for (let i = 1; i < screenPoints.length; i++) {
                              this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                          }
                          this.ctx.closePath(); // 闭合路径以形成多边形
                          this.ctx.stroke(); // 描边
                          this.ctx.fill(); //填充多边形
                          this.ctx.font = '16px Arial';
                      });
                  }
              }
              const isSelected = this.selectedGdPolygon && this.selectedGdPolygon.polygonItem
              this.ctx.beginPath();
              if (isSelected) {
                this.ctx.strokeStyle = this.highlightColor;
                this.ctx.lineWidth = 4;
                // 绘制多边形
                this.ctx.fillStyle = 'transparent';
                const tempPoint = this.selectedGdPolygon.screenPoints
                this.ctx.moveTo(tempPoint[0][0], tempPoint[0][1]);
                for (let i = 1; i < tempPoint.length; i++) {
                  this.ctx.lineTo(tempPoint[i][0], tempPoint[i][1]);
                }
                this.ctx.closePath(); // 闭合路径以形成多边形
                this.ctx.stroke(); // 描边
                this.ctx.fillStyle = 'rgba(255,0,0, 0.2)'; // 填充颜色
                this.ctx.fill(); //填充多边形
                this.ctx.font = '16px Arial';
                this.ctx.fillStyle = 'blue';
              }
              // })
            },
            //获取全部需叠加在全景图层
            async getBufferGD(){
              let layerRes = await getBufferLayerApi()
              if(layerRes.code === 0){
                let tempLayers = layerRes.data;
                for(let i = 0; i < tempLayers.length;i++){
                  let child = tempLayers[i]
                  child.check = false;
                  child.color= window.config.colorList[i] || '#09c9ea'
                }
                this.allLayers = tempLayers;
                // const queryPromises = tempLayers.map(layerInfo =>
                //     this.getLayerBuffer(layerInfo)
                // )
                // // 等待所有图层查询完成
                // const pageResults = await Promise.all(queryPromises);
                // if( pageResults && pageResults.length){
                //   for( let i = 0 ; i < tempLayers.length;i++){
                //      let child = tempLayers[i]
                //       for( let j = 0; j < pageResults.length;j++){
                //         let tempChild = pageResults[j]
                //          if(child.id === tempChild.id){
                //            child.gdPolygons = tempChild.points
                //          }
                //       }
                //   }
                // }
              }else{
                this.$message.error(layerRes.msg);
              }
            },
           getLayerBuffer( param ){
              let op = {
                panorama_image_id: this.currentTask.imageId,
                resource_id: param.id
              }
               return getPointBufferLayerApi(op).then((res) => {
                   if (res.code === 0) {
                       const gdPolygons = res.data.map((item) => ({ points: item }));
                       return { points: gdPolygons, id: param.id }; // 直接 return 结果
                   } else {
                       return { points: [], id: param.id }; // 错误时也 return 结果
                   }
               }).catch((error) => {
                   // 捕获异常，返回兜底结果
                   return { points: [], id: param.id };
               });
            },

            handleMeasure(type) {
                this.activeToolBarType = type;
                this.drawPolygonFlag = false;
                this.editFlag = false;
                this.drawRectPolygonFlag= false;
                if (this.activeToolBarType === 'measureDistance'){
                    this.isMeasureDistance = true

                } else if (this.activeToolBarType === 'measureArea'){
                    this.isMeasureArea = true
                }
            },
            judgePoints(points){
                const screenPoints = [];
                const isInViews = [];
                points.forEach((coord) => {
                    //将全景图坐标pitch，yaw转为屏幕坐标
                    const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                    screenPoints.push(point);
                    const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                    isInViews.push(isInView);
                });
                if (isInViews.indexOf(true) === -1) return []; //所有点均不在视角范围内，不绘制多边形
                if (screenPoints.length === 0) return [];
                return screenPoints
            },
            drawMeasureLine() {
                const color = ['red', 'rgba(190, 0, 0, 0.3)'];
                this.drawLine(this.measureDistancePoints, color);
            },
            drawLine(points,color){
                const screenPoints = this.judgePoints(points)
                // 没有点或只有1个点，不绘制线（可保留点绘制）
                if (screenPoints.length < 2) {
                    if (screenPoints.length === 1) {
                        // 绘制单个点
                        const [x, y] = screenPoints[0];
                        this.ctx.beginPath();
                        this.ctx.arc(x, y, 3, 0, Math.PI * 2);
                        this.ctx.fillStyle = 'red';
                        this.ctx.fill();
                    }
                    return;
                }
                // 点大于等于2个时，绘制折线（连接所有连续点）
                this.ctx.beginPath();
                this.ctx.strokeStyle = color[0]; // 线的颜色
                this.ctx.lineWidth = 3; // 线的宽度
                // 从第一个点开始，依次连接所有后续点
                this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]); // 起点
                for (let i = 1; i < screenPoints.length; i++) {
                    this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]); // 连接到第i个点
                }
                this.ctx.stroke(); // 绘制线条
                if (!this.isMeasureDistance){
                    const points = []
                    for (let i = 0; i < this.measureDistancePoints.length; i++) {
                        const coor = this.measureDistancePoints[i]
                        const drawPoint = imageToLatLon(this.currentTask.latitude, this.currentTask.longitude, this.currentTask.height, coor[1], coor[0], this.currentTask.yawDegree)
                        points.push(L.latLng(drawPoint[0], drawPoint[1]));
                    }
                    const MEASURERESULT = calculateTotalDistance(points)
                    this.ctx.font = '16px Arial';
                    this.ctx.fillStyle = 'white';
                    this.ctx.fillText(`${MEASURERESULT.toFixed(2)}米`, screenPoints[screenPoints.length - 1][0]+1, screenPoints[screenPoints.length - 1][1]+1);
                }
            },
            drawMeasureArea() {
                const color = ['red', 'rgba(190, 0, 0, 0.3)'];
                const screenPoints = [];
                const isInViews = [];
                this.measureAreaPoints.forEach((coord) => {
                    //将全景图坐标pitch，yaw转为屏幕坐标
                    const point = sphericalToScreen(this.viewer, coord[0], coord[1], this.canvas);
                    screenPoints.push(point);
                    const isInView = isPointInView(this.viewer, coord[0], coord[1], this.canvas);
                    isInViews.push(isInView);
                });
                if (isInViews.indexOf(true) === -1) return; //所有点均不在视角范围内，不绘制多边形
                if (screenPoints.length === 0) return;
                this.ctx.beginPath();
                this.ctx.strokeStyle = color[0];
                this.ctx.lineWidth = 3;
                if (screenPoints.length === 1) {
                    // 绘制点
                    const [x, y] = screenPoints[0];
                    this.ctx.arc(x, y, 3, 0, Math.PI * 2); // 小圆表示点
                    this.ctx.fillStyle = 'red';
                    this.ctx.fill();
                } else if (screenPoints.length === 2) {
                    // 绘制线段
                    this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                    this.ctx.lineTo(screenPoints[1][0], screenPoints[1][1]);
                    this.ctx.stroke();
                } else {
                    // 绘制多边形
                    this.ctx.fillStyle = color[1];
                    this.ctx.moveTo(screenPoints[0][0], screenPoints[0][1]);
                    for (let i = 1; i < screenPoints.length; i++) {
                        this.ctx.lineTo(screenPoints[i][0], screenPoints[i][1]);
                    }
                    this.ctx.closePath(); // 闭合路径以形成多边形
                    this.ctx.stroke(); // 描边
                    this.ctx.fill(); //填充多边形

                }
                if (!this.isMeasureArea){
                    const points = []
                    for (let i = 0; i < this.measureAreaPoints.length; i++) {
                        const coor = this.measureAreaPoints[i]
                        const drawPoint = imageToLatLon(this.currentTask.latitude, this.currentTask.longitude, this.currentTask.height, coor[1], coor[0], this.currentTask.yawDegree)
                        points.push(L.latLng(drawPoint[0], drawPoint[1]));
                    }
                    const MEASURERESULT = calculateTotalArea(points)
                    this.ctx.font = '16px Arial';
                    this.ctx.fillStyle = 'white';
                    const center = this.getPolygonCenterXY(screenPoints);
                    this.ctx.fillText(`${MEASURERESULT.toFixed(2)}平方米`, center[0] - 60, center[1]);
                }
            },
            handleClear(){
                this.measureDistancePoints = []
                this.measureAreaPoints = []
                this.activeToolBarType = ''
            },
          async getClueNameList() {
            const classNameListResponse = await getEnumOptionApi('Class_Name')
            if (classNameListResponse.code === 0) {
              classNameListResponse.data.Class_Name.map(item => {
                this.classList.push(item.name)
              })
            }
          }
        },
        async mounted() {
          await this.getClueNameList();
            this.pointId = this.$route.query.pointId;
            this.getBufferGD();
            this.showSmallMap = true;

            // 全景图对象
            if (this.currentObj.imageId) {
                // this.currentIndex = 1
                this.currentTask = this.currentObj; //在初始传递组件和点击marker的时候要更新currentTask，选择当前最新image_id进行提价复核,否则会提交到之前的image_id
                this.imageName = this.currentObj.imageName;
                this.pointName = this.currentObj.pointName;
                this.yawDegree = this.currentObj.yawDegree; //这个是为了实时计算偏向角
                this.initYawDegree = this.currentObj.yawDegree; //这个是为了归位的
                await this.handleViewerLoad();
                this.isShowPanoramaList = true;
            }
            // 监听窗口大小改变，screenfull.isFullscreen的值为是否全屏，若是则true，反之false
            window.onresize = () => {
                this.isScreenFull = screenfull.isFullscreen;
                if (this.canvas) {
                    this.canvas.width = this.viewer.getContainer().clientWidth;
                    this.canvas.height = this.viewer.getContainer().clientHeight;
                }
            };
            this.$nextTick(() => {
                if (this.$refs.smallMap && this.currentTask) {
                    this.$refs.smallMap.focusOnTask(this.currentTask, 18);
                }
            });
        },
        computed: {
            calculateTableNum() {
                return this.filteredData.length;
            },
            formattedShotTime() {
                const timeMatch = this.currentTask?.imageName?.match(/(\d{4})(\d{2})(\d{2})\d{6}/)
                return timeMatch ? `${timeMatch[1]}-${timeMatch[2]}-${timeMatch[3]}` : '未知日期'
            }
        },
        watch: {
            currentObj: {
                async handler(newVal) {
                    this.destroyExistingWebGLContext()
                    if (newVal.imageId) {
                      this.allLayers.forEach((layer) => {
                        if (layer.hasOwnProperty('gdPolygons')) {
                          delete layer.gdPolygons;
                        }
                      });
                        this.currentTask = newVal; //在初始传递组件和点击marker的时候要更新currentTask，选择当前最新image_id进行提价复核,否则会提交到之前的image_id
                        this.imageName = newVal.imageName;
                        this.pointName = newVal.pointName;
                        this.removeAllHotspots();
                        this.removeAllQuanjingHotspots();
                        await this.showPanorama();
                        await this.getFrameArea();
                    }
                }
            },
            clueList: {
                handler() {
                    this.filteredData = this.clueList;
                }
            },
            drawPolygonFlag: {
                handler(newVal) {
                    if (!newVal) {
                        if (this.drawPoints.length < 3) {
                            this.$message({ message: '请至少选择三个点', type: 'warning' });
                            this.drawPoints = [];
                            this.drawPolygons();
                        } else {
                            this.handlePostFrameArea();
                        }
                    }
                }
            },
            drawRectPolygonFlag: {
                handler(newVal) {
                    if (!newVal) {
                        if (this.drawRectPoints.length < 3) {
                            this.$message({ message: '请至少选择三个点', type: 'warning' });
                            this.drawRectPoints = [];
                            this.drawTargetPolygons();
                        } else {
                            this.targetLabelVisible = true
                            // this.handleTargetFrameArea();
                        }
                    }
                }
            },
            isMeasureArea: {
                handler(newVal) {
                    if (!newVal) {
                        if (this.measureAreaPoints.length < 3) {
                            this.$message({ message: '请至少选择三个点', type: 'warning' });
                            this.measureAreaPoints = [];
                            // this.drawPolygons();
                        }
                    }
                }
            }
        }
    };
</script>

<style scoped>
    @import '@/css/pannellum.css';
    @import '@/assets/css/pannellumCommon.css';
    #overlay {
        z-index: 1000;
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none; /* 确保不会干扰Pannellum的交互 */
    }

    ::v-deep .transparent-dialog .el-dialog__headerbtn .el-icon-close:hover {
        background-color: transparent;
    }

    #hotspot-buttons {
        display: none;
        position: absolute;
        z-index: 100;
        background-color: rgba(0, 0, 0, 0.6);
    }

    #hotspot-buttons button {
        margin: 5px;
        padding: 5px 10px;
        cursor: pointer;
        border: none;
        background: none;
        color: white;
    }

    #hotspot-buttons button :hover {
        color: #2db6f4;
    }
    .close-chahao {
        position: absolute;
        top: 5px;
        right: 0px;
        z-index: 999;
    }
    .close-chahao-btn {
        padding: 7px 7px;
        margin-right: 5px;
        background-color: rgba(0, 0, 0, 0.3);
        color: white;
        border: none;
    }
    .detectlist,
    .undetected-region-list {
        background-color: rgba(0, 0, 0, 0.4);
        box-shadow: none;
        z-index: 999;
        color: #fff;
        position: absolute;
        width: 480px;
        height: 500px;
        overflow-y: auto;
        padding: 10px;
        display: flex;
        flex-direction: column;
        min-height: 40px;
        cursor: grab;
    }

    .detectlist .title,
    .undetected-region-list .title {
        display: flex;
        text-align: center;
        border-bottom: 1px solid #fff;
        padding-bottom: 10px;
    }

    .detectlist .title span,
    .undetected-region-list .title span {
        text-align: center;
        font-weight: 700;
        width: 98%;
    }

    ::v-deep .el-button--small.is-circle {
        padding: 4px;
    }

    ::v-deep .el-table::before {
        left: 0;
        bottom: 0;
        width: 100%;
        height: 0px;
    }

    ::v-deep .transparent-dialog {
        background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
        box-shadow: none; /* 可选，移除阴影 */
        z-index: 999;
        color: #fff;
    }

    ::v-deep .el-dialog {
        background-color: rgba(0, 0, 0, 0.4); /* 半透明背景 */
        box-shadow: none; /* 可选，移除阴影 */
        z-index: 999;
        color: #fff;
        position: absolute;
        right: 50px;
        width: 360px;
    }

    ::v-deep .el-dialog__body {
        height: 200px;
        overflow-y: auto;
    }

    ::v-deep .el-table,
    ::v-deep.el-table tr,
    ::v-deep .el-table th,
    ::v-deep.el-table th.el-table__cell {
        background-color: rgba(0, 0, 0, 0.1); /* 半透明背景 */
        box-shadow: none; /* 可选，移除阴影 */
        z-index: 999;
        color: #fff;
        overflow-y: auto;
    }

    ::v-deep .el-table__body tr:hover > td {
        background-color: rgba(0, 0, 0, 0.6) !important;
    }

    ::v-deep .el-dialog__header,
    ::v-deep .el-dialog__header {
        text-align: center;
        font-weight: 700;
        border-bottom: 1px solid #fff;
    }

    ::v-deep .el-dialog__title,
    ::v-deep .el-dialog__title {
        color: #fff;
        font-size: 16px;
    }

    ::v-deep .gt-od-list-data .el-dialog__body {
        padding: 10px; /* 根据需要调整内边距 */
        color: #fff;
    }

    ::v-deep .label-dialog .el-dialog {
        position: absolute;
        /*width: 400px;*/
        left: 50%;
        margin-left: -200px;
        background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
        box-shadow: none; /* 可选，移除阴影 */
        z-index: 9999;
        color: #fff;
        top: 100px;
    }

    ::v-deep .label-dialog .el-dialog__body {
        height: 30%;
    }

    ::v-deep .gt-toolbar-right {
        position: absolute;
        right: 10px;
        top: 250px;
        width: 40px;
        z-index: 99999;
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        margin-bottom: -10px;
    }

    ::v-deep .gt-toolbar-right div {
        width: 40px;
        height: 40px;
        cursor: pointer;
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
    }

    ::v-deep .gt-toolbar-right .gt-alarms-list img {
        width: 24px;
        height: 24px;
    }

    ::v-deep .gt-toolbar-right .gt-alarms-text span {
        font-size: 12px;
        color: #fff;
        line-height: 1.2;
        user-select: none;
    }

    .analysis-result-content {
        color: #fff;
        font-size: 14px;
        line-height: 1.6;
        white-space: pre-wrap;
        word-break: break-word;
        max-height: 60vh;
        overflow-y: auto;
    }

    .analysis-result-empty {
        color: rgba(255, 255, 255, 0.7);
        font-size: 14px;
        text-align: center;
        padding: 20px 0;
    }

    ::v-deep .transparent-dialog .el-dialog__header,
    .label-dialog .el-dialog__header {
        text-align: center;
        font-weight: 700;
        border-bottom: 1px solid #fff;
    }

    ::v-deep .transparent-dialog .el-dialog__title,
    .label-dialog .el-dialog__title {
        color: #fff;
        font-size: 16px;
    }

    ::v-deep .transparent-dialog .el-dialog__body {
        padding: 10px; /* 根据需要调整内边距 */
        color: #fff;
    }

    ::v-deep .label-dialog .el-form-item__label {
        color: #fff;
        width: 100px;
        text-align: left;
    }

    ::v-deep .pannellum-layer {
        z-index: 9999;
        position: fixed;
        right: 3%;
        top: 3%;
    }

    ::v-deep .el-radio .el-radio__input .el-radio__inner {
        border-radius: 2px;
    }

    ::v-deep .custom-hotspot {
        width: 25px;
        height: 40px;
        background-image: url('@/assets/images/marker-icon-blue.png');
        background-size: 100% 100%;
        position: absolute;
        transform: translate(-50%, -50%);
        z-index: 999;
    }

    ::v-deep .custom-hotspot2 {
        width: 25px;
        height: 40px;
        background-image: url('@/assets/images/marker-icon-red.png');
        background-size: 100% 100%;
        position: absolute;
        transform: translate(-50%, -50%);
        z-index: 999;
    }

    ::v-deep .el-radio .el-radio__input.is-checked .el-radio__inner::after {
        box-sizing: content-box;
        content: '';
        transition: transform 0.15s ease-in 0.05s;
        transform-origin: center;
        transform: rotate(-45deg) scaleY(1);
        width: 6px;
        height: 3px;
        border: 2px solid white;
        border-top: transparent;
        border-right: transparent;
        text-align: center;
        display: block;
        position: absolute;
        top: 18%;
        left: 18%;
        vertical-align: middle;
        border-radius: 0;
        background: none;
    }

    ::v-deep .gt-img-desc {
        width: 100%;
        text-overflow: clip;
        overflow: hidden;
        height: 20px;
        line-height: 20px;
        white-space: nowrap;
        text-align: center;
        font-size: 10px;
        color: #fff;
        text-shadow: 3px 3px 3px #000;
    }

    ::v-deep div.pnlm-tooltip span {
        visibility: visible;
        width: 100px;
        background-color: rgba(0, 0, 0, 0);
    }

    ::v-deep .map-containerlarge {
        position: absolute;
        bottom: 0; /* 距离底部10px */
        left: 0; /* 距离左侧10px */
        width: 30%; /* 设定宽度 */
        height: calc(100% - 60px);
        z-index: 9999999;
        border: 1px solid #fff;
        display: flex;
        flex-direction: column;
    }

    ::v-deep .leaflet-control-attribution {
        display: none !important;
    }

    .gt-reback {
        position: absolute;
        right: 10px;
        top: 100px;
        width: 40px;
        z-index: 800;
        border: white;
        margin-bottom: -10px;
        width: 70px;
        height: 30px;
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 1rem;
        cursor: pointer; /* 添加手型指针 */
        background-color: white;
    }

    .layer-checkbox {
        margin-right: 8px;
    }

    .show-yaw {
        width: 100%;
        height: 30px;
        z-index: 9999999;
        position: absolute;
        display: flex;
        justify-content: center; /* 只需要声明一次 */
        align-items: center;
        font-size: 0.9rem;
        color: black;
        line-height: 30px; /* 设置行高与容器高度一致 */
    }

    .select-gd{
        z-index: 9999999;
        position: absolute;
        font-size: 0.9rem;
        color: black;
        line-height: 32px;
        top: 40px;
        left: 10px;
        height: 32px;

    }

    .el-checkbox__input.is-checked+.el-checkbox__label {
        color: #303133;
    }
    .gongju_left {
        width: 95%;
        height: 100%;
        overflow-wrap: break-word; /* 允许在单词内换行 */
        word-break: break-word; /* 允许在单词内换行 */
        padding-left: 10px;
        margin-left: 10px;
        font-size: 20px;
    }

    .gongju_main {
        width: 30%;
        height: 100%;
        justify-content: space-between;
        text-align: center; /* 确保文本在水平方向上居中 */
    }

    .gongju_right {
        width: 30%;
        height: 100%;
        text-align: right;
    }

    ::v-deep .highlight-row {
        background-color: #6f6a6a !important; /* 你选择的颜色 */
    }

    ::v-deep .el-form-item--small .el-form-item__content,
    .el-form-item--small .el-form-item__label {
        line-height: 32px;
        width: 205px;
    }

    .btn-uploading {
        text-align: center;
    }

    .rectangle {
        position: absolute;
        border: 2px solid red;
        background-color: #2a7be8;
        z-index: 9999999;
    }

    .draw-canvas {
        position: absolute;
        top: 0;
        left: 0;
    }

    ::v-deep .el-input__inner {
        width: 130px;
    }

    ::v-deep .el-input {
        display: inline-block;
    }

    .gt-query {
        display: flex;
        flex-direction: row;
        padding-bottom: 10px;
        /*justify-content: space-between;*/
        padding-top: 10px;
        border-bottom: 1px solid #fff;
        overflow: hidden;
    }

    ::v-deep .el-table__body,
    .el-table__footer,
    .el-table__header {
        table-layout: fixed;
        border-collapse: separate;
        width: 360px !important;
    }

    ::v-deep .el-table__header {
        table-layout: fixed;
        border-collapse: separate;
        width: 360px !important;
    }

    .tablenum {
        width: 30px;
        border-radius: 50%;
        background-color: #2db6f4;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .model {
        width: 25px;
        height: 40px;
        background-size: 100% 100%;
        position: absolute;
        transform: translate(-50%, -50%);
        z-index: 999;
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

    .hotspot-image {
        width: 50px; /* 热点图片的宽度 */
        height: 50px; /* 热点图片的高度 */
        border-radius: 50%; /* 如果需要，可以设置圆形 */
        cursor: pointer; /* 鼠标悬停时的指针样式 */
    }

    .result-dialog {
        width: 370px;
        height: 300px;
        background-color: white;
        position: absolute;
        z-index: 9999999;
        top: 200px;
        left: 450px;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .verify-title {
        height: 30px;
        background-color: #1890ff;
        width: 100%;
        display: flex;
        align-items: center;
    }

    .verify-title span {
        margin-left: 10px;
        font-weight: bold;
        font-size: 14px;
        text-align: center;
        color: white;
        width: 90%;
    }

    .result-form {
        width: 100%;
        margin-top: 10px;
        margin-left: 10px;
    }

    .gt-form-item {
        display: flex;
        align-items: center;
    }

    ::v-deep .gt-form-item .el-form-item__content {
        margin-left: 0 !important;
    }

    ::v-deep .gt-form-item .el-input__inner {
        /*width: 100%;*/
    }

    .small-map-container {
        width: 50%;
        height: 100%;
        background-color: white;
    }

    .small-map {
        width: 100%;
        height: 100%;
    }

    .small-map-container-larger {
        position: absolute;
        bottom: 0; /* 距离底部10px */
        left: 0; /* 距离左侧10px */
        width: 600px;
        height: 600px;
        z-index: 9999999;
        border: 1px solid #fff;
        display: flex;
        flex-direction: column;
    }

    ::v-deep .form_class .el-input__inner {
        width: 100%;
        color: white;
    }

    .btn {
        margin-left: 3px;
    }

    .collapsible-content {
        transition: all 0.3s ease;
        overflow: hidden;
    }

    .collapsible-content.collapsed {
        height: 0;
        opacity: 0;
        padding: 0;
        margin: 0;
        visibility: hidden;
    }

    /* 表格容器设置 */
    .table-container {
        height: 400px;
        overflow-y: auto;
    }

    .table-container-frame {
        height: 430px;
        overflow-y: auto;
    }
    ::v-deep .el-table .cell {
        box-sizing: border-box;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        word-break: break-all;
        line-height: 23px;
        padding-left: 10px;
        padding-right: 10px;
        display: flex;

    }
    ::v-deep .el-button--small{
        padding:0;
    }
    ::v-deep .el-button.is-disabled{
        color: gray !important;
    }
    ::v-deep .el-input, .el-textarea {
        display: inline-block;
        width: auto;
        margin-right: 10px;
    }
    .toolbar {
        width: 17%;
        height: 30px;
        position: absolute;
        top: 20px;
        right: 20px;
        border-radius: 5px;
        z-index: 999;
        font-weight: bold;
        line-height: 35px;
        background-color: rgb(218 213 213 / 38%);
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        padding: 0 20px;
        color: black;
    }
    .toolbar div {
        cursor: pointer;
    }
    .toolbar div:hover {
        color: #1890ff;
    }
    .baractive {
        color: #1890ff;
    }
    ::v-deep .pnlm-zoom-in.disabled{
        background-color: #cccccc; /* 灰色背景 */
        color: #888888;
        cursor:not-allowed;
    }
    ::v-deep .pnlm-zoom-out.disabled {
        background-color: #cccccc; /* 灰色背景 */
        color: #888888;
        cursor:not-allowed;
    }
    ::v-deep .el-collapse-item__header {
        display: flex;
        align-items: center;
        height: 32px;
        line-height: 32px;
        color: #303133;
        cursor: pointer;
        font-size: 0.9rem;
        font-weight: 500;
        transition: border-bottom-color .3s;
        outline: 0;
        border-bottom:none;
        background-color: rgb(218 213 213 / 38%);
        margin-left: 0px;
        padding:0 10px
    }
    ::v-deep .el-collapse {
        border-top: none;
        border-bottom: none;
        padding:0 10px
    }
    ::v-deep .el-collapse-item__wrap {
        border-bottom: none;
        background-color: rgb(218 213 213 / 38%);
        padding:10px
    }
    .speed-control {
        position: absolute;
        top: 250px;
        background: rgba(255, 255, 255, 0.34);
        border-radius: 5px;
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 999;
        right: 60px;
        height: 360px;
        width: 40px;
    }

    .speed-btn-group ul li {
        list-style-type: none; /* 去掉项目符号 */
        color: black;
        cursor: pointer;
        margin-top: 10px;
    }

    .speed-btn-group ul li:hover {
        color: #0a6fc0;
    }

    .speed-btn-group ul li.activate {
        color: #0a6fc0; /* 激活状态的文字颜色 */
        font-weight: bold; /* 激活状态的文字加粗 */
    }
    .angleRadio {
        margin-top: 8px;
    }
    ::v-deep .el-radio-button--mini .el-radio-button__inner {
        padding: 2px;
    }
    /* 固定十字标识 */
    ::v-deep .crosshair {
      width: 30px;
      height: 30px;
      background-image: url('@/assets/images/guangbiao.png');
      background-size: 100% 100%;
      position: absolute;
      transform: translate(-50%, -50%);
      z-index: 999;
    }
</style>
