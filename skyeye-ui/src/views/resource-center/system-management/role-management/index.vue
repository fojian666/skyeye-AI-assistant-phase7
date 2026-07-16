<template>
    <div class="authority-management">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">权限管理</span>
        </div>

        <div class="gt-breadcrumb-cnt">
            <div class="button-group">
                <a-input-search placeholder="请输入角色名称" class="search-input" enter-button @search="onSearch" pressEnter="onSearch" />
                <a-button class="editable-add-btn" @click="showNewRoleModel">新增角色</a-button>
            </div>

            <div class="table-box">
                <a-table :columns="columns" :data-source="tableData.dataSource" :loading="loading">
                    <template slot="operation" slot-scope="text, record">
                        <a-button-group class="role-operate-group">
                            <a-button style="background-color: #009688; border-color: #009688" @click="getMenusByRole(record.id)">关联菜单 </a-button>
                            <a-button style="background-color: #177de4; border-color: #177de4" @click="getUsersByRole(record.id)">关联用户 </a-button>
                            <a-button style="background-color: #ffb800; border-color: #ffb800" @click="editRoleInfo(record)">编辑 </a-button>
                            <a-button style="background-color: #ff5722; border-color: #ff5722" @click="deleteRoleConfirm(record)">删除 </a-button>
                        </a-button-group>
                    </template>
                </a-table>
            </div>
        </div>

        <!--    新增、修改角色-->
        <a-modal v-model="newRole.model" :title="newRole.title" centered :footer="null" wrapClassName="rc-light-modal">
            <a-form-model class="add-role-form" @submit="addNewRole" ref="newRoleForm" :model="newRole.form" :rules="newRole.rules">
                <a-form-model-item ref="name" label="名称" prop="name" name="name" required>
                    <a-input
                        v-model:value="newRole.form.name"
                        placeholder="请输入角色名称"
                        @blur="
                            () => {
                                $refs.name.onFieldBlur();
                            }
                        " />
                </a-form-model-item>

                <a-form-model-item ref="abbreviation" label="缩写" prop="abbreviation" required>
                    <a-input
                        v-model:value="newRole.form.abbreviation"
                        placeholder="请输入缩写"
                        @blur="
                            () => {
                                $refs.abbreviation.onFieldBlur();
                            }
                        " />
                </a-form-model-item>

                <a-form-model-item label="备注">
                    <a-input
                        v-model:value="newRole.form.remark"
                        type="textara"
                        @blur="
                            () => {
                                $refs.remark.onFieldBlur();
                            }
                        " />
                </a-form-model-item>

                <a-form-model-item ref="order" label="排序号" prop="order" required>
                    <a-input
                        v-model.number="newRole.form.order"
                        placeholder="请输入排序号"
                        @blur="
                            () => {
                                $refs.order.onFieldBlur();
                            }
                        " />
                </a-form-model-item>

                <a-form-model-item style="margin-left: 55%">
                    <a-button type="primary" html-type="submit">{{ newRole.title }}</a-button>
                    <a-button @click="cancleAddNewRole" style="margin-left: 10px">取消</a-button>
                </a-form-model-item>
            </a-form-model>
        </a-modal>

        <!--    关联菜单-->
        <a-modal
            id="menuModel"
            width="720px"
            height="560px"
            v-model="menuData.model"
            title="菜单权限管理"
            centered
            :footer="null"
            wrapClassName="rc-light-modal">
            <div class="menu-body">
                <div class="menu-btn">
                    <a-button type="primary" @click="setMenusByRole">提交</a-button>
                    <a-button @click="getMenusByRole(role_id)">重置</a-button>
                </div>

                <div class="menu-tree">
                    <a-tree
                        v-model="menuData.selectValue"
                        checkable
                        :replaceFields="menuData.replaceFields"
                        :defaultExpandedKeys="menuData.selectValue"
                        :selected-keys="menuData.selectValue"
                        @check="check"
                        :tree-data="menuData.treeData" />
                </div>
            </div>
        </a-modal>

        <!--    关联角色-->
        <a-modal
            id="userModel"
            width="820px"
            height="540px"
            v-model="userData.model"
            title="用户数据"
            centered
            :footer="null"
            wrapClassName="rc-light-modal">
            <div class="user-body">
                <div style="margin-bottom: 16px">
                    <a-button type="primary" @click="setUsersByRoles" :disabled="!hasUserSelected">保存数据 </a-button>
                    <span style="margin-left: 8px">
                        <template v-if="hasUserSelected">
                            {{ `已选择 ${userData.selectedRowKeys.length} 个用户` }}
                        </template>
                    </span>
                </div>
                <a-table
                    class="user-table"
                    rowKey="id"
                    :columns="userData.userColums"
                    :data-source="userData.data"
                    :row-selection="{ selectedRowKeys: userData.selectedRowKeys, onChange: onSelectUser }" />
            </div>
        </a-modal>
    </div>
</template>

<script>
import { Modal } from 'ant-design-vue';
import {
    deleteRoleDataApi,
    getMenuRoleDataApi,
    getRoleDataApi,
    getUserRoleDataApi,
    postMenuRoleDataApi,
    postRoleDataApi,
    postUserRoleDataApi,
    putRoleDataApi
} from '@/api/commonApi';

const columns = [
    {
        title: 'ID',
        dataIndex: 'id',
        key: 'id'
    },

    {
        title: '角色名称',
        dataIndex: 'name',
        key: 'name'
    },
    {
        title: '角色缩写',
        dataIndex: 'abbreviation',
        key: 'abbreviation'
    },
    {
        title: '备注',
        dataIndex: 'remark',
        key: 'remark'
    },
    {
        title: '排序号',
        dataIndex: 'order',
        key: 'order'
    },
    {
        title: '操作',
        dataIndex: 'operation',
        scopedSlots: { customRender: 'operation' }
    }
];

const userColums = [
    {
        title: '用户ID',
        dataIndex: 'id',
        key: 'id'
    },
    {
        title: '用户名',
        dataIndex: 'name'
    },
    {
        title: '角色',
        dataIndex: 'role'
    },
    {
        title: '备注',
        dataIndex: 'description'
    },
    {
        title: '真实姓名',
        dataIndex: 'realname'
    }
];

export default {
    name: 'AuthorityManagement',
    components: {},
    data() {
        return {
            columns,
            tableData: {
                roleName: '',
                dataSource: [],
                count: 0
            },

            loading: false,

            role_id: '',

            newRole: {
                model: false,
                title: '新增角色',
                form: {
                    id: '',
                    name: '',
                    abbreviation: '',
                    remark: '',
                    order: undefined
                },
                rules: {
                    name: [
                        { required: true, message: '角色名称不能为空！', trigger: 'blur' },
                        { max: 40, message: '该名称过长', trigger: 'blur' }
                    ],
                    abbreviation: [
                        { required: true, message: '缩写不能为空！', trigger: 'blur' },
                        { max: 40, message: '该名称过长', trigger: 'blur' }
                    ],
                    order: [
                        { required: true, message: '排序号不能为空！', trigger: 'blur' },
                        { type: 'number', message: '排序号必须为数字！', trigger: 'blur' }
                    ],
                    remark: [{ max: 40, message: '备注信息过长', trigger: 'blur' }]
                }
            },

            menuData: {
                model: false,
                selectValue: [],
                treeData: [],
                replaceFields: {
                    children: 'children',
                    title: 'caption',
                    key: 'id',
                    value: 'id'
                }
            },

            userData: {
                model: false,
                data: [],
                userColums,
                selectedRowKeys: []
            },
            idsArr: []
        };
    },
    created() {
        this.getRoleShow();
    },
    computed: {
        hasUserSelected() {
            return this.userData.selectedRowKeys.length > 0;
        }
    },
    methods: {
        // 获取初试的角色表格数据
        async getRoleShow() {
            const res = await getRoleDataApi(this.tableData.roleName);
            if (res.code === 0) {
                res.data.forEach((item, i) => {
                    item.key = i;
                });
                this.tableData.dataSource = res.data;
                this.tableData.count = res.data.length;
            } else {
                return this.$message.warning(res.msg);
            }
        },
        // 根绝用户名模糊搜索
        onSearch(value) {
            this.tableData.roleName = value;
            this.getRoleShow();
            this.tableData.roleName = '';
        },
        // 添加、编辑角色
        showNewRoleModel() {
            this.newRole.model = true;
        },
        async addNewRole(e) {
            e.preventDefault();
            this.$refs.newRoleForm.validate(async (valid) => {
                let params = {
                    name: this.newRole.form.name,
                    abbreviation: this.newRole.form.abbreviation,
                    remark: this.newRole.form.remark,
                    order: this.newRole.form.order
                };
                if (valid) {
                    // 添加角色
                    if (this.newRole.title === '新增角色') {
                        const res = await postRoleDataApi(params);
                        if (res.code === 0) {
                            this.$message.success(res.msg);
                            this.cancleAddNewRole();
                        } else {
                            this.$message.warning(res.msg);
                        }
                    }
                    // 编辑角色信息
                    else {
                        params['id'] = this.newRole.form.id;
                        const res = await putRoleDataApi(params);
                        if (res.code === 0) {
                            this.$message.success(res.msg);
                            this.cancleAddNewRole();
                        } else {
                            this.$message.error(res.msg);
                        }
                    }
                } else {
                    this.$message.warning('表单验证未通过！');
                    return false;
                }
            });
        },
        cancleAddNewRole() {
            this.$refs.newRoleForm.resetFields();
            this.newRole.form.remark = '';
            this.newRole.model = false;
            this.newRole.title = '新增角色';
            this.getRoleShow();
        },
        editRoleInfo(record) {
            this.newRole.form = record;
            this.newRole.title = '修改角色信息';
            this.newRole.model = true;
        },
        // 关联用户
        async getUsersByRole(role_id) {
            const res = await getUserRoleDataApi();
            if (res.code === 0) {
                this.role_id = role_id;
                this.userData.data = res.data;
                // 如用户已经为该角色，需要选中
                this.userData.selectedRowKeys = [];
                this.userData.data.forEach((item) => {
                    if (item.role_id === this.role_id) {
                        this.userData.selectedRowKeys.push(item.id);
                    }
                });
                this.userData.model = true;
            } else {
                this.$message.warning(res.msg);
            }
        },
        onSelectUser(selectedRowKeys) {
            this.userData.selectedRowKeys = selectedRowKeys;
        },
        async setUsersByRoles() {
            // 提交角色id与用户的id组
            const params = {
                role_id: this.role_id,
                user_id: this.userData.selectedRowKeys
            };
            const res = await postUserRoleDataApi(params);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.userData.model = false;
            } else {
                this.$message.warning(res.msg);
            }
        },
        // 管理菜单
        async getMenusByRole(role_id) {
            const res = await getMenuRoleDataApi(role_id);
            if (res.code === 0) {
                this.role_id = role_id;
                this.menuData.treeData = res.data;
                this.menuData.selectValue = res.value;
                this.menuData.model = true;
            } else {
                return this.$message.warning(res.msg);
            }
        },
        check(checkedKeys, e) {
            this.idsArr = [...checkedKeys, ...e.halfCheckedKeys];
        },
        async setMenusByRole() {
            // 提交角色id与菜单权限的id组
            const params = {
                role_id: this.role_id,
                menu_id: this.idsArr
            };
            console.log(params);
            const res = await postMenuRoleDataApi(params);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.menuData.model = false;
            } else {
                this.$message.warning(res.msg);
            }
        },
        // 删除角色
        deleteRoleConfirm(record) {
            let then = this;
            Modal.confirm({
                title: '确定要删除该角色吗?',
                content: (h) => <div style="color:red;">该角色关联的菜单、用户，删除后无法恢复！</div>,
                onOk() {
                    then.deleteRole(record.id);
                },
                onCancel() {
                    this.$message.warning('取消收藏！');
                },
                class: 'test'
            });
        },
        async deleteRole(role_id) {
            //  删除该角色
            const params = {
                id: role_id
            };
            const res = await deleteRoleDataApi(params);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.getRoleShow();
            } else {
                this.$message.warning(res.msg);
            }
        }
    }
};
</script>

<style scoped>
/*  组件布局*/
.authority-management {
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

/*  表格工具栏*/
.button-group {
    height: 50px;
}

.button-group button {
    height: 36px;
    width: 100px;
    background-color: #009688;
    color: #fff;
}

.search-input {
    width: 25%;
    line-height: 36px;
    margin-right: 10px;
}

.search-input .ant-btn-primary {
    background-color: #177de4;
}

::v-deep .ant-input-group .ant-input,
::v-deep .ant-input-group-addon .ant-btn.ant-input-search-button {
    height: 36px;
}

/*  新增用户*/
::v-deep .add-role-form .ant-form-item {
    width: 98%;
    font-size: 16px;
    display: flex;
}

::v-deep .add-role-form .ant-form-item .ant-form-item-label {
    width: 20%;
    text-align: center;
}

::v-deep .add-role-form .ant-form-item .ant-form-item-control-wrapper {
    width: 75%;
}

.role-operate-group button {
    margin: 0 10px;
    color: #ffffff;
}

.role-operate-group button:hover {
    opacity: 0.6;
}

/*  角色与菜单管理权限*/
#menuModel .ant-modal-body {
    max-height: 500px;
    padding: 15px;
}

#menuModel .menu-body {
    width: 100%;
    height: 100%;
}

#menuModel .menu-btn button {
    margin: 0 5px;
}

#menuModel .menu-tree {
    margin-top: 15px;
    border-left: 1px solid #dcdcdc;
    height: 420px;
    overflow-y: auto;
}

/*  角色与用户权限管理*/
#userModel .user-body {
    width: 100%;
    height: 100%;
}

#userModel .user-table {
    height: 420px;
    overflow-y: auto;
}
</style>
