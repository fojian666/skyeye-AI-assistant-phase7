<template>
    <div class="content-box">
        <!-- 面包屑导航 -->
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-manage"></i>
            <span class="gt-current-position">服务目录</span>
        </div>
        <div class="gt-breadcrumb-cnt">
            <el-tabs v-model="serviceSelectedTab" class="service-tabs" @tab-click="handleServiceTabClick">
                <el-tab-pane
                    v-for="item in serviceList"
                    :key="item.id"
                    :label="item.name"
                    :name="item.id" />
            </el-tabs>
            <el-form :model="form" ref="ruleForm" label-width="100px">
                <el-row :gutter="20">
                    <el-col :span="4">
                        <el-form-item label="服务名称：" prop="name">
                            <el-input placeholder="请输入" v-model="form.name" clearable />
                        </el-form-item>
                    </el-col>
                    <el-col :span="4">
                        <el-form-item label="注册时间：" prop="createDate">
                            <el-date-picker
                                v-model="form.createDate"
                                type="date"
                                placeholder="请选择时间"
                                value-format="yyyy-MM-dd"
                                style="width: 100%" />
                        </el-form-item>
                    </el-col>
                    <el-col :span="4">
                        <el-form-item label="所属行政区：" prop="county" label-width="110px">
                            <el-select v-model="form.county" placeholder="请选择行政区" clearable style="width: 100%">
                                <el-option v-for="item in selectOption" :key="item" :label="item" :value="item" />
                            </el-select>
                        </el-form-item>
                    </el-col>
                    <el-col :span="1" class="btn">
                        <el-button type="primary" icon="el-icon-search" @click="search" class="search" size="mini">搜索</el-button>
                    </el-col>
                    <el-col :span="1" class="btn">
                        <el-button icon="el-icon-refresh-left" @click="resetForm" class="reset" size="mini">重置</el-button>
                    </el-col>
                </el-row>
            </el-form>
            <CpTab
                :cpTablList="cpTablList"
                :selectTab="currentSelectedTab"
                :showButton="true"
                @cpTabClick="batchDeleteSource"
                @cpTabItemClick="cpTabItemClick"></CpTab>
            <div class="list-content">
                <div class="content-card" v-for="item in sourceListsData" :key="item.id">
                    <el-checkbox @change="(checked) => onChange(checked, item.id)"></el-checkbox>
                    <div @click="mapLoad(item.id, item.sourceType)">
                        <img :src="item.img_url" />
                        <h3>{{ item.name }}</h3>
                        <p class="service-type">服务类型：{{ item.source_type }}</p>
                        <p class="region">行政区：{{ item.county }}</p>
                        <p class="service">服务类别：{{ item.service_type }}</p>
                        <div class="service-content1">
                            <div class="content-item">
                                <div class="ai-banner-title">
                                    <div></div>
                                    <p>注册时间</p>
                                </div>
                                <p>{{ item.append_time }}</p>
                            </div>
                            <div class="content-item">
                                <div class="ai-banner-title">
                                    <div></div>
                                    <p>配置人员</p>
                                </div>
                                <p>{{ item.owner }}</p>
                            </div>
                            <div class="content-item right_module">
                                <div class="ai-banner-title">
                                    <div></div>
                                    <p>生产时间</p>
                                </div>
                                <p>{{ item.create_time }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="space"></div>
            <div class="pagination">
                <div class="pagination-describe">
                    共 {{ total }} 条记录 第{{ params.page + '/' + Math.ceil(total / params.limit) }}
                    页
                </div>
                <div class="page-number">
                    <el-pagination
                        background
                        layout="total, prev, pager, next, jumper"
                        :current-page="params.page"
                        :page-size="params.limit"
                        :total="total"
                        @current-change="handlePageChange" />
                </div>
            </div>
        </div>

    </div>
</template>

<script>
import CpTab from '@/components/cp-tab';
import { getResourceListsApi, deleteResourceApi } from '@/api/commonApi';

export default {
    name: 'ResourceDirectory',
    components: { CpTab },
    data() {
        return {
            form: {
                name: '',
                createDate: '',
                county: '',
                source_type: ''
            },
            sourceTypeMap: {
                yxfw: '影像服务',
                ywsgsjfw: '业务栅格数据服务',
                ywslsjfw: '业务矢量数据服务'
            },
            sourceListsData: [],
            params: {
                limit: 8,
                page: 1,
                order_by: 'CreateDate'
            },
            total: 0,
            serviceList: [
                {
                    name: '全部',
                    id: 'all'
                },
                {
                    name: '影像服务',
                    id: 'yxfw'
                },
                {
                    name: '业务栅格数据服务',
                    id: 'ywsgsjfw'
                },
                {
                    name: '业务矢量数据服务',
                    id: 'ywslsjfw'
                }
            ],
            cpTablList: [
                {
                    name: '按时间排序',
                    id: 'CreateDate',
                    icon: 'arrow-down'
                },
                {
                    name: '按名称排序',
                    id: 'name',
                    icon: 'arrow-down'
                }
            ],
            currentSelectedTab: 'CreateDate',
            checkedList: [],
            source_ids: [],
            serviceSelectedTab: 'all',
            selectOption: []
        };
    },
    watch: {
        'form.createDate': function (newVal) {
            if (newVal === null) {
                this.form.createDate = '';
            }
        }
    },
    mounted() {
        this.sourceLists();
    },
    methods: {
        common_event(event_name) {
            this[event_name]();
        },
        search() {
            this.params.page = 1;
            this.sourceLists();
        },
        resetForm() {
            const sourceType = this.form.source_type;
            this.$refs.ruleForm.resetFields();
            this.form.source_type = sourceType;
            this.params.page = 1;
            this.sourceLists();
        },
        buildListParams() {
            const params = {
                ...this.params,
                ...this.form,
                pageIndex: this.params.page,
                pageSize: this.params.limit,
                orderField: this.params.order_by,
                orderType: '1'
            };
            if (this.form.source_type) {
                params.sourceType = this.form.source_type;
                params.source_type = this.form.source_type;
            }
            return params;
        },
        getSourceType(item) {
            return item.sourceType || item.source_type || '';
        },
        setItemImage(item) {
            const type = this.getSourceType(item);
            if (type === '影像服务') {
                item.img_url = require('@/assets/images/tupian-renwuzx-2.png');
            } else if (type === '业务栅格数据服务') {
                item.img_url = require('@/assets/images/tupian-renwuzx-5.png');
            } else {
                item.img_url = require('@/assets/images/tupian-renwuzx-6.png');
            }
        },
        async sourceLists() {
            const params = this.buildListParams();
            const res = await getResourceListsApi(params);

            if (res.code !== 0) {
                this.sourceListsData = [];
                return this.$message.warning(res.msg || (res.data && res.data.msg));
            }
            let list = res.data || [];
            if (this.form.source_type) {
                list = list.filter((item) => this.getSourceType(item) === this.form.source_type);
            }
            list.forEach((item) => this.setItemImage(item));
            this.sourceListsData = list;
            this.selectOption = [...new Set(list.map((item) => item.county || null).filter(Boolean))];
            this.total = res.total;
        },
        cpTabItemClick(obj) {
            this.currentSelectedTab = obj.key;
            this.params.order_by = obj.key;
            this.sourceLists();
        },
        handleServiceTabClick(tab) {
            const tabKey = tab.name;
            this.serviceSelectedTab = tabKey;
            this.params.page = 1;
            if (tabKey === 'all') {
                this.form.source_type = '';
            } else {
                this.form.source_type = this.sourceTypeMap[tabKey] || '';
            }
            this.sourceLists();
        },
        batchDeleteSource() {
            if (this.checkedList.length === 0) return this.$message.warning('请选择要删除的数据!');
            this.$confirm('此操作将永久删除, 是否继续?', '提示', {
                confirmButtonText: '确定',
                cancelButtonText: '取消',
                type: 'warning'
            })
                .then(async () => {
                    let params = {
                        resource_ids: this.source_ids
                    };
                    const res = await deleteResourceApi(params);
                    if (res.code !== 0) {
                        return this.$message.warning(res.msg);
                    }
                    this.$message.success(res.msg);
                    this.source_ids = [];
                    this.checkedList = [];
                    this.sourceLists();
                })
                .catch(() => {
                    this.$message.info('已取消删除');
                });
        },
        onChange(checked, id) {
            if (checked && id) {
                if (!this.source_ids.includes(id)) {
                    this.checkedList.push(checked);
                    this.source_ids.push(id);
                }
                return;
            }
            const index = this.source_ids.indexOf(id);
            if (index > -1) {
                this.source_ids.splice(index, 1);
                this.checkedList.splice(index, 1);
            }
        },
        handlePageChange(page) {
            this.params.page = page;
            this.sourceLists();
        },
        mapLoad(id, source_type) {
            this.$router.push({
                path: '/resource-center/resource-directory/resource-details',
                query: { id, source_type }
            });
        }
    }
};
</script>

<style scoped>

.content-box {
    margin: 0;
    padding: 0;
    background-color: #edf0f7;
    color: #333;
    line-height: 1.5;
}
ul li {
    list-style: none;
    float: left;
    margin-left: 20px;
    cursor: pointer;
}

.content-card {
    width: calc(25% - 16px);
    border: 1px solid #e9e9e9;
    position: relative;
    float: left;
    margin: 16px 16px 0 0;
    cursor: pointer;
}

.content-card:hover {
    border: 1px solid #1890ff;
}

.content-card img {
    width: 100%;
    height: 130px;
}

.content-card h3 {
    font-weight: 700;
    font-size: 16px;
    position: absolute;
    left: 23px;
    top: 32px;
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
    width: calc(100% - 40px);
    display: block;
    word-break: break-all;
    word-wrap: break-word;
}

.content-card .service-type {
    position: absolute;
    left: 23px;
    top: 61px;
}

.content-card .region {
    position: absolute;
    left: 23px;
    top: 82px;
}

.service {
    position: absolute;
    left: 23px;
    top: 103px;
}

.service-content1 {
    display: flex;
    height: 45px;
    margin: 16px 0;
}

.service-content1 .content-item {
    width: 33%;
    border-right: 1px solid #ededed;
    display: flex;
    align-items: center;
    flex-direction: column;
}

.content-item > p {
    margin-top: 3px;
}

.service-content1 .right_module {
    border-right: 0;
}

.ai-banner-title {
    display: flex;
    align-items: center;
    justify-content: center;
}

.ai-banner-title p {
    font-weight: 700;
    color: #000;
}

.ai-banner-title div {
    width: 5px;
    height: 5px;
    background-color: #0077e8;
    margin-right: 4px;
}

.content-card ::v-deep .el-checkbox {
    position: absolute;
    left: 6px;
    top: 6px;
}

.list-content {
    height: calc(100% - 270px);
    width: 100%;
    overflow: auto;
}

.space {
    width: 100%;
    height: 70px;
}

.pagination-describe {
    margin-top: 5px;
    position: absolute;
    bottom: 20px;
    left: 20px;
}

.page-number {
    position: absolute;
    bottom: 20px;
    right: 10px;
}

.batch-delete {
    position: absolute;
    top: 10px;
    right: 0;
}


.reset {
    margin-left: 10px;
}
.btn {
    margin-top: 4px;
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
    background-color: #fff;
}

.service-tabs {
    margin-bottom: 12px;
}

.service-tabs ::v-deep .el-tabs__header {
    margin-bottom: 0;
}
</style>
