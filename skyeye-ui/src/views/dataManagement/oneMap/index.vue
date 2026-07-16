<template>
    <div class="se-container">
        <div class="left-content-map" v-show="showTree" style="height: 100%">
            <div class="title">
                <span class="tab-title">一张图</span>
                <el-button type="text" style="float: right" class="iconfont icon-shouqi" @click="showTree = !showTree"></el-button>
            </div>
            <div class="filter">
                <el-input placeholder="请输入关键字" v-model="keyword" style="width: 280px; margin-right: 10px"></el-input>
            </div>
            <div class="tree-container">
                <el-tree
                    :data="data"
                    :show-checkbox="true"
                    :render-content="renderContent"
                    :default-expand-all="true"
                    @check-change="loadOrDeleteMap"
                    ref="tree"
                    node-key="label"
                    :filter-node-method="filterNode"
                    :props="defaultProps"
                    :highlight-current="false"></el-tree>
            </div>
        </div>
        <div class="left-content-map" v-show="!showTree" style="height: 46px">
            <div class="title">
                <span class="tab-title">一张图</span>
                <el-button type="text" style="float: right" class="iconfont icon-zhankai" @click="showTree = !showTree"></el-button>
            </div>
        </div>
        <div class="right-content">
            <Map2dPanel
                v-show="currentMode === '2d'"
                ref="map2d"
                :tree-data="data"
                :selected-nodes="currentLeafNodes"
                :initial-center="center"
                :initial-zoom="zoom"
                :map-ready="oneMapReady"
                :panorama-point-list="panoramaPointList"
                :temp-point-list="tempPointList"
                :top-view-list="topViewList"
                @date-change="onDateChange"
                @zoom-change="onZoomChange" />
            <Map3dPanel
                v-show="currentMode === '3d'"
                ref="map3d"
                :tree-data="data"
                :initial-center="center"
                :initial-zoom="zoom"
                :map-ready="oneMapReady"
                :panorama-point-list="panoramaPointList"
                :temp-point-list="tempPointList"
                :top-view-list="topViewList"
                @zoom-change="onZoomChange" />
        </div>
        <div class="se-map-tool">
            <div class="mode-toggle">
                <div class="mode-btn" @click="modeMenuExpanded = !modeMenuExpanded">
                    {{ currentMode === '2d' ? '2D' : '3D' }}
                </div>
                <div class="mode-menu" v-show="modeMenuExpanded">
                    <div class="mode-option" :class="{ active: currentMode === '2d' }" @click="switchMode('2d')">2D</div>
                    <div class="mode-option" :class="{ active: currentMode === '3d' }" @click="switchMode('3d')">3D</div>
                </div>
            </div>
            <div class="zoom-num">{{ currentShowZoom }}</div>
            <div class="map-reset" @click="map_reset" title="地图复位"><i class="iconfont icon-quantu"></i></div>
        </div>
    </div>
</template>

<script>
import { getOneMapApi, getPanoramaPointByCountryApi, getTopViewDataApi, get3dtilesListApi } from '@/api/commonApi';
import Map2dPanel from '@/views/dataManagement/oneMap/components/Map2dPanel.vue';
import Map3dPanel from '@/views/dataManagement/oneMap/components/Map3dPanel.vue';
import { normalizeStaticResourceUrl } from '@/utils/staticResourceUrl';
import { isTempPanoramaPoint, mergeNanjingTestPanoramaPoint } from '@/views/dataManagement/oneMap/oneMapDebug';

const THREE_D_DATA_GROUP_LABEL = '三维数据';

function labelSuffixFromUrl(url) {
    if (!url) return '';
    const parts = String(url).replace(/\/$/, '').split('/');
    return parts[parts.length - 1] || '';
}

function map3dtilesItemToTreeNode(item, usedLabels) {
    let label = item.name || labelSuffixFromUrl(item.url) || '三维模型';
    if (usedLabels.has(label)) {
        label = `${label}_${labelSuffixFromUrl(item.url)}`;
    }
    usedLabels.add(label);
    return {
        label,
        service: normalizeStaticResourceUrl(item.url),
        center: JSON.stringify([item.latitude, item.longitude]),
        height: item.height != null ? item.height : 0,
        maximumScreenSpaceError: item.maximumScreenSpaceError != null ? item.maximumScreenSpaceError : 16,
        data_type: '3dtiles',
        source_type: '三维瓦片'
    };
}

function dedupeByLabel(nodes) {
    const seen = new Set();
    const result = [];
    (nodes || []).forEach((node) => {
        if (!node || !node.label || seen.has(node.label)) return;
        seen.add(node.label);
        result.push(node);
    });
    return result;
}

export default {
    name: 'oneMap',
    components: { Map2dPanel, Map3dPanel },
    data() {
        return {
            showTree: true,
            keyword: '',
            defaultProps: {
                children: 'children',
                label: 'label'
            },
            data: [
                { label: '基础地理数据', children: [] },
                { label: '资源调查数据', children: [] },
                { label: '低空业务数据', children: [] }
            ],
            currentLeafNodes: [],
            center: window.config.center,
            zoom: window.config.zoom,
            currentShowZoom: window.config.zoom,
            selectNodes: [],
            currentMode: '2d',
            modeMenuExpanded: false,
            oneMapReady: false,
            panoramaPointList: [],
            tempPointList: [],
            topViewList: [],
            threeDDataGroupInserted: false
        };
    },
    created() {
        /** 勿放入 data：Promise 被 observe 后会破坏 .then 链 */
        this._layerSyncChain = Promise.resolve();
        this._oneMap3DDirChildren = [];
    },
    watch: {
        keyword(val) {
            this.$refs.tree.filter(val);
        }
    },
    async mounted() {
        await this.fetchOneMapBundle({ time: '' });
        this._onNavigateMap = (e) => {
            const { lat, lng, polygon, address } = e.detail || {};
            if (lat == null || lng == null) return;
            const panel = this.getActivePanel();
            if (!panel) return;
            // 优先用 polygon fitBounds 自适应缩放
            if (this.currentMode === '3d' && panel.flyToRegion3D) {
                panel.flyToRegion3D(lat, lng, polygon);
            } else if (this.currentMode === '3d' && panel.flyTo3D) {
                panel.flyTo3D(lat, lng, 16);
            } else if (panel.flyToRegion) {
                panel.flyToRegion(lat, lng, polygon);
            } else if (panel.flyTo) {
                panel.flyTo(lat, lng, 16);
            }
        };
        this._onDrawRegion = (e) => {
            const { polygon, name, lat, lng, subRegions } = e.detail || {};
            if (!polygon || !polygon.length) return;
            const panel = this.getActivePanel();
            if (!panel || !panel.drawRegion) return;
            panel.drawRegion(polygon, name, lat, lng, subRegions);
        };
        window.addEventListener('navigate-map', this._onNavigateMap);
        window.addEventListener('draw-region', this._onDrawRegion);
    },
    beforeDestroy() {
        window.removeEventListener('navigate-map', this._onNavigateMap);
        window.removeEventListener('draw-region', this._onDrawRegion);
    },
    methods: {
        filterNode(value, data) {
            if (!value) return true;
            return data.label.indexOf(value) !== -1;
        },
        closeAllLayers() {
            this.$refs.tree.setCheckedNodes([]);
        },
        renderContent(h, { node }) {
            const hasChildren = !node.isLeaf;
            const childrenCount = hasChildren ? node.childNodes.length : 0;
            return (
                <span class="custom-tree-node" style="display:flex;align-items:center">
                    {node.isLeaf
                        ? [
                              <i key="icon" class="el-icon-document" style="margin-right:8px;padding-left:20px;color: #177DE4;"></i>,
                              <span
                                  key="label"
                                  title={node.label}
                                  style="font-size:14px;color:white;display:inline-block;width:230px;text-overflow:ellipsis;overflow:hidden;white-space:nowrap;">
                                  {node.label}
                              </span>
                          ]
                        : [
                              <i></i>,
                              <span key="label" style="font-size:16px;color:white;">
                                  {node.label}
                                  <span style="margin-left:4px;color:#ed3f14">({childrenCount})</span>
                              </span>
                          ]}
                </span>
            );
        },
        getActivePanel() {
            return this.currentMode === '3d' ? this.$refs.map3d : this.$refs.map2d;
        },
        syncZoomFromPanel() {
            const panel = this.getActivePanel();
            if (panel && panel.getZoom) {
                this.currentShowZoom = panel.getZoom();
            }
        },
        onZoomChange(zoom) {
            this.currentShowZoom = zoom;
        },
        loadOrDeleteMap() {
            const prev = this._layerSyncChain || Promise.resolve();
            this._layerSyncChain = prev
                .then(() => this._applyLayerSync())
                .catch((err) => {
                    return Promise.resolve();
                });
            return this._layerSyncChain;
        },
        async _applyLayerSync() {
            if (!this.$refs.tree) {
                return;
            }
            const leafNodes = this.$refs.tree.getCheckedNodes(true);
            const panel = this.getActivePanel();
            const prevCount = this.currentLeafNodes.length;

            if (!panel) {
                return;
            }

            if (this.currentMode === '3d') {
                const prev = this.currentLeafNodes;
                const addNodes = leafNodes.filter((node) => !prev.some((p) => p.label === node.label));
                const delNodes = prev.filter((node) => !leafNodes.some((p) => p.label === node.label));
                if (addNodes.length) await panel.addLayers3D(addNodes);
                if (delNodes.length) panel.removeLayers3D(delNodes);
            } else {
                await panel.syncLayers(leafNodes);
            }

            this.currentLeafNodes = leafNodes.slice();
        },
        hasTreeData() {
            return this.data.some((g) => g.children && g.children.length > 0);
        },
        getNestListCountFromTree() {
            const lowAltitude = this.data.find((item) => item.label === '低空业务数据');
            if (!lowAltitude || !lowAltitude.children) return 0;
            const nestNode = lowAltitude.children.find((i) => i.data_type === 'nest_location');
            return nestNode && nestNode.data ? nestNode.data.length : 0;
        },
        getDefaultCheckedNodes() {
            const defaultDisplayDataList = [];
            const lowAltitude = this.data.find((item) => item.label === '低空业务数据');
            if (lowAltitude && lowAltitude.children) {
                const panorama = lowAltitude.children.find((item) => item.data_type === 'panorama' || item.label === '全景点');
                const panoramaCoverage = lowAltitude.children.find(
                    (item) => item.data_type === 'panorama_coverage' || (item.label && item.label.includes('全景覆盖'))
                );
                const aerialPhoto = lowAltitude.children.find((item) => item.label === '航片');
                const d3Group = this.data.find((item) => item.label === THREE_D_DATA_GROUP_LABEL);
                if (d3Group && d3Group.children) {
                    d3Group.children.forEach((item) => {
                        if (item.data_type === '3dtiles') {
                            defaultDisplayDataList.push(item);
                        }
                    });
                }
                defaultDisplayDataList.push(panorama, panoramaCoverage, aerialPhoto);
            }
            this.data.forEach((group) => {
                (group.children || []).forEach((item) => {
                    if (item.isShow && item.isShow == 1) {
                        defaultDisplayDataList.push(item);
                    }
                });
            });
            const nodes = defaultDisplayDataList.filter(Boolean);

            return nodes;
        },
        async applyTreeCheck(nodes, reason) {
            if (!this.$refs.tree || !nodes || !nodes.length) {
                return;
            }

            this.$refs.tree.setCheckedNodes(nodes);
            await this.$nextTick();
            await this.loadOrDeleteMap();
        },
        async applyDefaultTreeCheck() {
            if (!this.$refs.tree) {
                return;
            }
            if (!this.hasTreeData()) {
                return;
            }
            await this.applyTreeCheck(this.getDefaultCheckedNodes(), 'default');
        },
        async switchMode(mode) {
            if (mode === this.currentMode) {
                this.modeMenuExpanded = false;
                return;
            }
            this.modeMenuExpanded = false;

            const fromPanel = this.getActivePanel();
            let savedCenter = null;
            let savedZoom = this.currentShowZoom;
            if (fromPanel && fromPanel.getViewState) {
                const vs = fromPanel.getViewState();
                if (vs) {
                    if (vs.center) savedCenter = vs.center;
                    if (vs.zoom != null) savedZoom = vs.zoom;
                }
            }
            if (this.currentMode === '2d' && this.$refs.map2d) {
                this.$refs.map2d.resetPanelUi();
                this.$refs.map2d.destroyMap();
            } else if (this.currentMode === '3d' && this.$refs.map3d) {
                this.$refs.map3d.resetPanelUi();
                this.$refs.map3d.destroyMap();
            }

            this.currentMode = mode;
            await this.$nextTick();
            await new Promise((resolve) => requestAnimationFrame(resolve));

            const toPanel = this.getActivePanel();
            if (!toPanel) return;

            if (savedCenter) {
                toPanel.setViewState({ center: savedCenter, zoom: savedZoom });
            }

            if (mode === '2d') {
                this.removeThreeDDataGroup();
                await toPanel.initMap2d();
                this.currentLeafNodes = [];
                await this.$nextTick();
                this.applyDefaultTreeCheck();
                if (toPanel.invalidateMapSize) {
                    toPanel.invalidateMapSize();
                }
            } else {
                await toPanel.initMap3D();
                await this.fetchAndInsert3dtilesGroup();
                this.currentLeafNodes = [];
                this.$nextTick(() => {
                    if (this.$refs.tree) {
                        this.$refs.tree.setCheckedNodes([]);
                    }
                });
            }
            this.syncZoomFromPanel();
        },
        map_reset() {
            const panel = this.getActivePanel();
            if (panel && panel.flyToHome) {
                panel.flyToHome();
            }
            this.syncZoomFromPanel();
        },
        onDateChange(time) {
            this.selectNodes = this.$refs.tree.getCheckedNodes(true);
            this.fetchOneMapBundle({ time }, { restoreChecked: true });
        },
        applyPanoramaListsFromResponse(data) {
            const temp = [];
            const panorama = [];
            (data || []).forEach((item) => {
                if (isTempPanoramaPoint(item)) {
                    temp.push(item);
                } else {
                    panorama.push(item);
                }
            });
            this.tempPointList = temp;
            this.panoramaPointList = mergeNanjingTestPanoramaPoint(panorama);
        },
        removeThreeDDataGroup() {
            const groupIndex = this.data.findIndex((g) => g.label === THREE_D_DATA_GROUP_LABEL);
            if (groupIndex === -1) {
                this.threeDDataGroupInserted = false;
                return;
            }
            const groupLabels = new Set((this.data[groupIndex].children || []).map((c) => c.label));
            this.data.splice(groupIndex, 1);
            this.threeDDataGroupInserted = false;
            this.currentLeafNodes = this.currentLeafNodes.filter((n) => !groupLabels.has(n.label));
            if (this.$refs.tree) {
                const checked = this.$refs.tree.getCheckedNodes(true).filter((n) => !groupLabels.has(n.label));
                this.$refs.tree.setCheckedNodes(checked);
                this.$nextTick(() => this.loadOrDeleteMap());
            }
        },
        async fetchAndInsert3dtilesGroup() {
            try {
                const res = await get3dtilesListApi();
                if (res.code !== 0) {
                    this.$message.error(res.msg || '获取三维数据失败');
                    return;
                }
                const dirChildren = (this._oneMap3DDirChildren || []).filter((n) => n.data_type !== '3dtiles');
                const usedLabels = new Set(dirChildren.map((n) => n.label));
                const apiChildren = (res.data || []).map((item) => map3dtilesItemToTreeNode(item, usedLabels));
                const merged = dedupeByLabel([...dirChildren, ...apiChildren]).map((node) =>
                    node.service ? { ...node, service: normalizeStaticResourceUrl(node.service) } : node
                );

                this.removeThreeDDataGroup();
                if (merged.length === 0) return;

                this.data.push({ label: THREE_D_DATA_GROUP_LABEL, children: merged });
                this.threeDDataGroupInserted = true;
                await this.$nextTick();
            } catch (err) {
                this.$message.error('获取三维数据失败');
            }
        },
        async fetchOneMapBundle(para, options = {}) {
            const { restoreChecked = false } = options;
            try {
                const [oneMapRes, panoramaRes, topViewRes, d3TilesRes] = await Promise.all([
                    getOneMapApi(para),
                    getPanoramaPointByCountryApi(para),
                    getTopViewDataApi(para),
                    get3dtilesListApi()
                ]);

                if (oneMapRes.code !== 0) {
                    this.$message.error('获取地图服务数据失败！');
                    return;
                }

                this.center = [oneMapRes.data.latitude, oneMapRes.data.longitude];
                this.data.forEach((item) => {
                    if (item.label === '基础地理数据') {
                        item.children = oneMapRes.data['基础地理数据'].children;
                    } else if (item.label === '资源调查数据') {
                        item.children = oneMapRes.data['资源调查数据'].children;
                    } else if (item.label === '低空业务数据') {
                        item.children = oneMapRes.data['低空业务数据'].children;
                    }
                });
                const oneMap3DGroup = oneMapRes.data[THREE_D_DATA_GROUP_LABEL];
                this._oneMap3DDirChildren = oneMap3DGroup && oneMap3DGroup.children ? oneMap3DGroup.children.slice() : [];
                // 合并 3DTiles API 返回的三维瓦片数据
                if (d3TilesRes && d3TilesRes.code === 0 && d3TilesRes.data && d3TilesRes.data.length) {
                    const usedLabels = new Set(this._oneMap3DDirChildren.map((n) => n.label));
                    const apiChildren = d3TilesRes.data.map((item) => map3dtilesItemToTreeNode(item, usedLabels));
                    this._oneMap3DDirChildren = dedupeByLabel([
                        ...this._oneMap3DDirChildren.filter((n) => n.data_type !== '3dtiles'),
                        ...apiChildren
                    ]);
                }
                const targetIndex = this.data[0].children.findIndex((item) => item.source_type === '影像服务');
                if (targetIndex !== -1) {
                    const targetTask = this.data[0].children.splice(targetIndex, 1)[0];
                    this.data[0].children.unshift(targetTask);
                }

                if (panoramaRes.code === 0) {
                    this.applyPanoramaListsFromResponse(panoramaRes.data);
                } else {
                    this.tempPointList = [];
                    this.panoramaPointList = [];
                    this.$message.error(panoramaRes.msg || '获取全景点位失败');
                }

                if (topViewRes.code === 0) {
                    this.topViewList = topViewRes.data || [];
                } else {
                    this.topViewList = [];
                    this.$message.error(topViewRes.msg || '获取俯视图数据失败');
                }

                this.oneMapReady = true;
                await this.$nextTick();
                if (this.currentMode === '2d' && this.$refs.map2d && this.$refs.map2d.waitForMapReady) {
                    await this.$refs.map2d.waitForMapReady();
                }
                if (this.hasTreeData()) {
                    if (para.time === '' && !restoreChecked) {
                        await this.applyTreeCheck(this.getDefaultCheckedNodes(), 'initial');
                    } else if (restoreChecked) {
                        await this.applyTreeCheck(this.selectNodes, 'restore');
                    }
                } else {
                }
            } catch (err) {
                this.$message.error('获取一张图数据失败！');
            }
        }
    }
};
</script>

<style lang="scss" scoped>
.se-container {
    height: 100%;
    display: flex;
    position: relative;
}

.filter {
    padding: 10px 0 10px 8px;
}

.left-content-map ::v-deep(.el-input .el-input__inner::placeholder) {
    color: gray;
}

.left-content-map {
    flex-shrink: 0;
}

.right-content {
    flex: 1;
    min-width: 0;
    height: 100%;
    position: relative;
    overflow: hidden;
}

.tree-container ::v-deep(.el-tree) {
    background-color: rgba(255, 255, 255, 0);
}

.tree-container ::v-deep(.el-checkbox) {
    position: absolute;
    right: 0;
}

.tree-container ::v-deep(.is-leaf) {
    display: none;
}

.tree-container ::v-deep(.el-tree-node) {
    padding: 4px 0;
}

.tree-container ::v-deep(.el-tree-node__content):hover,
.tree-container ::v-deep(.el-tree-node.is-current > .el-tree-node__content) {
    background-color: rgba(255, 255, 255, 0.3) !important;
}

.tree-container ::v-deep(.el-tree-node__children) {
    padding-top: 2px;
}

.tree-container {
    height: calc(100% - 100px);
    overflow-y: auto;
    padding: 0 8px;
}

.se-map-tool {
    position: absolute;
    right: 0;
    bottom: 0;
    z-index: 1000;
}

.zoom-num {
    position: absolute;
    z-index: 999;
    right: 10px;
    bottom: 45px;
    height: 27px;
    width: 27px;
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-weight: bold;
    background: rgba(0, 0, 0, 0.3);
}

.map-reset {
    position: absolute;
    z-index: 999;
    right: 10px;
    bottom: 10px;
    width: 27px;
    height: 27px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
}

.map-reset .iconfont {
    text-align: center;
    width: 100%;
    color: #fff;
}

.mode-toggle {
    position: absolute;
    z-index: 1000;
    right: 44px;
    bottom: 10px;
    display: flex;
    flex-direction: row-reverse;
}

.mode-btn {
    width: 27px;
    height: 27px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 10px;
    font-weight: bold;
    cursor: pointer;
    user-select: none;
    z-index: 1;
}

.mode-btn:hover {
    background: rgba(0, 0, 0, 0.5);
}

.mode-menu {
    display: flex;
    flex-direction: row;
    margin-right: 4px;
}

.mode-option {
    width: 27px;
    height: 27px;
    background: rgba(0, 0, 0, 0.3);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 10px;
    font-weight: bold;
    cursor: pointer;
    user-select: none;
    margin-right: 2px;
}

.mode-option:hover {
    background: rgba(0, 0, 0, 0.5);
}

.mode-option.active {
    background: rgba(66, 180, 242, 0.6);
}
</style>
