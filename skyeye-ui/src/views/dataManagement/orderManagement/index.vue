<template>
    <div class="se-container my-component">
        <div class="gt-right-content">
            <div class="t-query">
                <div class="t-query-items">
                    <div class="t-query-item">
                        <span class="idemonstration">订单名称</span>
                        <el-input placeholder="请输入" v-model="queryConditions.orderName" class="custom-elinput-height" clearable></el-input>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">数据类型</span>
                        <el-select v-model="queryConditions.dataType" placeholder="请选择" class="custom-elinput-height selectData" clearable>
                            <el-option v-for="item in dataTypeOptions" :key="item.value" :label="item.label" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">所属单位</span>
                        <el-select v-model="queryConditions.organization" class="selectData" clearable>
                            <el-option v-for="item in organizationOptions" :key="item.value" :label="item.name" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t-query-item">
                        <span class="idemonstration">采集方式</span>
                        <el-select v-model="queryConditions.collectType" placeholder="请选择" class="custom-elinput-height" clearable>
                            <el-option v-for="item in collectTypeOptions" :key="item.value" :label="item.label" :value="item.value" clearable>
                            </el-option>
                        </el-select>
                    </div>
                    <div class="t-query-item">
                        <span class="filterDateLabel">时间</span>
                        <el-date-picker
                            v-model="queryConditions.collectTime"
                            type="daterange"
                            range-separator="~"
                            start-placeholder="开始日期"
                            end-placeholder="结束日期"
                            format="yyyy-MM-dd"
                            value-format="yyyy-MM-dd"
                            class="custom-elinput-height filterDate">
                        </el-date-picker>
                    </div>
                </div>
                <div class="t-query-button">
                    <el-button type="primary" @click="getTableData" size="mini"> 查询 </el-button>
                    <el-button type="info" @click="resetQuery" size="mini"> 重置 </el-button>
                    <el-button type="danger" @click="handleDeleteView" size="mini"> 删除 </el-button>
                </div>
            </div>
            <div class="upload-data">
                <el-button class="right-button" type="primary" size="mini" @click="handleAddOrder">
                    <i class="iconfont icon-shangchuan" />
                    新建订单
                </el-button>
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
                    <el-table-column prop="orderName" label="订单名称"></el-table-column>
                    <el-table-column prop="dataType" label="数据类型" align="center"></el-table-column>
                    <el-table-column prop="organization" label="所属单位" align="center"></el-table-column>
                    <el-table-column prop="collectType" label="采集方式" align="center"></el-table-column>
                    <el-table-column prop="createPerson" label="操作用户" align="center"></el-table-column>
                    <el-table-column prop="collectTime" label="采集时间" align="center"></el-table-column>
                    <el-table-column label="操作">
                        <template slot-scope="scope">
                            <ul class="action-list">
                                <li class="action-item blue" @click="handleView(scope.row)">查看</li>
                                <li class="action-item">|</li>
                                <li class="action-item red" @click="handleDeleteView(scope.row)">删除</li>
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
        </div>
        <el-dialog title="新建订单" :visible.sync="dialogVisible" width="35%" top="100px" class="form-dialog" @close="resetForm">
            <el-form ref="form" :model="form" :rules="rules" label-width="80px">
                <el-form-item label="订单名称" prop="orderName" class="custom-input">
                    <el-input v-model="form.orderName" placeholder="请输入订单名称"></el-input>
                </el-form-item>
                <el-form-item label="数据类型" prop="dataType" class="custom-input">
                    <el-select v-model="form.dataType" placeholder="请选择数据类型" clearable>
                        <el-option v-for="item in dataTypeOptions" :key="item.value" :label="item.label" :value="item.value"></el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="所属单位" prop="organization" class="custom-input">
                    <el-input v-model="form.organization" placeholder="请选择或输入所属单位"></el-input>
                </el-form-item>
                <el-form-item label="采集方式" prop="collectType" class="custom-input">
                    <el-select v-model="form.collectType" clearable placeholder="请选择采集方式" :change-on-select="true">
                        <el-option v-for="item in collectTypeOptions" :key="item.value" :label="item.label" :value="item.value"> </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="行政区" ref="county" prop="county" class="custom-input">
                    <el-select
                        v-model="form.county"
                        filterable
                        remote
                        reserve-keyword
                        placeholder="请先输入行政区检索关键字"
                        :remote-method="filterCounty"
                        @change="filterCounty"
                        @blur="$refs.county.onFieldBlur()"
                        clearable>
                        <el-option
                            v-for="d in filterCountyData"
                            :key="d.value + '(' + d.key + ')'"
                            :label="d.value + '(' + d.key + ')'"
                            :value="d.value + '(' + d.key + ')'"
                            :data-code="d.key">
                        </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="选择航线" prop="route" class="custom-input">
                    <el-select v-model="form.route" clearable placeholder="请选择航线" :change-on-select="true">
                        <el-option v-for="item in routeList" :key="item.id" :label="item.name" :value="item.id"> </el-option>
                    </el-select>
                </el-form-item>
                <el-form-item label="采集时间" prop="collectTime" class="custom-input">
                    <el-date-picker
                        v-model="form.collectTime"
                        type="date"
                        placeholder="选择日期"
                        format="yyyy 年 MM 月 dd 日"
                        value-format="yyyy-MM-dd">
                    </el-date-picker>
                </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
                <el-button @click="resetForm">重置</el-button>
                <el-button type="primary" @click="submitForm('form')" :loading="isLoading">确 定</el-button>
            </span>
        </el-dialog>
    </div>
</template>

<script>
import {
    getOrderListApi,
    getEnumOptionApi,
    deleteMultDataApi,
    getRouteListApi,
    getMultDataDictApi,
    postOrderInfoApi,
    getRegionInfoListApi
} from '@/api/commonApi';

export default {
    name: 'OrderManagement',
    data() {
        return {
            selectItem: [],
            queryConditions: {
                orderName: '',
                collectTime: '',
                dataType: '',
                organization: '',
                collectType: ''
            },
            routeList: [],
            isLoading: false, // 新增 loading 状态
            dataTypeOptions: [],
            collectTypeOptions: [],
            regionSelect: [],
            pageSize: 10,
            total: 5,
            projects: [],
            currentPage: 1,
            baseUrl: process.env.VUE_APP_API_URL,
            dialogVisible: false,
            form: {
                orderName: '',
                dataType: '',
                organization: '',
                collectType: '',
                collectTime: '',
                county: '',
                route: ''
            },
            selectedFile: null, // 选中的文件
            regionZw: '',
            rules: {
                orderName: [
                    { required: true, message: '请输入订单名称', trigger: 'change' },
                    { min: 1, max: 80, message: '长度在 1 到 80 个字符', trigger: 'change' }
                ],
                dataType: [
                    { required: true, message: '请选择数据类型', trigger: 'change' },
                    { min: 1, max: 50, message: '长度在 1 到 50 个字符', trigger: 'change' }
                ],
                route: [{ required: true, message: '请选择航线', trigger: 'change' }],
                organization: [{ required: true, message: '请输入所属单位', trigger: 'change' }],
                collectType: [{ required: true, message: '请选择采集方式', trigger: 'change' }],
                collectTime: [{ required: true, message: '请选择采集时间', trigger: 'change' }],
                county: [{ required: true, message: '请选择行政区', trigger: 'change' }]
            },
            dataTypeIsAerialPhoto: false,
            collectionIdList: {},
            tiffInfos: [],
            organizationOptions: [],
            filterCountyData: [],
            countyList: []
        };
    },
    watch: {
        'form.dataType'(val) {
            if (val === '3') {
                //说明选择的是航片
                this.dataTypeIsAerialPhoto = true;
                //筛选数据
            } else {
                this.dataTypeIsAerialPhoto = false;
            }
        }
    },
    methods: {
        async getRouteData() {
            const para = {
                pageIndex: 1,
                pageSize: 100,
                routeType: '航线规划,人工选点',
                orderType: 1,
                orderField: 'createDate'
            };
            const res = await getRouteListApi(para);
            if (res.code === 0) {
                this.routeList = res.data;
            }
        },
        //重置筛选
        resetQuery() {
            this.queryConditions = { ...this.$options.data().queryConditions }; //ES6 重置查询条件
            this.getTableData();
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
        async getDictData() {
            const multDataDictRes = await getMultDataDictApi();
            if (multDataDictRes.code === 0) {
                const multDataDictData = multDataDictRes.data;
                if (multDataDictData.organization) {
                    this.organizationOptions = multDataDictData.organization;
                } else {
                    this.organizationOptions = [];
                }
            }
            const dictDataResponse = await getEnumOptionApi('multivariateType');
            if (dictDataResponse.code === 0) {
                dictDataResponse.data.multivariateType.map((item) => {
                    this.dataTypeOptions.push({ label: item.name, value: item.value });
                });
            }
            const dictDataResponse2 = await getEnumOptionApi('collectType');
            if (dictDataResponse2.code === 0) {
                dictDataResponse2.data.collectType.map((item) => {
                    this.collectTypeOptions.push({ label: item.name, value: item.value });
                });
            }
        },
        //获取表格数据
        async getTableData() {
            const para = {
                pageSize: this.pageSize,
                pageIndex: this.currentPage,
                startDate: this.queryConditions.collectTime ? this.queryConditions.collectTime[0] : '',
                endDate: this.queryConditions.collectTime ? this.queryConditions.collectTime[1] : '',
                orderName: this.queryConditions.orderName,
                dataType: this.queryConditions.dataType,
                organization: this.queryConditions.organization,
                collectType: this.queryConditions.collectType
            };
            const res = await getOrderListApi(para);
            if (res.code === 0) {
                this.projects = res.data;
                this.total = res.total;
            } else {
                this.$message.error(res.msg);
            }
        },
        //处理跳转
        handleView(row) {
            this.$message.warning('正在紧急开发中，敬请期待');
        },
        handleDeleteView(row) {
            // if(row.id){
            //     this.selectItem.push(row.id);
            // } 已经加入了变化监听事件了，不需要在额外push
            if (this.selectItem.length !== 0) {
                this.$confirm('确认删除该数据吗？', '提示', {
                    type: 'warning',
                    confirmButtonText: '确定',
                    cancelButtonText: '取消'
                })
                    .then(async () => {
                        try {
                            const params = {
                                ids: this.selectItem
                            };
                            const res = await deleteMultDataApi(params);
                            if (res.code === 0) {
                                this.$message.success('删除成功');
                                this.getTableData();
                                this.selectItem = [];
                            } else {
                                this.$message.error(res.msg);
                            }
                        } catch (error) {
                            // 处理错误，例如显示错误消息
                            this.$message.error('删除失败', res.msg);
                            this.selectItem = [];
                        }
                    })
                    .catch((error) => {
                        this.$message({
                            type: 'info',
                            message: '已取消删除'
                        });
                    });
            } else {
                this.$message.warning('请选择要删除的数据！');
            }
        },
        //获取选中的值
        handleSelectionChange(val) {
            this.selectItem = val.map((item) => item.id);
        },
        handleAddOrder() {
            this.dialogVisible = true;
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
        async submitForm() {
            const res = await postOrderInfoApi(this.form);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.dialogVisible = false;
                this.getTableData();
                this.resetForm();
                this.isLoading = false; // 结束loading加载
            } else {
                this.$message.error(res.msg);
                this.isLoading = false; // 结束加载
            }
        },
        resetForm() {
            this.$refs.form.resetFields(); // 重置表单验证状态和字段值
        },
        // 行政区筛选
        filterCounty(value) {
            if (value == '') {
                this.$message.warning('行政区检索条件不能为空！', 3);
                this.filterCountyData = [];
            } else {
                let reg = new RegExp(value);
                let arr = [];
                for (let i = 0; i < this.countyList.length; i++) {
                    if (reg.test(this.countyList[i].value)) {
                        arr.push(this.countyList[i]);
                    }
                }
                this.filterCountyData = arr;
            }
        },
        //获取区域的级联数据
        async getRegionOptions() {
            const res = await getRegionInfoListApi();
            this.countyList = res.data;
        }
    },
    computed: {},
    mounted() {
        this.getRegionOptions();
        this.getDictData();
        this.getRouteData();
        this.getTableData();
    },
    created() {}
};
</script>

<style lang="scss" scoped>
.upload-data {
    margin-left: 10px;
    padding-top: 16px;
    padding-bottom: 6px;
    border-top: 1px solid #0a579e;
}

.title {
    margin-left: 8px;
}

table {
    width: 100%;
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
    border-top: 1px solid #fff;
}

.t-query {
    height: 72px;
    display: flex;
    flex-direction: row;
    align-items: center;
    margin-bottom: 16px;
}
::v-deep.el-dialog {
    min-width: 420px;
}
.t-query div {
    display: flex;
}

.t-query-items {
    width: calc(100% - 245px);
    margin-top: 10px;
    margin-right: 16px;
}

.t-query-button {
    width: 245px;
    margin-top: 10px;
}

.el-button {
    margin-right: 2px; /* 给按钮之间添加一些间隔 */
}

.upload-demo ::v-deep(.el-upload),
.upload-demo ::v-deep(.el-upload .el-upload-dragger) {
    width: 100% !important;
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
    height: calc(100% - 240px);
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

.el-cascader--small {
    font-size: 13px;
    line-height: 32px;
    width: 100%;
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

.idemonstration {
    min-width: 88px;
    width: 100px;
    font-size: 14px;
    line-height: 16px;
    text-align: right;
    padding: 0 8px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}
.filterDateLabel {
    min-width: 40px;
    width: 60px;
    font-size: 14px;
    line-height: 16px;
    text-align: right;
    padding: 0 8px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
}
.icon {
    font-size: 24px;
    padding-right: 5px;
    background: linear-gradient(180deg, #ffffff 0%, #64d6ff 100%);
    -webkit-background-clip: text;
    color: transparent;
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

.left-content-body {
    padding-top: 17px;
}

.right-content-body {
    padding: 20px 10px 10px 10px;
    height: calc(100% - 40px);
}

.my-component .el-range-editor--small.el-input__inner {
    height: 32px;
    color: black;
}

::v-deep .el-select {
    display: inline-block;
    position: relative;
    width: 100%;
}

.form-dialog ::v-deep .custom-input .el-input__inner {
    color: black !important;
}

::v-deep .el-date-editor.el-input {
    width: 100%;
}
.filterDate {
    min-width: 120px;
}
.selectData {
    min-width: 100px;
}
</style>
