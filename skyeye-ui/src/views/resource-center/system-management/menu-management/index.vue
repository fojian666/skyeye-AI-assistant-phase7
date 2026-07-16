<template>
    <div class="menu-management">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">菜单管理</span>
        </div>

        <div class="gt-breadcrumb-cnt">
            <el-row :gutter="20" class="add">
                <el-col :span="7">
                    <el-input v-model="queryInfo.caption" clearable placeholder="请输入菜单名称" @keyup.enter.native="menu_operation"> </el-input>
                </el-col>
                <el-col :span="12">
                    <el-button type="primary" @click="menu_operation">查询</el-button>
                    <el-button type="primary" @click="add">新增</el-button>
                    <el-button type="primary" @click="expandAll">全部展开</el-button>
                    <el-button type="primary" @click="collapseAll">全部折叠</el-button>
                </el-col>
            </el-row>
            <!-- 菜单列表 -->
            <el-table
                :data="tableData"
                stripe
                ref="tableTreeRef"
                height="90%"
                style="width: 100%; overflow: hidden"
                border
                row-key="id"
                :tree-props="{ children: 'children', hasChildren: 'hasChildren' }">
                <el-table-column label="序号" type="index" align="center" width="80"></el-table-column>
                <el-table-column prop="caption" label="菜单名称" align="center" width="140"></el-table-column>
                <el-table-column prop="icon" label="图标" align="center" width="100">
                    <template v-slot="scope">
                        <span class="icon iconfont" :class="[scope.row.icon]"></span>
                    </template>
                </el-table-column>
                <el-table-column prop="url" label="链接" align="center"></el-table-column>
                <el-table-column prop="order" label="排序号" sortable align="center" width="100"></el-table-column>
                <el-table-column prop="display" label="是否显示" align="center" width="100">
                    <template v-slot="scope">
                        <el-tag size="mini" effect="dark" type="success" v-if="scope.row.display === 1">显示</el-tag>
                        <el-tag size="mini" effect="dark" type="info" v-else>隐藏</el-tag>
                    </template>
                </el-table-column>
                <el-table-column prop="remark" label="备注" align="center" width="110"></el-table-column>
                <el-table-column label="操作" align="center" width="160">
                    <template v-slot="scope">
                        <el-button type="primary" size="mini" @click="editData(scope.row)">编辑 </el-button>
                        <el-button type="danger" size="mini" @click="deleteData(scope.row.id)">删除 </el-button>
                    </template>
                </el-table-column>
            </el-table>
            <dialog-form ref="dialogFormRef"></dialog-form>
        </div>
    </div>
</template>

<script>
import DialogForm from './dialog-form';
import { deleteMenuDataApi, getMenuDataApi } from '@/api/commonApi';

export default {
    name: 'MenuManagement',
    components: {
        DialogForm
    },
    data() {
        return {
            // 获取用户列表的参数对象
            queryInfo: {
                // 搜索值
                caption: ''
            },
            tableData: [],
            defaultExpandAll: true
        };
    },
    created() {
        this.menu_operation();
    },
    methods: {
        async menu_operation() {
            const res = await getMenuDataApi(this.queryInfo.caption);
            if (res.code === 0) {
                this.tableData = res.form_data;
            } else {
            }

            // this.tableData = this.arrayToTree(res.new_data, 0);
        },
        // arrayToTree(array, pid) {
        //   let result = [];
        //   array.forEach((item) => {
        //     if (item.pid == pid) {
        //       item.children = this.arrayToTree(array, item.id);
        //       result.push(item);
        //     }
        //   });
        //   return result;
        // },
        add() {
            this.$refs.dialogFormRef.open('add', this.$store.state.menuList, (result) => {
                if (result) {
                    this.menu_operation();
                }
            });
        },
        editData(data) {
            this.$refs.dialogFormRef.open(
                'edit',
                this.$store.state.menuList,
                (result) => {
                    if (result) {
                        this.menu_operation();
                    }
                },
                data
            );
        },
        deleteData(id) {
            this.$confirm('此操作将永久删除该条数据, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    const res = await deleteMenuDataApi(id);
                    if (res.code === 0) {
                        this.$message.success(res.msg);
                        this.menu_operation();
                    } else {
                        this.$message.warning(res.msg);
                    }
                })
                .catch(() => {
                    this.$message({
                        type: 'info',
                        message: '已取消删除'
                    });
                });
        },
        expandAll() {
            this.defaultExpandAll = true;
            this.toggleExpand(this.tableData, this.defaultExpandAll);
        },
        collapseAll() {
            this.defaultExpandAll = false;
            this.toggleExpand(this.tableData, this.defaultExpandAll);
        },
        toggleExpand(data, isExpand) {
            data.forEach((item) => {
                this.$refs.tableTreeRef.toggleRowExpansion(item, isExpand);
                if (item.children != null) {
                    this.toggleExpand(item.children, isExpand);
                }
            });
        }
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
</style>
