<template>
    <div class="mmain">
        <div class="small-map-container" ref="smallMapContainer">
            <small-map
                    class="small-map"
                    ref="smallMap"
                    :temp-point-list="tempPointList"
                    :task-list="taskList"
                    :currentYaw="currentYaw"
                    :current-task="currentActivateItem"
                    :current-view-point="currentViewPoint"
                    :isMapChange="isMapChange"
                    :currentAddMarker="currentAddMaker"
                    :currentLocationMarker="currentLocationMarker"
                    :no_detection_area_list="no_detection_area_list"
                    :isAutoRotating="isAutoRotating"
                    @clickMarker="handleMarkerClick"
                    @clickMap="modifyTakePoint">
            </small-map>
        </div>
        <div class="multi-right">
            <div class="rmain">
                <div class="rm_left">
                    <verifypannelViewLeft v-if="pannellumDialogVisible"
                                          :key="uniquekey"
                                          :polygonItemId="polygonItemId"
                                          :relativeYaw="relativeYaw"
                                          :yaw="yaw"
                                          :pitch="pitch"
                                          :currentObj="currentObj"
                                          :tempAllLayersCheck="localAllLayersCheck"
                                          @angleParam="handleRightAngleParm"
                                          :isAddCluePoint="isAddCluePoint"
                                          @closeAddCluePoint="closeAddCluePoint"
                                          @clickView="handleClickView"
                                          @showClueInMap="showClueInMap"
                                          @updateAllLayersCheck="updateAllLayersCheck"
                                          ref="leftPanorama"
                    >
                    </verifypannelViewLeft>
                </div>
                <div class="rm_right">
                    <verifypannelViewRight v-if="pannellumDialogVisibleRight"
                                           :key="uniquekeyRight"
                                           :currentObjRight="currentObjRight"
                                           :angleParams="angleParams"
                                           :currentLeftObj="currentObj"
                                           :allLayersCheck="allLayersCheck"
                                           :polygonItemId="polygonItemId"
                                           :yaw="yaw"
                                           :relativeYaw="rightRelativeYaw"
                                           :pitch="pitch"
                                           :tempAllLayersCheck="localAllLayersCheck"
                                           ref="rightPanorama"
                    >
                        <!--                        -->
                    </verifypannelViewRight>
                </div>
                <div class="close-chahao"><el-button icon="el-icon-close"  @click="handleGoBack"></el-button></div>
                <div class="gt-toolbar-right">
                    <div class="gt-alarms-list" title="返回" @click="handleGoBack">
                        <img src="@/assets/images/back.png" />
                    </div>
                    <div v-if="isAutoRotating" class="gt-alarms-list" title="暂停自动播放" @click="autoPlay">
                        <img src="@/assets/images/stop.png" />
                    </div>
                    <div v-else class="gt-alarms-list" title="自动播放" @click="autoPlay">
                        <img src="@/assets/images/play.png" />
                    </div>
                    <div class="gt-alarms-list" @click="handleSetView" title="一键归位">
                        <img src="@/assets/images/guiwei.png" />
                    </div>
                    <div class="gt-alarms-list" @click="handleAddLeftCluePoint" title="添加目标">
                        <img src="@/assets/images/add.png" />
                    </div>
                </div>
                <div class="thumbnail-footer" :class="{ 'collapsed': isThumbnailCollapsed }">
                    <div class="thumbnail-content" v-if="!isThumbnailCollapsed">
                        <div class="rfoot">
                            <div class="left-dimg" v-if="isShowFirstImage">
                                <img :src="url" class="left-img"/>
                                <span><strong>基准：</strong>{{ firstImage.batchName ? firstImage.batchName.replace('临时批次', '') : ''}}</span>
                            </div>
                            <el-button @click="prevImages" :disabled="currentIndex === 0" circle icon="el-icon-arrow-left"
                                       class="rleft-btn" type="text"></el-button>
                            <div class="thumbnail-container">
                                <div class="dimg" v-for="(image, index) in currentshowimg" :key="index"
                                     @click="handleClickDiv(image,currentImage)">
                                    <div class="top-item">
                                        <img :src="url" :class="{ active: currentImage.batchName===image.batchName}"
                                             class="right-img"/>
                                        <el-button type="primary" plain size="mini" disabled class="prv-btn">上屏</el-button>
                                        <el-button type="primary" plain size="mini"
                                                   :class="{ 'right-active': activeRightIndex === index }"
                                                   @click="handleClickRight(image,currentImage,index)"
                                                   :disabled="isAlreadyShownRight(image)" class="next-btn">下屏
                                        </el-button>
                                    </div>

                                    <span>{{ image.batchName ? image.batchName.replace('临时批次', '') : ''}}</span>

                                </div>
                            </div>
                            <el-button @click="nextImages" :disabled="currentIndex === images.length - 1" class="rright-btn"
                                       circle icon="el-icon-arrow-right" type="text"></el-button>
                        </div>
                    </div>
                </div>
                <div @click="toggleThumbnail"
                     class="toggle-button"
                     :class="{ 'collapsed': isThumbnailCollapsed }">
                    <i :class="isThumbnailCollapsed ? 'el-icon-arrow-up' : 'el-icon-arrow-down'"></i>
                </div>
            </div>



            <!-- 速度控制条 -->
            <div v-if="isAutoRotating" class="speed-control">
                <el-radio-group v-model="angleRadio" size="mini" class="angleRadio" @change="handleAngleChange">
                    <el-radio-button label="近"></el-radio-button>
                    <el-radio-button label="远"></el-radio-button>
                </el-radio-group>
                <span style="margin-top: 5px">速度</span>
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
        </div>
    </div>
</template>

<script>
    import smallMap from '@/components/smallMap/index.vue';

    import verifypannelViewLeft from "@/views/panoramicDetection/verifyClue/multiComparison/verifypannelViewLeft.vue";
    import verifypannelViewRight from "@/views/panoramicDetection/verifyClue/multiComparison/verifypannelViewRight.vue";
    import {getOnePointMultiComInfoApi} from "@/api/commonApi";

    export default {
        name: 'threeScreen',
        components: {verifypannelViewLeft, verifypannelViewRight,smallMap},
        props: {
            currentActivateItem: Object,
            batchNumber: String,
            polygonItemId: String,
            yaw: Number,
            pitch: Number,
            currentAzimuth: Number,
            taskList: {
                type: Array,
                required: true
            },
            tempAllLayersCheck:Array, //只有第一次使用

        },
        data() {
            return {
                tempPointList:[],
                allLayers: [],            //全部图层
                currentTask:{},
                currentViewPoint: null,
                currentAddMaker: null,
                currentLocationMarker:null,
                no_detection_area_list: [],
                isMapChange: false, //是否按下打点
                rightRelativeYaw: 0,
                relativeYaw: 0,
                pannellumDialogVisible: false,
                pannellumDialogVisibleRight: false,
                uniquekey: 1,
                uniquekeyRight: 1,
                currentObj: {},
                currentObjRight: {},
                images: [],
                currentIndex: 0,// 当前显示的图片索引
                currentshowimg: [],//当前展示的图片列表
                limitimgcount: 8, //限制展示的图片数量
                angleParams: {'yaw': localStorage.getItem('initYaw'), 'pitch': 0, 'hfov': 0},//右侧View需要展示的图片数量
                url: require('@/assets/images/test.png'),
                isAddCluePoint: false,
                currentBatchTotalClues: 0,
                differenceValue: 0,
                isAutoRotating: false,
                rotationSpeed: 5,
                isShowFirstImage: true,
                firstImage: {
                    'batchName': '暂未获取',
                },
                allLayersCheck: [],
                activeRightIndex: 0,  // 右按钮激活的图片索引
                isThumbnailCollapsed: false,
                angleRadio:'',
                lastAllLayersCheck: [], // 保存子组件最后一次的 allLayersCheck
                localAllLayersCheck: [...this.tempAllLayersCheck], //深拷贝
                currentHfov:0,
                currentPitch:0,
                currentYaw:0,
                currentClickObj:{},
            }
        },
        methods: {
            showClueInMap(currentViewPoint){
                this.currentViewPoint=currentViewPoint;
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
                    const marker = L.marker([lat, lng], { icon: customIcon });
                    this.currentAddMaker = marker;
                    this.correctLabelVisible = true;
                }
            },
            //处理marker的点击事件
            async handleMarkerClick(task, lat, lon, markerData, marker) {
                this.allLayers.forEach((layer) => {
                    if (layer.hasOwnProperty('gdPolygons')) {
                        delete layer.gdPolygons;
                    }
                });
                if (this.viewer){
                    this.viewer.allRemoveHotSpot()
                }
                // this.removeAllHotspots();
                // this.removeAllQuanjingHotspots();
                if (this.currentTask.pointId !== task.pointId) {
                    this.currentTask = task;
                    this.currentDisplayTask = task; //更新左上角日期的，不能够替换因为仅有全景图切换
                }
                //更换地图内容
                this.pointName = this.currentTask.pointName;
                this.imageName = this.currentTask.imageName;
                // 显示全景图
                await this.showPanorama();
                this.$emit('markerclick', this.pointName);
            },
            handleAngleChange() {
                if (this.angleRadio === '远') {
                    this.currentHfov = 15
                    this.currentPitch = -15;
                    this.handleSpeedChange(2)
                } else if (this.angleRadio === '近') {
                    this.currentHfov = 100;
                    this.currentPitch = -70;
                    this.handleSpeedChange(5)
                } else {
                    this.currentHfov = 120;
                    this.currentPitch = 0;
                }
            },
            cacuRelativeYaw(Azimuth,type){
                var yawDegree = this.currentObj.yawDegree || 0; // 假设point1有yawDegree属性
                if (type == 'right'){
                    yawDegree = this.currentObjRight.yawDegree || 0; // 假设point1有yawDegree属性
                }
                var relativeYaw = ((Azimuth - yawDegree + 360) % 360); // 确保yaw角度在0-
                if (relativeYaw > 360) {
                    relativeYaw = relativeYaw - 360;
                }
                return relativeYaw
            },
            handleGoBack() {
                this.$emit('backToSoloPanoramic');
            },
            async initializeImages() {
                // 初始化时，填充currentshowimg数组   当前页展示的多期对比数量
                this.currentshowimg = this.images.slice(this.currentIndex, this.currentIndex + this.limitimgcount);
                if (!this.pannellumDialogVisible) {
                    this.pannellumDialogVisible = true;
                }
                if (!this.pannellumDialogVisibleRight) {
                    this.pannellumDialogVisibleRight = true;
                }
                this.uniquekeyRight += 1;
                this.uniquekey += 1;
                this.currentObj = this.firstImage;
                this.currentObjRight = this.currentshowimg[0];
            },
            //点击下一张图片
            nextImages() {
                if (this.currentIndex < this.images.length - 1) {
                    this.currentIndex++;
                    if (this.currentIndex >= this.limitimgcount) {
                        // 移除currentshowimg中的第一个元素
                        this.currentshowimg.shift();
                        // 将下一张图片添加到currentshowimg数组的末尾
                        this.currentshowimg.push(this.images[this.currentIndex]);
                    }
                }
            },
            //点击上一张图片
            prevImages() {
                if (this.currentIndex > 0) {
                    this.currentIndex--;
                    if (this.currentIndex <= this.limitimgcount) {
                        this.currentshowimg = this.images.slice(0, this.limitimgcount);
                    }
                }
            },
            //接收左侧传的角度，更改到右侧
            handleRightAngleParm(data) {
                this.angleParams = data
                this.currentYaw = data.yaw;
            },
            //处理点击下面的每个图片，更改当前索引以及用于展示的currentshowimg列表
            handleClickDiv(item, currentImage) {
                const currentImageIndex = this.images.findIndex((image) => image.batchId === currentImage.batchId)
                const clickImageIndex = this.images.findIndex((image) => image.batchId === item.batchId)
                //判断点的是后一个div还是前一个div
                if (currentImageIndex < clickImageIndex) {
                    const chazhi = clickImageIndex - currentImageIndex
                    //说明点击的是下一张
                    this.currentIndex = this.currentIndex + chazhi;
                    if (this.currentIndex >= this.limitimgcount) {
                        // 移除currentshowimg中的第一个元素
                        this.currentshowimg.shift();
                        // 将下一张图片添加到currentshowimg数组的末尾
                        this.currentshowimg.push(this.images[this.currentIndex]);
                    }
                } else if (currentImageIndex > clickImageIndex) {
                    const chazhi = currentImageIndex - clickImageIndex
                    //说明点击的是上一张
                    this.currentIndex = this.currentIndex - chazhi;
                    // this.currentIndex--;
                    if (this.currentIndex <= this.limitimgcount) {
                        this.currentshowimg = this.images.slice(0, this.limitimgcount);
                    }
                }
            },

            //处理添加线索点到左侧的情况
            handleAddLeftCluePoint() {
                if(this.currentObj.status === 2){
                    this.$message.warning('当前全景图已判读完毕，无法新增目标点！');
                }else {
                    this.isAddCluePoint = true
                    this.$message.info("仅支持在上方全景图上添加目标点");
                }
            },
            closeAddCluePoint(data) {
                this.isAddCluePoint = data.value;
            },
            autoPlay() {
                this.isAutoRotating = !this.isAutoRotating;
                if (this.isAutoRotating) {
                    this.$refs.leftPanorama.startRotate(this.rotationSpeed,this.angleRadio,this.currentPitch,this.currentHfov);
                    this.$refs.rightPanorama.startRotate(this.rotationSpeed,this.angleRadio,this.currentPitch,this.currentHfov);
                    this.angleRadio = '';
                } else {
                    //发送停止旋转至左侧的指令
                    this.$refs.leftPanorama.stopRotate();
                    //发送停止旋转至右侧的指令
                    this.$refs.rightPanorama.stopRotate();
                    this.isAutoRotating = false
                }
            },
            updateRotateSpeed() {
                //发送开始旋转至左侧的指令
                this.$refs.leftPanorama.startRotate(this.rotationSpeed,this.angleRadio,this.currentPitch,this.currentHfov);
                //发送开始旋转至右侧的指令
                this.$refs.rightPanorama.startRotate(this.rotationSpeed,this.angleRadio,this.currentPitch,this.currentHfov);
            },
            handleClickView() {
                if (this.isAutoRotating) {
                    this.isAutoRotating = false
                    //发送停止旋转至左侧的指令
                    this.$refs.leftPanorama.stopRotate();
                    //发送停止旋转至右侧的指令
                    this.$refs.rightPanorama.stopRotate();
                }
            },
            handleSpeedChange(speed) {
                this.rotationSpeed = Number(speed);
                this.updateRotateSpeed();
            },
            updateAllLayersCheck(value) {
                this.allLayersCheck = value
                this.lastAllLayersCheck = JSON.parse(JSON.stringify(value));
            },
            handleClickRight(item, currentImage, index) {
                this.handleClickDiv(item, currentImage)
                if (!this.isAlreadyShown(item)) {
                    this.localAllLayersCheck = [...this.lastAllLayersCheck]
                    this.uniquekeyRight += 1;
                    this.currentObjRight = item;
                    this.activeRightIndex = index;
                    //this.$refs.leftPanorama.resetCheckService()
                } else {
                    this.$message.warning("该期线索已在左侧或者右侧显示，请选择其他时期线索!!!")
                }
            },
            isAlreadyShown(item) {
                // 检查是否已在左侧或右侧显示
                return this.currentObjRight === item || this.currentObj === item;
            },
            isAlreadyShownLeft(item) {
                return this.currentObj === item;
            },
            isAlreadyShownRight(item) {
                return this.currentObjRight === item;
            },
            async toggleThumbnail() {
                this.isThumbnailCollapsed = !this.isThumbnailCollapsed;
            },
            handleSetView(){
                this.$refs.leftPanorama.handleResetViewYaw()
            },
            async initMethod(){
                const multiObjres = await getOnePointMultiComInfoApi(this.currentActivateItem.imageId)
                if (multiObjres.code === 0) {
                    this.images = multiObjres.data;
                    if (this.images.length === 0) {
                        this.isShowFirstImage = false
                    } else {
                        this.firstImage = this.images.find(image => image.batchId === this.batchNumber)
                        this.images = this.images.filter(image => image.batchId !== this.batchNumber)
                    }
                    this.initializeImages()
                } else {
                    this.$message.error(multiObjres.msg)
                }
                this.relativeYaw = this.cacuRelativeYaw(this.currentAzimuth);
                this.rightRelativeYaw = this.cacuRelativeYaw(this.currentAzimuth,'right');
            }

        },

        computed: {
            currentImage() {
                return this.images[this.currentIndex];
            },

        },
        watch: {
            currentActivateItem: {
                async handler(newVal) {
                    this.localAllLayersCheck = [...this.lastAllLayersCheck];
                    this.currentIndex = 0; // 当前显示的图片索引
                    this.currentshowimg = [];
                    this.images = [];
                    this.initMethod();
                }
            },
        },
        async mounted() {
            await this.initMethod()
        },
        created() {
        }
    }
</script>


<style scoped>
    @import "@/assets/css/pannellumCommon.css";

    .mmain {
        display: flex;
        height: 100%;
        width: 100%;
        overflow-x: hidden;
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
    .multi-right {
        flex: 1;
        display: flex;
        flex-direction: column; /* 子元素垂直排列 */
        height: 100%; /* 容器高度 */
    }

    .rmain {
        height: 100%; /* 占容器高度的60% */
        align-items: center;
        justify-content: space-between;
    }

    .rfoot {
        display: flex;
        align-items: center;
        margin: 5px;
        overflow-x: auto;
        flex: 1;
        height: 100%;
    }

    .add-point {
        margin-right: 10px;
        background-color: transparent;
        cursor: pointer;
        font-size: 16px;
        transition: all 0.3s ease;
        color: black;
        text-align: center;
        margin-left: 10px;
        top: 10px;
        margin-top: 13px;
    }


    .add-point:hover {
        background-color: #1DA2FF; /* 鼠标悬停时的背景颜色 */
        color: white; /* 鼠标悬停时的文字颜色 */
    }

    .rm_left {
        width: 100%;
        height: 50%;
        border: #f44336 3px solid;
    }

    .rm_right {
        width: 100%;
        height: 50%;
        border: #4caf50 3px solid;
    }

    .thumbnail-container {
        display: flex;
        padding: 10px 0;
        white-space: nowrap;
        height: 100%;
        overflow-x: auto;
        flex: 1;
        height: 100%;

    }

    .left-dimg {
        font-size: 12px;
        position: relative; /* 使按钮容器的绝对定位相对于 .dimg */
        box-sizing: border-box;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-left: 30px;
        width: 120px;
        padding: 10px 0;
        white-space: nowrap;
    }

    .left-dimg span {
        display: block;
        text-align: center;
        font-size: 12px;
        height: 20px;
    }

    .dimg {
        font-size: 12px;
        position: relative;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
        width: 120px;
        overflow: hidden;

    }

    .dimg span {
        display: block;
        text-align: center;
        color: white;
        font-size: 12px;
        height: 20px;
        justify-items: center;
    }

    .right-img {
        width: 95%;
        height: 100%;
        margin: 0 5px;
        cursor: pointer;
    }

    .left-img {
        width: 97%;
        flex: 1;
        margin: 0 5px;
        cursor: pointer;
        border: 3px solid #f44336;
    }

    .dimg img.active {
        border: 3px solid #1DA2FF;
    }

    .rleft-btn {
        border: 1px solid #fff;
        color: black;
        margin-left: 5px;
        padding: 5px;
    }

    .rleft-btn:hover {
        background-color: #1DA2FF;
    }

    .rright-btn {
        border: 1px solid #fff;
        color: black;
        margin-right: 0px;
        padding: 5px;
    }

    .rright-btn:hover {
        background-color: #1DA2FF;
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
    ::v-deep .el-radio-button--mini .el-radio-button__inner {
        padding: 2px;
    }
    .angleRadio {
        margin-top: 8px;
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

    /* 左按钮点击成功样式 */
    .left-active {
        background-color: #ffebee !important;
        border-color: #f44336 !important;
        color: #f44336 !important;
        transition: all 0.3s;
    }

    /* 右按钮激活样式 */
    .right-active {
        background-color: #e8f5e9 !important;
        border-color: #4caf50 !important;
        color: #4caf50 !important;
    }

    .next-btn {
        position: absolute;
        top: 10px;
        right: 15px;
        font-size: 12px;
        padding: 5px;
    }

    .prv-btn {
        position: absolute;
        top: 10px;
        left: 15px;
        font-size: 12px;
        padding: 5px;
    }

    ::v-deep .el-icon-arrow-right:before {
        content: "\e6e0";
        color: white;
    }

    ::v-deep .el-icon-arrow-left:before {
        content: "\e6de";
        color: white;
    }

    .thumbnail-footer {
        position: absolute;
        overflow: hidden;
        bottom: 0px;
        background: #0b1a3954;
        height: 17%;
        width: 100%;
    }

    .thumbnail-footer.collapsed {
        height: 0; /* 折叠后的高度 */
    }

    .toggle-button {
        position: absolute;
        left: 75%;
        transform: translateX(-50%);
        width: 60px;
        height: 10px;
        background-color: rgba(0, 0, 0, 0.3);
        border-radius: 0 0 5px 5px;
        display: flex;
        justify-content: center;
        align-items: center;
        cursor: pointer;
        z-index: 1000;
    }
    .toggle-button:not(.collapsed) {
        bottom: calc(17% - 10px);
    }

    .thumbnail-content {
        height: 100%;
    }
    .close-chahao{
        position: absolute;
        top: 5px;
        right: 0px;
        z-index: 999;
    }
    ::v-deep .el-button--small {
        padding: 7px 7px;
        margin-right: 5px;
        background-color: rgba(0, 0, 0, 0.3);
        color: white;
        border: none;
    }
    .top-item{
        position: relative;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        flex: 1;
    }
</style>
