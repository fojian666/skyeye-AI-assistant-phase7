<template>
    <div class="se-container">
        <div class="se-left-content">
            <div class="left-content-header">
                <span class="icon iconfont icon-xinzengtianjia"></span>
                <span class="title">新增项目</span>
            </div>
            <div class="left-content-body">
                <div class="excel-upload">
                    <el-form :model="form" ref="form">
                        <el-form-item label="上传文件" label-width="80px">
                            <el-input type="text" placeholder="请上传包含 shp 的 zip 压缩包" v-model="form.zipFile" class="custom-input-height">
                                <template slot="append">
                                    <el-button icon="el-icon-folder-opened" size="mini" @click="checkZipFile"></el-button>
                                    <input
                                        type="file"
                                        id="taskMgmtZip"
                                        accept=".zip,.shp"
                                        style="display: none"
                                        @change="handleFileUpload"
                                        class="custom-input-height" />
                                </template>
                            </el-input>
                        </el-form-item>
                        <el-form-item label="项目类别" label-width="80px">
                            <el-select v-model="form.dataType" class="custom-input-height" style="width: 100%">
                                <el-option v-for="item in dataTypeList" :key="item.value" :label="item.label" :value="item.value" />
                            </el-select>
                        </el-form-item>
                        <el-form-item label="操作用户" label-width="80px">
                            <el-input v-model="form.uploadPerson" disabled class="custom-input-height"></el-input>
                        </el-form-item>
                        <el-form-item class="button-container">
                            <el-button class="right-button" type="primary" size="mini" :loading="submitting" @click="handleSubmit">提交 </el-button>
                            <el-button class="right-button" type="info" size="mini" @click="resetForm">重置</el-button>
                        </el-form-item>
                    </el-form>
                </div>
            </div>
        </div>
        <div class="se-right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-grid"></span>
                <span class="title">项目监管</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <el-form :inline="true" size="medium" :model="filterInfo" ref="filterInfo">
                        <el-form-item label="项目编号">
                            <el-input
                                v-model="filterInfo.task_id"
                                placeholder="请输入项目编号"
                                size="mini"
                                class="custom-elinput-height"
                                clearable />
                        </el-form-item>
                        <el-form-item label="项目状态">
                            <el-select v-model="filterInfo.status" placeholder="请选择项目状态" size="mini" class="custom-elinput-height" clearable>
                                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
                            </el-select>
                        </el-form-item>
                        <el-form-item class="search-button">
                            <el-button type="primary" size="mini" @click="getTaskList">查询</el-button>
                            <el-button type="danger" size="mini" @click="deleteTask">删除</el-button>
                            <el-button type="info" size="mini" @click="resetTaskList">重置</el-button>
                        </el-form-item>
                    </el-form>
                    <div class="task-type-row">
                        <el-button
                            v-for="item in taskTypeOptions"
                            :key="item.value"
                            size="small"
                            class="task-type-btn"
                            :class="{ 'is-active': filterInfo.task_type === item.value }"
                            @click="selectTaskType(item.value)">
                            {{ item.label }}({{ taskTypeCounts[item.value] }})
                        </el-button>
                    </div>
                </div>
                <div class="grid-table" ref="gridTableWrap">
                    <el-table
                        ref="taskTable"
                        :height="tableHeight"
                        :data="taskData"
                        stripe
                        style="width: 100%"
                        border
                        @selection-change="handleSelectionChange"
                        v-loading="loading"
                        element-loading-background="rgba(0, 0, 0, 0)">
                        <el-table-column type="selection" width="60" align="center"></el-table-column>
                        <el-table-column prop="task_id" label="项目编号" align="center" width="120"></el-table-column>
                        <el-table-column prop="polygonName" label="项目名称" width="280"></el-table-column>
                        <el-table-column prop="county" label="所属区县" align="center" width="160"></el-table-column>
                        <el-table-column prop="status" label="项目状态" align="center" width="120">
                            <template slot-scope="scope">
                                <span :class="getStatusColor(scope.row.status)">
                                    {{ statusText(scope.row.status) }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column prop="hasPic" label="是否已采集数据" align="center" width="140"></el-table-column>
                        <el-table-column prop="createPerson" label="创建用户" align="center" width="140"></el-table-column>
                        <el-table-column prop="collectTime" label="采集时间" align="center" width="200"></el-table-column>
                        <el-table-column prop="createTime" label="创建时间" align="center" width="200"></el-table-column>
                        <el-table-column label="操作" align="center" width="160" fixed="right" >
                            <template slot-scope="scope" >
                                <el-button type="text" size="mini" class="blue" @click="handleDataView(scope.row)"> 查看 </el-button>
                                <el-button type="text" size="mini" class="blue" @click="handleDataUpload(scope.row)"> 上传 </el-button>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                <div class="page">
                    <el-pagination
                        background
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange"
                        :current-page="filterInfo.page"
                        :page-sizes="[10, 20, 30, 40]"
                        :page-size="filterInfo.limit"
                        layout="sizes, prev, pager, next, total"
                        :total="dataCount" />
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import {
    TASK_MGMT_USE_MOCK,
    getSupervisionProjectListApi,
    buildSupervisionProjectListParams,
    addSupervisionProjectApi,
    deleteSupervisionProjectApi,
    TASK_TYPE_DATA_TYPE_MAP,
    DATA_TYPE_TO_TASK_TYPE
} from '@/api/taskMgmtApi';
import { mockGetSupervisionProjectListApi } from '@/views/taskManagementModule/mock/taskApi';
import { adaptProjectList } from '@/views/taskManagementModule/utils/projectListAdapter';
import county from '@/utils/county';

export default {
    name: 'TaskMgmtTaskList',
    data() {
        return {
            form: {
                zipFile: '',
                uploadPerson: '',
                dataType: 1
            },
            filterInfo: {
                task_type: 'temp_land_restore',
                task_id: '',
                status: '',
                county: '',
                limit: 10,
                page: 1
            },
            dataTypeList: [
                { label: '临时用地恢复', value: 1 },
                { label: '山水工程项目', value: 2 },
                { label: '建设项目', value: 3 }
            ],
            statusOptions: [
                { label: '待核实', value: 0 },
                { label: '已核实', value: 2 }
            ],
            taskTypeOptions: [
                { label: '临时用地恢复', value: 'temp_land_restore' },
                { label: '山水工程项目', value: 'mountain_water' },
                { label: '建设项目', value: 'construction' }
            ],
            taskTypeCounts: {
                temp_land_restore: 0,
                mountain_water: 0,
                construction: 0
            },
            countyList: [],
            filterCountyData: [],
            taskData: [],
            selectedTask: [],
            dataCount: 0,
            loading: false,
            uploadFile: null,
            submitting: false,
            tableHeight: 400,
            resizeObserver: null
        };
    },
    methods: {
        handleSizeChange(val) {
            this.filterInfo.limit = val;
            this.filterInfo.page = 1;
            this.getTaskList();
        },
        handleCurrentChange(val) {
            this.filterInfo.page = val;
            this.getTaskList();
        },
        handleSelectionChange(val) {
            this.selectedTask = val.map((item) => item.id);
        },
        checkZipFile() {
            document.querySelector('#taskMgmtZip').click();
        },
        handleFileUpload(event) {
            const file = event.target.files[0];
            if (file) {
                this.uploadFile = file;
                this.form.zipFile = file.name;
                this.$message.success('文件选择成功');
            }
        },
        async handleSubmit() {
            if (!this.uploadFile) {
                this.$message.warning('请先上传包含 shp 的 zip 压缩包');
                return;
            }
            const dataType = this.form.dataType;
            if (!dataType) {
                this.$message.warning('请选择项目类别');
                return;
            }
            const formData = new FormData();
            formData.append('dataType', dataType);
            formData.append('file', this.uploadFile);
            this.submitting = true;
            try {
                const res = await addSupervisionProjectApi(formData);
                if (res.code === 0) {
                    const count = (res.data && (res.data.projectCount || res.data.polygonCount)) || 1;
                    const msg = count > 1 ? `新增成功，已按 ${count} 个图斑创建 ${count} 个监管项目` : res.msg || '新增成功';
                    this.$message.success(msg);
                    this.resetForm();
                    const taskType = DATA_TYPE_TO_TASK_TYPE[Number(dataType)];
                    if (taskType) {
                        this.filterInfo.task_type = taskType;
                    }
                    this.filterInfo.page = 1;
                    this.getTaskList();
                } else {
                    this.$message.error(res.msg || '新增失败');
                }
            } catch (e) {
                console.warn('新增监管项目失败', e);
                this.$message.error('新增失败');
            } finally {
                this.submitting = false;
            }
        },
        resetForm() {
            this.form.zipFile = '';
            this.form.dataType = TASK_TYPE_DATA_TYPE_MAP[this.filterInfo.task_type] || 1;
            this.uploadFile = null;
            const input = document.querySelector('#taskMgmtZip');
            if (input) {
                input.value = '';
            }
        },
        selectTaskType(taskType) {
            if (this.filterInfo.task_type === taskType) return;
            this.filterInfo.task_type = taskType;
            this.handleTaskTypeChange();
        },
        handleTaskTypeChange() {
            this.filterInfo.task_id = '';
            this.filterInfo.status = '';
            this.filterInfo.county = '';
            this.filterInfo.page = 1;
            this.form.dataType = TASK_TYPE_DATA_TYPE_MAP[this.filterInfo.task_type] || 1;
            this.$router.replace({
                path: '/task-mgmt/verify-clue',
                query: { taskType: this.filterInfo.task_type }
            });
            this.getTaskList();
        },
        async getTaskList() {
            this.loading = true;
            const params = buildSupervisionProjectListParams({
                pageIndex: this.filterInfo.page,
                pageSize: this.filterInfo.limit,
                taskType: this.filterInfo.task_type,
                taskId: this.filterInfo.task_id,
                status: this.filterInfo.status,
                county: this.filterInfo.county
            });
            const fetchApi = TASK_MGMT_USE_MOCK ? mockGetSupervisionProjectListApi : getSupervisionProjectListApi;
            try {
                const res = await fetchApi(params);
                if (res.code === 0 && res.data) {
                    this.taskData = adaptProjectList(res.data);
                    this.dataCount = res.total != null ? res.total : this.taskData.length;
                    this.taskTypeCounts = {
                        temp_land_restore: res.count1 != null ? res.count1 : 0,
                        mountain_water: res.count2 != null ? res.count2 : 0,
                        construction: res.count3 != null ? res.count3 : 0
                    };
                } else {
                    this.taskData = [];
                    this.dataCount = 0;
                }
            } catch (e) {
                console.warn('任务列表接口请求失败', e);
                this.taskData = [];
                this.dataCount = 0;
            } finally {
                this.loading = false;
                this.updateTableHeight();
            }
        },
        resetTaskList() {
            this.filterInfo.task_id = '';
            this.filterInfo.status = '';
            this.filterInfo.county = '';
            this.filterInfo.page = 1;
            this.filterCountyData = [];
            this.getTaskList();
        },
        filterCounty(value) {
            if (!value) {
                this.filterCountyData = [];
                return;
            }
            const reg = new RegExp(value);
            this.filterCountyData = this.countyList.filter((item) => reg.test(item.label));
        },
        deleteTask() {
            if (!this.selectedTask.length) {
                this.$message.warning('请先选择要删除的任务');
                return;
            }
            this.$confirm('是否确认删除任务？删除不可撤销', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const params = this.selectedTask.length === 1 ? { id: this.selectedTask[0] } : { ids: this.selectedTask };
                    const res = await deleteSupervisionProjectApi(params);
                    if (res.code === 0) {
                        this.$message.success(res.msg || '删除成功');
                        this.selectedTask = [];
                        this.getTaskList();
                    } else {
                        this.$message.error(res.msg || '删除失败');
                    }
                })
                .catch(() => {
                    this.$message.info('已取消删除');
                });
        },
        handleDataView(row) {
            const id = row.id != null ? row.id : row.task_id;
            this.$router.push({
                path: '/task-mgmt/verify-clue',
                query: { id, taskType: this.filterInfo.task_type }
            });
        },
        handleDataUpload(row) {
            const taskId = row.id != null ? row.id : row.task_id;
            const taskName = row.task_id != null ? String(row.task_id) : '';
            this.$router.push({
                path: '/task-mgmt/data-upload',
                query: {
                    autoUpload: '1',
                    taskId,
                    taskName
                }
            });
        },
        getStatusColor(status) {
            switch (status) {
                case 0:
                    return 'blue';
                case 1:
                    return 'green';
                case 2:
                    return 'red';
                default:
                    return '';
            }
        },
        statusText(status) {
            switch (status) {
                case 0:
                    return '待核实';
                case 1:
                    return '核实中';
                case 2:
                    return '已完成';
                default:
                    return '未知';
            }
        },
        updateTableHeight() {
            this.$nextTick(() => {
                const wrap = this.$refs.gridTableWrap;
                if (!wrap) return;
                const height = wrap.clientHeight;
                if (height > 0) {
                    this.tableHeight = height;
                }
                this.$refs.taskTable && this.$refs.taskTable.doLayout();
            });
        }
    },
    mounted() {
        this.form.uploadPerson = localStorage.getItem('username') || '';
        if (this.$route.query.taskType) {
            this.filterInfo.task_type = this.$route.query.taskType;
        }
        this.form.dataType = TASK_TYPE_DATA_TYPE_MAP[this.filterInfo.task_type] || 1;
        this.getTaskList();
        this.$nextTick(() => {
            this.updateTableHeight();
            if (typeof ResizeObserver !== 'undefined' && this.$refs.gridTableWrap) {
                this.resizeObserver = new ResizeObserver(() => this.updateTableHeight());
                this.resizeObserver.observe(this.$refs.gridTableWrap);
            }
        });
        window.addEventListener('resize', this.updateTableHeight);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.updateTableHeight);
        if (this.resizeObserver) {
            this.resizeObserver.disconnect();
            this.resizeObserver = null;
        }
    }
};
</script>

<style lang="scss" scoped>
.title {
    margin-left: 8px;
}

::v-deep .el-form-item--medium .el-form-item__label {
    line-height: 36px;
    color: #fff !important;
}

.button-container {
    display: flex;
    padding: 14px;
    align-items: center;
    text-align: center;
    justify-content: center;
    border-top: 1px solid #0a579e;
}

.grid-table {
    margin-top: 20px;
    margin-left: 10px;
    margin-right: 18px;
    flex: 1;
    min-height: 0;
    overflow: hidden;
}

.se-right-content {
    display: flex;
    flex-direction: column;
    overflow: hidden;
}

.right-content-body {
    padding: 10px;
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-sizing: border-box;
}

::v-deep .el-table__fixed-right,
::v-deep .el-table__fixed-right-patch {
    background-color: #00092d;
}

::v-deep .el-table__fixed-right .el-table__fixed-body-wrapper,
::v-deep .el-table__fixed-right .el-table__fixed-header-wrapper {
    background-color: #00092d;
}

.task-type-row {
    width: 100%;
    margin-top: 8px;
    margin-bottom: 10px;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    border-top: 1px solid #0a579e;
}

::v-deep .task-type-btn {
    background-color: #00092d;
    border-color: #0a579e;
    color: #fff;
    border-radius: 2px;
    padding: 8px 16px;
    margin-left: 0;
    margin-top: 8px;
}

::v-deep .task-type-btn:hover,
::v-deep .task-type-btn:focus {
    background-color: #001a4d;
    border-color: #177de4;
    color: #fff;
}

::v-deep .task-type-btn.is-active,
::v-deep .task-type-btn.is-active:hover,
::v-deep .task-type-btn.is-active:focus {
    background: linear-gradient(0deg, #3b8df1 0%, rgba(0, 99, 191, 0) 100%);
    border-color: #177de4;
    color: #fff;
}

.se-filter-form .el-form-item {
    margin-bottom: 0;
}

.se-filter-form {
    padding: 10px 10px 0 10px;
    flex-shrink: 0;
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
    float: left;
    font-size: 14px;
    line-height: 40px;
    padding: 0 12px 0 0;
    box-sizing: border-box;
    color: #fff;
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

.upload-tip {
    margin-top: 6px;
    padding-left: 80px;
    color: #8fc7ff;
    font-size: 12px;
    line-height: 18px;
}

::v-deep .el-input--small .el-input__inner {
    height: 40px;
    line-height: 40px;
}

.blue {
    color: #409eff;
}
</style>

<style lang="scss">
@import '@/assets/css/table/new-common.scss';
</style>
