<template>
    <div class="vmain" v-if="batchNumber !== 0">
        <div class="mleft" v-if="isListVisible && !pointId">
            <div class="list-up">
                <div class="vtitle">批次号：{{batchNumber}}</div>
                <div class="fangkuai">{{total_todo_count}}</div>
            </div>
            <div class="filter">
                <!--线索筛选-->
                <el-form :model="formInfo">
                    <el-form-item>
                        <el-input placeholder="全景点名称" v-model="formInfo.pointName" style="width: 75%; margin-right: 10px" clearable></el-input>
                        <el-button type="primary" @click="getData" style="background-color: #11a8ed" size="mini">搜索</el-button>
                    </el-form-item>
                    <el-form-item>
                        <span>业务状态:</span>
                        <el-select style="width: 85px; margin: 0 5px" v-model="formInfo.status" clearable>
                            <el-option v-for="item in filterStatusList" :key="item.value" :label="item.label"
                                       :value="item.value"></el-option>
                        </el-select>
                        <span>有无线索:</span>
                        <el-select style="width: 85px; margin: 0 5px" v-model="formInfo.hadClue" clearable>
                            <el-option v-for="item in filterHadClueList" :key="item.value" :label="item.label"
                                       :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                </el-form>
            </div>
            <div class="vcards">
                <div
                        v-for="(item, index) in cards"
                        :key="index"
                        class="vcard"
                        :style="borderStyle(index)"
                        @click="handleCardClick(index,item)"
                >
                    <div class="card-title">{{ item.pointName}}</div>
                    <div style="height: 1px;width: 100%;background-color: #cccccc"></div>
                    <div class="card-info">
                        <span>图片名称: {{ item.imageName}}</span>
                        <!--            上传人: {{ item.uploader }}<br>-->
                        <span>所属街道: {{ item.street }}</span>
                        <span>创建时间: {{ item.createTime}}</span>
                        <div class="cluecounts">
                            <div class="done-count">线索数：{{item.doneCount}}</div>
                            <div class="undone-count">未判读：{{item.todoCount}}</div>
                        </div>
                    </div>
                    <div :class="getPointsStatus(item.status)[1]">{{getPointsStatus(item.status)[0]}}</div>
                </div>

            </div>
            <el-pagination
                    small
                    background
                    layout="prev, pager, next,total"
                    v-model="currentPage"
                    :total="total"
                    :page-size="pageSize"
                    @current-change="handleCurrentChange"
                    style="position: fixed">
            </el-pagination>
        </div>
        <div class="rzhixian">
        </div>
        <div class="tright" v-if="showWay===1">
<!--            <div v-if="!pointId">-->
<!--                <div class="shouqi" @click="toggle_list(false)" v-if="isListVisible "><i class="iconfont icon-xiangzuoshouqi"></i></div>-->
<!--                <div class="shouqi" @click="toggle_list(true)" v-else><i class="iconfont icon-xiangyouzhankai"></i></div>-->
<!--            </div>-->
            <verifypannelViewer
                    v-if="pannellumDialogVisible"
                    @update-data="handleUpdateData"
                    :currentObj="currentObj"
                    :taskList="taskList"
                    :batchNumber = "batchNumber"
                    @reback="handleClueReBack"
                    @refreshpage="handlerefreshpage"
                    @markerclick="handleMarkerClick"
                    @handleTotalTodoCount="handleTotalTodoCount"
                    @backToMultiPanoramic="backToMultiPanoramic"
                    @backToThreeScreen="backToThreeScreen"
                    @updateParentAllLayersCheck="updateParentAllLayersCheck"

            >
            </verifypannelViewer>
        </div>
        <div  class="tright" v-else-if="showWay===3">
            <div v-if="!pointId">
                <div class="shouqi" @click="toggle_list(false)" v-if="isListVisible "><i class="iconfont icon-xiangzuoshouqi"></i></div>
                <div class="shouqi" @click="toggle_list(true)" v-else><i class="iconfont icon-xiangyouzhankai"></i></div>
            </div>
            <three-screen   ref="multiComparision"
                            :currentActivateItem="currentObj"
                            :batchNumber="batchNumber"
                            :key="uniquekey"
                            :yaw="yaw"
                            :pitch="pitch"
                            :hfov="hfov"
                            :taskList="taskList"
                            :tempAllLayersCheck="tempAllLayersCheck"
                            @backToSoloPanoramic="backToSoloPanoramic"></three-screen>
        </div>
        <div class="tright" v-else>
            <multiComparision
                    ref="multiComparision"
                    :currentActivateItem="currentObj"
                    :batchNumber="batchNumber"
                    :key="uniquekey"
                    :yaw="yaw"
                    :pitch="pitch"
                    :hfov="hfov"
                    :tempAllLayersCheck="tempAllLayersCheck"
                    @backToSoloPanoramic="backToSoloPanoramic"
            >
            </multiComparision>
        </div>
    </div>
    <div style="font-size: 1.5rem;font-weight: bold" v-else>请先至任务管理页面选择对应批次数据，在进行线索核实！</div>
</template>

<script>
    import verifypannelViewer from "@/views/panoramicDetection/verifyClue/verifypannelViewer.vue";
    import multiComparision from "@/views/panoramicDetection/verifyClue/multiComparison/index.vue";
    import threeScreen from "@/views/panoramicDetection/verifyClue/multiComparison/threeScreen";
    import {
        getCurrentPageVerifyClueQuanjingPointsApi
        ,getAllPanoramaImageByBatchIdApi}
        from "@/api/commonApi";
    export default {
        name:'VerifyClue',
        components: {verifypannelViewer,multiComparision,threeScreen},
        data(){
            return{
                pointId:null,
                yaw:0,
                pitch:0,
                hfov:0,
                batchNumber:21,
                pageSize: 5,
                isListVisible:true,
                total: 5,
                currentPage:1,
                searchIcon:'el-icon-search',
                activeIndex:'',
                cards: [],
                pannellumDialogVisible: false,
                uniquekey: 1,
                currentObj: {},
                taskList: [],
                mapVisible: true,
                mapService:this.$store.state.mapService,
                center:this.$store.state.center,
                markerclicktag:0,
                total_todo_count:0,
                showWay:1,
                formInfo:{
                    pointName:'',
                    status:null,
                    hadClue:null
                },
                filterStatusList:[
                    {
                        value: 0,
                        label: '待判读'
                    },
                    {
                        value: 1,
                        label: '判读中'
                    },
                    {
                        value: 2,
                        label: '已判读'
                    }
                ],
                filterHadClueList:[
                    {
                        value: 0,
                        label: '无'
                    },
                    {
                        value: 1,
                        label: '有'
                    }
                ],
                tempAllLayersCheck: []
            }
        },
        methods:{
            toggle_list(flag){
                this.isListVisible = flag;
            },
            async handleUpdateData(){
                const para = {
                    pageIndex: this.currentPage,
                    pageSize: this.pageSize,
                    batchId:this.batchNumber,
                    pointName:this.formInfo.pointName,
                    imageName:this.formInfo.imageName,
                    status:this.formInfo.status,
                    hadClue:this.formInfo.hadClue
                }
                const res = await getCurrentPageVerifyClueQuanjingPointsApi(para)
                if (res.code === 0) {
                    this.cards = res.data.cards;
                }
            },
            async handleCurrentChange(val) {
                this.currentPage = val;
                const para = {
                    pageIndex: this.currentPage,
                    pageSize: this.pageSize,
                    batchId:this.batchNumber,
                    pointName:this.formInfo.pointName,
                    imageName:this.formInfo.imageName,
                    status:this.formInfo.status,
                    hadClue:this.formInfo.hadClue
                }
                const res =  await getCurrentPageVerifyClueQuanjingPointsApi(para)
                if (res.code === 0){
                    this.cards = res.data.cards;
                    this.total = res.total;
                    this.markerclicktag = '-1';
                    // this.taskList = res.data  //是为了画地图里面所有全景点的marker需要
                }else{
                    this.$message.error(res.msg)
                }
            },
            handleCardClick(index,item) {
                this.markerclicktag = 0
                this.activeIndex = index
                // this.uniquekey += 1;
                if (!this.pannellumDialogVisible){
                    this.pannellumDialogVisible = true;
                }
                this.currentObj = item;
                this.currentObj.point_id = this.taskList.find((i) => i.pointName === item.pointName).point_id;
            },
            handleClueReBack(tag){
                if (tag === '-1'){
                    this.$emit('rebackTask')
                    this.$router.push('/panoramic-detection/task-management')
                }
            },
            handlerefreshpage(){
                this.getData()
            },
            async getData(pointId){
                const para = {
                    pageIndex: this.currentPage,
                    pageSize: this.pageSize,
                    batchId:this.batchNumber,
                    pointName:this.formInfo.pointName,
                    imageName:this.formInfo.imageName,
                    status:this.formInfo.status,
                    hadClue:this.formInfo.hadClue
                }
                const res = await getCurrentPageVerifyClueQuanjingPointsApi(para)
                if (res.code === 0){
                    this.cards = res.data.cards;
                    this.total = res.total;
                    this.total_todo_count = res.data.total_todo_count;
                    //获取所有全景点
                    const paraAll = {
                        batchId: this.batchNumber,
                        pointName:this.formInfo.pointName,
                        imageName:this.formInfo.imageName,
                        status:this.formInfo.status,
                        hadClue:this.formInfo.hadClue
                    }
                    const resallQuanjingPoint = await getAllPanoramaImageByBatchIdApi(paraAll)
                    if (resallQuanjingPoint.code === 0){
                        this.taskList = resallQuanjingPoint.data.cards  //是为了画地图里面所有全景点的marker需要
                        this.handleCardClick(0,this.cards[0])
                    }else{
                        this.$message.error(resallQuanjingPoint.msg)
                    }
                }else {
                    this.$message.error(res.msg)
                }
            },
            async getCurrentData(pointId){
                //获取所有全景点
                const paraAll = {
                    batchId: this.batchNumber,
                    pointName:this.formInfo.pointName,
                    imageName:this.formInfo.imageName,
                    status:this.formInfo.status,
                    hadClue:this.formInfo.hadClue
                }
                const resallQuanjingPoint = await getAllPanoramaImageByBatchIdApi(paraAll)
                if (resallQuanjingPoint.code === 0){
                    this.taskList = resallQuanjingPoint.data.cards  //是为了画地图里面所有全景点的marker需要
                    let current = this.taskList.find((i) => i.pointId === pointId)
                    this.markerclicktag = 0
                    if (!this.pannellumDialogVisible){
                        this.pannellumDialogVisible = true;
                    }
                    this.currentObj = current;
                }else{
                    this.$message.error(resallQuanjingPoint.msg)
                }
            },
            async handleMarkerClick(tag){
                const index = this.taskList.findIndex((item) => item.pointName === tag);
                //根据index值确认数据分页
                this.currentPage = Math.floor(index / 5) + 1;
                await this.handleCurrentChange(this.currentPage);
                this.markerclicktag = 0;
                this.activeIndex = index % 5;


            },
            borderStyle(index) {
                if (this.markerclicktag === '-1') {
                    return {
                        border: '1px solid #ccc',
                    };
                } else {
                    return {
                        border: this.activeIndex === index ? '2px solid #11A8ED' : '1px solid #ccc',
                    };
                }
            },
            handleTotalTodoCount(data){
                this.total_todo_count = data
            },
            backToMultiPanoramic(currentTask,yaw,pitch,hfov){
                this.showWay=2;
                this.yaw=yaw;
                this.pitch=pitch;
                this.hfov=hfov;
                this.currentObj = currentTask;
            },
            backToThreeScreen(){
                this.showWay = 3;
            },
            backToSoloPanoramic(){
                this.showWay=1
            },
            getPointsStatus(status) {
                switch (status) {
                    case 1:
                        return ['判读中','status'];
                    case 2:
                        return ['已判读','done-status'];
                    default:
                        return ['待判读','init-status'];
                }
            },
            updateParentAllLayersCheck(value){ //这个是单景查看更新该index的图层信息
                this.tempAllLayersCheck = value
            }
        },
        computed: {
        },
        watch: {
            isListVisible(val) {
                this.pannellumDialogVisible=false
                this.$nextTick(() => {
                    this.pannellumDialogVisible = true
                })
            },
          async 'formInfo.hadClue'(newValue, oldValue) {
            await this.getData()
          },
        },
        async mounted() {
            this.batchNumber=this.$route.query.id;
            this.username =localStorage.getItem("username");
            if(!this.username){
                this.$router.push('/login')
            }
            this.pointId = this.$route.query.pointId;
            if (this.pointId){
                this.getCurrentData(this.pointId)
            }else{
                this.getData()
            }

        },
        created() {

        }
    }
</script>


<style scoped>
    .vmain{
        display: flex;
        height: 100%;
        width: 100%;
    }
    .mleft{
        width: 320px;
        height: 100%;
        position: relative;
    }
    .tright{
        flex: 1;
        width: calc(100% - 320px);
        height: 100%;
        position: relative;
    }
    .tright1{
        flex: 1;
        width: calc(100% - 320px);
        height: 100%;
        position: relative;
    }
    .rzhixian{
        flex: 0 0 1px;
        height: 100%;
        background-color: #E4E7ED;
    }
    .vtitle{
        font-size: 1rem;
        font-weight: bold;
        margin: 10px;
    }
    .shouqi{
        width:16px;
        height:120px;
        font-size: 1rem;
        justify-content: center;
        display: flex;
        align-items: center;
        position: absolute; /* 设置为绝对定位 */
        top: 50%; /* 垂直居中 */
        left: 0; /* 左边对齐 */
        background-color: #2db6f4;
        z-index:999;
        transform: translateY(-50%); /* 垂直居中修正 */
        border-bottom-right-radius: 50px;
        border-top-right-radius: 50px;
    }
    .shouqi:hover{
        cursor: pointer;
    }
    .el-pager li,
    .el-pagination__editor,
    .el-pagination .btn-prev,
    .el-pagination .btn-next {
        margin: 0 1px !important;
    }

    .vinput{
        margin: 10px;
        height: 3%;
    }
    .vcards{
        margin: 0px 10px;
        overflow-y: auto;
        height: calc(100% - 200px);
    //flex:1;
        justify-content: space-between; /* 确保卡片之间有间距 */
    }
    .vcard {
        position: relative;
        border: 1px solid #ccc;
        margin-bottom: 4px;
        cursor: pointer; /* 添加手型指针 */
        transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out, background-color 0.3s ease-in-out; /* 添加平滑过渡效果 */
        overflow: hidden;
        flex: 1;
    }

    .card-title {
        font-weight: bold;
        margin-bottom: 5px;
        margin-top: 5px;
        margin-left: 10px;
    }

    .card-info {
        font-size: 12px;
        display: flex;
        flex-direction: column;
        padding: 10px;
    }
    .card-info span{
        margin-bottom: 8px;
    }
    .el-pagination {
        bottom: 10px;
    }
    .vcard:hover{
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); /* 添加阴影效果 */
    }
    #mapContainer {
        height: 100%;
        width: 100%;
        background-color: #ffffff;
    }

    .cluecounts {
        position: absolute;
        right: 0px;
        top: 0px;
        color: #fff;
        padding: 5px;
        width: 160px;
        height: 30px;
        text-align: center;
        align-items: center;
        justify-content: center;
        /* font-size: 14px; */
        display: flex;
        flex-direction: row;
    }

    .fangkuai{
        width: 34px;
        height: 34px;
        background-color: #2DB6F4;
        margin-top: 5px;
        display: flex; /* 使用 flex 布局 */
        justify-content: center; /* 水平居中 */
        align-items: center; /* 垂直居中 */
        font-size: 14px; /* 设置字体大小，根据需要调整 */
        color: white;

    }
    .list-up{
        height: 40px;
        display: flex;
        flex-direction: row;
    }
    .done-count{
        width: 50%;
        height: 100%;
        background-color: mediumseagreen;
    }
    .undone-count{
        width: 50%;
        height: 100%;
        background-color: red;
    }

    .el-color-picker__icon, .el-input, .el-textarea {
        display: inline-block;
        width: 100%;
    }

    .status ,.done-status, .init-status{
        position: absolute;
        right: -25px;
        bottom: 10px;
        width: 100px;
        height: 20px;
        text-align: center;
        color: #fff;
        font-size: 12px;
        transform: rotate(45deg);
        -ms-transform: rotate(45deg);
        -o-transform: rotate(45deg);
        -webkit-transform: rotate(316deg);

        overflow: hidden;
    }
    .status{
        background: #2DB6F4;
    }
    .init-status{
        background: #ccc;
    }
    .done-status {
        background: #fd6805;
    }
    ::v-deep .el-pagination{
        bottom: 0px;
    }
    .filter{
        height: 100px;
        margin-top: 15px;
    }
    ::v-deep .el-form-item--mini.el-form-item, .el-form-item--small.el-form-item {
        margin-bottom: 18px;
        margin-left: 5px;
    }
    ::v-deep .el-input__inner {
        color: #fff;
    }
</style>
