<template>
    <div class="se-content-right-body">
        <div class="right-content">
            <div class="right-content-header">
                <span class="icon iconfont icon-geoai-list"></span>
                <span class="title">任务管理</span>
            </div>
            <div class="right-content-body">
                <div class="se-filter-form">
                    <div>
                        <span class="filter-label">开始日期：</span>
                        <el-date-picker
                            v-model="filterForm.time"
                            type="daterange"
                            range-separator="至"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            format="yyyy-MM-dd"
                            value-format="yyyy-MM-dd">
                        </el-date-picker>
                    </div>
                    <div>
                        <span class="filter-label">所属区域：</span>
                        <el-tooltip
                            :content="filterForm.regionZw.join(' / ')"
                            placement="top"
                            :disabled="!filterForm.regionZw || filterForm.regionZw.length === 0">
                            <el-cascader
                                ref="cascaderRef"
                                :options="regionOptions"
                                v-model="filterForm.regionSelect"
                                style="max-width: 130px"
                                @change="handleRegionChange"
                                clearable
                                :change-on-select="true"></el-cascader>
                        </el-tooltip>
                    </div>
                    <div>
                        <span class="filter-label">任务状态：</span>
                        <el-select v-model="filterForm.status" placeholder="请选择" style="max-width: 100px" clearable>
                            <el-option v-for="item in batchStatusList" :key="item.value" :label="item.name" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div>
                        <span class="filter-label">任务类型：</span>
                        <el-select v-model="filterForm.batchType" placeholder="请选择" style="max-width: 100px" clearable>
                            <el-option v-for="item in batchTypeOptions" :key="item.value" :label="item.name" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div>
                        <el-input placeholder="请输入任务名称" style="max-width: 150px" v-model="filterForm.keyword" clearable></el-input>
                    </div>
                    <div>
                        <el-button type="primary" size="mini" @click="handleSelectTableData">查询</el-button>
                        <el-button type="info" size="mini" @click="resetQuery">重置</el-button>
                        <el-button type="danger" size="mini" @click="batchDelete">删除</el-button>
                        <el-button type="primary" size="mini" @click="handleOpenDialog">新增任务</el-button>
                    </div>
                </div>
                <div class="se-data-table">
                    <el-table
                        :data="projects"
                        border
                        :default-sort="{ prop: 'startDate', order: 'descending' }"
                        max-height="100%"
                        height="100%"
                        width="100%"
                        @selection-change="handleSelectionChange"
                        @row-click="handleRowClick">
                        <el-table-column type="selection" width="50"></el-table-column>
                        <el-table-column prop="batch_name" label="任务名称" align="center" width="160"></el-table-column>
                        <el-table-column prop="batch_id" label="任务编号" sortable align="center" width="160"></el-table-column>
                        <el-table-column prop="batch_type" label="任务类型" width="120" sortable>
                            <template slot-scope="scope">
                                <span v-if="scope.row.batch_type === 0">固定任务</span>
                                <span v-else>临时任务</span>
                            </template>
                        </el-table-column>
                        <el-table-column prop="done_count" label="已上传/待上传" align="center"></el-table-column>
                        <el-table-column prop="start_date" label="开始日期" align="center"></el-table-column>
                        <el-table-column prop="end_date" label="结束日期" align="center"></el-table-column>
                        <el-table-column prop="status" label="状态" align="center">
                            <template slot-scope="scope">
                                <span :style="{ color: getStatusColor(scope.row.status) }">
                                    {{ scope.row.status }}
                                </span>
                            </template>
                        </el-table-column>
                        <el-table-column prop="fcw" label="防尘网数量(个)" align="center"></el-table-column>
                        <el-table-column prop="wd" label="围挡数量(个)" align="center"></el-table-column>
                        <el-table-column prop="jj" label="机具数量(个)" align="center"></el-table-column>
                        <el-table-column prop="suspected_clue_count" label="疑似违法线索数(个)" align="center"></el-table-column>
                        <el-table-column prop="pending_clue_count" label="待核实线索数(个)" align="center"></el-table-column>
                        <el-table-column prop="confirmed_clue_count" label="有效线索数(个)" align="center"></el-table-column>
                        <el-table-column prop="region" label="所属区域" align="center"></el-table-column>
                        <el-table-column label="操作" align="center" width="200">
                            <template slot-scope="scope">
                                <ul class="action-list">
                                    <el-button type="text" size="mini" @click="skipToVerifyClue(scope.row)">查看</el-button>
                                    <el-button type="text" size="mini" @click="finishVerify(scope.row)" :disabled="isMarked(scope.row.orginalStatus)"
                                        ><span :style="{ color: changeStyle(scope.row.orginalStatus) }">判读完成</span>
                                    </el-button>
                                    <el-button type="text" size="mini" @click="exportBatchShp(scope.row)" v-if="isMarked(scope.row.orginalStatus)"
                                        ><span :style="{ color: showDownloadShpStyle(scope.row.orginalStatus) }">导出SHP</span>
                                    </el-button>
                                    <el-button
                                        type="text"
                                        size="mini"
                                        @click="handleSkipPath(scope.row)"
                                        v-if="scope.row.pointType === 0"
                                        style="margin-left: 10px"
                                        >上传</el-button
                                    >
                                </ul>
                            </template>
                        </el-table-column>
                    </el-table>
                </div>
                <el-pagination
                    background
                    layout="total, sizes,  prev, pager, next, jumper"
                    v-model="filterForm.pageIndex"
                    class="pagination"
                    :total="total"
                    :page-size="filterForm.pageSize"
                    @size-change="handleSizeChange"
                    @current-change="handleCurrentChange">
                </el-pagination>
            </div>
        </div>
        <el-dialog title="新增任务" :visible.sync="dialogVisible" width="520px" top="100px" custom-class="custom-dialog" @close="resetForm">
            <el-form size="medium" :model="form" ref="form" :rules="rules" label-width="100px">
                <el-form-item label="开始日期:" prop="begindate">
                    <el-date-picker v-model="form.begindate" type="date" placeholder="选择开始日期" format="yyyy-MM-dd" value-format="yyyy-MM-dd">
                    </el-date-picker>
                </el-form-item>
                <el-form-item label="结束日期:" prop="enddate">
                    <el-date-picker v-model="form.enddate" type="date" placeholder="选择结束日期" format="yyyy-MM-dd" value-format="yyyy-MM-dd">
                    </el-date-picker>
                </el-form-item>
                <el-form-item label="时间间隔:" prop="time_interval">
                    <el-input v-model.number="form.time_interval" placeholder="以天为单位"></el-input>
                </el-form-item>
                <el-form-item label="任务数量:" prop="tasknum">
                    <el-input v-model="tasknum" disabled></el-input>
                </el-form-item>
                <el-form-item label="区域选择:" prop="region">
                    <el-cascader
                        :options="regionOptions"
                        v-model="form.region"
                        :change-on-select="true"
                        ref="cascaderRefDialog"
                        @change="handleRegionChange"></el-cascader>
                </el-form-item>
                <el-form-item label="业务数据:" prop="resource">
                    <el-select v-model="form.resourceIdList" placeholder="请选择" multiple>
                        <!--multiple clearable-->
                        <el-option v-for="item in resourceOptions" :key="item.id" :label="item.name" :value="item.id"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="变化检测:" prop="changeDetection">
                    <el-radio-group v-model="form.changeDetection">
                        <el-radio border :label="1">是</el-radio>
                        <el-radio border :label="0">否</el-radio>
                    </el-radio-group>
                </el-form-item>

                <el-form-item class="t-btn">
                    <el-button type="primary" size="small" @click="submitForm('form')">添加任务</el-button>
                    <el-button type="info" size="small" @click="reset">重置任务</el-button>
                </el-form-item>
            </el-form>
        </el-dialog>
    </div>
</template>

<script>
import {
    getTaskManageTable,
    getRegionOptions,
    addBatchTask,
    batchDeleteTaskApi,
    getEnumOptionApi,
    getBufferLayerApi,
    changeBatchToHszApi,
    exportBatchShpApi,
    getDownloadAiResultApi
} from '@/api/commonApi';
import { mapState, mapMutations, mapActions } from 'vuex';

export default {
    name: 'Task',
    data() {
        return {
            regionOptions: [],
            resourceOptions: [],
            batchStatusList: [],
            batchTypeOptions: [
                { name: '固定任务', value: '0' },
                { name: '临时任务', value: '1' }
            ],
            dialogVisible: false,
            filterForm: {
                time: [],
                batchType: '', //批次类别
                status: '', //批次状态
                keyword: '', //批次名称
                id: '', //批次ID
                pageIndex: 1,
                startDate: '',
                county: '',
                gridId: '',
                done: 0,
                regionSelect: [],
                regionZw: []
            },
            total: 5,
            projects: [],
            baseUrl: process.env.VUE_APP_API_URL, //请求地址
            rules: {
                begindate: [{ required: true, message: '请选择开始日期', trigger: 'blur' }],
                enddate: [{ required: true, message: '请选择结束日期', trigger: 'blur' }],
                time_interval: [
                    { required: true, message: '请选择时间间隔且为数字类型', trigger: 'blur', type: 'number' },
                    {
                        validator: (rule, value, callback) => {
                            if (value === 0 || value === '0') {
                                callback(new Error('时间间隔不能为0'));
                            } else {
                                callback();
                            }
                        },
                        trigger: 'submit' // 关键点：只在提交时校验
                    }
                ],
                region: [{ required: true, message: '请选择所属区域', trigger: 'blur' }]
                // resource: [{required: true, message: '请选择资源', trigger: 'blur'}],
            },
            form: {
                time_interval: 0,
                begindate: '',
                enddate: '',
                region: '',
                resourceIdList: '',
                changeDetection: 0
            }
        };
    },
    watch: {
        'form.begindate'(newVal, oldVal) {
            if (this.form.enddate !== '' && new Date(newVal) >= new Date(this.form.enddate)) {
                this.$message.warning('结束日期不能大于开始日期');
                this.form.enddate = '';
            }
        },
        'form.enddate'(newVal, oldVal) {
            if (new Date(newVal) <= new Date(this.form.begindate)) {
                this.$message.warning('结束日期不能大于开始日期');
                this.form.enddate = '';
            }
        },
        'form.time_interval'(newVal, oldVal) {
            if (this.form.begindate !== '' && this.form.enddate !== '') {
                const start = new Date(this.form.begindate);
                const end = new Date(this.form.enddate);
                const diffTime = Math.abs(end - start + 1);
                if (newVal > Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1) {
                    this.$message.warning('时间间隔不能大于日期之差');
                    this.form.time_interval = 0;
                }
            }
        },
        'filterForm.time'(newVal, oldVal) {
            if (newVal !== null) {
                this.filterForm.startDate = this.filterForm.time[0];
                this.filterForm.endDate = this.filterForm.time[1];
            } else {
                this.filterForm.startDate = '';
                this.filterForm.endDate = '';
            }
        }
    },
    methods: {
        ...mapMutations('filter', ['SET_TABLE_FILTERS']),
        ...mapActions('filter', ['updateTableFilters']),
        // 恢复筛选条件
        restoreFilters() {
            // 从 Vuex 获取存储的筛选条件
            const filters = this.storedFilters;
            console.log(filters);
            // 复制其他筛选条件
            this.filterForm = {
                time: filters.time || [],
                batchType: filters.batchType || '',
                keyword: filters.keyword || '',
                status: filters.status || '',
                pageSize: filters.pageSize || 10,
                pageIndex: filters.pageIndex || 1,
                id: filters.id || '',
                county: filters.county || '',
                gridId: filters.gridId || '',
                startDate: filters.startDate || '',
                endDate: filters.endDate || '',
                regionSelect: filters.regionSelect || [],
                regionZw: filters.regionZw || []
            };
        },
        // 保存筛选条件到 Vuex
        saveFiltersToVuex() {
            // 处理时间格式
            const filtersToSave = {
                ...this.filterForm
            };
            // 提交到 Vuex
            this.updateTableFilters(filtersToSave);
        },
        //重置
        reset() {
            this.form.enddate = '';
            this.form.begindate = '';
            this.form.time_interval = 0;
            this.form.region = '';
            this.form.resourceIdList = '';
        },
        handleOpenDialog() {
            this.dialogVisible = true;
        },
        resetForm() {
            this.$refs.form.resetFields(); // 重置表单验证状态和字段值
            // 手动处理非表单绑定的字段（如 fileList）
            this.form.fileList = [];
        },
        resetQuery() {
            this.filterForm.time = [];
            this.filterForm.regionSelect = '';
            this.filterForm.status = '';
            this.filterForm.keyword = '';
            this.filterForm.pageSize = 10;
            this.filterForm.startDate = '';
            this.filterForm.endDate = '';
            this.filterForm.batchType = '';
            this.filterForm.keyword = '';
            this.filterForm.gridId = '';
            this.$store.commit('filter/RESET_FILTERS');
            this.getTableData();
        },
        handleDock(row) {
            //下载报告
            this.$confirm('是否下载该报告?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(() => {
                    try {
                        let url = `${this.baseUrl}/reports/batch-download/${row.id}`;
                        const link = document.createElement('a');
                        link.href = url;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link); // 移除临时链接
                    } catch (error) {
                        if (error.response && error.response.status === 404) {
                            this.$message.error('文件未找到');
                        } else {
                            this.$message.error('下载文件时发生错误');
                        }
                    }
                })
                .catch(() => {
                    this.$message({ type: 'info', message: '已取消下载' });
                });
        },
        //设置任务状态颜色
        getStatusColor(status) {
            switch (status) {
                // case '●部分检测':
                case '●待判读':
                    return '#22c961';
                case '●待推送':
                    return 'green';
                case '●已推送':
                    return 'black';
                case '●检测失败':
                    return 'red';
                case '●核实中':
                    return '#22c961';
                case '●待上传':
                    return 'gray';
                case '●检测中':
                    return '#4caf50';
                default:
                    return 'gray';
            }
        },
        //处理当前页数
        handleSizeChange(val) {
            this.filterForm.pageSize = val;
            this.getTableData();
        },
        //处理当前页
        handleCurrentChange(val) {
            this.filterForm.pageIndex = val;
            this.getTableData();
        },
        //表单模糊查询
        handleSelectTableData() {
            if (this.filterForm.regionSelect.length >= 1) {
                const index = this.filterForm.regionSelect.length - 1;
                const tempnum = this.filterForm.regionSelect[index];
                if (tempnum.length <= 9) {
                    this.filterForm.county = tempnum;
                } else {
                    this.filterForm.gridId = tempnum;
                }
            }
            this.filterForm.pageIndex = 1;
            this.saveFiltersToVuex();
            this.getTableData();
        },
        //获取表格数据
        async getTableData() {
            const res = await getTaskManageTable(this.filterForm);
            if (res.code === 0) {
                this.projects = res.data;
                this.total = res.total;
            } else {
                this.$message.error(res.msg);
            }
        },
        //处理跳转
        skipToVerifyClue(row) {
            const [uploadedCount, notUploadedCount] = row.done_count.split('/');
            if (uploadedCount === '0') {
                this.$message.warning('该任务没有上传的全景图,当前无法查看');
            } else {
                const id = row.batch_id;
                this.$router.push({ name: 'verifyClue', query: { id } });
            }
        },
        //结束判读
        async finishVerify(row) {
            const params = {
                batchId: row.batch_id
            };
            const res = await changeBatchToHszApi(params);
            if (res.code === 0) {
                this.$message.success('处理成功');
                this.getTableData();
            } else {
                this.$message.error(res.msg);
            }
        },
        //导出批次绘制的shp
        async exportBatchShp(row) {
            const params = {
                batchId: row.batch_id
            };
            const res = await exportBatchShpApi(params);
            if (res.code === 0) {
                const file_name = res.data.file_name;
                const file_id = res.data.file_id;
                this.downloadFiles(file_id, file_name);
                this.$message.success('处理成功');
            } else {
                this.$message.error(res.msg);
            }
        },
        isMarked(orginalStatus) {
            if (orginalStatus === 4) {
                return true;
            } else {
                return false;
            }
        },
        async downloadFiles(file_id, file_name) {
            try {
                // let url = `/lais/site/inspection/interpretation_task/download_result/${row.id}`;

                const response = await getDownloadAiResultApi(file_id);
                const url = window.URL.createObjectURL(new Blob([response]));

                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', file_name); // 假设文件路径的最后一部分是文件名

                document.body.appendChild(link);
                link.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link); // 移除临时链接
                this.$message.success('下载成功！');
            } catch (error) {
                console.error('下载失败:', error);
                // 尝试读取错误信息
                if (error.response?.data) {
                    const reader = new FileReader();
                    reader.onload = () => alert(reader.result);
                    reader.readAsText(error.response.data);
                }
            }
        },
        //跳转图片上传页面
        handleSkipPath(row) {
            const batch_id = row.batch_id;
            this.$router.push({ path: '/panoramic-detection/panorama-upload', query: { batch_id } });
        },
        showDownloadShpStyle(status) {
            if (status === 4) {
                return '#177DE4';
            } else {
                return 'gray';
            }
        },
        changeStyle(status) {
            if (status === 4) {
                return 'gray';
            } else {
                return '#177DE4';
            }
        },
        //获取区域的级联数据
        async getRegionoptions() {
            const res = await getRegionOptions();
            this.regionOptions = res.data;
        },
        //获取资源数据
        async getResourceOptions() {
            const res = await getBufferLayerApi();
            this.resourceOptions = res.data;
        },

        //提交表单
        submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (valid) {
                    this.addTask();
                } else {
                    console.log('error submit!!');
                    return false;
                }
            });
        },

        //添加任务
        async addTask() {
            try {
                if (this.form.region.length < 2) {
                    //this.$message.warning('区域必须选择到网格！');
                    //return;
                }
                const senddata = {
                    startDate: this.form.begindate,
                    endDate: this.form.enddate,
                    intervalDays: this.form.time_interval,
                    region: this.form.region.join('/'),
                    regionZw: this.filterForm.regionZw.join('/'),
                    username: localStorage.getItem('username'),
                    resourceIdList: this.form.resourceIdList,
                    changeDetect: this.form.changeDetection
                };
                const res = await addBatchTask(senddata);
                if (res.code === 0) {
                    this.$message.success('添加任务成功');
                    this.getTableData();
                    this.dialogVisible = false;
                } else {
                    this.$message.error(res.msg);
                }
            } catch (e) {
                console.log('添加任务失败', e);
            }
        },
        //处理级联状态的返回值
        handleRegionChange(value) {
            // value 是选中项的 value 数组
            let selectedLabels = [];
            const findLabels = (options, values) => {
                let currentLabels = [];
                for (let i = 0; i < options.length; i++) {
                    if (options[i].value === values[0]) {
                        currentLabels.push(options[i].label);
                        if (options[i].children && values.length > 1) {
                            const childLabels = findLabels(options[i].children, values.slice(1));
                            if (childLabels.length > 0) {
                                currentLabels = currentLabels.concat(childLabels);
                            }
                        }
                    }
                }
                return currentLabels;
            };
            selectedLabels = findLabels(this.regionOptions, value);
            // 这里可以进行进一步的操作，例如发送到服务器或更新其他数据
            this.filterForm.regionZw = selectedLabels;
            const cascader = this.$refs.cascaderRef;
            if (cascader) {
                cascader.dropDownVisible = false;
            }
            const cascaderRefDialog = this.$refs.cascaderRefDialog;
            if (cascaderRefDialog) {
                cascaderRefDialog.dropDownVisible = false;
            }
        },
        //获取任务状态选项值
        async getStatus() {
            const res = await getEnumOptionApi('Batch_Status');
            if (res.code === 0) {
                this.batchStatusList = res.data['Batch_Status'];
            } else {
                this.$message.error(res.msg);
            }
        },
        //获取选中的值
        handleSelectionChange(val) {
            this.selectitems = val.map((item) => item.batch_id);
        },
        handleRowClick(row) {
            this.$router.replace({ query: { ...this.$route.query, selectedId: row.batch_id } });
        },
        //批量删除
        async batchDelete() {
            if (this.selectitems.length !== 0) {
                this.$confirm('确认删除任务吗？', '提示', {
                    type: 'warning',
                    confirmButtonText: '确定',
                    cancelButtonText: '取消'
                })
                    .then(async () => {
                        try {
                            const params = {
                                batchIds: this.selectitems
                            };
                            const res = await batchDeleteTaskApi(params);
                            if (res.code === 0) {
                                this.$message.success('删除成功');
                                this.getTableData();
                            }
                        } catch (error) {
                            // 处理错误，例如显示错误消息
                            this.$message.error('删除失败', res.msg);
                        }
                    })
                    .catch((error) => {
                        this.$message({
                            type: 'info',
                            message: '已取消删除'
                        });
                    });
            } else {
                this.$message.error('请选择要删除的项目！');
            }
        }
    },
    computed: {
        ...mapState('filter', {
            storedFilters: (state) => state.tableFilters
        }),
        tasknum() {
            if (this.form.begindate !== '' && this.form.enddate !== '') {
                if (this.form.time_interval !== 0 && typeof this.form.time_interval == 'number') {
                    const start = new Date(this.form.begindate);
                    const end = new Date(this.form.enddate);
                    const diffTime = Math.abs(end - start + 1);
                    // 计算天数差并除以时间间隔，然后向下取整
                    return Math.floor(diffTime / (1000 * 60 * 60 * 24) / this.form.time_interval); // 将毫秒转换为天数
                } else {
                    return 0;
                }
            }
            return 0; // 如果开始日期或结束日期未设置，返回0
        }
    },
    async mounted() {
        this.getRegionoptions();
        this.getResourceOptions();
        this.getStatus();
        this.getTableData();
    },
    created() {
        this.restoreFilters();
    }
};
</script>

<style lang="scss" scoped>
.right-content {
    width: 100%;
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
}

.el-cascader--medium {
    width: 100%;
}

.el-select--medium {
    width: 100%;
}

table {
    width: 100%;
}

.t-btn {
    display: flex;
    padding-top: 20px;
    align-items: center; /* 垂直居中 */
    margin: 0 auto;
    text-align: center;
    justify-content: center;
}

.page {
    position: absolute; //绝对定位
    right: 20px;
    bottom: 20px;
}

.el-color-picker__icon,
.el-input,
.el-textarea {
    display: inline-block;
}

.el-cascader-menu {
    min-width: 100px;
    box-sizing: border-box;
    color: #606266;
    border-right: solid 1px #e4e7ed;
}

.se-filter-form {
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-wrap: nowrap; /* 禁止子元素换行 */
}
.el-button {
    margin-right: 2px; /* 给按钮之间添加一些间隔 */
}

/* 确保这些样式只在 .right-content 类下生效 */
.right-content .el-cascader,
.right-content .el-select,
.right-content .el-input {
    width: 100%; /* 设置宽度为100% */
}

.se-data-table {
    margin-top: 20px;
    height: calc(100% - 100px);
}

.action-list {
    list-style: none; /* 移除列表前的默认项目符号 */
    padding: 0; /* 移除默认的内边距 */
    margin: 0; /* 移除默认的外边距 */
    display: flex;
}

.action-item {
    cursor: pointer; /* 鼠标悬停时显示指针样式 */
    color: #409eff; /* 设置文字颜色为蓝色 */
    padding: 5px; /* 添加一些内边距 */
}

.el-pagination {
    bottom: 10px;
    right: 30px;
    margin-right: 0;
    float: right;
    position: fixed;
}

.el-cascader--small {
    font-size: 13px;
    line-height: 32px;
}

.se-filter-form div {
    margin-right: 10px;
}

::v-deep .el-date-editor .el-range-separator {
    padding: 0;
    display: inline-block;
    height: 100%;
    margin: 0;
    text-align: center;
    line-height: 28px;
    font-size: 12px;
    width: 5%;
}

.icon {
    font-size: 24px;
    color: #42b4f2;
    padding-right: 5px;
}

.se-content-right-body {
    width: 100%;
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
    box-sizing: border-box;
}
.right-content-body {
    padding: 10px;
    height: calc(100% - 60px);
}

::v-deep .el-date-editor--daterange.el-input__inner {
    width: 300px;
}

::v-deep .el-date-editor {
    width: 100%;
}

.se-container .el-range-editor--small.el-input__inner {
    height: 32px;
}

::v-deep .el-radio {
    width: 120px;
}

::v-deep .el-form-item__content {
    width: calc(100% - 100px);
}
</style>
