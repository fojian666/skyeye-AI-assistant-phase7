<template>
    <div class="se-container my-component">
        <div class="left-content">
            <div class="left-content-header">
                <img src="@/assets/images/table/renwu.svg" width="16" height="16" />
                <span class="title">新增任务</span>
            </div>
            <div class="left-content-body">
                <div class="left-form">
                    <div class="t_items">
                        <span class="demonstration">
                            <img src="@/assets/images/table/xinghao.svg" width="8" height="8" />
                            <span>任务名称</span>
                        </span>
                        <el-input v-model="taskName" class="custom-input-height" placeholder="请填写任务名称"></el-input>
                    </div>
                    <div class="t_items">
                        <span class="demonstration">
                            <img src="@/assets/images/table/xinghao.svg" width="8" height="8" />
                            <span>算法选择</span>
                        </span>
                        <el-select v-model="algorithm" class="custom-input-height" placeholder="请选择算法">
                            <el-option v-for="algorithm in algorithmOptions" :key="algorithm" :label="algorithm" :value="algorithm"></el-option>
                        </el-select>
                    </div>
                    <div class="t_items">
                        <span class="demonstration">
                            <img src="@/assets/images/table/xinghao.svg" width="8" height="8" />
                            <span>当前数据</span>
                        </span>
                        <el-select v-model="algorithm" class="custom-input-height" placeholder="请选择数据">
                            <el-option v-for="algorithm in algorithmOptions" :key="algorithm" :label="algorithm" :value="algorithm"></el-option>
                        </el-select>
                    </div>
                    <div class="t_items">
                        <span class="demonstration">
                            <span>对比数据</span>
                        </span>
                        <el-select v-model="algorithm" class="custom-input-height" placeholder="请选择对比数据">
                            <el-option v-for="algorithm in algorithmOptions" :key="algorithm" :label="algorithm" :value="algorithm"></el-option>
                        </el-select>
                    </div>
                    <div class="t-btn">
                        <el-button class="right-button" type="info" @click="reset">取消</el-button>
                        <el-button class="right-button" type="primary" @click="addTask">确定</el-button>
                    </div>
                </div>
            </div>
        </div>
        <div class="right-content">
            <!--      <div class="right-content-header">-->
            <!--        <span class="icon iconfont icon-geoai-list"></span>-->
            <!--        <span class="title">批次管理</span>-->
            <!--      </div>-->
            <!--      <div class="right-content-body">-->
            <div class="t-query">
                <div class="t-query-items">
                    <div class="t-query-item">
                        <span class="idemonstration">任务名称</span>
                        <el-input placeholder="请输入" v-model="queryinput" class="custom-input-height" clearable></el-input>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">算法类型</span>
                        <el-select v-model="taskState" placeholder="请选择" class="custom-input-height" clearable>
                            <el-option v-for="item in regionOtionsState" :key="item.value" :label="item.name" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">所属单位</span>
                        <el-select v-model="taskState" placeholder="请选择" class="custom-input-height" clearable>
                            <el-option v-for="item in regionOtionsState" :key="item.value" :label="item.name" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">创建时间</span>
                        <el-date-picker
                            v-model="datequery"
                            type="daterange"
                            range-separator="~"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            format="yyyy-MM-dd"
                            value-format="yyyy-MM-dd"
                            class="custom-input-height">
                        </el-date-picker>
                    </div>
                </div>
                <div class="t-query-button">
                    <el-button type="primary" @click="getTableData">
                        <i class="iconfont icon-sousuo" />
                        查询
                    </el-button>
                    <el-button type="info" @click="resetQuery">
                        <i class="iconfont icon-geoai-change" />
                        重置
                    </el-button>
                    <el-button type="danger" @click="batchdelete">
                        <i class="iconfont icon-shanchu1" />
                        删除
                    </el-button>
                </div>
            </div>
            <div class="ttable">
                <el-table
                    :data="projects"
                    border
                    :default-sort="{ prop: 'startDate', order: 'descending' }"
                    max-height="100%"
                    height="100%"
                    width="100%"
                    @selection-change="handleSelectionChange">
                    <el-table-column type="selection" width="50"></el-table-column>
                    <el-table-column
                        type="index"
                        label="序号"
                        align="center"
                        width="60"
                        :index="(index) => (currentPage - 1) * pageSize + index + 1"></el-table-column>
                    <el-table-column prop="taskName" label="任务名称" width="228"></el-table-column>
                    <el-table-column prop="dataType" label="分析算法" width="360"></el-table-column>
                    <el-table-column prop="taskProgress" label="任务进度" width="200" align="center">
                        <template slot-scope="scope">
                            <el-progress :percentage="scope.row.taskProgress" :show-text="false" define-back-color="#202e48"> </el-progress>
                        </template>
                    </el-table-column>
                    <el-table-column prop="dataNum" label="疑似线索数（个）" width="164" align="center">
                        <template slot-scope="scope">
                            <span :style="{ color: '#49B8FF' }">
                                {{ scope.row.dataNum }}
                            </span>
                        </template>
                    </el-table-column>
                    <el-table-column prop="unit" label="所属单位" width="198" align="center"></el-table-column>
                    <el-table-column prop="createPerson" label="创建人" width="149" align="center"></el-table-column>
                    <el-table-column prop="createDate" label="创建时间" width="149" align="center"></el-table-column>
                    <el-table-column label="操作">
                        <template slot-scope="scope">
                            <ul class="action-list">
                                <li class="action-item blue" @click="skipToVerifyClue(scope.row)"><i class="iconfont icon-geoai-look" /></li>
                                <li class="action-item">|</li>
                                <li class="action-item red" @click="handleDock(scope.row)"><i class="iconfont icon-shanchu" /></li>
                                <li class="action-item">|</li>
                                <li class="action-item orange" @click="handleDock(scope.row)"><i class="iconfont icon-24px" /></li>
                                <li class="action-item">|</li>
                                <li class="action-item green" @click="handleDock(scope.row)"><i class="iconfont icon-fenxiang" /></li>
                            </ul>
                        </template>
                    </el-table-column>
                </el-table>
            </div>
            <div class="page">
                <el-pagination
                    background
                    layout="total, sizes,  prev, pager, next, jumper"
                    v-model="currentPage"
                    class="pagination"
                    :total="total"
                    :page-size="pageSize"
                    @size-change="handleSizeChange"
                    @current-change="handleCurrentChange">
                </el-pagination>
            </div>

            <!--      </div>-->
        </div>
    </div>
</template>

<script>
import { getTaskManageTable, getRegionOptions, addBatchTask, batchDeleteTaskApi, getDictByType } from '@/api/commonApi';
import ImageMap from '@/views/intelligentMonitoring/objectDetection/ImageMap.vue';

export default {
    name: 'Task',
    components: { ImageMap },
    data() {
        return {
            regionoptions: [],
            taskName: '',
            time_interval: '',
            begindate: '',
            enddate: '',
            region: '',
            regionZw: '',
            regionOtionsState: [],
            taskState: '',
            regionSelect: [],
            pageSize: 10,
            total: 5,
            projects: [],
            currentPage: 1,
            queryinput: '',
            datequery: '',
            enddatequery: '',
            begindatequery: '',
            baseUrl: process.env.VUE_APP_API_URL,
            algorithm: '',
            algorithmOptions: ['算法1', '算法2', '算法3']
        };
    },
    watch: {
        begindate(newVal, oldVal) {
            if (this.enddate !== '' && new Date(newVal) >= new Date(this.enddate)) {
                this.$message.warning('结束日期不能大于开始日期');
                this.enddate = '';
            }
        },
        enddate(newVal, oldVal) {
            if (new Date(newVal) <= new Date(this.begindate)) {
                this.$message.warning('结束日期不能大于开始日期');
                this.enddate = '';
            }
        },
        time_interval(newVal, oldVal) {
            if (this.begindate !== '' && this.enddate !== '') {
                const start = new Date(this.begindate);
                const end = new Date(this.enddate);
                const diffTime = Math.abs(end - start + 1);
                if (newVal > Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1) {
                    this.$message.warning('时间间隔不能大于日期之差');
                    this.time_interval = 0;
                }
            }
        },
        datequery(newVal, oldVal) {
            if (newVal !== null) {
                this.begindatequery = this.datequery[0];
                this.enddatequery = this.datequery[1];
            } else {
                this.begindatequery = '';
                this.enddatequery = '';
            }
        }
    },
    methods: {
        //重置
        reset() {
            this.enddate = '';
            this.begindate = '';
            this.time_interval = 0;
            this.region = '';
        },
        resetQuery() {
            this.datequery = '';
            this.regionSelect = '';
            this.taskState = '';
            this.queryinput = '';
        },
        handleView(row) {},
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
                        console.log(error);
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
                    return 'blue';
                case '●待推送':
                    return 'green';
                case '●已推送':
                    return 'black';
                case '●检测失败':
                    return 'red';
                case '●核实中':
                    return 'blue';
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
            this.pageSize = val;
            this.getTableData();
        },
        //处理当前页
        handleCurrentChange(val) {
            this.currentPage = val;
            this.getTableData();
        },
        //获取表格数据
        async getTableData() {
            var gridId;
            if (this.regionSelect.length > 1) {
                const index = this.regionSelect.length - 1;
                gridId = this.regionSelect[index];
            }
            const para = {
                keyword: this.queryinput,
                pageSize: this.pageSize,
                pageIndex: this.currentPage,
                status: this.taskState,
                gridId: gridId,
                startDate: this.begindatequery,
                endDate: this.enddatequery
            };
            const res = await getTaskManageTable(para);
            if (res.code === 0) {
                // this.projects = res.data
                this.projects = [
                    {
                        taskName: '天德湖公园',
                        dataType: '新增非农化行为全景监测',
                        taskProgress: 30,
                        dataNum: 12,
                        unit: '自然资源局',
                        createPerson: '北海',
                        createDate: '2025-03-12'
                    }
                ];
                this.total = res.total;
            } else {
                this.$message.error(res.msg);
            }
        },
        //处理跳转
        skipToVerifyClue(row) {
            const [uploadedCount, notUploadedCount] = row.doneCount.split('/');
            if (uploadedCount === '0') {
                this.$message.warning('该批次没有上传的线索,当前无法查看');
            } else {
                const id = row.id;
                this.$router.push({ name: 'verifyClue', query: { id } });
            }
        },
        //获取区域的级联数据
        async getRegionoptions() {
            const res = await getRegionOptions();
            this.regionoptions = res.data;
        },
        //添加任务
        async addTask() {
            const senddata = {
                startDate: this.begindate,
                endDate: this.enddate,
                intervalDays: this.time_interval,
                region: this.region.join('/'),
                regionZw: this.regionZw.join('/'),
                username: localStorage.getItem('username')
            };
            const res = await addBatchTask(senddata);
            if (res.code === 0) {
                this.$message.success('添加任务批次成功');
                this.getTableData();
            } else {
                this.$message.error(res.msg);
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
            selectedLabels = findLabels(this.regionoptions, value);
            // 这里可以进行进一步的操作，例如发送到服务器或更新其他数据
            this.regionZw = selectedLabels;
        },
        //获取任务状态选项值
        async getstatus() {
            const res = await getDictByType('Batch_Status');
            if (res.code === 0) {
                this.regionOtionsState = res.data['Batch_Status'];
            } else {
                this.$message.error(res.msg);
            }
        },
        //获取选中的值
        handleSelectionChange(val) {
            this.selectitems = val.map((item) => item.id);
        },
        //批量删除
        async batchdelete() {
            if (this.selectitems.length !== 0) {
                this.$confirm('确认删除任务吗？', '提示', {
                    type: 'warning',
                    confirmButtonText: '确定',
                    cancelButtonText: '取消'
                })
                    .then(async () => {
                        try {
                            const res = await batchDeleteTaskApi(this.selectitems);
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
        tasknum() {
            if (this.begindate !== '' && this.enddate !== '' && this.time_interval !== 0) {
                const start = new Date(this.begindate);
                const end = new Date(this.enddate);
                const diffTime = Math.abs(end - start + 1);
                // 计算天数差并除以时间间隔，然后向上取整
                return Math.floor(diffTime / (1000 * 60 * 60 * 24) / this.time_interval); // 将毫秒转换为天数
            }
            return 0; // 如果开始日期或结束日期未设置，返回0
        }
    },
    async mounted() {
        // this.getRegionoptions()
        // this.getstatus()
        // this.getTableData()
    }
};
</script>

<style lang="scss" scoped>
.my-component {
    @import '@/assets/css/table/new-common';
}

.title {
    margin-left: 8px;
}

.se-container {
    //padding: 10px;
    height: 100%;
    position: relative;
    background-color: #050e1f;
}

.left-content {
    width: 327px;
    height: 100%;
    border-radius: 2px;
    background-color: #00092d;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
    padding: 16px;
}

.right-content {
    width: calc(100% - 327px);
    height: 100%;
    flex-direction: column;
    border-radius: 2px;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.5);
    background-color: #00092d;
    //background-color: #fff;
}

.left-content-header,
.right-content-header {
    padding: 13px;
    font-weight: 700;
    font-size: 16px;
    color: #ffffff;
    height: 48px;
    line-height: 19px;
    background: linear-gradient(90deg, #0063bf 0%, rgba(10, 28, 62, 0.2) 100%);
    border-radius: 4px;
    display: flex;
    align-items: center;
}

table {
    width: 100%;
}

.left-form {
    margin-left: 13px;
    width: 94%;
    height: 80%;
}

.t_items {
    display: flex;
    align-items: center; /* 垂直居中 */
    height: 40px;
    margin-bottom: 8px;
}

.t-btn {
    display: flex;
    margin-top: 17px;
    padding: 14px;
    align-items: center; /* 垂直居中 */
    text-align: center;
    justify-content: center;
    border-top: 1px solid #0a579e;
}

.page {
    margin-right: 18px;
    margin-left: 10px;
    margin-bottom: 10px;
    height: 64px;
    background: rgba(6, 18, 42, 0.6);
    border: 1px solid #fff;
}

.el-color-picker__icon,
.el-input,
.el-textarea {
    display: inline-block;
    width: 202px;
}

.el-cascader-menu {
    min-width: 100px;
    box-sizing: border-box;
    color: #606266;
    border-right: solid 1px #e4e7ed;
}

.t-query {
    height: 72px;
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-right: 18px;
}

.t-query div {
    display: flex;
}

.t-query-items {
    width: calc(100% - 272px);
    margin-top: 10px;
    margin-right: 16px;
}

.t-query-item {
    width: 25%;
}

.t-query-button {
    width: 272px;
    margin-top: 10px;
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

.ttable {
    margin-left: 10px;
    margin-right: 18px;
    margin-top: 10px;
    height: calc(100% - 154px);
}

.action-list {
    list-style: none; /* 移除列表前的默认项目符号 */
    padding: 0; /* 移除默认的内边距 */
    margin: 0; /* 移除默认的外边距 */
    display: flex;
}

.action-item {
    cursor: pointer; /* 鼠标悬停时显示指针样式 */
    color: #0a579e; /* 设置文字颜色为蓝色 */
    padding: 5px; /* 添加一些内边距 */
}

.el-pagination {
    height: 100%;
    padding: 16px;
    float: right;
}

.el-cascader--small {
    font-size: 13px;
    line-height: 32px;
    width: 220px;
}

.el-date-editor .el-range-separator {
    display: inline-block;
    height: 100%;
    margin: 0;
    line-height: 32px;
    font-size: 14px;
    width: 5%;
    color: #303133;
}

.demonstration {
    width: 30%;
    font-size: 14px;
    color: #ffffff;
    line-height: 16px;
    text-align: right;
}

.demonstration span {
    padding: 0 8px 0 4px;
}

.idemonstration {
    width: 108px;
    font-size: 14px;
    color: #ffffff;
    line-height: 16px;
    text-align: right;
    padding: 10px 8px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}

::v-deep .el-date-editor .el-range-separator {
    padding: 0;
    display: inline-block;
    height: 100%;
    margin: 0;
    text-align: center;
    line-height: 32px;
    font-size: 14px;
    width: 5%;
    color: #303133;
}

.icon {
    font-size: 24px;
    padding-right: 5px;
    background: linear-gradient(180deg, #ffffff 0%, #64d6ff 100%);
    -webkit-background-clip: text;
    color: transparent;
}

.left-content-body {
    padding-top: 17px;
}

.right-content-body {
    padding: 20px 10px 10px 10px;
    height: calc(100% - 40px);
}
</style>
