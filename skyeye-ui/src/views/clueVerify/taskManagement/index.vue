<template>
    <div class="se-container">
        <div class="left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">新增核实任务</span>
            </div>
            <div class="left-content-body">
                <div class="excel-upload">
                    <!--上传网格表单-->
                    <el-form :inline="true" size="small" :model="form" ref="form">
                        <el-form-item label="上传坐标文件:" label-width="110px" style="margin-bottom: 20px;display: flex">
                            <el-input type="text" placeholder="请上传excel" v-model="form.excelfile">
                                <template slot="append">
                                    <el-button icon="el-icon-folder-opened" size="medium" @click="checkexcel"></el-button>
                                    <input type="file" id="excel" accept=".xlsx, .xls" style="display: none;"
                                           @change="handleFileUpload"/>
                                </template>
                            </el-input>
                        </el-form-item>
                        <el-form-item label="上传人:" label-width="100px">
                            <el-input v-model="form.uploadPerson" disabled></el-input>
                        </el-form-item>
                        <el-form-item class="button-container">
                            <el-button type="primary" @click="handelSubmit">提交</el-button>
                            <el-button @click="resetForm">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content" v-if="!isShowMap">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-grid"></span>
                <span class="title">任务管理</span>
            </div>
            <div class="right-content-body">
                <div class="filter">
                    <!--数据筛选-->
                    <el-form :inline="true" size="small" :model="filterInfo" ref="filterInfo">
                        <el-form-item>
                            <el-input v-model="filterInfo.task_name" placeholder="请输入任务编号"/>
                        </el-form-item>
                        <el-form-item>
                            <el-button type="primary" @click="getTaskList(filterInfo.task_name)">查询</el-button>
                            <el-button @click="handleTask">删除</el-button>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="grid-table">
                    <!--网格数据-->
                    <el-table max-height="100%" height="100%" :data="taskData" stripe style="width: 100%" border @selection-change="handleSelectionChange">
                        <el-table-column type="selection" width="55" align="center"></el-table-column>
                        <el-table-column prop="task_id" label="任务编号" align="center" width="200"></el-table-column>
                        <el-table-column prop="create_time" label="开始日期" align="center" width="100"></el-table-column>
                        <el-table-column prop="task_name" label="文件名称" align="center" width="100"></el-table-column>
                        <el-table-column prop="status" label="状态" align="center" width="70"></el-table-column>
                        <el-table-column prop="count" label="需核实点位数" align="center" width="120"></el-table-column>
                        <el-table-column prop="video_done_capture" label="视频已拍摄/待拍摄" align="center" width="130"></el-table-column>
                        <el-table-column label="操作"  align="center">
                            <template slot-scope="scope" >
                                <el-button type="text" size="medium" :style="{ color: pushBtnText(scope.row.status)[1] }"  @click="handleCoordinateEdit(scope.row)" :disabled="scope.row.status === '待拍摄'">坐标编辑</el-button>
                                <el-button type="text" size="medium" :style="{ color: pushBtnText(scope.row.status)[1] }"  @click="handleInformationPush(scope.row)" :disabled="scope.row.status === '待拍摄'">{{pushBtnText(scope.row.status)[0]}}</el-button>
                                <el-button type="text" size="medium" style="color: blue" @click="">数据上传</el-button>
                                <el-button type="text" size="medium" style="color: blue" @click="">数据下载</el-button>
                                <el-button type="text" size="medium" style="color: blue" @click="handleDataView(scope.row)">数据查看</el-button>
                                <el-button type="text" size="medium" style="color: blue" @click="">任务终止</el-button>

                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                <div class="page">
                    <!--分页设置-->
                    <el-pagination
                            background
                            @size-change="handleSizeChange"
                            @current-change="handleCurrentChange"
                            :current-page="filterInfo.page"
                            :page-sizes="[10, 20, 30, 40]"
                            :page-size="filterInfo.limit"
                            layout="sizes, prev, pager, next, total"
                            :total="dataCount"
                    >
                    </el-pagination>
                </div>
            </div>
        </div>
        <div class="right-contentmap" id="mapContainer" v-if="isShowMap"></div>
        <div v-if="isShowMap" class="info-title" style="position: absolute">
            <span>任务编号：{{currentTaskNum}}</span>
            <div>
                <el-button class="goback" type="primary" icon="el-icon-plus"  @click="handleAddmarker">添加点位</el-button>
                <el-button class="goback" type="primary" icon="el-icon-circle-close"  @click="handleCancle">取消添加</el-button>
                <el-button class="goback" type="primary" icon="el-icon-delete"  @click="removeMarker">删除点位</el-button>
                <el-button class="goback" type="primary" icon="el-icon-back"  @click="handleGoBack">返回上级</el-button>
            </div>

        </div>

        <el-dialog width="30%" :visible.sync="uploading" append-to-body>
            <el-progress :text-inside="true" :stroke-width="18" :percentage="upProgress" status="success" style="margin-top:10px"></el-progress>
        </el-dialog>

        <el-dialog title="添加线索点"
                   :visible.sync="labelVisible"
                   :modal="false"
                   class="label-dialog"
                   :close-on-click-modal="false"
                   @close="handelAddCancle"
        >
            <el-form class="form_class">
                <el-form-item label="点位x:" style="display: flex">
                    <el-input v-model="pixel_x">
                    </el-input>
                </el-form-item>
                <el-form-item label="点位y:" style="display: flex">
                    <el-input v-model="pixel_y"></el-input>
                </el-form-item>
                <el-form-item label="行政区划:" style="display: flex">
                    <el-input v-model="division_code"></el-input>
                </el-form-item>
                <el-form-item label="层级:" style="display: flex">
                    <el-input v-model="level"></el-input>
                </el-form-item>
                <el-form-item label="地址:" style="display: flex">
                    <el-input v-model="address"></el-input>
                </el-form-item>
                <div class="btn-uploading">
                    <el-button style="margin-right: 20px" type="primary" size="medium" @click="handleAddMarker">添加
                    </el-button>
                    <el-button style="margin-left: 20px" size="medium" @click="handelAddCancle">取消</el-button>
                </div>
            </el-form>
        </el-dialog>

    </div>
</template>

<script>
import {
    getMapInfoApi, getClueVerifyTableApi, verifyClueByTaskIDApi, addMarkerApi, deleteMarkerApi,postInformationPush,
    deleteTaskApi
} from '@/api/commonApi';
import axios from "axios";
import {TiledMapLayer} from "@supermap/iclient-leaflet";
export default {
    name: 'GridManagementIndex',
    data() {
        return {
            upProgress: 0,//上传进度
            uploading: false,//上传进度表单控制
            form: {
                excelfile: '',
                uploadPerson: '',
            }, //上传表单
            filterInfo: {
                keyword: '',
                dataRange:[],
                task_status:'',
                task_name:'',
                limit: 10,
                page: 1
            }, //筛选参数
            baseUrl:process.env.VUE_APP_API_URL,//请求地址
            taskData:[],
            selectedTask:[],
            dataCount:1,
            uploadfile: null,
            mapService: '',
            center: '',
            crs: L.CRS.EPSG4326,
            drawMarkers: [],//在地图上加载的所有marker集合
            marker: null,//线索标记
            clusterLayer: L.layerGroup(),//聚合图层组
            allClueList: [],//所有线索集合，10000
            isShowMap:false,
            addMarkerList:[],
            isMapClickEnabled:false,
            currentClickMarkerID:-1,
            defaultIconBlue:L.icon({
                    iconUrl: require('@/assets/images/marker-icon-blue.png'),
                    iconSize: [25, 40], // 图标大小
                    iconAnchor: [12.5, 40], // 图标锚点（中心点）
                    popupAnchor: [-3, -40] // 弹出窗偏移量
            }),
            //换成红色图标
             redIcon : L.icon({
                 iconUrl: require('@/assets/images/marker-icon-red.png'),
                 iconSize: [25, 40], // 图标大小
                 iconAnchor: [12.5, 40], // 图标锚点（中心点）
                 popupAnchor: [-3, -40] // 弹出窗偏移量
             }),
            currentTaskNum:0,
            pixel_x: 0,
            pixel_y: 0,
            level:0,
            division_code:'',
            address:'',
            labelVisible:false,
            current_add_marker:null,
            pushed: false
        };
    },
    methods: {
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.filterInfo.limit = val;
            this.filterInfo.page = 1
        },
        handleCurrentChange(val) {
            // 改变页码
            this.filterInfo.page = val;
        },
        handleSelectionChange(val){
            //选择的网格数据
            this.selectedTask = val.map((item) => item.task_id)
        },
        checkexcel() {
            //网格标签点击事件
            document.querySelector('#excel').click()
        },
        handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                this.form.excelfile = file.name; // 设置文件名
                this.$message.success("文件上传成功")
            }
        },
        async handelSubmit(){
            let file = document.getElementById('excel');
            this.uploadfile = file.files[0];
            // // 创建一个 FormData 对象
            const formData = new FormData();
            // // 将文件添加到 FormData 对象中
            formData.append('file', this.uploadfile);
            try {
                const res = await axios.post(this.baseUrl+"/common/files", formData, {
                    headers: {'content-type': 'application/x-www-form-urlencoded','Authorization': 'Bearer ' + localStorage.getItem('tokens')},

                });
                if (res.data.code === 0) {
                    this.uploading = null;
                    this.resetForm();
                    this.getTaskList();
                    this.$message.success('上传成功！');
                } else {
                    this.$message.error(res.msg);
                }
            } catch (error) {
                this.$message.error("上传失败");
            }

        },
        async getTaskList(task_name) {
            //  获取线索表格记录
            const para = {
                task_name:task_name,
                limit: this.filterInfo.limit,
                page: this.filterInfo.page,
            }
            const res = await getClueVerifyTableApi(para);
            if (res.code!==0){
                this.$message.error(res.msg)
                return
            }else{
                this.taskData = res.data
                this.dataCount = res.count
            }
        },
        resetForm(){
            this.form.excelfile = '';
            this.form.uploadPerson = ''
        },
        initMap() {
            if (process.env.NODE_ENV === "production"){
                this.map = L.map('mapContainer',
                    {
                        crs: this.crs,
                        center: this.center,//中心坐标
                        zoom: 12,//缩放级别
                        zoomControl: false, //缩放组件
                        attributionControl: false, //去掉右下角logo
                        preferCanvas: true,
                    });
                //加载全景点
                const layer = new TiledMapLayer(this.mapService);
                layer.addTo(this.map);
            }else{
                const center = []
                if (this.allClueList.length > 0){
                    center.push(this.allClueList[0].latitude)
                    center.push(this.allClueList[0].longitude)
                }else{
                    center = this.center
                }
                this.map = L.map('mapContainer',{attributionControl: false}).setView(center,14);
                // 添加天地图瓦片图层
                const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
            }
            // //初始化地图
            // this.map = L.map('mapContainer',
            //     {
            //         crs: this.crs,
            //         center: this.center,//中心坐标
            //         zoom: 12,//缩放级别
            //         zoomControl: false, //缩放组件
            //         attributionControl: false, //去掉右下角logo
            //         preferCanvas: true,
            //     });
            // //加载全景点
            // const layer = new TiledMapLayer(this.mapService);
            // layer.addTo(this.map);
            this.allClueList.forEach((item, index) => {
                const marker = L.marker([item.latitude, item.longitude], {icon: this.defaultIconBlue})
                marker.bindPopup(item.address).addTo(this.map)
                const marker_obj = {'id': item.clue_id, 'marker': marker,"latitude":item.latitude,"longitude":item.longitude}
                this.drawMarkers.push(marker_obj)
                marker.on('click', (e) => {
                    this.currentClickMarkerID = marker_obj
                    marker_obj.marker.setIcon(this.redIcon)
                    this.drawMarkers.forEach((item) => {
                        if (item.id !== marker_obj.id) {
                            item.marker.setIcon(this.defaultIconBlue)
                        }
                    })
                })
            })
        },
        async mapClick(e) {
            const defaultIconviolet = L.icon({
                iconUrl: require('@/assets/images/marker-icon-violet.png'),
                iconSize: [25, 40], // 图标大小
                iconAnchor: [12.5, 40], // 图标锚点（中心点）
                popupAnchor: [-3, -40] // 弹出窗偏移量
            })
            const lat = e.latlng.lat;
            const lon = e.latlng.lng;
            const marker = L.marker([lat, lon], {icon: defaultIconviolet})
            marker.addTo(this.map)
            this.pixel_x = lon
            this.pixel_y = lat
            this.labelVisible = true
            this.current_add_marker = marker

        },
        async handleAddMarker(){
            const parm = {
                task_id:this.currentTaskNum,
                longitude:this.pixel_x,
                latitude:this.pixel_y,
                division_code:this.division_code,
                level:this.level,
                address:this.address
            }
            const res = await addMarkerApi(parm);
            if (res.code === 0){
                this.$message.success('添加点位成功')
                // const marker_obj = {'id': '2222', 'marker': this.current_add_marker,"latitude":lat,"longitude":lon}
                // this.drawMarkers.push(marker_obj)
                // marker.on('click', (e) => {
                //     this.currentClickMarkerID = marker_obj
                // })
                this.labelVisible = false
                if (this.map){
                    this.map.remove(); // 移除地图实例
                }
                await this.getAllClue(this.currentTaskNum)
                this.initMap()
            }else {
                this.map.removeLayer(this.current_add_marker);
                this.$message.error(res.msg)
                this.labelVisible = false
            }
        },

        async getAllClue(task_id) {
            //获取线索列表
            const form = {
                task_id: parseInt(task_id)
            }
            const res = await verifyClueByTaskIDApi(form)
            if (res.code !== 0) {
                this.$message.error(res.msg)
                return
            }else{
                this.allClueList = res.data
            }
        },
        handleGoBack(){
            this.map.remove()
            this.isShowMap = false
        },
        handleCancle(){
          this.isMapClickEnabled = false
            this.map.off('click', this.mapClick);
        },
       async handleCoordinateEdit(row){
            this.isShowMap = true
            const res = await getMapInfoApi();
            if (res.code === 0) {
                this.mapService = res.data.map_service;
                this.center = res.data.center;
                this.currentTaskNum = row.task_id
                await this.getAllClue(row.task_id)
                this.initMap();
            }
        },
        async handleInformationPush(row) {
            //异常点推送接口
            // const res = await postInformationPush(row);
            const res = await postInformationPush({'task_id':row.task_id});
            if (res.code === 0) {
              this.$message.success("推送成功！")
                // this.initMap();
                this.getTaskList()

            }else{
                this.$message.error(res.msg)
            }
        },
        handleAddmarker(){
            this.isMapClickEnabled = true
            this.map.on('click', this.mapClick);
        },
        async removeMarker() {
            const marker = this.currentClickMarkerID.marker
            const id = this.currentClickMarkerID.id
            const markerToRemove = this.drawMarkers.find(m => m.id === id);
            if (markerToRemove) {
                const res = await deleteMarkerApi({verify_clue_id:id})
                if (res.code === 0){
                    this.map.removeLayer(markerToRemove.marker);
                    this.drawMarkers = this.drawMarkers.filter(m => m.id !== id);
                }else{
                    this.$message.error(res.msg)
                }
            }
        },
        handleDataView(row){
            const task_id = row.task_id
            this.$router.push({name:'mapOverview',query:{ task_id}})
        },
        handelAddCancle(){
            this.map.removeLayer(this.current_add_marker);
            this.labelVisible = false

        },
        pushBtnText(status){
            if(status === '待拍摄'){
                return ['已推送','gray']
            }else{
                return ['坐标推送','blue']
            }
        },
        handleTask(){
            this.$confirm('是否确认任务,删除不可撤销?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteTaskApi(JSON.stringify({'task_id_list':this.selectedTask}))
                    if (res.code === 0){
                        this.$message.success(res.msg)
                        this.getTaskList()
                    }else{
                        this.$message.error(res.msg)
                    }
                })
                .catch((error) => {
                    console.log(error)
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });

                })
        }
    },

    created() {

    },
    async mounted() {
        this.form.uploadPerson = localStorage.getItem('username')
        this.getTaskList(this.filterInfo.task_name)
    },
    computed:{

    },
    watch:{

    }
};
</script>

<style lang="scss" scoped>
.se-container {
  padding: 10px;
  height: 100%;
  position: relative;
}
.left-content {
  width: 320px;//侧边栏设置
  height: 100%;
  border-radius: 2px;
  background-color: #fff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}
.border{
  width: 10px;
  height: 100%;
}
::v-deep .grid-upload .el-input {
  width: 220px;//输入框设置
}

.button-container {
  display: flex;
  justify-content: center;
}
.right-content {
  width: calc(100% - 340px);//剩余宽度
  height: 100%;
  flex-direction: column;
  border-radius: 2px;
  background-color: #fff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}
.right-contentmap{
  width: calc(100% - 340px);//剩余宽度
  height: 100%;
  flex-direction: column;
  border-radius: 2px;
  background-color: #fff;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}
.grid-table {
  margin-top: 20px;
  flex-grow: 1;//占据剩余高度
  height: calc(100% - 100px);
}
.page {
  position: absolute;//绝对定位
  right: 20px;
  bottom: 20px;
}
.filter .el-form-item{
  margin: 0 30px 0 0;
}
.icon {
  font-size: 24px;
  color: #42b4f2;
  padding-right: 5px;
}

.left-content-header, .right-content-header {
  padding: 0 16px;
  border-bottom: 1px solid #dcdcdc;
  color: #000;
  font-weight: 700;
  font-size: 16px;
  height: 40px;
  line-height: 40px;
}

.left-content-body {
  padding-top: 20px;
}

.right-content-body {
  padding: 20px 10px 10px 10px;
  height: calc(100% - 40px);

}
.el-input-group {
  line-height: normal;
  display: inline-table;
  width: 85%;
  border-collapse: separate;
  border-spacing: 0;
}
.info-title{
  position: absolute;
  z-index: 9999;
  width: calc(100% - 340px);
  height: 40px;
  right: 0px;
  display: flex;
  top: 10px;
  background-color: #ebeef596;
  align-items: center;
}
.info-title span{
  width: 65%;
  color: white;
  font-weight: bold;
  font-size: 18px;
}
.info-title div{
  flex: 1;
}
::v-deep .label-dialog .el-dialog {
  position: absolute;
  width: 400px;
  left: 50%;
  margin-left: -200px;
  background-color: #fff; /* 半透明背景 */
  box-shadow: none; /* 可选，移除阴影 */
  z-index: 999;
  color: #fff;
}
::v-deep .transparent-dialog .el-dialog__header, .label-dialog .el-dialog__header {
  text-align: center;
  font-weight: 700;
  border-bottom: 1px solid #fff;
}

::v-deep .transparent-dialog .el-dialog__title, .label-dialog .el-dialog__title {
  color: black;
  font-size: 16px;
}
::v-deep .label-dialog .el-form-item__label {
  color: black;
  width: 80px;
  text-align: left;
}
::v-deep .leaflet-top {
  top: 50px;
}
</style>
