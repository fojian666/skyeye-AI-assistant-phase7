<template>
    <div class="se-container">
        <div class="left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">新增视频检测</span>
            </div>
            <div class="left-content-body">
                <div class="left-form">
                    <el-form ref="form" :model="form" :rules="rules" label-position="left" label-width="90px"
                             style="margin-top: 10px">
                        <el-form-item prop="name" label="任务名称:">
                            <el-input v-model="form.name" placeholder="请输入任务名称">
                            </el-input>
                        </el-form-item>

                        <el-form-item label="上传视频:" prop="inputPath">
                            <el-upload
                                ref="upload"
                                class="upload-demo"
                                :action="fileUploadUrl"
                                :headers="headers"
                                accept=".mp4,.mov,.avi,.flv,.wmv,.mkv"
                                :limit="1"
                                :file-list="fileList"
                                :on-success="getUploadFile"
                                :on-remove="handleRemoveFile"
                                :on-progress="handleUploadProgress">
                                <el-button size="mini" type="primary">点击上传</el-button>
                            </el-upload>
                        </el-form-item>
                        <el-form-item prop="frameInterval" label="抽帧间隔:">
                            <el-input v-model="form.frameInterval" type="number"
                                      placeholder="请输入间隔时长">
                                <template slot="append">秒</template>
                            </el-input>
                        </el-form-item>
                        <el-form-item prop="shotTime" label="拍摄时间:">
                            <el-date-picker
                                v-model="form.shotTime"
                                type="date"
                                placeholder="选择日期">
                            </el-date-picker>
                        </el-form-item>
                        <el-form-item prop="selectedModel" label="模型场景:">
                            <el-select v-model="form.modelSceneList" placeholder="请选择" clearable multiple>
                                <el-option v-for="item in modelSceneList" :key="item.id" :label="item.name"
                                           :value="item.id">
                                </el-option>
                            </el-select>
                        </el-form-item>

                        <el-form-item>
                            <el-button type="info" class="gt-main-form-item-btn" @click="resetForm" size="mini">重置</el-button>
                            <el-button type="primary" @click="startDetection" class="gt-main-form-item-btn" size="mini">检测</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
        <div class="border"></div>
        <div class="right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-list"></span>
                <span class="title">任务管理</span>
            </div>
            <div class="right-content-body">
                <div class="t-query">
                    <!--数据筛选-->
                    <el-form :inline="true" size="medium" :model="filterInfo" ref="filterInfo">
                        <el-form-item>
                            <el-input v-model="filterInfo.name" placeholder="请输入任务名称" class="custom-elinput-height"/>
                        </el-form-item>
                        <el-form-item class="search-button">
                            <el-button type="primary" size="mini" @click="getVideoTaskList">查询</el-button>
                            <el-button type="danger" size="mini" @click="deleteTask">删除</el-button>
                            <el-button type="info" size="mini" @click="resetTaskList">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>

                <!-- 替换表格为卡片布局 -->
                <div class="card-list" v-loading="loading">
                    <!-- 修复1：给卡片添加cursor:pointer，确保视觉反馈，且事件绑定更稳定 -->
                    <div
                        class="task-card"
                        v-for="(item, index) in videoTaskList"
                        :key="item.taskId || index"
                        @click="openVideoDialog(item)"
                        style="cursor: pointer;"
                    >
                        <!-- 视频封面/缩略图 -->
                        <div class="card-cover">
                            <!-- 修复2：给播放图标添加@click.stop，避免事件冒泡冲突 -->
                            <div class="play-icon" @click.stop></div>
                            <!-- 假封面图，可替换为实际视频封面 -->
                            <img :src="item.coverUrl" alt="视频封面" class="cover-img">
                            <!-- 任务状态标签 -->
                            <div class="status-tag" :class="getStatusColor(item.status)">
                                {{ statusText(item.status) }}
                            </div>
                        </div>

                        <!-- 卡片内容 -->
                        <div class="card-content">
                            <h3 class="task-name">{{ item.name }}</h3>

                            <div class="card-info">
                                <div class="info-item">
                                    <span class="label">抽帧间隔：</span>
                                    <span class="value">{{ item.frameInterval }}秒</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">拍摄时间：</span>
                                    <span class="value">{{ item.shotTime || '未设置' }}</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">检测线索：</span>
                                    <span class="value">{{ item.clueCount }}条</span>
                                </div>
                                <div class="info-item">
                                    <span class="label">有效线索：</span>
                                    <span class="value">{{ item.effectiveClueCount }}条</span>
                                </div>
                            </div>

                            <!-- 模型场景标签 -->
                            <div class="tag-group">
                                <el-tag
                                    v-for="(tag, idx) in item.modelSceneList.slice(0, 3)"
                                    :key="idx"
                                    size="small"
                                    type="info"
                                >
                                    {{ tag.modelSceneName }}
                                </el-tag>
                                <el-tag
                                    v-if="item.modelSceneList.length > 3"
                                    size="small"
                                    type="warning"
                                >
                                    +{{ item.modelSceneList.length - 3 }}
                                </el-tag>
                            </div>

                            <!-- 操作按钮
                            <div class="card-actions">
                                <el-button type="text" size="mini" class="blue" @click.stop="handleDataView(item)">查看</el-button>
                                <el-button type="text" size="mini" class="orange" @click.stop="download(item)">下载</el-button>
                                <el-button type="text" size="mini" class="red" @click.stop="deleteTask(item)">删除</el-button>
                            </div>-->
                        </div>
                    </div>

                    <!-- 空数据提示 -->
                    <div class="empty-tip" v-if="videoTaskList.length === 0 && !loading">
                        <el-empty description="暂无任务数据"></el-empty>
                    </div>
                </div>

                <!--分页设置-->
                <div class="page">
                    <el-pagination
                        background
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange"
                        :current-page="filterInfo.pageIndex"
                        :page-sizes="[6, 12, 18, 24]"
                        :page-size="filterInfo.pageSize"
                        layout="sizes, prev, pager, next, total"
                        :total="dataCount">
                    </el-pagination>
                </div>
            </div>
        </div>

        <!-- 视频播放弹窗 -->
        <!-- 修复3：移除draggable（旧版Element Plus不支持，会导致渲染异常），确保v-model绑定正确 -->
        <el-dialog
            :visible.sync="videoDialogVisible"
            title="视频播放"
            width="80%"
        >
            <div class="video-player-container">
                <!-- 修复4：添加muted属性，解决浏览器自动播放限制（否则play()会报错） -->
                <video
                    ref="videoPlayer"
                    :src="currentVideoUrl"
                    controls
                    autoplay
                    muted
                    class="video-player"
                >
                    您的浏览器不支持HTML5视频播放
                </video>
            </div>
            <div class="video-task-info" v-show="currentTask">
                <h4>任务信息：{{ currentTask.name || '' }}</h4>
                <div class="task-detail">
                    <span>状态：<span :class="getStatusColor(currentTask.status)">{{ statusText(currentTask.status) }}</span></span>
                    <span>抽帧间隔：{{ currentTask.frameInterval }}秒</span>
                    <span>检测线索：{{ currentTask.clueCount }}条</span>
                </div>
            </div>
        </el-dialog>
    </div>
</template>

<script>
import {
    addVideoTaskApi,
    deleteVideoTaskApi,
    getVideoTaskListApi,downloadReportApi,
    getModelSceneListApi, getDownloadVideoClueFileApi
} from "@/api/commonApi";
import staticTable from "@/views/intelligent/interpretationTaskManagement/component/staticTable";

export default {
    name: 'videoManagement',
    components: {
        staticTable,
    },
    data() {
        return {
            uploadProgress: 50, //上传进度
            uploadFileName: '', //上传的压缩包名称
            selectedTask: [],
            fileList: [],
            form: {
                frameInterval: '', //抽帧间隔
                name: '',//项目名称
                shotTime: '',
                threshold: '50',//碎斑阈值
                modelSceneList: [],  //表单中的模型类别
                fileId: ''
            },
            dataCount: 12, // 假数据总数
            filterInfo: {
                name: '',
                pageIndex: 1,
                pageSize: 8 // 卡片布局默认每页6个
            }, //筛选参数
            headers: {Authorization: 'Bearer ' + sessionStorage.getItem('token') || 'unknown'},
            serverPaths: [],  //获取共享路径下额所有影像路径
            modelSceneList: [], //模型类别
            showTable: false,
            translationStatus: [],
            // 假数据 - 视频任务列表
            videoTaskList: [],
            isShowChange: false,
            openDialog: false,
            loading: false,
            rules: {
                name: [{required: true, message: '请输入任务名称', trigger: 'blur'}],
                shotTime: [{required: true, message: '请选择拍摄时间', trigger: 'blur'}],
                frameInterval: [{required: true, message: '请输入抽帧间隔', trigger: 'blur'}],
                selectedModel: [{required: true, message: '请选择模型类型', trigger: 'blur'}],
            },
            // 视频播放弹窗相关（确认初始值正确）
            videoDialogVisible: false,
            currentVideoUrl: '',
            currentTask: {}
        };
    },
    computed: {
        fileUploadUrl() {
            return '/lais/site/inspection/video-interpretation-task/file-upload';
        },
    },
    watch: {},
    created() {
        this.getModelSceneList();
        // 初始化假数据
        this.initFakeData();
    },
    mounted() {
        // 替换原有接口请求，使用假数据
        this.getVideoTaskList();
    },
    methods: {
        // 初始化假数据
        initFakeData() {
            // 模拟不同状态的任务数据

        },
        async download(row) {
            const res = await getDownloadVideoClueFileApi(row.taskId)
            if (!res) {
                this.$message.error('请先处理待判读线索！');
                return;
            }
            if (res.code !== 0) {
                this.$message.error(res.msg || '下载文件时发生错误');
                return;
            }
            let fileName = res.data.fileName || row.name + '.zip';
            let fileId = res.data.fileId;

            const response = await downloadReportApi(fileId);
            // 创建一个临时的a标签来模拟下载
            const url = window.URL.createObjectURL(new Blob([response]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();
        },
        // 打开视频播放弹窗（修复6：添加日志，确保方法执行；简化逻辑，优先保证Dialog弹出）
        openVideoDialog(task) {
            this.videoDialogVisible = true; // 优先赋值，确保Dialog弹出

            console.log(this.videoDialogVisible)
            console.log('点击卡片，触发openVideoDialog', task); // 调试日志
            this.currentTask = task;
            this.currentVideoUrl = task.videoUrl;
            // 视频播放逻辑放到nextTick，且添加错误捕获
            this.$nextTick(() => {
                const video = this.$refs.videoPlayer;
                if (video) {
                    video.play().catch(err => {
                        console.log('视频自动播放失败（浏览器限制）：', err);
                        // 即使播放失败，也不影响Dialog显示
                    });
                }
            });
        },
        // 停止视频播放（弹窗关闭前）
        stopVideoPlay() {
            console.log(11111)
            const video = this.$refs.videoPlayer;
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
            this.currentVideoUrl = '';
            this.currentTask = null;
            //this.videoDialogVisible = false; // 显式重置
        },
        // 处理查看事件
        handleDataView(row) {
            this.$router.push({path: `/video-detection/clue-view/${row.taskId}`})
        },
        // 重置模糊查询
        resetTaskList() {
            this.filterInfo.name = '';
            this.getVideoTaskList(this.filterInfo);
        },
        //处理选择事件（批量删除用）
        handleSelectionChange(val) {
            this.selectedTask = val.map((item) => item.taskId);
        },
        //处理上传文件
        getUploadFile(response, file, fileList) {
            if (response.code === 0) {
                this.uploadFileName = response.data;
                this.form.fileId = response.data.fileId;
                this.$message.success(response.msg);
            } else {
                this.$refs.upload.handleRemove(file);
                this.$message.error(response.msg);
            }
            if (this.loading) {
                this.loading.close();
                this.loading = null;
            }
        },
        //处理每页数量变化
        handleSizeChange(val) {
            this.filterInfo.pageSize = val;
            this.filterInfo.pageIndex = 1;
            this.getVideoTaskList();
        },
        //处理页码的变化
        handleCurrentChange(val) {
            this.filterInfo.pageIndex = val;
            this.getVideoTaskList();
        },
        //获取视频检测任务列表（保留原有逻辑，可切换回真实接口）
        async getVideoTaskList() {
            // 注释真实接口，使用假数据
            const resp = await getVideoTaskListApi(this.filterInfo);
            if (resp.code === 0) {
              this.videoTaskList = resp.data;
              this.dataCount = resp.total;
            }
        },
        handleRemoveFile(file, fileList) {
            this.uploadFileName = '';
            if (this.loading) {
                this.loading.close();
                this.loading = null;
            }
        },
        handleUploadProgress(event) {
            this.loading = this.$loading({
                text: '正在上传文件中，请稍后...',
                background: 'rgba(0, 0, 0, 0.6)',
                lock: true,
                spinner: 'el-icon-loading'
            });
            return true;
        },
        getStatusColor(status) {
            switch (status) {
                case 0: return 'status-pending'; // 待检测
                case 1: return 'status-processing'; // 进行中
                case 2: return 'status-success'; // 已完成
                case 3: return 'status-error'; // 报错
                case 4: return 'status-stop'; // 已终止
                default: return 'status-stop';
            }
        },
        statusText(status) {
            switch (status) {
                case 0: return '待检测';
                case 1: return '进行中';
                case 2: return '已完成';
                case 3: return '报错';
                default: return '已终止';
            }
        },
        //初始化表单
        resetForm() {
            this.form = {
                inputPath: '',
                name: '',
                frameInterval: '',
                threshold: '50',
                shotTime: '',
                modelSceneList: [],
                fileId: ''
            }
            this.fileList = [];
        },
        //获取所有检测模型
        async getModelSceneList() {
            const params = {
                "pageIndex": -1,
                "pageSize": 10,
                "name": ""
            }
            // 模拟模型场景数据（替换真实接口）
            this.modelSceneList = [
                {id: 1, name: '人员检测'},
                {id: 2, name: '消防设施'},
                {id: 3, name: '车辆违规'},
                {id: 4, name: '设备异常'},
                {id: 5, name: '人员闯入'},
                {id: 6, name: '违章停车'}
            ];

            // 真实接口逻辑（保留）
            // const res = await getModelSceneListApi(params)
            // if (res.code === 0) {
            //   this.modelSceneList = res.data
            // } else {
            //   this.$message.error(res.msg)
            // }
            this.loading = false
        },
        //开始检测
        async startDetection() {
            // 表单验证
            try {
                await this.$refs.form.validate();
            } catch (err) {
                this.$message.warning('请完善表单必填项！');
                return;
            }

            const paras = {
                name: this.form.name,
                videoType: "",
                modelSceneList: this.form.modelSceneList,
                shotTime: this.form.shotTime,
                frameInterval: this.form.frameInterval,
                fileId: this.form.fileId
            }

            // 模拟创建任务（替换真实接口）
            this.$message.success(this.form.name + " 任务已创建成功！");
            // 新增假任务数据
            this.videoTaskList.unshift({
                taskId: 'task_' + Date.now(),
                name: this.form.name,
                status: 0, // 待检测
                frameInterval: this.form.frameInterval,
                shotTime: this.form.shotTime,
                clueCount: 0,
                effectiveClueCount: 0,
                modelSceneList: this.form.modelSceneList.map(id => {
                    const model = this.modelSceneList.find(item => item.id === id);
                    return {id, modelSceneName: model ? model.name : '未知场景'};
                }),
                coverUrl: `https://picsum.photos/400/220?random=${Math.random()}`,
                videoUrl: 'https://cdn.pixabay.com/video/2021/07/04/119326-564756236_large.mp4'
            });
            this.dataCount = this.videoTaskList.length;
            this.getVideoTaskList();
            this.resetForm();

            // 真实接口逻辑（保留）
            // const res = await addVideoTaskApi(paras)
            // if (res.code === 0) {
            //   this.$message.success(this.form.name + " 任务已创建成功！");
            //   this.getVideoTaskList();
            //   this.resetForm();
            // } else {
            //   this.$message.error(res.msg)
            // }
        },
        deleteTask(row) {
            this.$confirm('是否确认删除任务，删除不可撤销?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).then(async () => {
                let taskIds = [];
                if (row && row.taskId) {
                    // 单个删除
                    taskIds = [row.taskId];
                } else {
                    // 批量删除
                    taskIds = this.selectedTask;
                }

                if (taskIds.length === 0) {
                    this.$message.warning('请选择要删除的任务！');
                    return;
                }

                // 模拟删除（替换真实接口）
                this.videoTaskList = this.videoTaskList.filter(item => !taskIds.includes(item.taskId));
                this.dataCount = this.videoTaskList.length;
                this.$message.success("任务删除成功！");
                this.selectedTask = [];
                this.getVideoTaskList();

                // 真实接口逻辑（保留）
                // const res = await deleteVideoTaskApi(taskIds);
                // if (res.code === 0) {
                //   this.$message.success("任务删除成功！");
                //   this.getVideoTaskList();
                //   this.selectedTask = [];
                // } else {
                //   this.$message.error(res.msg);
                // }
            }).catch((error) => {
                console.log(error);
                this.$message({
                    type: 'info',
                    message: '已取消删除'
                });
            });
        },
        closeDialog() {
            this.openDialog = false;
        },
    },
}
</script>

<style lang="scss" scoped>
.se-container {
    height: 100%;
    position: relative;
    color: white;
    display: flex;
}



.border {
    width: 1px;
    height: 100%;
    background-color: #ccc;
}



// 卡片布局核心样式
.card-list {
    padding: 10px;
    height: calc(100% - 130px);
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 15px;

    // 任务卡片样式
    .task-card {
        height: 310px;

        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        cursor: pointer;
        transition: all 0.3s ease;

        &:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }

        // 视频封面区域
        .card-cover {
            position: relative;
            height: 180px;
            overflow: hidden;

            .cover-img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                transition: all 0.3s ease;
            }

            &:hover .cover-img {
                transform: scale(1.05);
            }

            // 纯CSS绘制播放按钮
            .play-icon {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 48px;
                height: 48px;
                opacity: 0;
                transition: all 0.3s ease;
                // 绘制三角形播放图标
                &::after {
                    content: '';
                    display: block;
                    width: 0;
                    height: 0;
                    border-style: solid;
                    border-width: 16px 0 16px 28px;
                    border-color: transparent transparent transparent rgba(255, 255, 255, 0.8);
                }
            }

            &:hover .play-icon {
                opacity: 1;
            }

            .status-tag {
                position: absolute;
                top: 10px;
                right: 10px;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
        }

        // 卡片内容区域
        .card-content {
            padding: 12px;

            .task-name {
                font-size: 16px;
                font-weight: bold;
                color: #42b4f2;
                margin: 0 0 8px 0;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .card-info {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 6px;
                font-size: 12px;
                color: #c0c6d0;
                margin-bottom: 8px;

                .info-item {
                    display: flex;
                    justify-content: space-between;

                    .label {
                        color: #8fa4b8;
                    }
                }
            }

            .tag-group {
                margin-bottom: 10px;
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
            }

            .card-actions {
                display: flex;
                justify-content: flex-end;
                gap: 8px;

                .el-button {
                    padding: 0;
                    font-size: 12px;
                }

                .blue {
                    color: #42b4f2;
                }

                .orange {
                    color: #ff9500;
                }

                .red {
                    color: #ff3b30;
                }
            }
        }
    }

    // 空数据提示
    .empty-tip {
        grid-column: 1 / -1;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
    }
}

// 状态标签样式
.status-pending {
    background-color: #177de4;
    color: white;
}

.status-processing {
    background-color: #00cc66;
    color: white;
}

.status-success {
    background-color: #009688;
    color: white;
}

.status-error {
    background-color: #ff3b30;
    color: white;
}

.status-stop {
    background-color: #8e8e93;
    color: white;
}

// 视频播放弹窗样式
.video-player-container {
    width: 100%;
    padding: 10px 0;

    .video-player {
        width: 100%;
        height: 500px;
        border-radius: 8px;
    }
}

.video-task-info {
    padding: 10px 0;
    border-top: 1px solid #177de4;
    margin-top: 10px;

    h4 {
        margin: 0 0 8px 0;
        color: #42b4f2;
    }

    .task-detail {
        display: flex;
        gap: 20px;
        font-size: 14px;
        color: #c0c6d0;
    }
}

// 原有样式适配


.right-content-body {
    padding: 10px 10px 10px 10px;
    height: calc(100% - 40px);
    display: flex;
    flex-direction: column;
}


.page {
    margin-top: auto;
    padding: 10px;
    text-align: right;
}

.el-pagination {
    --el-pagination-text-color: #c0c6d0;
    --el-pagination-button-color: #0f244d;
    --el-pagination-button-hover-color: #177de4;
}

// 表单样式保持不变
.left-form {
    margin-left: 10px;
    margin-right: 10px;
    width: 95%;
    height: 80%;
}


::v-deep .left-form .el-input {
    width: 200px;
    display: flex;
}

::v-deep .el-input-group__append {
    line-height: 32px;
    height: 32px;
    background-color: transparent;

    border-left: none;
    text-align: center;
    justify-content: center;
    display: flex;
}

::v-deep input[type='number'] {
    -moz-appearance: textfield !important;
}

::v-deep input::-webkit-outer-spin-button,
::v-deep input::-webkit-inner-spin-button {
    -webkit-appearance: none !important;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}
</style>