<template>
    <div class="model-info">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">模型管理</span>
        </div>
        <div class="gt-breadcrumb-cnt">
            <el-row :gutter="20" class="add">
                <el-col :span="7">
                    <!-- 搜索与添加区域 -->
                    <el-input placeholder="请输入模型名称" clearable v-model="queryInfo.name" @clear="getModelList">
                        <el-button slot="append" icon="el-icon-search" @click="getModelList"></el-button>
                    </el-input>
                </el-col>
                <el-col :span="4">
                    <!-- 添加模型区域 -->
                    <el-button type="primary" @click="addDialogVisible = true"><i class="iconfont icon-tianjia"></i>新增模型 </el-button>
                </el-col>
            </el-row>
            <!--模型列表 -->
            <el-table :data="modelList" height="70%" stripe style="width: 100%" border>
                <el-table-column type="index" label="编号" align="center" width="60"></el-table-column>
                <el-table-column prop="name" label="模型名称" align="center"></el-table-column>
                <el-table-column prop="framework" label="模型框架" align="center"></el-table-column>
                <el-table-column prop="type" label="模型类型" align="center"></el-table-column>
                <el-table-column prop="labelRels" label="模型标签" align="center">
                    <template slot-scope="scope">
                        <div v-if="scope.row.labelRels && scope.row.labelRels.length">
                            <el-tooltip placement="top">
                                <div slot="content">
                                    <div v-for="label in scope.row.labelRels" :key="label.id">{{ label.labelName }} ({{ label.labelValue }})</div>
                                </div>
                                <div>
                                    <span v-for="(label, index) in scope.row.labelRels.slice(0, 4)" :key="label.id" class="tag-item">
                                        {{ label.labelName }}
                                    </span>
                                    <span v-if="scope.row.labelRels.length > 4" class="tag-item"> +{{ scope.row.labelRels.length - 4 }} </span>
                                </div>
                            </el-tooltip>
                        </div>
                        <div v-else class="no-tags">无标签</div>
                    </template>
                </el-table-column>
                <el-table-column prop="network" label="模型网络" align="center" width="150"></el-table-column>
                <el-table-column prop="epoch" label="迭代次数" align="center" width="100"></el-table-column>
                <el-table-column label="操作" align="center">
                    <template v-slot="scope">
                        <!-- 修改按钮 -->
                        <el-button type="primary" icon="el-icon-edit" size="medium" @click="showEditDialog(scope.row)"></el-button>
                        <!-- 删除按钮 -->
                        <el-button type="danger" icon="el-icon-delete" size="medium" @click="removeModelData(scope.row.id)"></el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
                @current-change="handleCurrentChange"
                :current-page="queryInfo.pageIndex"
                @size-change="handleSizeChange"
                :page-size="queryInfo.pageSize"
                :page-sizes="[5, 10, 15, 20]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="total">
            </el-pagination>

            <!-- 添加模型对话框 -->
            <el-dialog
                title="添加模型"
                :visible.sync="addDialogVisible"
                width="50%"
                custom-class="rc-light-dialog"
                @close="addDislogClosed"
                :modal-append-to-body="false">
                <!-- 内容主题区域 -->
                <el-form label-width="100px" ref="addFormRef" :model="addForm">
                    <el-form-item label="模型名称" prop="name" placeholder="请选择模型名称">
                        <el-input v-model="addForm.name"></el-input>
                    </el-form-item>
                    <el-form-item label="模型框架" prop="framework" placeholder="请选择模型框架">
                        <el-select v-model="addForm.framework" style="width: 100%">
                            <el-option v-for="item in frameworkList" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="模型网络" prop="network" placeholder="请选择模型网络">
                        <el-select v-model="addForm.network" style="width: 100%">
                            <el-option v-for="item in networkList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="模型类型" prop="type">
                        <el-select v-model="addForm.type" style="width: 100%" placeholder="请选择模型类型">
                            <el-option v-for="item in modelTypeList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="迭代次数" prop="epoch">
                        <el-input v-model="addForm.epoch" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="标签类别:" prop="labels">
                        <el-select v-model="addForm.labelRels" placeholder="请选择标签类别" multiple clearable style="width: 100%">
                            <el-option v-for="item in labelList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="排序号" prop="orderIndex">
                        <el-input v-model="addForm.orderIndex" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="模型描述" prop="note" placeholder="请选择模型描述">
                        <el-input v-model="addForm.note" type="textarea"></el-input>
                    </el-form-item>
                </el-form>
                <!-- 底部按钮区域 -->
                <span slot="footer" class="dialog-footer">
                    <el-button @click="addDialogVisible = false">取 消</el-button>
                    <el-button type="primary" @click="addModel">确 定</el-button>
                </span>
            </el-dialog>
            <!-- 修改模型信息对话框 -->
            <el-dialog
                title="修改模型"
                @close="editClosed"
                :visible.sync="editDialogVisble"
                width="50%"
                custom-class="rc-light-dialog"
                :modal-append-to-body="false">
                <el-form :model="editForm" ref="editFormRef" label-width="70px">
                    <el-form-item label="模型ID">
                        <el-input v-model="editForm.id" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="模型名称">
                        <el-input v-model="editForm.name"></el-input>
                    </el-form-item>
                    <el-form-item label="模型框架" prop="framework" placeholder="请选择模型框架">
                        <el-select v-model="editForm.framework" style="width: 100%">
                            <el-option v-for="item in frameworkList" :key="item" :label="item" :value="item"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="模型网络" prop="network">
                        <el-select v-model="editForm.network" style="width: 100%" placeholder="请选择模型类别">
                            <el-option v-for="item in networkList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="模型类型" prop="type">
                        <el-select v-model="editForm.type" style="width: 100%" placeholder="请选择模型类型">
                            <el-option v-for="item in modelTypeList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="迭代次数" prop="epoch">
                        <el-input v-model="editForm.epoch" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="标签类别:" prop="labels">
                        <el-select v-model="editForm.labelRels" placeholder="请选择标签类别" multiple clearable style="width: 100%">
                            <el-option v-for="item in labelList" :key="item.value" :label="item.name" :value="item.value"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="排序号" prop="orderIndex">
                        <el-input v-model="editForm.orderIndex" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="模型描述" prop="note">
                        <el-input v-model="editForm.note" type="textarea"></el-input>
                    </el-form-item>
                </el-form>
                <span slot="footer" class="dialog-footer">
                    <el-button @click="editDialogVisble = false">取 消</el-button>
                    <el-button type="primary" @click="editModelInfo">确 定</el-button>
                </span>
            </el-dialog>
        </div>
    </div>
</template>

<script>
import { deleteModelInfoApi, getEnumOptionApi, getModelListApi, postModelInfoApi, updateModelInfoApi } from '@/api/commonApi';

export default {
    name: 'modelInfo',
    data() {
        return {
            // 获取模型列表的参数对象
            queryInfo: {
                // 搜索值
                name: '',
                // 当前的页数
                pageIndex: 1,
                // 当前每次显示多少条数据
                pageSize: 10
            },
            modelList: [],
            networkList: [],
            modelTypeList: [],
            frameworkList: ['tensorflow', 'pyTorch', 'caffe', 'paddlepaddle'],
            total: 0,
            filterCountyData: [],
            countyList: [],
            // 添加模型数据的对象
            addForm: {
                name: '',
                framework: '',
                epoch: '',
                orderIndex: '',
                note: '',
                network: '',
                labelRels: [],
                status: 1,
                type: '',
                versionCode: 'V3.0'
            },
            // 修改模型消息对话框显示和隐藏
            editDialogVisble: false,
            // 控制分配角色对话框的显示和隐藏
            setRolesDialogVisible: false,
            // 控制模型对话框的显示和隐藏
            addDialogVisible: false,
            labelList: [],
            // 查询模型的对象
            editForm: {
                name: '',
                framework: '',
                network: '',
                epoch: '',
                id: '',
                orderIndex: '',
                note: '',
                status: 1,
                type: '',
                versionCode: 'V3.0',
                labelRels: []
            }
        };
    },
    components: {},
    created() {},
    mounted() {
        this.getModelList();
        this.initLabels();
        //this.constructTreeSelect(country_dict);
    },
    methods: {
        async initLabels() {
            const res = await getEnumOptionApi('scene_labels');
            if (res.code === 0) {
                this.labelList = res.data.scene_labels;
            }
            const res1 = await getEnumOptionApi('model_network');
            if (res1.code === 0) {
                this.networkList = res1.data.model_network;
            }
            const res2 = await getEnumOptionApi('model_type');
            if (res2.code === 0) {
                this.modelTypeList = res2.data.model_type;
            }
        },

        // 行政区检索字典表
        constructTreeSelect(obj) {
            for (let key in obj) {
                // 构建对象
                let city_name = obj[key].name ? obj[key].name : obj[key];
                this.countyList.push({ key: key, value: city_name });
                // 含有child递归遍历
                if (obj[key].hasOwnProperty('child')) {
                    this.constructTreeSelect(obj[key].child);
                }
            }
        },
        // 行政区筛选
        filterCounty(value) {
            if (value === '') {
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
        async getModelList() {
            const res = await getModelListApi(this.queryInfo);
            if (res.code === 0) {
                this.modelList = res.data;
                this.total = res.total;
            }
        },
        // 监听 limit 改变事件 每页显示的个数
        handleSizeChange(newSize) {
            this.queryInfo.pageSize = newSize;
            this.getModelList();
        },
        // 监听 页码值 改变的事件 当前页面值
        handleCurrentChange(newPage) {
            this.queryInfo.pageIndex = newPage;
            this.getModelList();
        },
        // 监听添加模型的对话框关闭事件
        addDislogClosed() {
            this.$refs.addFormRef.resetFields();
        },
        // 点击按钮,添加模型
        addModel() {
            this.$refs.addFormRef.validate(async (valid) => {
                if (!valid) return;
                const labelRels = [];
                const than = this;
                // 将选中的ID数组转换为对象数组
                this.addForm.labelRels.forEach(function (value) {
                    var label = than.labelList.find(function (item) {
                        return item.value === value;
                    });

                    if (label) {
                        labelRels.push({
                            labelValue: label.value,
                            labelName: label.name
                        });
                    }
                });
                const params = {
                    name: this.addForm.name,
                    framework: this.addForm.framework,
                    epoch: this.addForm.epoch,
                    orderIndex: this.addForm.orderIndex,
                    note: this.addForm.note,
                    network: this.addForm.network,
                    labelRels: labelRels,
                    status: 1,
                    type: this.addForm.type,
                    versionCode: 'V3.0'
                };
                const res = await postModelInfoApi(params);
                if (res.code === 0) {
                    // 隐藏添加模型的对话框
                    this.addDialogVisible = false;
                    // 添加成后重新获取模型数据,不需要用户手动刷新
                    this.getModelList();
                    // 成功
                    this.$message.success('新增成功！');
                } else {
                    try {
                        this.$message.warning(JSON.parse(res.msg).message);
                    } catch {
                        this.$message.warning(res.msg);
                    }
                }
            });
        },
        // 展示编辑模型的对话框
        async showEditDialog(data) {
            const currentRowData = JSON.parse(JSON.stringify(data));
            const network = this.networkList.find(function (item) {
                return item.name === currentRowData.network;
            });
            const modelType = this.modelTypeList.find(function (item) {
                return item.name === currentRowData.type;
            });
            this.editForm.name = currentRowData.name;
            this.editForm.framework = currentRowData.framework;
            this.editForm.epoch = currentRowData.epoch;
            this.editForm.id = currentRowData.id;
            this.editForm.orderIndex = currentRowData.orderIndex;
            this.editForm.network = network.value;
            this.editForm.type = modelType.value;
            if (data.labelRels) {
                this.editForm.labelRels = data.labelRels.map((item) => item.labelValue) || [];
            }

            this.editDialogVisble = true;
        },
        // 监听修改模型对话框的关闭事件
        editClosed() {
            this.$refs.editFormRef.resetFields();
        },
        editModelInfo() {
            this.$refs.editFormRef.validate(async (valid) => {
                if (!valid) return;
                const labelRels = [];
                const than = this;
                // 将选中的ID数组转换为对象数组
                this.editForm.labelRels.forEach(function (value) {
                    var label = than.labelList.find(function (item) {
                        return item.value === value;
                    });

                    if (label) {
                        labelRels.push({
                            labelValue: label.value,
                            labelName: label.name
                        });
                    }
                });
                const params = {
                    name: this.editForm.name,
                    framework: this.editForm.framework,
                    network: this.editForm.network,
                    epoch: this.editForm.epoch,
                    id: this.editForm.id,
                    orderIndex: this.editForm.orderIndex,
                    note: this.editForm.note,
                    status: 1,
                    type: this.editForm.type,
                    versionCode: 'V3.0',
                    labelRels: labelRels
                };
                const res = await updateModelInfoApi(params);
                if (res.code === 0) {
                    this.editDialogVisble = false;
                    this.getModelList();
                    this.$message.success(res.msg);
                } else {
                    this.$message.warning(res.msg);
                }
            });
        },
        // 根据id删除对应的模型信息
        async removeModelData(id) {
            const confirmRusult = await this.$confirm('此操作将永久删除该模型, 是否继续?', '永久删除该模型', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).catch((err) => err);
            if (confirmRusult !== 'confirm') {
                return this.$message.info('已经取消了删除');
            }
            const params = [id];
            const res = await deleteModelInfoApi(params);
            if (res.code === 0) {
                this.$message.success('删除成功');
                this.getModelList();
            } else {
                this.$message.warning('删除失败');
            }
        }
    }
};
</script>

<style scoped>
* {
    font-size: 14px;
}

/*  组件布局*/
.model-info {
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
    background-color: #fff;
    z-index: 9999;
    box-sizing: border-box;
    border-left: 1px solid #dcdcdc;
}

.gt-breadcrumb-box .icon-geoai-manage {
    font-size: 20px;
    color: rgb(43, 179, 244);
    margin-right: 6px;
}

.gt-current-position {
    margin-left: 5px;
    font-size: 18px;
    line-height: 40px;
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
    position: relative;
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

::v-deep .el-input__inner {
    color: #606266;
}
</style>
