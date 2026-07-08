<template>
    <div class="se-container">
        <div class="main-content">
            <div class="left-content">
                <div v-if="isProject" >
                <div @click="dialogTableVisible = true" class="left-content-top">
                    <div class="upload-btn-item">
                        <i class="el-icon-upload" style="font-size: 45px"></i>
                        <div>点此上传文件并开始解译</div>
                    </div>
                </div>
                <div class="left-content-middle">
                    <el-form>
                        <el-form-item>
                            <el-input type="text" placeholder="请输入项目名称" v-model="searchName">
                                <template slot="append">
                                    <el-button icon="el-icon-search" size="medium"
                                               @click="searchProject"></el-button>
                                </template>
                            </el-input>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="left-content-bottom">

                        <div style="height: 20%"
                                v-for="(item, index) in displayProj"
                                :key="index"
                        >
                            <projectcards :proj="item" @opentask="openTask" @removeProject="removeProject(index)"/>
                        </div>
                </div>
                <el-pagination
                        small
                        background
                        layout="prev, pager, next, total"
                        :page-size="projectPageSize"
                        :total="totalProjectCount"
                        :current-page.sync="projCurrentPage"
                        @current-change="handleProjectPageChange"
                        style="position: fixed"

                >
                </el-pagination>
                </div>
                <div v-if="isTask">
                    <div class="left-content-top-task">
                         <div> <i class="el-icon-back" @click="goBack"  style="font-size:16px"></i>
                             <span style="font-size: 16px;margin-left: 10px">{{ currentProjectName }}</span>
                         </div>


                    </div>
                    <div class="left-content-middle">
                        <el-form>
                            <el-form-item>
                                <el-input type="text" placeholder="请输入任务名称" v-model="searchName">
                                    <template slot="append">
                                        <el-button icon="el-icon-search" size="medium" @click="searchTask"></el-button>
                                    </template>
                                </el-input>

                            </el-form-item>
                        </el-form>
                    </div>
                    <div class="left-content-bottom">
                            <div
                                    v-for="(item, index) in taskList"
                                    :key="index"
                            >
                                <cards :data="item" @open-pannellumViewer="openpannellumViewer"
                                       @remove="removeCard(index)"/>
                            </div>

                    </div>

                    <el-pagination
                            small
                            background
                            layout="prev, pager, next, total"
                            :page-size="pageSize"
                            :total="totalTaskCount"
                            :current-page.sync="currentPage"
                            @current-change="handleTaskPageChange"
                            style="position: fixed"
                    >
                    </el-pagination>
                </div>

            </div>

            <div class="right-content">
                <pannellumViewer v-if="pannellumDialogVisible" @open-pannellumViewer="openpannellumViewer"
                                 :key="uniquekey" :currentObj="currentObj" :taskList="taskList"></pannellumViewer>
                <div v-if="mapVisible" id="map"></div>
            </div>

        </div>

<!--        <el-dialog title="上传数据" :visible.sync="dialogTableVisible" width="30%" append-to-body>-->
<!--            <div style="width: 100%; height: 35vh; padding-top: 10px">-->
<!--                <el-form class="form_class">-->
<!--                    <el-form-item label="视角选择:" label-width="100px">-->
<!--                        <el-radio-group v-model="checkedview">-->
<!--                            <el-radio v-for="view in views" :label="view" :key="view"></el-radio>-->
<!--                        </el-radio-group>-->
<!--                    </el-form-item>-->
<!--                    <el-form-item label="文件上传:" label-width="100px">-->
<!--                        <el-input type="text" placeholder="请上传图片文件" v-model="fileName">-->
<!--                            <template slot="append">-->
<!--                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkFile"></el-button>-->
<!--                                <input type="file" id="fileinput" style="display: none;"-->
<!--                                       @change="handleFolderSelection"/>-->
<!--                            </template>-->
<!--                        </el-input>-->
<!--                    </el-form-item>-->
<!--                    <el-form-item label="操作人员:" label-width="100px">-->
<!--                        <el-input v-model="username" :disabled="true"></el-input>-->
<!--                    </el-form-item>-->
<!--                    <div class="btn-uploading">-->
<!--                        <el-button style="margin-right: 20px" type="primary" size="medium" @click="inference">解译<i-->
<!--                                class="el-icon-upload el-icon&#45;&#45;right"></i></el-button>-->
<!--                        <el-button style="margin-left: 20px" size="medium" @click="resetBtn">重置</el-button>-->
<!--                    </div>-->
<!--                </el-form>-->
<!--            </div>-->

<!--            <el-dialog-->
<!--                    width="30%"-->
<!--                    :visible.sync="uploading"-->
<!--                    append-to-body>-->
<!--                <el-progress-->
<!--                        :text-inside="true"-->
<!--                        :stroke-width="18"-->
<!--                        :percentage="upProgress"-->
<!--                        status="success"-->
<!--                        style="margin-top:10px">-->
<!--                </el-progress>-->
<!--            </el-dialog>-->
<!--        </el-dialog>-->
        <el-dialog title="上传数据" :visible.sync="dialogTableVisible" width="30%" append-to-body>
            <div style="width: 100%; height: 35vh; padding-top: 10px">
                <el-form class="form_class">
                    <el-form-item label="任务名称:" label-width="100px">
                        <el-input placeholder="请输入名称" v-model="task_name"></el-input>
                    </el-form-item>
                    <el-form-item label="视角选择:" label-width="100px">
                        <el-radio-group v-model="checkedview">
                            <el-radio v-for="view in views" :label="view" :key="view"></el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <el-form-item label="文件上传:" label-width="100px">
                        <el-input type="text" placeholder="请上传文件夹" v-model="folderPath">
                            <template slot="append">
                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkFile"></el-button>
                                <input type="file" id="fileinput" webkitdirectory style="display: none;"
                                       @change="handleFolderSelection"/>
                            </template>
                        </el-input>
                    </el-form-item>
                    <el-form-item label="操作人员:" label-width="100px">
                        <el-input v-model="username" :disabled="true"></el-input>
                    </el-form-item>
                    <div class="btn-uploading">
                        <el-button style="margin-right: 20px" type="primary" size="medium" @click="inference">解译<i
                                class="el-icon-upload el-icon--right"></i></el-button>
                        <el-button style="margin-left: 20px" size="medium" @click="resetBtn">重置</el-button>
                    </div>
                </el-form>
            </div>

            <el-dialog
                    width="30%"
                    :visible.sync="uploading"
                    append-to-body>
                <el-progress
                        :text-inside="true"
                        :stroke-width="18"
                        :percentage="upProgress"
                        status="success"
                        style="margin-top:10px">
                </el-progress>
            </el-dialog>
        </el-dialog>


    </div>

</template>

<script>
    import Cards from "./Cards";
    import projectcards from "./projectCards";
    import pannellumViewer from "./pannellumViewer";
    import axios from "axios";
    import {TiledMapLayer} from '@supermap/iclient-leaflet';
    import {getTaskDataListApi,getMapInfoApi,postProjectApi} from "@/api/commonApi";

    export default {
        name: "PanoramaIndex",
        data() {
            return {
                currentPage: 1, //当前页码
                pageSize: 5, //每页显示的数量
                projCurrentPage: 1, //当前页码
                projectPageSize:4, //每页显示的数量
                taskList: [], //当前页要展示的数据
                displayProj:[],
                delete_card_count: 0, //当前已删除的card数量
                fileList: [], //文件列表
                folderPath: "", //文件夹名称

                dialogTableVisible: false,
                fileName: "", //文件名称
                uploading: false,
                uploadSuccess: null, // 文件夹上传状态标识
                searchName: "",
                currentObj: {},
                task_name: '',

                mapVisible: true,
                task_type: '全景检测',
                checkedview: '正视',
                views: ['正视', '斜视'],
                username: '',
                showDetails: false,
                selectedCardData: {},
                detailsKey: "",
                pannellumDialogVisible: false,
                uniquekey: 0,
                upProgress: 0,
                isProject:true,
                isTask:false,
                projID:0,
                currentProjectName:'',
                totalTaskCount:0,//任务总数量
                totalProjectCount:0,//项目总数量

                mapService: '',
                center: '',
                baseUrl: process.env.VUE_APP_API_URL,
            };
        },
        computed: {},
        watch: {},
        components: {
            Cards,
            projectcards,
            pannellumViewer,
        },
        async mounted() {
            this.username = localStorage.getItem("username");
            if (!this.username) {
                this.$router.push('/login')
            }
            this.fetchProject();
            const res = await getMapInfoApi();
            if (res.code === 0) {
                this.mapService = res.data.map_service;
                this.center = res.data.center;
                this.initMap();
                this.fetchTask();
            }

        },
        methods: {
            initMap(){

                    this.map = L.map('map',{
                        crs: L.CRS.EPSG3857,
                        center: this.center,//中心坐标
                        zoom: 14,//缩放级别
                        zoomControl: false, //缩放组件
                        attributionControl: false, //去掉右下角logo
                    }).setView(this.center, 14);
                    // 添加天地图瓦片图层
                    const layer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
                    layer.addTo(this.map);


            },
            openpannellumViewer(obj) {
                this.uniquekey += 1;
                this.pannellumDialogVisible = true;
                this.mapVisible = false;
                this.currentObj = obj;
            },
            checkFile() {
                document.querySelector('#fileinput').click()
            },
            handleFolderSelection(event) {
                const selectedFolder = event.target.files[0];
                if (selectedFolder) {
                    this.folderPath = selectedFolder.webkitRelativePath.split('/')[0]; // 更新文件夹路径
                    this.uploadSuccess = null; // 重置上传状态
                }
            },
            async inference() {
                try {
                    this.uploading = true;
                    //拿到元素节点
                    let twos = document.getElementById('fileinput');
                    //读取dom节点图片
                    const fileList = twos.files;
                    if (fileList.length > 0 && this.task_name.length > 0) {
                        const folderPath = fileList[0].webkitRelativePath.split('/')[0];
                        let formData = new FormData();
                        for (let i = 0; i < fileList.length; i++) {
                            formData.append('files' + i, fileList[i]);
                        }
                        // 传递 任务名、文件夹路径到后端
                        formData.append('folderPath', folderPath);
                        formData.append('project_name', this.task_name);
                        formData.append('view_angle',this.checkedview);

                        let own = this;
                        const {data: res} = await axios.post(this.baseUrl + "/common/panorama", formData, {
                            headers: {'content-type': 'application/x-www-form-urlencoded'},
                            onUploadProgress: progressEvent => {
                                // 计算上传进度并更新你的进度条
                                own.upProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                            }
                        });
                        // 设置文件夹名称和上传成功状态
                        this.uploading = null;
                        this.uploadSuccess = true;
                        this.dialogTableVisible = false;
                        await this.fetchProject();
                        this.$message({
                            message: '解译成功！',
                            type: 'success'
                        });
                    } else {
                        this.$message({
                            message: '请填写数据信息',
                            type: 'warning'
                        });
                    }
                } catch (error) {
                    this.uploading = null;
                    this.uploadSuccess = false;
                    this.$message.error('解译失败，请重试。');
                }
            },
            resetBtn() {
                this.fileName = '';
            },
            //监听项目页码变化
            handleProjectPageChange(newPage) {
                this.projcurrentPage = newPage;
                this.fetchProject();
            },
            //监听任务页码变化
            handleTaskPageChange(newPage) {
                this.currentPage = newPage;
                this.fetchTask();
            },
            //删除卡片
            removeCard(index) {
                var del_index = (this.currentPage - 1) * this.pageSize + index;
                this.taskList.splice(del_index, 1);
                this.fetchTask()
            },
            removeProject(index) {
                this.fetchProject()
            },
            //获取项目数据
            async fetchProject() {
                const params = {
                    query: '',
                    page: this.projcurrentPage,
                    limit: this.projectPageSize,
                    project_source:'全景融合',
                };
                const res = await postProjectApi(params)
                if (res.code===0) {
                    this.displayProj = res.data;
                    this.totalProjectCount = res.count;
                }else{
                    this.$message.warning("项目数据获取失败！")
                }
            },
            goBack() {
                this.isProject = true;
                this.isTask = false;
                this.clearMap();
            },
            openTask(id,project_name){
                this.isProject=false;
                this.isTask=true;
                this.projID = id;
                this.currentProjectName=project_name;
                this.fetchTask();
            },

            //获取全景融合任务数据
            async fetchTask() {
                const params = {
                    keyword: this.searchName,
                    page: this.currentPage,
                    limit: this.pageSize,
                    task_type: this.task_type,
                    project_id:this.projID,
                }
                const res = await getTaskDataListApi(params)
                if (res.code === 0) {
                    this.taskList = res.data;
                    this.totalTaskCount = res.count;
                    // 清空地图上的所有标记
                    this.clearMap();
                    //遍历数据，在地图上添加标记
                    this.taskList.forEach(taskData => {
                        const lat = taskData.latitude;
                        const lon = taskData.longitude;
                        // 创建标记并添加到地图上
                        this.addMarker(lat, lon, taskData);
                    });
                } else {
                    this.$message.warning("任务数据获取失败！")
                }

            },
            addMarker(lat, lon, taskData) {
                // 创建标记并添加到地图上
                const customIcon = L.icon({
                    iconUrl: '../../static/video_mark_model.png',
                    iconSize: [32, 40],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32],
                });
                const Pcontent = taskData.task_name;
                const marker = L.marker([lat, lon], {icon: customIcon}).addTo(this.map);
                marker.bindPopup(Pcontent);
            },
            clearMap() {
                // 清除地图上的所有标记
                if (this.map) {
                    this.map.eachLayer((layer) => {
                        if (layer instanceof L.Marker) {
                            this.map.removeLayer(layer);
                        }
                    });
                }
            },
            async searchTask() {
                // 触发搜索操作，根据名称筛选数据
                if (this.searchName) {
                    this.fetchTask()
                }
            },
            async searchProject() {
                // 触发搜索操作，根据名称筛选数据
                if (this.searchName) {
                    const params = {
                        project_name: this.searchName,
                        project_source:'全景融合',
                        page: this.projcurrentPage,
                        limit: 4,
                    }
                    const res = await postProjectApi(params)
                    // 检查返回数据是否存在并且包含 data 属性
                    if (res.code===0) {
                        this.displayProj = res.data;
                        this.totalProjectCount = res.count;
                    }
                } else {
                    // 如果搜索名称为空，使用全部数据
                    this.fetchProject(); // 调用原先的 fetchData 方法获取全部数据
                }

            },



        },

        created() {
            document.body.style.overflow = "hidden";
        },
    };
</script>

<style lang="scss" scoped>
  .se-container {
    display: flex;
    height: 100%;
  }

  .business-sidebar {
    width: 90px;
  }

  .business-sidebar .el-menu-item {
    display: flex;
    align-items: center;
  }


  .el-menu-item .menu-text {
    padding: 10px 14px 6px 14px;
    font-size: 18px;
    font-weight: bold;
  }

  .main-content {
    display: flex;
    flex: 1;
    width: 100%;
  }

  .left-content {
    width: 320px;
    height: 100%;
  }

  .right-content {
    flex: 1;
  }

  .left-content-top {
    margin: 10px;
    width: 300px;
    border: 2px dashed gray;
    border-radius: 5px;
  }
  .left-content-top-task{
    margin: 10px;
    width: 300px;
  }
  .left-content-middle {
    width: 300px;
    height: 32px;
    margin:0 10px;
    text-align: start;
  }

  .left-content-bottom {
    width: 300px;
    height: calc(100% - 188px);
    margin: 10px;
  }

  .form_class {
    margin-right: 30px;
  }

  .input-item {
    margin: 20px;
  }

  .btn-uploading {
    margin-top: 30px;
    text-align: center;
  }

  .txt-uploading {
    margin: 20px;
  }

  .el-pagination {
    bottom: 10px;
  }

  .el-pager li,
  .el-pagination__editor,
  .el-pagination .btn-prev,
  .el-pagination .btn-next {
    margin: 0 1px !important;
  }


  .upload-btn-item {
    text-align: center;
    cursor: pointer;
  }

  .el-menu-item {
    height: 140px !important;
    float: left;
    width: 100%;
    text-align: center;
    color: #fff;
    cursor: pointer;
    overflow: hidden;
    line-height: 24px !important;
    box-sizing: border-box;
    padding: 8px !important;
    margin: 0 !important;
    white-space: normal !important;
  }

  .leftmenu-title {
    background: rgba(23, 125, 228, 0.2);
    border-radius: 10px;
    overflow: hidden;
    transition: border-radius 0.3s ease;
    position: relative;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    padding-top: 20%;
  }

  .el-menu-item:focus, .el-menu-item:hover {
    background-color: white !important;
  }

  .el-menu-item.is-active > div {
    background: #42b4f2 !important;
  }

  #map {
    height: 100%;
    width: 100%;
    background-color: #ffffff;
  }

  .custom-icon {
    font-size: 26px;
    color: #42b4f2
  }

  .back-btn {
    border: 0.1rem solid rgb(200, 200, 200);
    border-radius: 0.2rem;
    display: flex;
    width: 50px;
    margin: 10px 20px;
    justify-content: center;
    align-items: center;
    padding: 0 0.3rem;
    font-size: 0.8rem;
    cursor: pointer;
  }

  .bread-crumb {
    margin-left: 15px;
    margin-top: 10px;
    margin-bottom: 10px;

  }
  .el-form{
    width: 100%;
  }

   .left-content-middle .el-form-item{
      margin-bottom: 0;
      margin-right: 0;
      width:100%
    }
  .el-icon-back{
    cursor: pointer;
  }
.el-icon-back:hover{
  color:#42b4f2
}



</style>