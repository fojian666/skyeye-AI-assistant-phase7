<template>
    <div class="se-container">
        <div class="title-bg-tab">
            <span>{{ subTitle }}</span>
        </div>
        <div class="gt-right-content">
            <div class="left-content">
                <div class="filter">
                    <el-form :model="formInfo" size="medium">
                        <el-form-item>
                            <el-input placeholder="请输入关键字" v-model="treeKeyword" style="width: 100%; margin-right: 10px"></el-input>
                        </el-form-item>
                    </el-form>
                </div>
                <div class="tree-container">
                    <el-tree
                        :data="treeData"
                        :show-checkbox="false"
                        :render-content="renderContent"
                        :default-expand-all="false"
                        ref="tree"
                        node-key="label"
                        :filter-node-method="filterNode"
                        :default-expanded-keys="expandedKeys"
                        :props="defaultProps"
                        @node-click="getPanoramaImage"
                        highlight-current></el-tree>
                </div>
            </div>
            <div class="border"></div>
            <div class="right-container">
                <div class="right-content">
                    <div class="content-card" v-for="(item, index) in panoramaPoint" :key="index">
                        <div style="width: 100%" @click="showPanorama(item)">
                            <div class="card-img">
                                <img :src="item.image_path" alt="" style="width: 100%; object-fit: contain" />
                            </div>
                            <div class="card-info">
                                <span class="card-info-title">{{ item.point_name }}</span>
                                <div class="card-content">
                                    <div class="card-item-title">
                                        <div>街道名称：</div>
                                        <div>最新图片编号：</div>
                                        <div>最新图片名称：</div>
                                        <div>最新拍摄时间：</div>
                                    </div>
                                    <div class="card-item-value">
                                        <div>{{ item.street }}</div>
                                        <div>{{ item.image_id }}</div>
                                        <div>{{ item.image_name }}</div>
                                        <div>{{ item.create_time }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="page">
                    <!--分页设置-->
                    <el-pagination
                        background
                        @size-change="handleSizeChange"
                        @current-change="handleCurrentChange"
                        :current-page="formInfo.page"
                        :page-sizes="[6, 12, 50, 100]"
                        :page-size="formInfo.limit"
                        layout="total, sizes, prev, pager, next, jumper"
                        :total="dataCount">
                    </el-pagination>
                </div>
            </div>
            <el-dialog
                class="img-dialog"
                :visible.sync="imgVisible"
                width="50%"
                :show-close="false"
                :close-on-click-modal="false"
                :modal-append-to-body="false">
                <template slot="title">
                    <div class="card-detail-title" style="display: flex; align-items: center; justify-content: space-between">
                        <div style="display: inline-block">
                            <span class="iconfont icon-xinzengtianjia" style="margin-right: 5px"></span>
                            <span class="title">全景预览</span>
                        </div>
                        <span class="el-icon-close" @click="imgVisible = false" style="cursor: pointer"></span>
                    </div>
                </template>
                <verifypannelViewer
                    v-if="imgVisible"
                    class="panoramanic-show"
                    :pointId="showPointID"
                    :currentPointObj="showPoint"
                    :updateSectorYaw="updateSectorYaw" />
            </el-dialog>
        </div>
    </div>
</template>

<script>
import { getPanoramaByGridApi, getRegionDataApi } from '@/api/commonApi';
import verifypannelViewer from '@/views/pattern-verifiy/patternMapOverview/verifypannelViewer.vue';

export default {
    name: 'panoramaImage',
    components: { verifypannelViewer },
    data() {
        return {
            expandedKeys: [], //初始展开的节点
            showPointID: '',
            showPoint: {},
            panoramaPoint: [], //全景点数据
            imgVisible: false,
            defaultProps: {
                children: 'children',
                label: 'label'
            },
            formInfo: {
                gridId: '',
                page: 1,
                limit: 6
            },
            dataCount: 0, //全景数量
            treeKeyword: '', //树搜索关键字
            treeData: [],
            subTitle: '',
            initYaw: 0,
            initPitch: 0,
            initHfov: 0
        };
    },
    watch: {
        treeKeyword: function (val) {
            this.$refs.tree.filter(val);
        },
        '$store.state.dataMenuList': function (newValue, oldValue) {
            this.findSubTitle(newValue);
        }
    },
    methods: {
        updateSectorYaw(dictValue) {
            this.initYaw = dictValue.currentYaw;
            this.initPitch = dictValue.currentPitch;
            this.initHfov = dictValue.currentHfov;
        },
        handleSizeChange(val) {
            // 改变每页展示的数据
            this.formInfo.limit = val;
            this.formInfo.page = 1;
            this.getPanorama();
        },
        // 改变页码
        handleCurrentChange(val) {
            this.formInfo.page = val;
            this.getPanorama();
        },
        //全景点所有的全景图片
        showPanorama(item) {
            this.imgVisible = true;
            this.showPoint = item;
            this.showPointID = item.point_id;
        },
        // 过滤树节点
        filterNode(value, data) {
            if (!value) return true;
            return data.label.indexOf(value) !== -1;
        },
        //设置树子节点样式
        renderContent(h, { node, data, store }) {
            const hasChildren = !node.isLeaf;
            // 获取子节点数量
            const childrenCount = hasChildren ? node.childNodes.length : 0;
            if (node.level === 1) {
                return (
                    <span class="custom-tree-node">
                        <span key="label" style="font-size:16px;color:white">
                            {node.label}
                        </span>
                    </span>
                );
            } else if (node.level === 2) {
                if (node.isLeaf) {
                    return (
                        <span class="custom-tree-node">
                            <span key="label" style="font-size:16px;color:white;padding-left:24px">
                                {node.label}
                                <span style="margin-left:4px;color:#f24b43">({childrenCount})</span>
                            </span>
                        </span>
                    );
                } else {
                    return (
                        <span class="custom-tree-node">
                            <span key="label" style="font-size:16px;color:white;">
                                {node.label}
                                <span style="margin-left:4px;color:#f24b43">({childrenCount})</span>
                            </span>
                        </span>
                    );
                }
            } else {
                return (
                    <span class="custom-tree-node" style="display:flex;align-items:center">
                        <i key="icon" class="el-icon-document" style="margin-right:8px;padding-left:20px"></i>
                        <span
                            key="label"
                            title={node.label}
                            style="font-size:14px;color:white;display:inline-block;width:230px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;">
                            {node.label}
                        </span>
                    </span>
                );
            }
        },
        //根据叶节点获取所有全景影像
        getPanoramaImage(data, node) {
            if (node.level === 3) {
                this.formInfo.page = 1;
                this.formInfo.gridId = data.value;
                this.getPanorama();
            }
        },
        //获取全景点数据
        getPanorama() {
            this.formInfo.pageIndex = this.formInfo.page;
            this.formInfo.pageSize = this.formInfo.limit;
            getPanoramaByGridApi(this.formInfo).then((res) => {
                if (res.code === 0) {
                    this.panoramaPoint = res.data;
                    this.dataCount = res.total;
                } else {
                    this.$message.error(res.msg);
                }
            });
        },
        //获取区域树状数据
        getRegionData() {
            getRegionDataApi().then((res) => {
                if (res.code === 0) {
                    this.treeData = res.data;
                    // 默认展开第一个节点并获取初始数据
                    this.$nextTick(() => {
                        const allNodes = this.$refs.tree.store.nodesMap;

                        const initNode = Object.values(allNodes).filter((item) => item.level === 3);
                        if (initNode.length > 0) {
                            this.expandedKeys = [initNode[0].data.label];
                            this.$refs.tree.setCurrentKey(initNode[0].data.label);
                            this.formInfo.gridId = initNode[0].data.value;
                            this.getPanorama();
                        }
                    });
                } else {
                    this.$message.error(res.msg);
                }
            });
        },
        findSubTitle(newValue) {
            const filteredItems = newValue.filter((item) => item.url === this.$route.path);
            this.subTitle = filteredItems.length > 0 ? filteredItems[0].name : null;
        }
    },
    mounted() {
        this.getRegionData();
        this.findSubTitle(this.$store.state.dataMenuList);
    },
    computed: {}
};
</script>

<style lang="scss" scoped>
.gt-right-content {
    @import '@/assets/css/table/new-common';
}

.gt-right-content {
    display: flex;
}

.se-container {
    position: relative;
    height: 100%;
    display: flex;
    flex-direction: column;
    background-color: #050e1f;
}

.left-content {
    width: 320px;
    height: calc(100% - 20px);
    position: relative;
    margin: 10px 0 10px 10px;
}

.right-container {
    width: calc(100% - 340px);
    overflow: auto;
}

.border {
    width: 10px;
    margin-right: 10px;
    height: 100%;
}

.tree-container ::v-deep(.is-leaf) {
    display: none;
}

.tree-container ::v-deep(.el-tree-node) {
    padding: 4px 0;
}

.tree-container ::v-deep(.el-tree-node__children) {
    padding-top: 2px;
}

.tree-container {
    height: calc(100% - 50px);
    overflow: auto;
}

.content-card {
    width: calc(33% - 18px);
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
    border-radius: 12px;
    position: relative;
    float: left;
    margin-right: 16px;
    margin-bottom: 16px;
    cursor: pointer;
    overflow: hidden;
    padding: 16px;
}

.card-info {
    overflow: clip;
    display: flex;
    flex-direction: column;
}

.card-content {
    display: flex;
    margin-top: 8px;
}

.card-info-title {
    font-size: 16px;
    color: #ffffff;
    padding: 8px 0;
    border-bottom: 1px solid #fff;
}

.card-item-title {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    font-size: 14px;
    color: #b3ccef;
}

.card-item-value {
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    font-size: 14px;
    color: #ffffff;
}

.right-content {
    height: calc(100% - 74px);
    overflow-y: auto;
    padding: 16px 16px 0 8px;
}

.content-card:hover {
    border-color: #1890ff;
}

::v-deep(.el-dialog) {
    height: 75%;
}

::v-deep(.el-dialog__header) {
    padding: 8px;
    background-color: #42b4f2;
    color: white;
}

::v-deep(.el-dialog__body) {
    padding: 0;
    height: calc(100% - 40px);
}

::v-deep(.panoramanic-show) {
    width: 100%;
}
</style>
