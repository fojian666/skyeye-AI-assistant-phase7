<template>
    <div class="menu-management">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">机巢设置</span>
        </div>
        <div class="gt-breadcrumb-cnt">
            <el-row :gutter="20" class="add">
                <el-col :span="7">
                    <el-input v-model="queryInfo.name" clearable placeholder="请输入机巢名称" @keyup.enter.native=""> </el-input>
                </el-col>
                <el-col :span="12">
                    <el-button type="primary" @click="getTableData">查询</el-button>
                    <el-button type="primary" @click="dialogVisible = true">新增</el-button>
                    <el-button type="success" @click="importDialogVisible = true">批量导入</el-button>
                    <el-button type="danger" @click="deleteTableData">删除</el-button>
                </el-col>
            </el-row>
            <!-- 用户列表 -->
            <el-table
                :data="tableData"
                stripe
                height="80%"
                style="width: 100%; overflow: hidden"
                border
                row-key="id"
                @selection-change="handleSelectionChange">
                <el-table-column type="selection" width="55"> </el-table-column>
                <el-table-column prop="name" label="机巢名称" align="center"></el-table-column>
                <el-table-column prop="model" label="机巢型号" align="center"> </el-table-column>
                <el-table-column prop="nestSn" label="机巢SN" align="center"></el-table-column>
                <el-table-column prop="planeModel" label="飞机型号" align="center"></el-table-column>
                <el-table-column prop="planeSn" label="飞机SN" align="center"> </el-table-column>
                <el-table-column prop="location" label="机巢位置" align="center"></el-table-column>
                <el-table-column prop="organization" label="所属单位" align="center"></el-table-column>
                <el-table-column prop="createDate" label="注册时间" align="center"></el-table-column>
                <el-table-column prop="status" label="飞机状态" align="center"></el-table-column>
                <el-table-column label="操作" align="center" width="240" fixed="right">
                    <template v-slot="scope">
                        <el-button type="primary" size="mini" @click="handeEdit(scope.row)">编辑</el-button>
                        <el-button type="danger" size="mini" @click="deleteSoloData(scope.row.id)">删除 </el-button>
                    </template>
                </el-table-column>
            </el-table>
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
        <el-dialog title="新增机巢" :visible.sync="dialogVisible" width="30%" custom-class="rc-light-dialog" left>
            <el-form ref="form" :model="form" :rules="rules" label-width="80px">
                <el-form-item label="机巢名称" prop="name">
                    <el-input v-model="form.name"></el-input>
                </el-form-item>
                <el-form-item label="机巢型号" prop="model">
                    <el-autocomplete v-model="form.model" :fetch-suggestions="querySearchAsync" placeholder="请输入内容"></el-autocomplete>
                </el-form-item>
                <el-form-item label="机巢 SN" prop="nestSn">
                    <el-input v-model="form.nestSn"></el-input>
                </el-form-item>
                <el-form-item label="飞机型号" prop="planeModel">
                    <el-autocomplete
                        v-model="form.planeModel"
                        :fetch-suggestions="querySearchPlaneModelsAsync"
                        placeholder="请输入内容"></el-autocomplete>
                </el-form-item>
                <el-form-item label="飞机 SN" prop="planeSn">
                    <el-input v-model="form.planeSn"></el-input>
                </el-form-item>
                <el-form-item label="机巢位置" prop="locatiogetn">
                    <el-cascader
                        :options="regionOptions"
                        v-model="form.location"
                        @change="handleRegionChange"
                        clearable
                        :change-on-select="true"></el-cascader>
                </el-form-item>
                <el-form-item label="所属单位" prop="organization">
                    <el-autocomplete
                        v-model="form.organization"
                        :fetch-suggestions="querySearchOrganizationAsync"
                        placeholder="请选择或输入所属单位"></el-autocomplete>
                </el-form-item>
                <el-form-item label="机巢经度" prop="longitude">
                    <el-input v-model="form.longitude"></el-input>
                </el-form-item>
                <el-form-item label="机巢维度" prop="latitude">
                    <el-input v-model="form.latitude"></el-input>
                </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
                <el-button @click="reset">重置</el-button>
                <el-button type="primary" @click="submitForm('form')">确 定</el-button>
            </span>
        </el-dialog>
        <el-dialog title="批量导入机巢" :visible.sync="importDialogVisible" width="480px" custom-class="rc-light-dialog" @close="resetImportForm">
            <div class="import-tips">
                <p>请按模板填写后上传 Excel（.xls / .xlsx），表头需与模板一致。</p>
                <el-button type="text" icon="el-icon-download" @click="downloadImportTemplate">下载导入模板</el-button>
            </div>
            <el-form label-width="90px">
                <el-form-item label="导入文件">
                    <el-input v-model="importFileName" placeholder="请选择 Excel 文件" readonly>
                        <template slot="append">
                            <el-button icon="el-icon-folder-opened" @click="triggerImportFileSelect"></el-button>
                            <input
                                ref="importFileInput"
                                type="file"
                                accept=".xls,.xlsx,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                style="display: none"
                                @change="handleImportFileChange" />
                        </template>
                    </el-input>
                </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
                <el-button @click="importDialogVisible = false">取 消</el-button>
                <el-button type="primary" :loading="importLoading" @click="submitImportExcel">开始导入</el-button>
            </span>
        </el-dialog>
        <el-dialog title="修改机巢" :visible.sync="editDialogVisible" width="30%" custom-class="rc-light-dialog" left :modal-append-to-body="false">
            <el-form ref="editForm" :model="editForm" label-width="80px">
                <el-form-item label="机巢名称">
                    <el-input v-model="editForm.name"></el-input>
                </el-form-item>
                <el-form-item label="机巢型号">
                    <el-autocomplete v-model="editForm.model" :fetch-suggestions="querySearchAsync" placeholder="请输入内容"></el-autocomplete>
                </el-form-item>
                <el-form-item label="机巢 SN">
                    <el-input v-model="editForm.nestSn"></el-input>
                </el-form-item>
                <el-form-item label="飞机型号">
                    <el-autocomplete
                        v-model="editForm.planeModel"
                        :fetch-suggestions="querySearchPlaneModelsAsync"
                        placeholder="请输入内容"></el-autocomplete>
                </el-form-item>
                <el-form-item label="飞机 SN">
                    <el-input v-model="editForm.planeSn"></el-input>
                </el-form-item>
                <el-form-item label="机巢位置">
                    <el-cascader
                        :options="regionOptions"
                        v-model="editForm.location"
                        @change="handleRegionChange"
                        clearable
                        :change-on-select="true"></el-cascader>
                </el-form-item>
                <el-form-item label="所属单位">
                    <el-autocomplete
                        v-model="editForm.organization"
                        :fetch-suggestions="querySearchOrganizationAsync"
                        placeholder="请选择或输入所属单位"></el-autocomplete>
                </el-form-item>
                <el-form-item label="机巢经度">
                    <el-input v-model="editForm.longitude"></el-input>
                </el-form-item>
                <el-form-item label="机巢维度">
                    <el-input v-model="editForm.latitude"></el-input>
                </el-form-item>
            </el-form>
            <span slot="footer" class="dialog-footer">
                <el-button type="primary" @click="submitEditForm('editForm')">修改</el-button>
            </span>
        </el-dialog>
    </div>
</template>

<script>
import {
    addNestApi,
    deleteTableDataApi,
    getNestInfoApi,
    getNestTableApi,
    getRegionOptions,
    importNestExcelApi,
    modifyNestInfoApi
} from '@/api/commonApi';

export default {
    name: 'MenuManagement',
    components: {},
    data() {
        return {
            // 获取用户列表的参数对象
            queryInfo: {
                // 搜索值
                name: ''
            },
            tableData: [],
            defaultExpandAll: true,
            multipleSelection: [],
            dialogVisible: false,
            form: {
                name: '',
                model: '',
                nestSn: '',
                planeModel: '',
                planeSn: '',
                location: '',
                organization: '',
                longitude: '',
                latitude: ''
            },
            nestModelsOptions: [],
            organizationListOptions: [],
            planeModelsOptions: [],
            rules: {
                name: [{ required: true, message: '请输入机巢名称', trigger: 'blur' }],
                model: [{ required: true, message: '请选择或输入机巢型号', trigger: 'change' }],
                nestSn: [{ required: true, message: '请输入机巢SN', trigger: 'blur' }],
                planeModel: [{ required: true, message: '请选择或输入飞机型号', trigger: 'change' }],
                planeSn: [{ required: true, message: '请输入飞机SN', trigger: 'blur' }],
                location: [{ required: true, message: '请选择机巢位置', trigger: 'blur' }],
                organization: [{ required: true, message: '请选择或输入所属单位', trigger: 'blur' }],
                longitude: [{ required: true, message: '请输入经度', trigger: 'blur' }],
                latitude: [{ required: true, message: '请输入纬度', trigger: 'blur' }]
            },
            pageSize: 10,
            total: 5,
            currentPage: 1,
            regionZw: [],
            editForm: {
                name: '',
                model: '',
                nestSn: '',
                planeModel: '',
                planeSn: '',
                location: '',
                organization: '',
                longitude: '',
                latitude: ''
            },
            editDialogVisible: false,
            regionOptions: {},
            importDialogVisible: false,
            importFileName: '',
            importFile: null,
            importLoading: false
        };
    },
    created() {},
    methods: {
        handleSelectionChange(val) {
            // this.multipleSelection = val;
            this.multipleSelection = val.map((item) => item.id);
        },
        querySearchAsync(queryString, cb) {
            var restaurants = this.nestModelsOptions;
            var results = queryString ? restaurants.filter(this.createStateFilter(queryString)) : restaurants;
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => {
                cb(results);
            }, 1000 * Math.random());
        },
        querySearchPlaneModelsAsync(queryString, cb) {
            var restaurants = this.planeModelsOptions;
            var results = queryString ? restaurants.filter(this.createStateFilter(queryString)) : restaurants;
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => {
                cb(results);
            }, 1000 * Math.random());
        },
        querySearchOrganizationAsync(queryString, cb) {
            var restaurants = this.organizationListOptions;
            var results = queryString ? restaurants.filter(this.createStateFilter(queryString)) : restaurants;
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => {
                cb(results);
            }, 1000 * Math.random());
        },

        createStateFilter(queryString) {
            return (state) => {
                return state.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0;
            };
        },
        async getRegionoptions() {
            const res = await getRegionOptions();
            this.regionOptions = res.data;
        },
        async getNestInfo() {
            getNestInfoApi().then((res) => {
                if (res.code === 0) {
                    this.nestModelsOptions = res.data.nest_models;
                    this.organizationListOptions = res.data.organization_list;
                    this.planeModelsOptions = res.data.plane_models;
                } else {
                    this.$message.error(res.msg);
                }
            });
        },
        async submitForm(formName) {
            this.$refs[formName].validate((valid) => {
                if (this.regionZw && this.regionZw.length) {
                    this.form.location = this.regionZw.join('');
                }
                const para = {
                    ...this.form
                };
                addNestApi(this.form).then((res) => {
                    if (res.code === 0) {
                        this.dialogVisible = false;
                        this.getTableData();
                    } else {
                        this.$message.error(res.msg);
                    }
                });
            });
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
            this.regionZw = selectedLabels;
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
        async getTableData() {
            const para = {
                name: this.queryInfo.name,
                page: this.currentPage,
                limit: this.pageSize
            };
            const res = await getNestTableApi(para);
            if (res.code === 0) {
                this.tableData = res.data;
                this.total = res.total;
            } else {
                this.$message.error(res.msg);
            }
        },
        reset() {
            this.$refs['form'].resetFields();
        },
        deleteTableData() {
            deleteTableDataApi({ nestIds: this.multipleSelection }).then((res) => {
                if (res.code === 0) {
                    this.getTableData();
                } else {
                    this.$message.error(res.msg);
                }
            });
        },
        deleteSoloData(id) {
            this.$confirm('此操作将永久删除该文件, 是否继续?', '提示', {
                type: 'warning'
            })
                .then(() => {
                    deleteTableDataApi({ nestIds: [id] }).then((res) => {
                        if (res.code === 0) {
                            this.$message.success(res.msg);
                            this.getTableData();
                        } else {
                            this.$message.error(res.msg);
                        }
                    });
                })
                .catch(() => {
                    this.$message('删除失败');
                });
        },
        handeEdit(row) {
            this.editForm = JSON.parse(JSON.stringify(row)); //可以防止表格数据被双向更改
            this.editDialogVisible = true;
        },
        async handleView() {
            this.$message.info('该功能暂未开放');
        },
        handleStop() {
            this.$message.info('该功能暂未开放');
        },
        //修改机巢信息
        submitEditForm(formName) {
            if (this.regionZw.length !== 0) {
                this.editForm.location = this.regionZw.join('');
            }
            modifyNestInfoApi(this.editForm).then((res) => {
                if (res.code === 0) {
                    this.editDialogVisible = false;
                    this.getTableData();
                } else {
                    this.$message.error(res.msg);
                }
            });
        },
        async handleGetRegion() {
            const res = await getRegionOptions();
            if (res.code === 0) {
                this.regionOptions = res.data;
            } else {
                this.$message.error(res.msg);
            }
        },
        downloadImportTemplate() {
            const headers = ['机巢名称', '机巢型号', '机巢SN', '飞机型号', '飞机SN', '机巢位置', '所属单位', '机巢经度', '机巢纬度'];
            const example = [
                '示例机巢01',
                '大疆机场2',
                'NEST-SN-001',
                'M300 RTK',
                'PLANE-SN-001',
                '广东省深圳市南山区',
                '示例单位',
                '113.930000',
                '22.530000'
            ];
            const csvContent = '\uFEFF' + [headers.join(','), example.join(',')].join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = '机巢导入模板.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        },
        triggerImportFileSelect() {
            this.$refs.importFileInput.click();
        },
        handleImportFileChange(event) {
            const file = event.target.files[0];
            if (!file) {
                return;
            }
            const fileName = file.name.toLowerCase();
            if (!fileName.endsWith('.xls') && !fileName.endsWith('.xlsx')) {
                this.$message.error('仅支持 .xls 或 .xlsx 格式文件');
                event.target.value = '';
                return;
            }
            this.importFile = file;
            this.importFileName = file.name;
        },
        resetImportForm() {
            this.importFileName = '';
            this.importFile = null;
            this.importLoading = false;
            if (this.$refs.importFileInput) {
                this.$refs.importFileInput.value = '';
            }
        },
        //导入excel数据
        async submitImportExcel() {
            if (!this.importFile) {
                this.$message.warning('请先选择 Excel 文件');
                return;
            }
            const formData = new FormData();
            formData.append('file', this.importFile);
            this.importLoading = true;
            try {
                const res = await importNestExcelApi(formData);
                if (res.code === 0) {
                    this.$message.success(res.msg || '导入成功');
                    this.importDialogVisible = false;
                    this.resetImportForm();
                    this.currentPage = 1;
                    await this.getTableData();
                } else {
                    this.$message.error(res.msg || '导入失败');
                }
            } catch (e) {
                this.$message.error('导入失败，请稍后重试');
            } finally {
                this.importLoading = false;
            }
        }
    },

    mounted() {
        // this.getRegionoptions()
        this.handleGetRegion();
        this.getNestInfo();
        this.getTableData();
    }
};
</script>

<style scoped lang="scss">
* {
    font-size: 14px;
}

/*  组件布局*/
.menu-management {
    margin: 0;
    padding: 0;
    background-color: #edf0f7 !important;
    color: #333;
    font-size: 14px;
    line-height: 1.5;
}

/*  表头面包屑*/
.gt-breadcrumb-box {
    height: 40px;
    line-height: 40px;
    background-color: #fff;
    z-index: 9999;
    box-sizing: border-box;
    padding: 0 16px;
    border-left: 1px solid #dcdcdc;
}

.gt-breadcrumb-box .icon-geoai-manage {
    font-size: 20px;
    color: rgb(43, 179, 244);
}

.gt-current-position {
    margin-left: 5px;
    margin-right: 10px;
    font-size: 18px;
    font-weight: 700;
}

.gt-current-position span {
    margin: 0 10px;
    color: #999;
}

/*  内容*/
.gt-breadcrumb-cnt {
    margin-top: 8px;
    padding: 10px;
    height: calc(100% - 48px);
    width: 100%;
    background-color: #fff;
}

.el-table {
    margin-top: 15px;
}

.el-switch {
    height: 25px !important;
}

.box-card {
    height: 100%;
}

.el-card__body,
.el-main {
    padding: 20px;
    position: relative;
}

.el-pagination {
    position: absolute;
    bottom: 10px;
    right: 30px;
    margin-top: 30px;
    height: 6%;
}

::v-deep(.el-breadcrumb) {
    height: 40px;
    /*变成弹性盒模型*/
    display: flex;
    /*在中间*/
    align-items: center;
    margin-left: 10px;
    margin-bottom: 10px;
}

::v-deep(.el-switch__core) {
    width: 54px !important;
    height: 24px;
    border-radius: 100px;
    border: none;
}

::v-deep(.el-switch__core::after) {
    width: 20px;
    height: 20px;
    top: 2px;
}

::v-deep(.el-switch.is-checked .el-switch__core::after) {
    margin-left: -21px;
}

/*关闭时文字位置设置*/
::v-deep(.el-switch__label--right) {
    position: absolute;
    z-index: 1;
    right: 6px;
    margin-left: 0px;
    color: rgba(255, 255, 255, 0.9019607843137255);
}

span {
    font-size: 12px;
}

/* 激活时另一个文字消失 */
::v-deep(.el-switch__label.is-active) {
    display: none;
}

/*开启时文字位置设置*/
::v-deep(.el-switch__label--left) {
    position: absolute;
    z-index: 1;
    left: 5px;
    margin-right: 0px;
    color: rgba(255, 255, 255, 0.9019607843137255);
}

span {
    font-size: 12px;
}

.el-select {
    width: 100%;
}

::v-deep(.el-card__body) {
    padding-top: 8px;
    height: 100%;
}

.bread-crumb {
    height: 6%;
}

.add {
    height: 5%;
}

::v-deep .el-button--mini {
    padding: 4px 8px !important;
}

::v-deep .el-cascader {
    width: 100%;
}
::v-deep .el-autocomplete {
    position: relative;
    display: block;
}
.page {
    position: absolute; //绝对定位
    right: 20px;
    bottom: 40px;
}

.import-tips {
    margin-bottom: 12px;
    color: #666;
    line-height: 1.6;
}

.import-tips p {
    margin: 0 0 4px;
}
</style>
