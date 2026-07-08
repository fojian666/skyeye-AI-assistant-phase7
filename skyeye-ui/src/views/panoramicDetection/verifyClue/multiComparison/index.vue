<template>
    <div class="mmain">
        <div class="multi-right">
            <div class="rtop">
        <span @click="handleGoBack" class="gt-reback">
          <i class="el-icon-back"></i>
          {{currentPointObj.pointName}}
        </span>
                <div class="marquee">
                    <div class="marquee-content">
                        <span class="marquee-text" style="color: red">注意事项温馨提示：</span>
                        <span class="marquee-text">（1）本页面可点击左箭头进行返回单期线索核实页面；</span>
                        <span class="marquee-text">（2）点击添加辅助点，仅支持在左侧全景图中进行添加，右侧暂不支持；</span>
                        <span class="marquee-text">（3）点击下方图片可切换右侧全景图，不支持切换左侧全景图。</span>
                    </div>
                </div>
                <div class="tools">
                    <div v-if="isAutoRotating" class="gt-alarms-list" title="暂停自动播放" @click="autoPlay">
                        <img src="@/assets/images/blackStop.png"/>
                    </div>
                    <div v-else class="gt-alarms-list" title="自动播放" @click="autoPlay">
                        <img src="@/assets/images/blackBegin.png"/>
                    </div>
                    <div  class="gt-alarms-list" title="添加辅助点" @click="handleAddLeftCluePoint">
                        <img src="@/assets/images/blackAdd.png"/>
                    </div>
                </div>
            </div>
            <div class="zhixian"></div>
            <div class="rmain">
                <div class="rm_left">
                    <verifypannelViewLeft v-if="pannellumDialogVisible" :initYaw="yaw" :initPitch="pitch" :initHfov="hfov"
                                          :key="uniquekey" :currentObj="currentObj" @angleParam="handleRightAngleParm"
                                          :isAddCluePoint="isAddCluePoint"  @closeAddCluePoint="closeAddCluePoint"
                                          @clickView="handleClickView"
                                          @updateAllLayersCheck="updateAllLayersCheck"
                                          ref="leftpanorama"
                    >
                    </verifypannelViewLeft>
                </div>
                <div class="rm_right">
                    <verifypannelViewRight v-if="pannellumDialogVisibleRight" :initYaw="yaw" :initPitch="pitch" :initHfov="hfov"
                                           :key="uniquekeyRight" :currentObjRight="currentObjRight"
                                           :angleParams="angleParams"
                                           :currentLeftObj="currentObj"
                                           :allLayersCheck="allLayersCheck"
                                           ref="rightpanorama"
                    >

                    </verifypannelViewRight>
                </div>
            </div>
            <div class="rfoot">
                <div class="left-dimg" v-if="isShowFirstImage">
                    <img :src="url" class="left-img"/>
                    <span><strong>基准：</strong>{{firstImage.batchName}}</span>
                </div>
                <el-button  @click="prevImages" :disabled="currentIndex === 0" circle icon="el-icon-arrow-left" class="rleftbtn"></el-button>
                <div class="thumbnail-container" >
                    <div class="dimg" v-for="(image, index) in currentshowimg" :key="index" @click="handleClickDiv(image,currentImage)">
                        <img :src="url" :class="{ active: currentImage.batchName===image.batchName}" class="right-img"/>
                        <span>{{image.batchName}}</span>
                    </div>
                </div>
                <el-button  @click="nextImages" :disabled="currentIndex === images.length - 1" class="rrightbtn" circle icon="el-icon-arrow-right"></el-button>
            </div>
            <!-- 速度控制条 -->
            <div v-if="isAutoRotating" class="speed-control">
                <span style="margin-top: 5px">速度</span>
                <div class="speed-btn-group">
                    <ul>
                        <li @click="handleSpeedChange(5)" :class="{ activate: rotationSpeed === 5 }"> &nbsp;5x</li>
                        <li @click="handleSpeedChange(10)" :class="{ activate: rotationSpeed === 10 }">10x</li>
                        <li @click="handleSpeedChange(15)" :class="{ activate: rotationSpeed === 15 }">15x</li>
                        <li @click="handleSpeedChange(20)" :class="{ activate: rotationSpeed === 20 }">10x</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
    import verifypannelViewLeft from "@/views/panoramicDetection/verifyClue/multiComparison/verifypannelViewLeft.vue";
    import verifypannelViewRight from "@/views/panoramicDetection/verifyClue/multiComparison/verifypannelViewRight.vue";
    import {getOnePointMultiComInfoApi} from "@/api/commonApi";

    export default {
        name:'multiComparision',
        components: {verifypannelViewLeft,verifypannelViewRight},
        props:{
            currentActivateItem:Object,
            batchNumber:String,
            yaw:Number,
            pitch:Number,
            hfov:Number,
        },
        data(){
            return{
                cards: [],
                pannellumDialogVisible: false,
                pannellumDialogVisibleRight: false,
                uniquekey: 1,
                uniquekeyRight: 1,
                currentObj: {},
                currentObjRight: {},
                taskList: [], //当前页要展示的数据
                images: [],
                currentIndex: 0,// 当前显示的图片索引
                currentshowimg:[],//当前展示的图片列表
                limitimgcount:5, //限制展示的图片数量
                angleParams:{'yaw':this.yaw,'pitch':this.pitch,'hfov':this.hfov},//右侧View需要展示的图片数量
                url:require('@/assets/images/test.png'),
                isAddCluePoint:false,
                currentPointObj: '',
                currentBatchTotalClues:0,
                differenceValue:0,
                isAutoRotating:false,
                rotationSpeed:5,
                isShowFirstImage:true,
                firstImage:{
                    'batchName':'暂未获取',
                },
                allLayersCheck:[]
            }
        },
        methods:{
            handleGoBack() {
                this.$emit('backToSoloPanoramic');
            },
            async initializeImages() {
                // 初始化时，填充currentshowimg数组   当前页展示的多期对比数量
                this.currentshowimg = this.images.slice(this.currentIndex, this.currentIndex + this.limitimgcount);
                if (!this.pannellumDialogVisible){
                    this.pannellumDialogVisible = true;
                }
                if (!this.pannellumDialogVisibleRight){
                    this.pannellumDialogVisibleRight = true;
                }
                this.currentObj = this.firstImage;
                this.currentObjRight = this.currentshowimg[0];

            },
            //点击下一张图片
            nextImages() {
                if (this.currentIndex < this.images.length - 1) {
                    this.currentIndex++;
                    if (this.currentIndex >= this.limitimgcount){
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
            handleRightAngleParm(data){
                this.angleParams = data
            },
            //处理点击下面的每个图片，更改当前索引以及用于展示的currentshowimg列表
            handleClickDiv(item,currentImage){
                const currentImageIndex = this.images.findIndex((image) => image.batchId === currentImage.batchId)
                const clickImageIndex = this.images.findIndex((image) => image.batchId === item.batchId)
                //判断点的是后一个div还是前一个div
                if (currentImageIndex < clickImageIndex){
                    const chazhi = clickImageIndex - currentImageIndex
                    //说明点击的是下一张
                    this.currentIndex = this.currentIndex + chazhi;
                    if (this.currentIndex >= this.limitimgcount){
                        // 移除currentshowimg中的第一个元素
                        this.currentshowimg.shift();
                        // 将下一张图片添加到currentshowimg数组的末尾
                        this.currentshowimg.push(this.images[this.currentIndex]);
                    }
                }else if(currentImageIndex > clickImageIndex){
                    const chazhi = currentImageIndex - clickImageIndex
                    //说明点击的是上一张
                    this.currentIndex = this.currentIndex - chazhi;
                    // this.currentIndex--;
                    if (this.currentIndex <= this.limitimgcount) {
                        this.currentshowimg = this.images.slice(0, this.limitimgcount);
                    }
                }
                if(this.currentObjRight !== item && this.currentObj !== item){
                    this.uniquekeyRight += 1;
                    this.currentObjRight = item;
                }else{
                    this.$message.warning("该期线索已在左侧或者右侧显示，请选择其他时期线索!!!")
                }

            },

            //处理添加线索点到左侧的情况
            handleAddLeftCluePoint(){
                this.isAddCluePoint = true
            },
            closeAddCluePoint(data){
                this.isAddCluePoint = data.value
            },
            autoPlay(){
                this.isAutoRotating = !this.isAutoRotating;
                if(this.isAutoRotating){
                    this.$refs.leftpanorama.startRotate(this.rotationSpeed);
                    this.$refs.rightpanorama.startRotate(this.rotationSpeed);
                }else{
                    //发送停止旋转至左侧的指令
                    this.$refs.leftpanorama.stopRotate();
                    //发送停止旋转至右侧的指令
                    this.$refs.rightpanorama.stopRotate();
                    this.isAutoRotating = false
                }
            },
            updateRotateSpeed(){
                //发送更新速度的指令
                //发送开始旋转至左侧的指令
                this.$refs.leftpanorama.startRotate(this.rotationSpeed);
                //发送开始旋转至右侧的指令
                this.$refs.rightpanorama.startRotate(this.rotationSpeed);
            },
            handleClickView(){
                if (this.isAutoRotating){
                    this.isAutoRotating = false
                    //发送停止旋转至左侧的指令
                    this.$refs.leftpanorama.stopRotate();
                    //发送停止旋转至右侧的指令
                    this.$refs.rightpanorama.stopRotate();
                }
            },
            handleSpeedChange(speed) {
                this.rotationSpeed = Number(speed);
                this.updateRotateSpeed();
            },
            updateAllLayersCheck(value){
                this.allLayersCheck = value
            }

        },
        computed: {
            currentImage() {
                return this.images[this.currentIndex];
            },

        },
        watch: {
            currentshowimg(newvalue,oldvalue){
            },
            isAddCluePoint(newvalue,oldvalue){

            }
        },
        async mounted() {
            this.currentPointObj = this.currentActivateItem;
            const multiObjres = await getOnePointMultiComInfoApi(this.currentActivateItem.imageId)
            if (multiObjres.code === 0){
                this.images = multiObjres.data;
                if (this.images.length==0){
                    this.isShowFirstImage = false
                }else{
                    this.firstImage = this.images.find(image => image.batchId === this.batchNumber)
                    this.images = this.images.filter(image => image.batchId !== this.batchNumber)
                    // this.firstImage = this.images[0]  //先拿到基准数据在变更this.images
                    // this.images = this.images.slice(1)
                }
                this.initializeImages()
            }else {
                this.$message.error(multiObjres.msg)
            }

        },
        created() {}
    }
</script>


<style scoped>
    .mmain{
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
        width:calc(100% - 320px);
    }

    .rtop {
        display: flex;
        height: 60px; /* 占容器高度的10% */
        align-items: center;
        flex-direction: row;
        justify-content: space-between;
    }

    .zhixian{
        height: 2px;
        width: 100%;
        background-color: #d9d9d9;
        margin-bottom: 10px;
    }

    .rmain {
        display: flex;
        height: 65%; /* 占容器高度的60% */
        align-items: center;
        justify-content: space-between;
    }

    .rfoot {
        display: flex;
        align-items: center;
        margin: 10px;
        overflow-x: auto;
        flex: 1;
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
        top: 10;
        margin-top: 13px;
    }
    .gt-reback{
        font-size: 1rem;
        font-weight: bold;
        padding-left: 20px;
        cursor: pointer;
        padding-right: 10px;
        width: 10%;
    }

    .gt-reback i:hover {
        color: #1DA2FF; /* 鼠标悬停时的文字颜色 */
    }

    .add-point:hover {
        background-color: #1DA2FF; /* 鼠标悬停时的背景颜色 */
        color: white; /* 鼠标悬停时的文字颜色 */
    }

    .rm_left{
        width: 49%;
        height: 100%;
        margin-left: 10px;
        border: #f44336 3px solid;
    }
    .rm_right{
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
    .left-dimg{
        font-size: 0.9rem;
        position: relative; /* 使按钮容器的绝对定位相对于 .dimg */
        width: calc((100% / 5) - (var(--gap, 0px))); /* 减去间隙，如果有的话 */
        box-sizing: border-box;
        height: 90%;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .left-dimg span {
        display: block;
        text-align: center;
    }

    .dimg{
        font-size: 0.9rem;
        position: relative; /* 使按钮容器的绝对定位相对于 .dimg */
        width: calc((100% / 5) - (var(--gap, 0px))); /* 减去间隙，如果有的话 */
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .dimg span {
        display: block;
        text-align: center;
    }

    .left-img, .right-img{
        width: 90%; /* 缩略图的宽度 */
        height:90%;
        margin: 0 5px;
        cursor: pointer;
    }

    .dimg img.active {
        border: 3px solid #4caf50;
    }
    .left-img{
        border: 3px solid #f44336;
    }

    .rleftbtn{
        border: 1px solid black;
        color: black;
        margin-left: 5px;
    }
    .rleftbtn:hover{
        background-color: #1DA2FF;
    }
    .rrightbtn{
        border: 1px solid black;
        color: black;

        margin-right: 0px;
    }
    .rrightbtn:hover{
        background-color: #1DA2FF;
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

    ::v-deep .el-form-item__content{
        width: 160px;
    }
    .marquee {
        width: 70%;
        overflow: hidden;
        white-space: nowrap;
        box-sizing: border-box;
    }

    .marquee-content {
        display: inline-block;
        padding-left: 100%;
        animation: marquee 40s linear infinite;
        font-size: 0.9rem;
        font-weight: bold;
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

    .tools{
        background: aliceblue;
        height: 100%;
        width: 10%;
        display: flex;
        flex-direction: row;
        align-items: center;
    }
    .speed-control {
        position: absolute;
        top: 150px;
        background: rgba(255, 255, 255, 0.34);
        border-radius: 5px;
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 999;
        left: 50px;
        height: 150px;
        width: 40px;

    }
    .gt-alarms-list{
        margin-left: 10px;
    }
    .gt-alarms-list img {
        width: 35px;
        height: 35px
    }
    .speed-btn-group ul li {
        list-style-type: none; /* 去掉项目符号 */
        color: black;
        cursor: pointer;
        margin-top: 10px;
    }
    .speed-btn-group ul li:hover{
        color: #0a6fc0;
    }
    .speed-btn-group ul li.activate {
        color: #0a6fc0; /* 激活状态的文字颜色 */
        font-weight: bold; /* 激活状态的文字加粗 */
    }
</style>
