<template>
    <div class="region-info">
        <!-- 面包屑导航 -->
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">区划管理</span>
        </div>

        <!-- 主体内容区 -->
        <div class="gt-breadcrumb-cnt">
            <!-- 搜索与新增区域 -->
            <el-form :inline="true" class="add">
                <el-form-item label-width="0">
                    <el-input placeholder="请输入区划名称/代码" clearable v-model="queryInfo.query" @clear="getRegionList" style="width: 260px">
                    </el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="handleSearchData">搜索</el-button>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="addDialogVisible = true"> <i class="iconfont icon-geoai-add-user"></i>新增区划 </el-button>
                </el-form-item>
            </el-form>
            <!-- 区划列表表格 -->
            <el-table :data="regionData.regionList" height="70%" stripe style="width: 100%" border>
                <el-table-column prop="region_id" label="区划ID" align="center" width="80"></el-table-column>
                <el-table-column prop="region_name" label="区划名称" align="center"></el-table-column>
                <el-table-column label="区划级别" align="center" width="100">
                    <template v-slot="scope">
                        {{ scope.row.region_level | levelFilter }}
                    </template>
                </el-table-column>
                <el-table-column prop="region_code" label="区划代码" align="center"></el-table-column>
                <el-table-column prop="parent_name" label="父级区划" align="center"></el-table-column>
                <el-table-column prop="longitude" label="经度" align="center" width="120"></el-table-column>
                <el-table-column prop="latitude" label="纬度" align="center" width="120"></el-table-column>
                <el-table-column prop="create_time" label="创建时间" align="center" width="180">
                    <template v-slot="scope">
                        {{ scope.row.create_time | dateFilter }}
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160px" align="center">
                    <template v-slot="scope">
                        <el-button type="primary" icon="el-icon-edit" size="mini" @click="showEditDialog(scope.row)"></el-button>
                        <el-button type="danger" icon="el-icon-delete" size="mini" @click="removeRegionById(scope.row.region_id)"></el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页控件 -->
            <el-pagination
                @current-change="handleCurrentChange"
                :current-page="queryInfo.page"
                @size-change="handleSizeChange"
                :page-size="queryInfo.limit"
                :page-sizes="[5, 10, 15, 20]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="regionData.total"></el-pagination>

            <!-- 新增区划对话框 -->
            <el-dialog title="新增区划" :visible.sync="addDialogVisible" width="50%" custom-class="rc-light-dialog" @close="addDialogClosed">
                <el-form label-width="120px" ref="addFormRef" :rules="rules" :model="addForm">
                    <el-form-item label="区划名称" prop="region_name">
                        <el-input v-model="addForm.region_name" placeholder="请输入区划名称"></el-input>
                    </el-form-item>
                    <el-form-item label="区划级别" prop="region_level">
                        <el-select v-model="addForm.region_level" placeholder="请选择区划级别" style="width: 100%" @change="filterParentRegion">
                            <el-option label="省" :value="2"></el-option>
                            <el-option label="市" :value="3"></el-option>
                            <el-option label="县" :value="4"></el-option>
                            <el-option label="街道" :value="5"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="区划代码" prop="region_code">
                        <el-input v-model="addForm.region_code" placeholder="请输入区划代码（如610000）"></el-input>
                    </el-form-item>
                    <el-form-item label="父级区划" prop="parent_id">
                        <el-select
                            v-model="addForm.parent_id"
                            placeholder="请选择父级区划（无父级则留空）"
                            filterable
                            style="width: 100%"
                            @change="getParentRegionInfo('add')">
                            <el-option
                                v-for="item in parentRegionList"
                                :key="item.region_id"
                                :label="item.region_name + '（' + item.region_code + '）'"
                                :value="item.region_id"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="经度" prop="longitude">
                        <el-input v-model="addForm.longitude" placeholder="请输入经度（如108.95）" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="纬度" prop="latitude">
                        <el-input v-model="addForm.latitude" placeholder="请输入纬度（如34.27）" type="number"></el-input>
                    </el-form-item>
                </el-form>
                <span slot="footer" class="dialog-footer">
                    <el-button @click="addDialogVisible = false">取 消</el-button>
                    <el-button type="primary" @click="addRegion">确 定</el-button>
                </span>
            </el-dialog>

            <!-- 编辑区划对话框 -->
            <el-dialog title="编辑区划" :visible.sync="editDialogVisible" width="50%" custom-class="rc-light-dialog" @close="editDialogClosed">
                <el-form label-width="120px" ref="editFormRef" :model="editForm">
                    <el-form-item label="区划ID">
                        <el-input v-model="editForm.region_id" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="区划名称" prop="region_name">
                        <el-input v-model="editForm.region_name" placeholder="请输入区划名称"></el-input>
                    </el-form-item>
                    <el-form-item label="区划级别" prop="region_level">
                        <el-select v-model="editForm.region_level" placeholder="请选择区划级别" style="width: 100%" @change="filterParentRegion">
                            <el-option label="省" :value="2"></el-option>
                            <el-option label="市" :value="3"></el-option>
                            <el-option label="县" :value="4"></el-option>
                            <el-option label="街道" :value="5"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="区划代码" prop="region_code">
                        <el-input v-model="editForm.region_code" placeholder="请输入区划代码（如610000）"></el-input>
                    </el-form-item>
                    <el-form-item label="父级区划" prop="parent_id">
                        <el-select
                            v-model="editForm.parent_id"
                            placeholder="请选择父级区划（无父级则留空）"
                            filterable
                            style="width: 100%"
                            @change="getParentRegionInfo('edit')">
                            <el-option
                                v-for="item in parentRegionList"
                                :key="item.region_id"
                                :label="item.region_name + '（' + item.region_code + '）'"
                                :value="item.region_id"></el-option>
                        </el-select>
                    </el-form-item>
                    <el-form-item label="经度" prop="longitude">
                        <el-input v-model="editForm.longitude" placeholder="请输入经度（如108.95）" type="number"></el-input>
                    </el-form-item>
                    <el-form-item label="纬度" prop="latitude">
                        <el-input v-model="editForm.latitude" placeholder="请输入纬度（如34.27）" type="number"></el-input>
                    </el-form-item>
                </el-form>
                <span slot="footer" class="dialog-footer">
                    <el-button @click="editDialogVisible = false">取 消</el-button>
                    <el-button type="primary" @click="editRegion">确 定</el-button>
                </span>
            </el-dialog>
        </div>
    </div>
</template>

<script>
import { getRegionListApi, addRegionApi, editRegionApi, deleteRegionApi, getParentRegionApi } from '@/api/commonApi';

export default {
    name: 'RegionManagement',
    filters: {
        levelFilter(level) {
            const levelMap = { 2: '省', 3: '市', 4: '区/县', 5: '镇/街道' };
            return levelMap[level] || '未知';
        },
        dateFilter(time) {
            if (!time) return '';
            return new Date(time)
                .toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                })
                .replace(/\//g, '-');
        }
    },
    data() {
        return {
            queryInfo: { query: '', page: 1, limit: 10 },
            levelMap: { 2: '省', 3: '市', 4: '区/县', 5: '镇/街道' },
            regionData: { regionList: [], total: 0 },
            parentRegionList: [],
            addForm: {
                region_name: '',
                region_level: '',
                region_code: '',
                parent_id: '',
                parent_name: '',
                parent_code: '',
                longitude: '',
                latitude: ''
            },
            editForm: {
                region_id: '',
                region_name: '',
                region_level: '',
                region_code: '',
                parent_id: '',
                parent_name: '',
                parent_code: '',
                longitude: '',
                latitude: ''
            },
            addDialogVisible: false,
            editDialogVisible: false,
            rules: {
                region_name: [{ required: true, message: '请输入区划名称', trigger: 'blur' }],
                region_level: [{ required: true, message: '请选择区划级别', trigger: 'change' }],
                region_code: [{ required: true, message: '请输入区划代码', trigger: 'blur' }],
                parent_id: [{ required: true, message: '请选择父级区划', trigger: 'change' }],
                longitude: [{ required: true, message: '请输入经度', trigger: 'blur' }],
                latitude: [{ required: true, message: '请输入纬度', trigger: 'blur' }]
            }
        };
    },
    created() {
        this.getRegionList();
    },
    methods: {
        handleSearchData() {
            this.queryInfo.page = 1;
            this.getRegionList();
        },
        async getRegionList() {
            try {
                const res = await getRegionListApi(this.queryInfo);
                if (res.code === 0) {
                    this.regionData.regionList = res.data;
                    this.regionData.total = res.total;
                } else {
                    this.$message.warning(res.msg || '获取区划列表失败');
                }
            } catch (err) {
                this.$message.error('网络错误');
                console.error(err);
            }
        },

        async filterParentRegion() {
            let keyword;
            if (this.addDialogVisible) {
                keyword = this.addForm.region_level;
            } else {
                keyword = this.editForm.region_level;
            }
            if (!keyword) return;
            try {
                const res = await getParentRegionApi(keyword);
                if (res.code === 0) {
                    this.parentRegionList = res.data;
                }
            } catch (err) {
                console.error(err);
            }
        },

        getParentRegionInfo(type) {
            let parentId, form;
            if (type === 'add') {
                parentId = this.addForm.parent_id;
                form = this.addForm;
            } else {
                parentId = this.editForm.parent_id;
                form = this.editForm;
            }
            if (!parentId) {
                form.parent_name = '';
                form.parent_code = '';
                return;
            }
            const parent = this.parentRegionList.find((item) => item.region_id === parentId);
            if (parent) {
                form.parent_name = parent.region_name;
                form.parent_code = parent.region_code;
            }
        },

        handleSizeChange(newSize) {
            this.queryInfo.limit = newSize;
            this.getRegionList();
        },
        handleCurrentChange(newPage) {
            this.queryInfo.page = newPage;
            this.getRegionList();
        },

        async addRegion() {
            this.$refs.addFormRef.validate(async (valid) => {
                if (!valid) return;
                try {
                    const res = await addRegionApi(this.addForm);
                    if (res.code === 0) {
                        this.$message.success('新增成功');
                        this.addDialogVisible = false;
                        this.getRegionList();
                    }
                } catch (e) {
                    console.error(e);
                }
            });
        },

        showEditDialog(region) {
            this.editForm = JSON.parse(JSON.stringify(region));
            // ✅ 修复：保留数字级别，不转中文
            // ✅ 修复：parent_id 直接使用 ID，不拼接文字
            this.filterParentRegion(); // 加载父级下拉
            this.editDialogVisible = true;
        },

        async editRegion() {
            this.$refs.editFormRef.validate(async (valid) => {
                if (!valid) return;
                try {
                    const res = await editRegionApi(this.editForm);
                    if (res.code === 0) {
                        this.$message.success('编辑成功');
                        this.editDialogVisible = false;
                        this.getRegionList();
                    }
                } catch (e) {
                    console.error(e);
                }
            });
        },

        async removeRegionById(regionId) {
            try {
                await this.$confirm('确定删除？', '警告', { type: 'warning' });
                const res = await deleteRegionApi({ region_id: regionId });
                if (res.code === 0) {
                    this.$message.success('删除成功');
                    this.getRegionList();
                }
            } catch (e) {
                this.$message.info('已取消');
            }
        },

        addDialogClosed() {
            this.$refs.addFormRef.resetFields();
            this.addForm = {
                region_name: '',
                region_level: '',
                region_code: '',
                parent_id: '',
                parent_name: '',
                parent_code: '',
                longitude: '',
                latitude: ''
            };
        },
        editDialogClosed() {
            this.$refs.editFormRef.resetFields();
            this.editForm = {
                region_id: '',
                region_name: '',
                region_level: '',
                region_code: '',
                parent_id: '',
                parent_name: '',
                parent_code: '',
                longitude: '',
                latitude: ''
            };
        }
    }
};
</script>

<style scoped>
* {
    font-size: 14px;
}

.region-info {
    margin: 0;
    padding: 0;
    background-color: #edf0f7;
    color: #333;
    line-height: 1.5;
}

.gt-breadcrumb-box {
    height: 40px;
    line-height: 40px;
    background: #fff;
    padding: 0 16px;
    border-left: 1px solid #dcdcdc;
}

.gt-breadcrumb-box .icon-geoai-manage {
    font-size: 20px;
    color: #2bb3f4;
}

.gt-current-position {
    margin-left: 5px;
    font-size: 18px;
    font-weight: 700;
}

.gt-breadcrumb-cnt {
    margin-top: 8px;
    padding: 10px;
    height: calc(100% - 48px);
    width: 100%;
    background: #fff;
}

.el-table {
    margin-top: 15px;
}

.el-pagination {
    position: absolute;
    bottom: 10px;
    right: 30px;
    height: 6%;
}

::v-deep(.el-breadcrumb) {
    height: 40px;
    display: flex;
    align-items: center;
    margin-left: 10px;
}

::v-deep(.el-form-item) {
    margin-bottom: 16px;
}

.add {
    height: 5%;
    margin-bottom: 10px;
}
</style>
