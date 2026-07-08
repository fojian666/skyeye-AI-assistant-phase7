<template>
    <div class="log-view">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">日志查看</span>
        </div>

        <div class="gt-breadcrumb-cnt">
            <el-row :gutter="20" class="add">
                <el-col :span="4" style="display: flex; align-items: center">
                    <span style="width: 120px; height: 32px; font-size: 15px; line-height: 32px">应用名称：</span>
                    <el-input v-model="queryInfo.serviceName" clearable> </el-input>
                </el-col>
                <el-col :span="4" style="display: flex; align-items: center">
                    <span style="width: 120px; height: 32px; font-size: 15px; line-height: 32px">请求地址：</span>
                    <el-input v-model="queryInfo.url" clearable> </el-input>
                </el-col>
                <el-col :span="4" style="display: flex; align-items: center">
                    <span style="width: 120px; height: 32px; font-size: 15px; line-height: 32px">用户：</span>
                    <el-input v-model="queryInfo.userName" clearable> </el-input>
                </el-col>
                <el-col :span="4" style="display: flex; align-items: center">
                    <span style="width: 120px; height: 32px; font-size: 15px; line-height: 32px">事件：</span>
                    <el-input v-model="queryInfo.type" clearable> </el-input>
                </el-col>
                <el-col :span="4">
                    <el-button type="primary" @click="getLogs">搜索</el-button>
                </el-col>
            </el-row>
            <!-- 用户列表 -->
            <el-table :data="tableData" stripe height="70%" style="width: 100%; overflow: hidden" border>
                <!--<el-table-column prop="id" label="编号" align="center"></el-table-column> -->
                <el-table-column prop="principal" label="操作账号" align="center" width="160"></el-table-column>
                <el-table-column prop="principal" label="姓名" align="center" width="160"></el-table-column>
                <el-table-column prop="name" label="请求地址" align="center" ></el-table-column>
                <el-table-column prop="index" label="服务名称" align="center" width="300"></el-table-column>
                <el-table-column prop="timestamp_millis" label="操作时间" align="center" width="200"></el-table-column>
                <el-table-column prop="event" label="事件" align="center" width="200">
                    <template slot-scope="scope">
                        <el-tag :type="typeTag(scope.row.event)" disable-transitions>{{ scope.row.event }} </el-tag>
                    </template>
                </el-table-column>
                <!--        <el-table-column-->
                <!--            prop="content"-->
                <!--            label="操作内容"-->
                <!--            align="center"-->

                <!--        ></el-table-column>-->
            </el-table>

            <!-- 分页 -->
            <el-pagination
                @current-change="handleCurrentChange"
                :current-page="queryInfo.page"
                @size-change="handleSizeChange"
                :page-size="queryInfo.limit"
                :page-sizes="[10, 20, 30, 40]"
                layout="total, sizes, prev, pager, next, jumper"
                :total="total">
            </el-pagination>
        </div>
    </div>
</template>

<script>
import { getLogDataApi } from '@/api/commonApi';

export default {
    name: 'LogView',
    components: {
    },
    data() {
        return {
            options: [
                {
                    value: 'login',
                    label: 'login'
                },
                {
                    value: 'create',
                    label: 'create'
                },
                {
                    value: 'update',
                    label: 'update'
                },
                {
                    value: 'select',
                    label: 'select'
                },
                {
                    value: 'delete',
                    label: 'delete'
                }
            ],
            // 获取用户列表的参数对象
            queryInfo: {
                // 搜索值
                type: '',
                // 当前的页数
                page: 1,
                // 当前每次显示多少条数据
                limit: 10,
                userName: '',
                url: '',
                serviceName: '',
                conditions: []
            },
            total: 0,
            tableData: []
        };
    },
    created() {
        this.getLogs();
    },
    methods: {
        async getLogs() {
            this.queryInfo.conditions = [];
            if (this.queryInfo.serviceName) {
                this.queryInfo.conditions.push({ key: 'scpAppName', type: 'like', value: this.queryInfo.serviceName });
            }
            if (this.queryInfo.url) {
                this.queryInfo.conditions.push({ key: 'httpUrl', type: 'like', value: this.queryInfo.url });
            }
            if (this.queryInfo.type) {
                this.queryInfo.conditions.push({ key: 'event', type: 'like', value: this.queryInfo.type });
            }
            this.queryInfo.conditions = JSON.stringify(this.queryInfo.conditions);
            this.queryInfo.conditions = encodeURIComponent(this.queryInfo.conditions);
            const res = await getLogDataApi(this.queryInfo);
            this.tableData = res.data;
            this.total = res.count;
        },
        // 监听 limit 改变事件 每页显示的个数
        handleSizeChange(newSize) {
            this.queryInfo.limit = newSize;
            this.getLogs();
        },
        // 监听 页码值 改变的事件 当前页面值
        handleCurrentChange(newPage) {
            this.queryInfo.page = newPage;
            this.getLogs();
        },
        typeTag(type) {
            switch (type) {
                case 'login':
                    return '';
                case 'create':
                    return 'success';
                case 'update':
                    return 'warning';
                case 'select':
                    return 'primary';
                case 'delete':
                    return 'danger';
            }
        }
    }
};
</script>

<style scoped lang="scss">
* {
    font-size: 14px;
}

/*  组件布局*/
.log-view {
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
</style>
