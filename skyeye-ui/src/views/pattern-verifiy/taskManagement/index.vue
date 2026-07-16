<template>
    <div class="se-container">
        <div class="se-left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">新增图斑核实任务</span>
            </div>
            <div class="left-content-body">
                <div class="excel-upload">
                    <!--上传网格表单-->
                    <el-form :model="form" ref="form">
                        <el-form-item label="上传文件" label-width="80px">
                            <el-input type="text" placeholder="请上传zip压缩包" v-model="form.shpZipFile" class="custom-input-height">
                                <template slot="append">
                                    <el-button icon="el-icon-folder-opened" size="mini" @click="checkShpZip"></el-button>
                                    <input
                                        type="file"
                                        id="excel"
                                        accept=".zip"
                                        style="display: none"
                                        @change="handleFileUpload"
                                        class="custom-input-height" />
                                </template>
                            </el-input>
                        </el-form-item>
                        <el-form-item label="操作用户" label-width="80px">
                            <el-input v-model="form.uploadPerson" disabled class="custom-input-height"></el-input>
                        </el-form-item>
                        <el-form-item class="button-container">
                            <el-button class="right-button" type="primary" size="mini" @click="handleSubmit">提交 </el-button>
                            <el-button class="right-button" type="info" size="mini" @click="resetForm">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
        <div class="se-right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-grid"></span>
                <span class="title">任务管理</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <!--数据筛选-->
                    <el-form :inline="true" size="medium" :model="filterInfo" ref="filterInfo">
                        <el-form-item>
                            <el-input v-model="filterInfo.task_id" placeholder="请输入任务编号" size="small" class="custom-elinput-height" />
                        </el-form-item>
                        <el-form-item class="search-button">
                            <el-button type="primary" size="small" @click="getTaskList(filterInfo.task_id)">查询</el-button>
                            <el-button type="danger" size="small" @click="deleteTask">删除</el-button>
                            <el-button type="info" size="small" @click="resetTaskList">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="grid-table">
                    <!--网格数据-->
                    <el-table
                        max-height="100%"
                        height="100%"
                        :data="taskData"
                        stripe
                        style="width: 100%"
                        border
                        @selection-change="handleSelectionChange"
                        v-loading="loading">
                        <el-table-column type="selection" width="55" align="center"></el-table-column>
                        <el-table-column
                            type="index"
                            label="序号"
                            align="center"
                            width="80"
                            :index="(index) => (filterInfo.page - 1) * filterInfo.limit + index + 1"></el-table-column>
                        <el-table-column prop="task_id" label="任务编号" align="center" width="240"></el-table-column>
                        <el-table-column prop="street" label="所属街道" align="center"></el-table-column>
                        <el-table-column prop="status" label="状态" align="center">
                            <template slot-scope="scope">
                                <span :class="getStatusColor(scope.row.status)">
                                    {{ statusText(scope.row.status) }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column prop="todo_count" label="待核实图斑数" align="center"></el-table-column>
                        <el-table-column prop="occupy" label="占用图斑数" align="center"></el-table-column>
                        <el-table-column prop="no_occupied" label="未占用图斑数" align="center"></el-table-column>
                        <el-table-column prop="total_count" label="图斑总数" align="center"></el-table-column>
                        <el-table-column prop="verifier" label="核实人" align="center"></el-table-column>
                        <el-table-column label="操作" align="center">
                            <template slot-scope="scope">
                                <el-button type="text" size="mini" class="blue" @click="handleDataView(scope.row)">查看 </el-button>
                                <el-button type="text" size="mini" class="orange" @click="handleExportReport(scope.row)">导出 </el-button>
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
                        :total="dataCount">
                    </el-pagination>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { postPolygonTaskStatusApi, deleteTaskApi, patternVerifiTableApi, uploadPolygonTaskApi, exportPolygon, JudgeClueApi } from '@/api/commonApi';

export default {
    name: 'GridManagementIndex',
    data() {
        return {
            upProgress: 0, //上传进度
            uploading: false, //上传进度表单控制
            form: {
                shpZipFile: '',
                uploadPerson: ''
            }, //上传表单
            filterInfo: {
                keyword: '',
                dataRange: [],
                task_status: '',
                task_id: '',
                limit: 10,
                page: 1
            }, //筛选参数
            taskData: [],
            selectedTask: [],
            dataCount: 1,
            uploadfile: null,
            loading: false,
            baseUrl: process.env.VUE_APP_API_URL //请求地址
        };
    },
    methods: {
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.filterInfo.limit = val;
            this.filterInfo.page = 1;
            this.getTaskList(this.filterInfo.task_id);
        },
        handleCurrentChange(val) {
            this.loading = true;
            // 改变页码
            this.filterInfo.page = val;
            this.getTaskList(this.filterInfo.task_id);
            this.loading = false;
        },
        handleSelectionChange(val) {
            //选择的网格数据
            this.selectedTask = val.map((item) => item.id);
        },
        checkShpZip() {
            //网格标签点击事件
            document.querySelector('#excel').click();
        },
        handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                this.form.shpZipFile = file.name; // 设置文件名
                this.$message.success('文件上传成功');
            }
        },
        //处理上传文件
        async handleSubmit() {
            let file = document.getElementById('excel');
            if (file.files[0] === undefined) {
                return this.$message.error('请先上传文件');
            }
            this.uploadfile = file.files[0];
            // // 创建一个 FormData 对象
            const formData = new FormData();
            // // 将文件添加到 FormData 对象中
            formData.append('file', this.uploadfile);
            formData.append('taskType', 0);
            try {
                const res = await uploadPolygonTaskApi(formData);
                if (res.code === 0) {
                    this.uploading = null;
                    this.resetForm();
                    this.getTaskList('');
                    this.$message.success('上传成功！');
                } else {
                    this.$message.error(res.msg);
                }
            } catch (error) {
                this.$message.error('上传失败');
            }
        },
        async getTaskList(task_id) {
            //  获取线索表格记录
            const para = {
                taskId: task_id,
                taskType: '0',
                pageSize: this.filterInfo.limit,
                pageIndex: this.filterInfo.page
            };
            const res = await patternVerifiTableApi(para);
            if (res.code !== 0) {
                this.$message.error('图斑核实任务数据获取失败！');
                return;
            } else {
                this.taskData = res.data;
                this.dataCount = res.total;
            }
        },
        async resetTaskList() {
            this.filterInfo.task_id = '';
            const para = {
                task_id: '',
                limit: this.filterInfo.limit,
                page: this.filterInfo.page
            };
            const res = await patternVerifiTableApi(para);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            } else {
                this.taskData = res.data;
                this.dataCount = res.count;
            }
        },
        resetForm() {
            this.form.shpZipFile = '';
        },

        async handleDataView(row) {
            const id = row.id;
            const status = row.status;
            if (status === 0) {
                const res = await postPolygonTaskStatusApi(id);
            }
            this.$router.push({ name: 'patternMapOverview', query: { id } });
        },
        deleteTask() {
            this.$confirm('是否确认任务,删除不可撤销?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteTaskApi(JSON.stringify({ task_id_list: this.selectedTask }));
                    if (res.code === 0) {
                        this.$message.success(res.msg);
                        this.getTaskList();
                    } else {
                        this.$message.error(res.msg);
                    }
                })
                .catch((error) => {
                    console.log(error);
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
        },
        getStatusColor(status) {
            switch (status) {
                // case '●部分检测':
                case 0:
                    return 'blue';
                case 1:
                    return 'green';
                case 2:
                    return 'red';
            }
        },
        statusText(status) {
            switch (status) {
                // case '●部分检测':
                case 0:
                    return '待核实';
                case 1:
                    return '核实中';
                case 2:
                    return '已完成';
            }
        },
        async handleExportReport(row) {
            const para = {
                task_id: row.task_id,
                id: row.id
            };
            if (row.status !== 2) {
                this.$message.warning('当前任务尚未完成，请完成后再导出报告');
                return;
            }
            const res = await JudgeClueApi(row.id);
            if (res.code === 0) {
                try {
                    let url = `/lais/site/inspection/polygon-task/export_polygon?id=${para.id}`;
                    const link = document.createElement('a');
                    link.href = url;
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link); // 移除临时链接
                    this.$message.success('下载成功！');
                } catch (error) {
                    if (error.response && error.response.status === 404) {
                        this.$message.error(error.response.error);
                    } else {
                        this.$message.error('下载文件时发生错误');
                    }
                }
            } else {
                this.$message.error(res.msg);
            }
        },
        async handleCloseTask(row) {
            try {
                const response = await exportPolygon(row.id);
                // 创建一个临时的a标签来模拟下载
                const url = window.URL.createObjectURL(new Blob([response]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', row.task_id + '.zip');
                document.body.appendChild(link);
                link.click();
                // 清理
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    this.$message.error('文件未找到');
                } else {
                    this.$message.error('下载文件时发生错误');
                }
            }
        }
    },

    created() {},
    async mounted() {
        this.form.uploadPerson = localStorage.getItem('username');
        this.getTaskList(this.filterInfo.task_id);
    },
    computed: {},
    watch: {}
};
</script>

<style lang="scss" scoped>
.title {
    margin-left: 8px;
}

::v-deep .el-form-item--medium .el-form-item__label {
    line-height: 36px;
    color: white;
}

::v-deep .grid-upload .el-input {
    width: 220px; //输入框设置
}

.button-container {
    display: flex;
    padding: 14px;
    align-items: center; /* 垂直居中 */
    text-align: center;
    justify-content: center;
    border-top: 1px solid #0a579e;
}

.grid-table {
    margin-top: 20px;
    margin-left: 10px;
    margin-right: 18px;
    flex-grow: 1; //占据剩余高度
    height: calc(100% - 151px);
}

.se-filter-form .el-form-item {
    margin-bottom: 0;
}

.se-filter-form {
    padding: 10px 10px 0 10px;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}

.right-content-body {
    padding: 10px;
    height: calc(100% - 20px);
}

.el-input-group {
    line-height: normal;
    display: inline-table;
    border-collapse: separate;
    border-spacing: 0;
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

::v-deep .transparent-dialog .el-dialog__header,
.label-dialog .el-dialog__header {
    text-align: center;
    font-weight: 700;
    border-bottom: 1px solid #fff;
}

::v-deep .leaflet-top {
    top: 50px;
}
.search-button {
    margin-left: 16px;
}

::v-deep .el-input--medium .el-input__inner {
    height: 32px;
    line-height: 32px;
}
::v-deep .excel-upload .el-form-item__label {
    text-align: right;
    vertical-align: middle;
    float: left;
    font-size: 14px;
    line-height: 40px;
    padding: 0 12px 0 0;
    box-sizing: border-box;
}
::v-deep .el-input--medium .el-input__inner {
    height: 36px;
    line-height: 36px;
    color: white;
}

::v-deep .el-input-group__append,
.el-input-group__prepend {
    background-color: transparent;
}
.left-content-body {
    padding: 20px 6px;
}
::v-deep .el-input--small .el-input__inner {
    height: 40px;
    line-height: 40px;
}
</style>
