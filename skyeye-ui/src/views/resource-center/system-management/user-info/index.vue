<template>
    <div class="user-info">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">用户管理</span>
        </div>
        <div class="gt-breadcrumb-cnt">
            <el-form :inline="true" class="add">
                <el-form-item label-width="80px" label="用户名:">
                    <el-input placeholder="请输入用户名" clearable v-model="queryInfo.query" @clear="getUserList" size="small"> </el-input>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="getUserList" size="small">搜索</el-button>
                </el-form-item>
                <el-form-item>
                    <el-button type="primary" @click="addDialogVisible = true" size="small">
                        <i class="iconfont icon-geoai-add-user"></i>新增用户
                    </el-button>
                </el-form-item>
            </el-form>
            <!-- 用户列表 -->
            <el-table :data="userData.userList" height="70%" stripe style="width: 100%" border>
                <el-table-column prop="id" label="用户ID" align="center" width="80"></el-table-column>
                <el-table-column prop="username" label="用户名" align="center"></el-table-column>
                <el-table-column prop="role" label="角色" align="center"></el-table-column>
                <el-table-column prop="is_superuser" label="是否是超级管理员" align="center"></el-table-column>
                <el-table-column prop="county" label="行政区" align="center"></el-table-column>
                <el-table-column prop="date_joined" label="注册时间" align="center"></el-table-column>
                <el-table-column label="状态" align="center" width="100px">
                    <template v-slot="scope">
                        <el-switch
                            v-model="scope.row.is_active"
                            active-color="#13ce66"
                            inactive-color="#ff4949"
                            active-value="true"
                            inactive-value="false"
                            @change="userStatusChanged(scope.row)"></el-switch>
                    </template>
                </el-table-column>
                <el-table-column label="操作" width="160px" align="center">
                    <template v-slot="scope">
                        <!-- 修改按钮 -->
                        <el-button type="primary" icon="el-icon-edit" size="mini" @click="showEditDialog(scope.row)"></el-button>
                        <!-- 删除按钮 -->
                        <el-button type="danger" icon="el-icon-delete" size="mini" @click="removeUserById(scope.row.id)"></el-button>
                    </template>
                </el-table-column>
            </el-table>

            <!-- 分页 -->
            <el-pagination
                @current-change="handleCurrentChange"
                :current-page="queryInfo.page"
                @size-change="handleSizeChange"
                :page-size="queryInfo.limit"
                :page-sizes="[5, 10, 15, 20]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="userData.total">
            </el-pagination>

            <!-- 添加用户对话框 -->
            <el-dialog title="添加用户" :visible.sync="addDialogVisible" width="50%" custom-class="rc-light-dialog" @close="addDislogClosed">
                <!-- 内容主题区域 -->
                <el-form label-width="100px" ref="addFormRef" :model="addForm" :rules="addFormRules">
                    <el-form-item label="账户名称" prop="username">
                        <el-input v-model="addForm.username"></el-input>
                    </el-form-item>
                    <el-form-item label="账号密码" prop="password">
                        <el-input v-model="addForm.password" type="password" show-password></el-input>
                    </el-form-item>
                    <el-form-item label="账户邮箱" prop="email">
                        <el-input v-model="addForm.email"></el-input>
                    </el-form-item>
                    <el-form-item label="用户角色" prop="email">
                        <el-select v-model="addForm.role" popper-class="rc-light-popper" style="width: 100%">
                            <el-option v-for="item in roleList" :key="item.id" :label="item.name" :value="item.id" />
                        </el-select>
                    </el-form-item>
                    <el-form-item ref="county" class="spacing" label="所属区县" prop="county">
                        <el-select
                            v-model="addForm.county"
                            placeholder="请先输入行政区检索关键字"
                            filterable
                            remote
                            popper-class="rc-light-popper"
                            style="width: 100%"
                            :remote-method="filterCounty">
                            <el-option v-for="d in filterCountyData" :key="d.key" :label="`${d.value}(${d.key})`" :value="`${d.value}(${d.key})`" />
                        </el-select>
                    </el-form-item>
                </el-form>
                <!-- 底部按钮区域 -->
                <span slot="footer" class="dialog-footer">
                    <el-button @click="addDialogVisible = false">取 消</el-button>
                    <el-button type="primary" @click="addUser">确 定</el-button>
                </span>
            </el-dialog>
            <!-- 修改用户信息对话框 -->
            <el-dialog title="修改用户" @close="aditClosed" :visible.sync="editDialogVisble" width="50%" custom-class="rc-light-dialog">
                <el-form :model="editForm" :rules="addFormRules" ref="editFormRef" label-width="70px">
                    <el-form-item label="用户ID">
                        <el-input v-model="editForm.id" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="用户名">
                        <el-input v-model="editForm.username" disabled></el-input>
                    </el-form-item>
                    <el-form-item label="邮箱" prop="email">
                        <el-input v-model="editForm.email"></el-input>
                    </el-form-item>
                    <el-form-item label="用户角色" prop="email">
                        <el-select v-model="editForm.role" popper-class="rc-light-popper" style="width: 100%">
                            <el-option v-for="item in roleList" :key="item.id" :label="item.name" :value="item.id" />
                        </el-select>
                    </el-form-item>
                    <el-form-item ref="county" class="spacing" label="所属区县" prop="county">
                        <el-select
                            v-model="editForm.county"
                            placeholder="请先输入行政区检索关键字"
                            filterable
                            remote
                            popper-class="rc-light-popper"
                            style="width: 100%"
                            :remote-method="filterCounty">
                            <el-option v-for="d in filterCountyData" :key="d.key" :label="`${d.value}(${d.key})`" :value="`${d.value}(${d.key})`" />
                        </el-select>
                    </el-form-item>
                </el-form>
                <span slot="footer" class="dialog-footer">
                    <el-button @click="editDialogVisble = false">取 消</el-button>
                    <el-button type="primary" @click="editUserInfo">确 定</el-button>
                </span>
            </el-dialog>
            <!-- 分配角色 -->
            <el-dialog
                title="分配角色"
                :visible.sync="setRolesDialogVisible"
                @close="setRolesDialogClosed"
                width="50%"
                custom-class="rc-light-dialog">
                <div>
                    <p>当前的用户 : {{ userInfo.username }}</p>
                    <p>当前的角色 : {{ userInfo.role }}</p>
                    <p>
                        分配新角色:
                        <el-select v-model="selectRoleId" placeholder="请选择" popper-class="rc-light-popper">
                            <el-option v-for="item in rolesList" :key="item.id" :label="item.roleName" :value="item.id" />
                        </el-select>
                    </p>
                </div>
                <span slot="footer" class="dialog-footer">
                    <el-button @click="setRolesDialogVisible = false">取 消</el-button>
                    <el-button type="primary" @click="saveRolesInfo">确 定</el-button>
                </span>
            </el-dialog>
        </div>
    </div>
</template>

<script>
import { userAddFormRulesMixin } from '@/utils/validate.js';
import {
    getRegionInfoListApi,
    deleteUserDataApi,
    getRoleDataApi,
    getUserListApi,
    postUserDataApi,
    postUserRoleApi,
    postUserStatusApi,
    putUserDataApi
} from '@/api/commonApi';

export default {
    name: 'Users',
    mixins: [userAddFormRulesMixin],
    data() {
        return {
            // 获取用户列表的参数对象
            queryInfo: {
                // 搜索值
                query: '',
                // 当前的页数
                page: 1,
                // 当前每次显示多少条数据
                limit: 10
            },
            // 存放用户的数据和数量
            userData: {
                userList: [],
                total: 0
            },
            filterCountyData: [],
            countyList: [],
            // 添加用户数据的对象
            addForm: {
                username: '',
                password: '',
                email: '',
                county: '',
                role: ''
            },
            // 修改用户消息对话框显示和隐藏
            editDialogVisble: false,
            // 控制分配角色对话框的显示和隐藏
            setRolesDialogVisible: false,
            regionOptions: [],
            // 控制用户对话框的显示和隐藏
            addDialogVisible: false,
            // 需要被分配角色的用户信息
            userInfo: {},
            // 分配角色列表
            rolesList: [],
            // 保存已经选中的角色id值
            selectRoleId: '',
            // 查询用户的对象
            editForm: {
                username: '',
                id: '',
                email: '',
                county: '',
                role: ''
            },
            roleList: []
        };
    },
    components: {},
    created() {
        this.getUserList();
    },
    methods: {
        //获取区域的级联数据
        async getRegionOptions() {
            const res = await getRegionInfoListApi();
            this.countyList = res.data;
        },
        // 行政区筛选
        filterCounty(value) {
            if (value === '' || value === ' ') {
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
        async getUserList() {
            const res = await getUserListApi(this.queryInfo);
            if (res.code === 0) {
                this.userData.userList = res.data;
                this.userData.total = res.count;
            } else {
                this.$message.warning(res.msg);
            }
        },
        async getRoleList() {
            const res = await getRoleDataApi('');
            if (res.code === 0) {
                this.roleList = res.data;
            }
        },
        // 监听 limit 改变事件 每页显示的个数
        handleSizeChange(newSize) {
            this.queryInfo.limit = newSize;
            this.getUserList();
        },
        // 监听 页码值 改变的事件 当前页面值
        handleCurrentChange(newPage) {
            this.queryInfo.page = newPage;
            this.getUserList();
        },
        // 监听Switch状态的改变
        async userStatusChanged(userInfo) {
            const params = {
                id: userInfo.id,
                is_active: userInfo.is_active
            };
            const res = await postUserStatusApi(params);
            if (res.code === 0) {
                this.getUserList();
                this.$message.success(res.msg);
            } else {
                this.$message.warning(res.msg);
            }
        },
        // 监听添加用户的对话框关闭事件
        addDislogClosed() {
            this.$refs.addFormRef.resetFields();
        },
        // 点击按钮,添加新用户
        addUser() {
            this.$refs.addFormRef.validate(async (valid) => {
                if (!valid) return;
                //通过URLSearchParams封装请求数据
                let params = {
                    username: this.addForm.username,
                    password: this.addForm.password,
                    email: this.addForm.email,
                    county: this.addForm.county,
                    role: this.addForm.role
                };
                const res = await postUserDataApi(params);
                if (res.code === 0) {
                    // 隐藏添加用户的对话框
                    this.addDialogVisible = false;
                    // 添加成后重新获取用户数据,不需要用户手动刷新
                    this.getUserList();
                    this.$message.success(res.msg);
                } else {
                    this.$message.warning(res.msg);
                }
            });
        },
        // 展示编辑用户的对话框
        async showEditDialog(data) {
            this.editForm = data;
            this.editDialogVisble = true;
            //this.$message.success(res.msg);
        },
        // 监听修改用户对话框的关闭事件
        aditClosed() {
            this.$refs.editFormRef.resetFields();
        },
        editUserInfo() {
            this.$refs.editFormRef.validate(async (valid) => {
                if (!valid) return;
                // 发起修改用户信息的数据请求
                const res = await putUserDataApi(this.editForm);
                if (res.code === 0) {
                    this.editDialogVisble = false;
                    this.getUserList();
                    this.$message.success(res.msg);
                } else {
                    this.$message.warning(res.msg);
                }
            });
        },
        // 根据id删除对应的用户信息
        async removeUserById(id) {
            // 询问用户是否删除用户
            const confirmRusult = await this.$confirm('此操作将永久删除该用户, 是否继续?', '永久删除该用户', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            }).catch((err) => err);
            // 用户点击了删除,则返回字符串 confirm
            // 用户取消了删除,则返回字符串 cancel
            if (confirmRusult !== 'confirm') {
                return this.$message.info('已经取消了删除');
            }
            const params = {
                id: id
            };
            const res = await deleteUserDataApi(params);
            if (res.code === 0) {
                this.$message.success(res.msg);
                this.getUserList();
            } else {
                this.$message.warning(res.msg);
            }
        },
        // 点击按钮,分配角色
        async saveRolesInfo() {
            if (!this.selectRoleId) {
                return this.$message.error('请选择要分配的角色!');
            }
            const params = {
                role_id: this.selectRoleId,
                user_id: this.userInfo.id
            };
            const res = await postUserRoleApi(params);
            if (res.code === 0) {
                this.$message.success(res.msg);
            } else {
                this.$message.warning(res.msg);
            }

            this.getUserList();
            this.setRolesDialogVisible = false;
        },
        // 分配角色对话框关闭
        setRolesDialogClosed() {
            this.selectRoleId = '';
            this.userInfo = '';
        }
    },
    mounted() {
        this.getRoleList();
        this.getRegionOptions();
    }
};
</script>

<style scoped>
* {
    font-size: 14px;
}

/*  组件布局*/
.user-info {
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
</style>
