<template>
    <div class="mmain">
        <div class="multi-right">
            <div class="rtop">
                <div style="display: inline-block; margin-left: 10px">
                    <span class="iconfont icon-xinzengtianjia" style="margin-right: 5px"></span>
                    <span class="title">多期全景对比</span>
                </div>
                <span class="el-icon-close" @click="closeMultiDiv" style="cursor: pointer; margin-right: 10px"></span>
            </div>
            <div class="zhixian"></div>
            <div class="rmain">
                <div class="rm_left">
                    <verifypannelViewLeft
                        v-if="pannellumDialogVisible"
                        :key="uniquekey"
                        :currentObj="currentObj"
                        @angleParam="handleRightAngleParam"
                        :leftAngleParams="leftAngleParams"
                        @updateAllLayersCheck="updateAllLayersCheck">
                    </verifypannelViewLeft>
                </div>
                <div class="rm_right">
                    <verifypannelViewRight
                        v-if="pannellumDialogVisibleRight"
                        :key="uniquekeyRight"
                        :currentObjRight="currentObjRight"
                        :angleParams="angleParams"
                        :currentLeftObj="currentObj"
                        :allLayersCheck="allLayersCheck">
                    </verifypannelViewRight>
                </div>
            </div>
            <div class="rfoot">
                <el-button @click="prevImages" :disabled="currentIndex === 0" circle icon="el-icon-arrow-left" class="rleftbtn"></el-button>
                <div class="thumbnail-container">
                    <div class="dimg" v-for="(image, index) in currentshowimg" :key="index" @click="handleClickDiv1(image, currentImage)">
                        <img :src="url" :class="{ active: currentImage.batchName === image.batchName }" />
                        <span>{{ image.batchName }}</span>
                        <el-button
                            type="primary"
                            plain
                            size="mini"
                            :class="{ 'left-active': activeLeftIndex === index }"
                            @click="handleClickLeft(image, currentImage, index)"
                            :disabled="isAlreadyShownLeft(image)"
                            class="prv-btn"
                            >左屏</el-button
                        >
                        <el-button
                            type="primary"
                            plain
                            size="mini"
                            :class="{ 'right-active': activeRightIndex === index }"
                            @click="handleClickRight(image, currentImage, index)"
                            :disabled="isAlreadyShownRight(image)"
                            class="next-btn"
                            >右屏</el-button
                        >
                    </div>
                </div>
                <el-button
                    @click="nextImages"
                    :disabled="currentIndex === images.length - 1"
                    class="rrightbtn"
                    circle
                    icon="el-icon-arrow-right"></el-button>
            </div>
        </div>
    </div>
</template>

<script>
import verifypannelViewLeft from '@/views/dataManagement/oneMap/multiView/verifypannelViewLeft.vue';
import verifypannelViewRight from '@/views/dataManagement/oneMap/multiView/verifypannelViewRight.vue';

export default {
    name: 'multiComparision',
    components: { verifypannelViewLeft, verifypannelViewRight },
    props: {
        listData: Array
    },
    data() {
        return {
            cards: [],
            pannellumDialogVisible: false,
            pannellumDialogVisibleRight: false,
            uniquekey: 1,
            uniquekeyRight: 1,
            currentObj: {},
            currentObjRight: {},
            taskList: [], //当前页要展示的数据
            images: [],
            currentIndex: 0, // 当前显示的图片索引
            currentshowimg: [], //当前展示的图片列表
            limitimgcount: 8, //限制展示的图片数量
            angleParams: { yaw: this.initYaw, pitch: this.initPitch, hfov: this.initHfov }, //右侧View需要展示的图片数量
            leftAngleParams: { yaw: this.initYaw, pitch: this.initPitch, hfov: this.initHfov }, //左侧View需要展示的图片数量
            url: require('@/assets/images/test.png'),
            isAddCluePoint: false,
            currentPointObj: '',
            currentBatchTotalClues: 0,
            differenceValue: 0,
            activeLeftIndex: 0, // 左按钮激活的图片索引
            activeRightIndex: 1, // 右按钮激活的图片索引
            allLayersCheck: []
        };
    },
    methods: {
        closeMultiDiv() {
            this.$emit('closeMultiDiv');
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
            if (this.currentshowimg.length >= 2) {
                this.currentObj = this.currentshowimg[0];
                this.currentObjRight = this.currentshowimg[1];
            }
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
        handleRightAngleParam(data) {
            this.angleParams = data;
        },
        //处理点击下面的每个图片，更改当前索引以及用于展示的currentshowimg列表
        handleClickDiv1(item, currentImage) {
            const currentImageIndex = this.images.findIndex((image) => image.batchId === currentImage.batchId);
            const clickImageIndex = this.images.findIndex((image) => image.batchId === item.batchId);
            //判断点的是后一个div还是前一个div
            if (currentImageIndex < clickImageIndex) {
                const chazhi = clickImageIndex - currentImageIndex;
                //说明点击的是下一张
                this.currentIndex = this.currentIndex + chazhi;
                if (this.currentIndex >= this.limitimgcount) {
                    // 移除currentshowimg中的第一个元素
                    this.currentshowimg.shift();
                    // 将下一张图片添加到currentshowimg数组的末尾
                    this.currentshowimg.push(this.images[this.currentIndex]);
                }
            } else if (currentImageIndex > clickImageIndex) {
                const chazhi = currentImageIndex - clickImageIndex;
                //说明点击的是上一张
                this.currentIndex = this.currentIndex - chazhi;
                // this.currentIndex--;
                if (this.currentIndex <= this.limitimgcount) {
                    this.currentshowimg = this.images.slice(0, this.limitimgcount);
                }
            }
        },

        handleClickLeft(item, currentImage, index) {
            this.handleClickDiv1(item, currentImage);
            if (!this.isAlreadyShown(item)) {
                this.uniquekey += 1;
                this.currentObj = item;
                this.activeLeftIndex = index;
            } else {
                this.$message.warning('该期线索已在左侧或者右侧显示，请选择其他时期线索!!!');
            }
        },
        handleClickRight(item, currentImage, index) {
            this.handleClickDiv1(item, currentImage);
            if (!this.isAlreadyShown(item)) {
                this.uniquekeyRight += 1;
                this.currentObjRight = item;
                this.activeRightIndex = index;
            } else {
                this.$message.warning('该期线索已在左侧或者右侧显示，请选择其他时期线索!!!');
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
        updateAllLayersCheck(value) {
            this.allLayersCheck = value;
        }
    },
    computed: {
        currentImage() {
            return this.images[this.currentIndex];
        }
    },
    watch: {},
    async mounted() {
        this.images = this.listData;
        this.initializeImages();
    },
    created() {}
};
</script>

<style scoped>
.mmain {
    display: flex;
    height: 100%;
    width: 100%;
    overflow-x: hidden;
}
.multi-right {
    flex: 1;
    display: flex;
    flex-direction: column; /* 子元素垂直排列 */
    height: 100%; /* 容器高度 */
    width: calc(100% - 320px);
}

.rtop {
    display: flex;
    height: 40px; /* 占容器高度的10% */
    align-items: center;
    flex-direction: row;
    justify-content: space-between;
    background-color: #409eff;
    color: white;
}

.zhixian {
    margin-bottom: 5px;
}

.rmain {
    display: flex;
    height: 65%; /* 占容器高度的60% */
    align-items: center;
    justify-content: space-between;
}

.rfoot {
    height: 25%; /* 占容器高度的30% */
    display: flex;
    align-items: center;
    margin: 10px;
    overflow-x: auto;
}
.rm_left {
    width: 49%;
    height: 100%;
    margin-left: 10px;
    border: #f44336 3px solid;
}
.rm_right {
    margin-right: 10px;
    width: 49%;
    height: 100%;
    border: #4caf50 3px solid;
}
.thumbnail-container {
    display: flex;
    overflow-x: auto;
    padding: 10px 0;
    width: 95%;
    overflow-x: auto;
    height: 100%;
}
.dimg {
    font-size: 0.9rem;
    position: relative; /* 使按钮容器的绝对定位相对于 .dimg */
    width: calc((100% / 8) - (var(--gap, 0px))); /* 减去间隙，如果有的话 */
    box-sizing: border-box;
}
.dimg span {
    display: block;
    text-align: center;
}
.dimg img {
    width: 90%; /* 缩略图的宽度 */
    height: 95%;
    margin: 0 5px;
    cursor: pointer;
    border: 2px solid transparent;
}

.dimg img.active {
    border: 5px solid #1da2ff;
}

.rleftbtn {
    border: 1px solid black;
    color: black;
    margin-left: 5px;
}
.rleftbtn:hover {
    background-color: #1da2ff;
}
.rrightbtn {
    border: 1px solid black;
    color: black;

    margin-right: 0px;
}
.rrightbtn:hover {
    background-color: #1da2ff;
}

::v-deep .el-dialog__body {
    height: 200px;
    overflow-y: auto;
}

::v-deep .label-dialog .el-dialog {
    position: absolute;
    /* bottom: 4%; */
    width: 400px;
    /* left: 50%; */
    margin-left: -200px;
    background-color: rgba(0, 0, 0, 0.6);
    box-shadow: none;
    z-index: 999;
    color: #fff;
    border: #e6f7ff 1px solid;
}

::v-deep .el-form-item__content {
    width: 160px;
}
.marquee {
    width: 70%;
    overflow: hidden;
    white-space: nowrap;
    box-sizing: border-box;
}
.marquee-text {
    display: inline-block;
    padding: 0 5px;
}

@keyframes marquee {
    from {
        transform: translateX(0);
    }
    to {
        transform: translateX(-100%);
    }
}

.gt-alarms-list {
    margin-left: 10px;
}
.gt-alarms-list img {
    width: 35px;
    height: 35px;
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

.next-btn {
    position: absolute;
    top: 10px;
    right: 25px;
    font-size: 16px;
}
.prv-btn {
    position: absolute;
    top: 10px;
    left: 15px;
    font-size: 16px;
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
</style>
