<template>

    <div class="se-container">
        <div class="main-content">
            <div class="left-content">
                <div style="position: relative">
                    <div @click="dialogTableVisible = true" class="left-content-top">
                        <div class="upload-btn-item">
                            <i class="el-icon-upload" style="font-size: 45px"></i>
                            <div>点此上传文件并开始解译</div>
                        </div>
                    </div>
                    <div class="left-content-middle">
                        <el-form >
                            <el-form-item>
                                <el-input type="text" placeholder="请输入任务名称" v-model="searchName">
                                    <template slot="append">
                                        <el-button icon="el-icon-search" size="medium" @click="searchData"></el-button>
                                    </template>
                                </el-input>

                            </el-form-item>
                        </el-form>
                    </div>

                    <div class="left-content-bottom">
                            <div style="height: 20%"
                                    v-for="(item, index) in dataList"
                                    :key="index"
                            >
                                <cards :data="item" @open-task-details="openTaskDetails" @remove="removeCard(index)"/>
                            </div>
                    </div>

                    <el-pagination
                            small
                            background
                            layout="prev, pager, next, total"
                            :page-size="pageSize"
                            :total="totalCount"
                            :current-page.sync="currentPage"
                            @size-change="handleSizeChange"
                            @current-change="handleCurrentChange"
                    >
                    </el-pagination>
                </div>

            </div>

            <div class="right-content">
                <div class="panel-fold"></div>
                <od-details v-show="showDetails" :oddata="selectedCardData" :key="detailsKey"
                            @openTaskDetails="openTaskDetails"></od-details>
                <div v-show="mapVisible" id="map"></div>
            </div>

        </div>

        <el-dialog title="上传数据" :visible.sync="dialogTableVisible" width="30%" append-to-body>
            <div style="width: 100%; height: 35vh; padding-top: 10px">
                <el-form class="form_class">
                    <el-form-item label="视角选择:" label-width="100px">
                        <el-radio-group v-model="currentCheckedView">
                            <el-radio v-for="view in views" :label="view" :key="view"></el-radio>
                        </el-radio-group>
                    </el-form-item>
                    <el-form-item label="文件上传:" label-width="100px">
                        <el-input type="text" placeholder="请上传图片文件" v-model="filePath">
                            <template slot="append">
                                <el-button icon="el-icon-folder-opened" size="medium" @click="checkFile"></el-button>
                                <input type="file" id="fileInput" style="display: none;"
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
    import OdDetails from './details.vue'
    import axios from "axios";

    import {getTaskDataListApi,getMapInfoApi} from "@/api/commonApi";
    import {TiledMapLayer, spatialAnalystService} from "@supermap/iclient-leaflet";
    export default {
        name: "OdIndex",
        data() {
            return {
                currentPage: 1, //当前页码
                pageSize: 4, //每页显示的数量
                totalCount:0,
                dataList: [], //当前页要展示的数据
                delete_card_count: 0, //当前已删除的card数量
                dialogTableVisible: false,
                filePath: "", //文件夹名称
                uploading: false,
                uploadSuccess: null, // 文件夹上传状态标识
                searchName: "",
                task_name: '',
                mapVisible: true,
                currentCheckedView: '正视',
                views: ['正视', '斜视'],
                username: '',
                showDetails: false,
                selectedCardData: {pictures:[]},
                detailsKey: "",
                upProgress: 0,
                map: null,
                task_type:'图片检测',
                mapService:'',
                center:'',
            };
        },
        computed: {
        },
        watch: {
        },
        components: {
            Cards,
            OdDetails,
        },
        async mounted() {
            this.username = localStorage.getItem("username");
            if (!this.username) {
                this.$router.push('/login')
            }

            const res = await getMapInfoApi();
            if (res.code === 0) {
                this.mapService = res.data.map_service;
                this.center = res.data.center;
                this.initMap();
                this.fetchData();
            }
        },
        methods: {
            openTaskDetails(taskData) {
                this.selectedCardData = taskData;
                this.showDetails = true;
                this.mapVisible = false;
                this.detailsKey = taskData.task_id
            },
            // 页面大小改变时会触发
            handleSizeChange(val) {
                this.pageSize = val;
                this.fetchData();
            },
            //页码改变事件
            handleCurrentChange(newPage) {
                this.currentPage = newPage;
                this.fetchData();
            },
            checkFile() {
                document.querySelector('#fileInput').click()
            },
            initMap(){

                    this.map = L.map('map').setView(this.center, 14);
                    // 添加天地图瓦片图层
                    const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);

            },
            handleFolderSelection(event) {
                const selectedFolder = event.target.files[0];
                if (selectedFolder) {
                    this.filePath = selectedFolder.name; // 更新文件夹路径
                    this.uploadSuccess = null; // 重置上传状态
                }
            },
            //开始解译
            async inference() {
                //拿到元素节点
                let file_input = document.getElementById('fileInput');
                //读取dom节点图片
                const fileObj = file_input.files[0];
                if (fileObj) {
                    this.uploading = true;
                    let formData = new FormData();
                    formData.append('files', fileObj);
                    // 传递 任务名、文件夹路径到后端
                    formData.append('filePath', filePath);
                    let own = this;
                    const {data: res} = await axios.post("/common/files1", formData, {
                        headers: {'content-type': 'application/x-www-form-urlencoded'},
                        onUploadProgress: progressEvent => {
                            // 计算上传进度并更新你的进度条
                            own.upProgress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                        }
                    });
                    // 设置文件夹名称和上传成功状态
                    this.filePath = filePath;
                    this.uploading = null;
                    this.uploadSuccess = true;
                    this.dialogTableVisible = false;
                    await this.fetchData(this.activeMenu);
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
            },
            resetBtn() {
                this.filePath = '';
            },

            //删除卡片
            removeCard(index) {
                var del_index = (this.currentPage - 1) * this.pageSize + index;
                this.dataList.splice(del_index, 1);
            },

            async fetchData() {
                const params = {
                    name: this.searchName,
                    page:this.currentPage,
                    limit:this.pageSize,
                    task_type:this.task_type,
                }
                const res = await getTaskDataListApi(params);
                this.totalCount = res.count;
                this.dataList = res.data;
                // 检查返回数据是否存在并且包含 data 属性
                if (res.code===0) {
                    // 清空地图上的所有标记
                    this.clearMap();
                    // 遍历数据，在地图上添加标记
                    this.dataList.forEach(taskData => {
                        const lat = taskData.latitude;
                        const lon = taskData.longitude;
                        // 创建标记并添加到地图上
                        this.addMarker(lat, lon, taskData);
                    });
                } else {
                    console.error("数据获取失败:", res.data);
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
                const content = taskData.task_name;
                const marker = L.marker([lat, lon], {icon: customIcon}).addTo(this.map);
                marker.bindPopup(content);
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
            //搜索模糊查询
            async searchData() {
                // 触发搜索操作，根据名称筛选数据
                if (this.searchName) {
                    const params = {
                        name: this.searchName,
                        page:this.currentPage,
                        limit:this.pageSize,
                        task_type:this.task_type,
                    }
                    const res = await getOdImageListApi(params)
                    // 检查返回数据是否存在并且包含 data 属性
                    if (res.code===0) {
                        this.dataList = res.data;
                        this.totalCount=res.count;
                    } else {
                        this.$message.warning("获取数据失败！")
                    }
                } else {
                    // 如果搜索名称为空，使用全部数据
                    this.fetchData(); // 调用原先的 fetchData 方法获取全部数据
                }

            }
        },

        created() {
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
    overflow: hidden;
  }
  .left-content-top {
    margin: 10px;
    width: 300px;
    border: 2px dashed gray;
    border-radius: 5px;
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
  .right-content {
    flex: 1;
  }

  #map {
    background-color: #ffffff;
    height: 100%;
    width: 100%;
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
    position: fixed;
    bottom: 10px;
    max-width:320px;
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


  .custom-icon {
    font-size: 26px;
    color: #42b4f2
  }

  /* 自定义 CSS */
  .el-dialog__wrapper {
    background-color: transparent !important; /* 去掉遮罩层 */
  }
</style>