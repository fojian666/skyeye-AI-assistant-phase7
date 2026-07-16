<template>
    <div
        class="all-polygon-container"
        v-if="isLoaded"
        v-loading="loading"
        element-loading-text="图斑生成中，请等候……"
        element-loading-spinner="el-icon-loading"
        element-loading-background="rgba(255,255,255,0.5)">
        <div class="details-left">
            <div class="details-left-title">
                <span class="title-text">
                    <i class="iconfont icon-zhuzhuangtu"></i>
                    <span>地类变化</span>
                </span>
                <span class="back-btn" @click="goBack">
                    <i class="iconfont icon-fanhui"></i>
                    <span>返回</span>
                </span>
            </div>
            <div class="details-left-item">
                <!--                <div class="header-border"></div>-->
                <div class="header-content">
                    <div class="header-item">
                        <a-divider class="divider" />
                        <span>总体分析</span>
                        <a-divider class="divider" />
                    </div>
                    <div class="header-item">
                        {{ mapData.county }}{{ mapData.nextImage.appendTime }}和{{ mapData.prevImage.appendTime }}影像变化检测结果，共计{{
                            mapData.count
                        }}处变化图斑，分布于
                        <template v-for="(item, index) in countyData">
                            <span>{{ item.county }}</span>
                            <span v-if="index !== countyData.length - 1">、</span>
                        </template>
                        {{ countyData.length }}地区
                        <span class="text-bold" @click="openOnePolygon">[查看]</span>
                    </div>
                    <a-divider class="divider1" dashed></a-divider>
                    <div class="header-item">
                        <span>{{ mapData.count }}处图斑变化</span>
                        <span>></span>
                        <span>|</span>
                        <span>{{ countyData.length }}个行政区</span>
                        <span>></span>
                    </div>
                </div>
            </div>
            <div class="details-left-item table-region">
                <div class="item-title regional-analysis">
                    <div>
                        <span>|</span>
                        <span>区域分析</span>
                    </div>
                    <el-select v-model="selectValue" @change="changeSelect" placeholder="请选择">
                        <el-option v-for="item in selectOptions" :key="item.value" :label="item.label" :value="item.value"> </el-option>
                    </el-select>
                </div>
                <a-table
                    class="my-table"
                    :columns="tableData.tableRegion.columns"
                    :dataSource="tableData.tableRegion.dataSource"
                    bordered
                    :pagination="false"
                    :customRow="rowClick">
                    <template slot="operation" slot-scope="record">
                        <a-button type="primary" size="small" @click="openOnePolygon(record)"> 查看 </a-button>
                    </template>
                </a-table>
            </div>
            <div class="details-left-item table-type">
                <div class="item-title">
                    <span>|</span>
                    <span>类型分析</span>
                </div>
                <a-table
                    class="my-table"
                    :sticky="true"
                    :columns="tableData.tableType.columns"
                    :dataSource="tableData.tableType.dataSource"
                    bordered
                    :customRow="typeRowClick"
                    :pagination="false"></a-table>
            </div>
        </div>
        <div
            class="details-right"
            id="details-map"
            v-loading="shpLoading"
            element-loading-text="推送shp中，请等候……"
            element-loading-spinner="el-icon-loading"
            element-loading-background="rgba(255,255,255,0.5)">
            <div class="ai-banner-title title-prev" ref="prev">前景时间：{{ mapData.prevImage.appendTime }}</div>
            <div class="ai-banner-title title-next" ref="next">后景时间：{{ mapData.nextImage.appendTime }}</div>
        </div>

        <ul :class="[serviceType === 'iserver' ? 'toolbox' : 'arcgis-toolbox']">
            <li>
                <span class="icon iconfont icon-dian" title="查经纬度" @click="drawPoint"></span>
            </li>
            <li>
                <span class="icon iconfont icon-icon-line-graph" title="测距" @click="measureLength" id="distance"></span>
            </li>
            <li>
                <span class="icon iconfont icon-duobianxing" title="测面积" @click="startDrawPolygon" id="area"></span>
            </li>
            <li>
                <span class="icon iconfont icon-qingchu" title="清除" @click="clearDraw" id="clear"></span>
            </li>
        </ul>
        <div class="tool-container">
            <div class="tool-item" @click="flyToFull">
                <span>全图</span>
            </div>
            <div class="division">|</div>
            <div class="tool-item" @click="layerDialog">
                <span>图层</span>
            </div>
            <!--            <div class="division">|</div>-->
            <!--            <div class="tool-item" @click="generateReport">-->
            <!--                <span>生成报告</span>-->
            <!--            </div>-->
            <!--            <div class="division">|</div>-->
            <!--            <div class="tool-item" @click="pushShp">-->
            <!--                <span>推送结果</span>-->
            <!--            </div>-->
        </div>
        <div class="layer-dialog" v-show="flag">
            <div class="container-title">请选择叠加图层</div>
            <a-checkbox @change="selectLayer($event, item)" v-for="item in layerOptions" :key="item.label">
                {{ item.label }}
            </a-checkbox>
        </div>
        <DownloadOption v-show="reportFlag" @confirm="reportGenerator" @close="close" :treeDataList="mapData"></DownloadOption>
    </div>
</template>

<script>
import DownloadOption from '@/components/download-option';
import '@/plugins/leaflet-side-by-side.min.js';
import { calcResolution, setSpotColor, drawPoint, measureDistance, measureArea, clearGraphical } from '@/utils/utils';
import { TiledMapLayer, FeatureService, ImageTileLayer, GetFeaturesBySQLParameters } from '@supermap/iclient-leaflet';
import { getDetailResultApi, getOneMapApi } from '@/api/commonApi';

//表格列的配置
const columnsRegion = [
    {
        title: '序号',
        dataIndex: 'key',
        key: 'key',
        width: '4rem',
        align: 'center'
    },
    {
        title: '行政区',
        dataIndex: 'county',
        key: 'county',
        align: 'center'
    },
    {
        title: '变化数量处',
        dataIndex: 'countyCount',
        key: 'countyCount',
        align: 'center'
    },
    {
        title: '操作',
        scopedSlots: { customRender: 'operation' },
        align: 'center'
    }
];
const columnsType = [
    {
        title: '序号',
        dataIndex: 'key',
        key: 'key',
        width: '4rem',
        align: 'center'
    },
    {
        title: '变化前',
        dataIndex: 'BHQDL',
        key: 'BHQDL',
        align: 'center'
    },
    {
        title: '变化后',
        dataIndex: 'BHHDL',
        key: 'BHHDL',
        align: 'center'
    },
    {
        title: '数量',
        dataIndex: 'num',
        key: 'num',
        align: 'center'
    }
];
let layer = [];
export default {
    name: 'LandChangeDetails',
    components: {
        DownloadOption
    },
    data() {
        return {
            map: null, //地图容器
            geojson: {},
            mapData: null, //地图数据
            isLoaded: false, //后台请求状态
            coordinate_system: '',
            desc: '',
            proj: '',
            tableData: {
                tableRegion: {
                    columns: Object.freeze(columnsRegion),
                    dataSource: []
                },
                tableType: {
                    columns: Object.freeze(columnsType),
                    dataSource: []
                }
            }, //表格数据
            listData: [], //查看页列表数据
            reportFlag: false,
            flag: false,
            layerOptions: [],
            zoom: 16,
            typeTableData: [],
            rowClick: (record) => ({
                // 事件
                on: {
                    click: () => {
                        // 点击改行时要做的事情
                        this.changePolygon(record);
                    }
                }
            }),
            typeRowClick: (record) => ({
                // 事件
                on: {
                    click: () => {
                        // 点击改行时要做的事情
                        this.typeAnalysis(record);
                    }
                }
            }),
            center: null,
            crs: {},
            view: null,
            featureLayer: null,
            polygonGraphicArr: null,
            serviceType: '',
            loading: false,
            shpLoading: false,
            selectOptions: [],
            selectValue: '',
            countyData: [],
            bhqdl: [],
            bhhdl: [],
            bhqdlOptions: [],
            bhhdlOptions: [],
            data: [
                { label: '基础地理数据', children: [] },
                { label: '资源调查数据', children: [] },
                { label: '低空业务数据', children: [] }
            ]
        };
    },
    async mounted() {
        await this.getDetailsData();
        await this.getSourceRelatedBussiness();
    },
    async created() {},
    methods: {
        //查看
        openOnePolygon(record) {
            const copyData = JSON.parse(JSON.stringify(this.listData));
            if (record.county) {
                this.listData = copyData.filter((item) => {
                    return item.title.indexOf(record.county) !== -1;
                });
            }
            let component = {
                name: 'OnePolygon',
                info: this.listData[0],
                listData: this.listData,
                reginOptions: this.selectOptions,
                bhqdlOptions: this.bhqdlOptions,
                bhhdlOptions: this.bhhdlOptions,
                defaultRegion: this.selectValue,
                task_id: this.$route.query.id
            };
            this.$router.push({
                path: '/intelligent/land-change/land-change-details/spot-view',
                query: { component }
            });
        },
        seePolygon(smid) {
            if (this.mapData.dataPath.includes('arcgis')) {
                this.$router.push({
                    path: '/intelligent/land-change/land-change-details/spot-view',
                    query: {
                        data_path: this.mapData.dataPath,
                        prev_url: this.mapData.prevImage.url,
                        next_url: this.mapData.nextImage.url,
                        sourceCounty: this.mapData.sourceCountyData,
                        image1: this.mapData.prevImage,
                        image2: this.mapData.nextImage,
                        task_id: this.$route.query.id
                    }
                });
            } else {
                let component = {
                    name: 'OnePolygon',
                    info: this.listData[0],
                    listData: this.listData,
                    reginOptions: this.selectOptions,
                    bhqdlOptions: this.bhqdlOptions,
                    bhhdlOptions: this.bhhdlOptions,
                    defaultRegion: this.selectValue,
                    task_id: this.$route.query.id,
                    smid: smid
                };
                this.$router.push({
                    path: '/intelligent/land-change/land-change-details/spot-view',
                    query: { component }
                });
            }
        },
        //初始化地图
        initSuperMap() {
            this.axios
                .get(
                    this.mapData.prevImage.url + `/collections/${this.mapData.prevImage.collectId}/items/${this.mapData.prevImage.tifId}` + '.json',
                    { withCredentials: false }
                )
                .then((res) => {
                    const serveData = res.data;
                    // const minX = serveData.bounds.left.toFixed(2);
                    // const minY = serveData.bounds.bottom.toFixed(2);
                    // const maxX = serveData.bounds.right.toFixed(2);
                    // const maxY = serveData.bounds.top.toFixed(2);
                    const bbox = serveData.properties['proj:bbox']; // 获取bbox
                    const minX = bbox[0].toFixed(2);
                    const minY = bbox[1].toFixed(2);
                    const maxX = bbox[2].toFixed(2);
                    const maxY = bbox[3].toFixed(2);
                    let transCenter = {};
                    if (this.coordinate_system === '4326' || this.coordinate_system === '4490') {
                        this.crs = L.CRS.EPSG4326;
                        this.center = eval(this.center);
                    } else if (this.coordinate_system === '3857') {
                        this.crs = L.Proj.CRS('EPSG:3857', {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)]
                        });
                        transCenter = this.crs.unproject(
                            L.point((parseFloat(minX) + parseFloat(maxX)) / 2, (parseFloat(maxY) + parseFloat(minY)) / 2)
                        );
                        this.center = [transCenter.lat, transCenter.lng];
                    } else {
                        const EPSG = 'EPSG:' + this.coordinate_system;
                        proj4.defs(EPSG, this.proj);
                        this.crs = L.Proj.CRS(EPSG, {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)]
                        });
                        transCenter = this.crs.unproject(
                            L.point((parseFloat(minX) + parseFloat(maxX)) / 2, (parseFloat(maxY) + parseFloat(minY)) / 2)
                        );
                        this.center = [transCenter.lat, transCenter.lng];
                    }

                    // 创建地图容器
                    this.map = L.map('details-map', {
                        crs: this.crs,
                        maxZoom: 23,
                        minZoom: 10,
                        zoom: this.zoom,
                        attributionControl: false,
                        logoControl: false,
                        trackResize: false
                    });
                    // 将图层添加到地图容器
                    // let leftLayer = L.supermap.tiledMapLayer(this.mapData.prev_image.url, {noWrap: true}).addTo(this.map);
                    // // 将图层添加到地图容器
                    // let rightLayer = L.supermap.tiledMapLayer(this.mapData.next_image.url, {noWrap: true}).addTo(this.map);
                    let leftLayer = new ImageTileLayer(this.mapData.prevImage.url, {
                        collectionId: this.mapData.prevImage.collectId,
                        names: [this.mapData.prevImage.tifName],
                        maxZoom: 24 //设置最大级别
                    }).addTo(this.map);
                    let rightLayer = new ImageTileLayer(this.mapData.nextImage.url, {
                        collectionId: this.mapData.nextImage.collectId,
                        names: [this.mapData.nextImage.tifName],
                        maxZoom: 24 //设置最大级别
                    }).addTo(this.map);
                    this.map.setView(this.center, 16);
                    let sideBySideControl = L.control.sideBySide(leftLayer, rightLayer).addTo(this.map);
                    L.geoJSON(this.mapData.geojson, {
                        coordsToLatLng: (coords) => {
                            return this.crs.unproject(L.point(coords[0], coords[1]));
                        },
                        style: () => {
                            return { fillColor: 'transparent', color: 'red' };
                        },
                        onEachFeature: function (feature, layer) {
                            layer.bindPopup(
                                "ID: <a onclick='seePolygon(" +
                                    feature.properties.SMID +
                                    ")'>" +
                                    feature.properties.SMID +
                                    '</a><br>行政区:' +
                                    feature.properties.XZQ +
                                    '<br>经度:' +
                                    feature.properties.ZXDX +
                                    '<br>纬度:' +
                                    feature.properties.ZXDY +
                                    '<br>变化前地类::' +
                                    feature.properties.BHQDL +
                                    '<br>变化后地类::' +
                                    feature.properties.BHHDL
                            );
                        }
                    }).addTo(this.map);
                    //监听卷帘移动事件，改变左右影像标题位置
                    // sideBySideControl.on('dividermove', e => {
                    //   this.$refs.prev.setAttribute('style', `left:${e.x - 10}px`)
                    //   this.$refs.next.setAttribute('style', `left:${e.x + 10}px`)
                    // })
                });
        },
        // 画点，显示经纬度
        drawPoint() {
            if (this.serviceType === 'iserver') {
                drawPoint(this.map);
            } else {
                this.view.on('click', (e) => {
                    const lat = Math.round(e.mapPoint.latitude * 1000) / 1000;
                    const lon = Math.round(e.mapPoint.longitude * 1000) / 1000;

                    this.view.popup.open({
                        title: '经纬度: [' + lon + ', ' + lat + ']',
                        location: e.mapPoint
                    });
                });
            }
        },
        //画线，测量距离
        measureLength() {
            if (this.serviceType === 'iserver') {
                measureDistance(this.map);
            }
        },
        // 画面，测量面积
        startDrawPolygon() {
            if (this.serviceType === 'iserver') {
                measureArea(this.map);
            }
        },
        clearDraw() {
            if (this.serviceType === 'iserver') {
                clearGraphical(this.map);
            }
        },
        // 对数组中的项去重，并统计每一项的个数
        unique(arr) {
            let hash = [];
            for (let i = 0; i < arr.length; i++) {
                for (let j = i + 1; j < arr.length; j++) {
                    if (arr[i].BHHDL === arr[j].BHHDL && arr[i].BHQDL === arr[j].BHQDL && arr[i].XZQ === arr[j].XZQ) {
                        ++i;
                        j = i;
                    }
                }
                arr[i].num = 0;
                hash.push(arr[i]);
            }
            hash.forEach((item, index) => {
                arr.forEach((item1) => {
                    if (item.BHHDL === item1.BHHDL && item.BHQDL === item1.BHQDL && item.XZQ === item1.XZQ) {
                        item.num++;
                    }
                });
            });
            return hash;
        },

        unique3(arr) {
            let hash = [];
            for (let i = 0; i < arr.length; i++) {
                for (let j = i + 1; j < arr.length; j++) {
                    if (arr[i].value === arr[j].value && arr[i].label === arr[j].label) {
                        arr.splice(j, 1);
                        j--;
                    }
                }
            }
            return arr;
        },
        //回返上个页面
        goBack() {
            this.$router.push('/intelligent/land-change');
        },
        //全图
        flyToFull() {
            if (this.mapData.dataPath.includes('arcgis')) {
                // 设置地图视图的显示中心和缩放级别
                this.view.goTo({
                    center: [118.69, 31.94],
                    zoom: this.zoom
                });
            } else {
                this.map.flyTo(this.center, 10);
            }
        },

        generateReport() {
            this.reportFlag = !this.reportFlag;
        },
        pushShp() {
            this.shpLoading = true;
            let params = new URLSearchParams();
            params.append('task_id', this.$route.query.id);
            this.axios.post(config.BASE_URL + 'common/upload_path', params).then((res) => {
                if (res.data.error !== 0) return this.$message.warning(res.data.msg);
                this.shpLoading = false;
                this.$message.success(res.data.msg);
            });
        },
        close() {
            this.reportFlag = false;
        },
        reportGenerator(optionList) {
            this.reportFlag = false;
            this.$message.success('开始生成报告！');
            let params = new URLSearchParams();
            params.append('task_id', this.$route.query.id);
            params.append('county', optionList);
            this.axios(config.BASE_URL + 'common/report_generator', { params })
                .then((res) => {
                    if (!res.data.status) {
                        return this.$message.warning(res.data.msg);
                    }
                    this.$message.success(res.data.msg);
                    //报告生成自动打开报告
                    window.open(config.BASE_URL + 'static/docx/' + res.data.filename, '_blank');
                })
                .catch((error) => {
                    this.$message.warning(error.response.data.msg);
                });
        },
        layerDialog() {
            if (this.layerOptions.length === 0) return this.$message.warning('没有叠加的图层！');
            this.flag = !this.flag;
        },
        async selectLayer(e, item) {
            let layerInfo = {};
            let checked = e.target.checked;
            if (checked) {
                let newLayer = null;
                if (item.datasourceName && item.datasetsName) {
                    newLayer = await this.getVectorData(item);
                } else {
                    newLayer = new TiledMapLayer(item.service).addTo(this.map);
                }
                layerInfo = {
                    layer: newLayer,
                    name: item.label
                };
                layer.push(layerInfo);
            } else {
                layer.forEach((i, index) => {
                    if (item.label == i.name) {
                        this.map.removeLayer(i.layer);
                        layer.splice(index, 1);
                    }
                });
            }
        },
        // 获取每一个行政区内图斑的SMID
        getSMID() {
            let geojsonURL =
                this.mapData.dataPath +
                '/datasources/' +
                this.mapData.datasourceName +
                '/datasets/' +
                this.mapData.datasetsName +
                '/features.geojson?fromIndex=0&toIndex=' +
                this.mapData.count;
            this.axios(geojsonURL, { withCredentials: false }).then((res) => {
                res.data.features.forEach((item) => {
                    this.tableData.tableRegion.dataSource.forEach((item1) => {
                        if (item1.county === item.properties.XZQ) {
                            item1.SMID = item.properties.SMID;
                        }
                    });
                });
            });
        },
        // 图斑高亮
        spotHighlight(record, zoom) {
            // 获取在给定图层的视图上创建的图层
            this.view.whenLayerView(this.featureLayer).then((layerView) => {
                const query = this.featureLayer.createQuery(); // 创建查询参数对象
                let FID = '';
                for (let i = 0; i < record.IDs.length; i++) {
                    if (i === record.IDs.length - 1) {
                        FID += 'FID=' + record.IDs[i];
                    } else {
                        FID += 'FID=' + record.IDs[i] + ' OR ';
                    }
                }
                query.where = FID; // 设置查询条件
                // 对要素服务执行查询
                this.featureLayer.queryFeatures(query).then((res) => {
                    if (this.polygonGraphicArr) {
                        this.view.graphics.removeMany(this.polygonGraphicArr); // 移除高亮图层
                    }
                    const color = [42, 194, 231];
                    this.polygonGraphicArr = setSpotColor(res.features, color, color, 0, 2);
                    this.view.graphics.addMany(this.polygonGraphicArr); // 将高亮图层添加到图层集合
                    const lat = res.features[0].geometry.rings[0][0][0];
                    const lng = res.features[0].geometry.rings[0][0][1];
                    // 设置地图视图的显示中心和缩放级别
                    this.view.goTo({
                        center: [lat, lng],
                        zoom: zoom
                    });
                });
            });
        },
        changePolygon(record) {
            this.tableData.tableType.dataSource = this.typeTableData.filter((item) => {
                return record.county === item.XZQ;
            });
            if (this.mapData.dataPath && this.mapData.dataPath.includes('arcgis')) {
                this.spotHighlight(record, 11);
            } else {
                this.map.removeLayer(this.geojson);
                // 创建sql查询参数对象
                let sqlParam = new SuperMap.GetFeaturesByIDsParameters({
                    queryParameter: {
                        attributeFilter: `XZQ='${record.county}'`
                    },
                    datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                    toIndex: -1
                });
                // 去指定的图层用sql查询参数执行查询
                new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                    let center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0]);
                    this.map.setView([center[0], center[1]], this.zoom);
                    this.geojson = L.geoJSON(serverResult.result.features, {
                        style: () => {
                            return { color: '#2AC2E7', fillColor: 'transparent' };
                        },
                        onEachFeature: function (feature, layer) {
                            layer.bindPopup(
                                "ID: <a onclick='seePolygon(" +
                                    feature.properties.SMID +
                                    ")'>" +
                                    feature.properties.SMID +
                                    '</a><br>行政区:' +
                                    feature.properties.XZQ +
                                    '<br>经度:' +
                                    feature.properties.ZXDX +
                                    '<br>纬度:' +
                                    feature.properties.ZXDY +
                                    '<br>变化前地类::' +
                                    feature.properties.BHQDL +
                                    '<br>变化后地类::' +
                                    feature.properties.BHHDL
                            );
                        }
                    });
                    this.geojson.addTo(this.map);
                });
            }
        },
        getCenter(arr) {
            let center = [];
            let x = 0,
                y = 0;
            arr.forEach((i) => {
                x += i[0];
                y += i[1];
            });
            center.push(y / arr.length);
            center.push(x / arr.length);
            return center;
        },
        typeAnalysis(record) {
            this.map.removeLayer(this.geojson);
            let idsParam = new SuperMap.GetFeaturesByIDsParameters({
                IDs: record.IDs,
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesByIDs(idsParam, (serverResult) => {
                let center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0]);
                const transCenter1 = this.crs.unproject(L.point(center[1], center[0]));
                this.map.setZoom(12);
                this.geojson = L.geoJSON(serverResult.result.features, {
                    coordsToLatLng: (coords) => {
                        return this.crs.unproject(L.point(coords[0], coords[1]));
                    },
                    style: () => {
                        return { color: '#2AC2E7', fillColor: 'transparent' };
                    },
                    onEachFeature: function (feature, layer) {
                        layer.bindPopup(
                            "ID: <a onclick='seePolygon(" +
                                feature.properties.SMID +
                                ")'>" +
                                feature.properties.SMID +
                                '</a><br>行政区:' +
                                feature.properties.XZQ +
                                '<br>经度:' +
                                feature.properties.ZXDX +
                                '<br>纬度:' +
                                feature.properties.ZXDY +
                                '<br>变化前地类::' +
                                feature.properties.BHQDL +
                                '<br>变化后地类::' +
                                feature.properties.BHHDL
                        );
                    }
                });
                this.geojson.addTo(this.map);
            });
        },
        changeSelect(value) {
            const currentTableData = this.countyData.filter((item) => {
                return item.county == value;
            });
            let newItem = Object.assign(currentTableData[0], { key: 1 });
            this.tableData.tableRegion.dataSource = [newItem];
        },
        async getSourceRelatedBussiness() {
            getOneMapApi({ time: '' }).then((res) => {
                if (res.code === 0) {
                    this.data.forEach((item) => {
                        if (item.label === '资源调查数据') {
                            this.layerOptions = res.data['资源调查数据'].children;
                        }
                    });
                }
            });
        },

        async getVectorData(node) {
            try {
                var sqlParam = new GetFeaturesBySQLParameters({
                    queryParameter: {
                        name: `${node.datasets_name}@${node.datasource_name}`,
                        attributeFilter: '1=1'
                    },
                    datasetNames: [`${node.datasource_name}:${node.datasets_name}`]
                });
                const vectorData = [];
                const featureService = await new FeatureService(node.service);
                const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
                serviceResult.features.features.forEach((item) => {
                    vectorData.push(item);
                });
                if (vectorData.length > 0) {
                    const geojsonFeature = {
                        type: 'FeatureCollection',
                        features: vectorData
                    };
                    const layer = L.geoJSON(geojsonFeature, {
                        style: {
                            color: 'red',
                            weight: 2,
                            opacity: 1,
                            fillColor: '#ffeb3b',
                            fillOpacity: 0
                        }
                    });
                    return layer;
                }
            } catch (error) {
                this.$message.error('加载矢量数据错误！', error);
            }
        },
        getFeaturesBySQLAsync(featureService, params) {
            return new Promise((resolve, reject) => {
                featureService.getFeaturesBySQL(params, (serviceResult) => {
                    if (serviceResult && serviceResult.result) {
                        resolve(serviceResult.result);
                    } else {
                        reject(new Error('No features found or invalid response'));
                    }
                });
            });
        },
        async getDetailsData() {
            const taskId = this.$route.query.id;
            const res = await getDetailResultApi(taskId);
            if (res.code === 0) {
                this.mapData = res.data;
                this.desc = '';
                this.isLoaded = true;
                // iserver服务
                this.serviceType = 'iserver';
                this.center = this.mapData.prevImage.center.split(',').map(Number) ? this.mapData.prevImage.center.split(',').map(Number) : [0, 0];
                this.coordinate_system = this.mapData.prevImage.coordinateSystem;
                this.proj = this.mapData.prevImage.proj;
                let geojsonURL =
                    this.mapData.dataPath +
                    '/datasources/' +
                    this.mapData.datasourceName +
                    '/datasets/' +
                    this.mapData.datasetsName +
                    '/features.geojson?fromIndex=0&toIndex=' +
                    this.mapData.count;
                this.axios(geojsonURL, { withCredentials: false }).then((res) => {
                    this.mapData.geojson = res.data;
                    const tempArr = [];
                    const bhqdlArr = [];
                    const bhhdlArr = [];
                    this.mapData.geojson.features.forEach((res) => {
                        let newItem = {
                            id: res.properties.SMID,
                            SmID: res.properties.SMID,
                            title: res.properties.SMID + '.' + res.properties.XZQ + '--' + res.properties.BHQDL + '>' + res.properties.BHHDL,
                            dataPath: this.mapData.dataPath,
                            dataSource: this.mapData.datasourceName,
                            dataSets: this.mapData.datasetsName,
                            image1: this.mapData.prevImage,
                            image2: this.mapData.nextImage,
                            sourceCounty: this.mapData.sourceCountyData,
                            selected: !(res.properties.SMID - 1)
                        };
                        tempArr.push({
                            BHQDL: res.properties.BHQDL,
                            BHHDL: res.properties.BHHDL,
                            XZQ: res.properties.XZQ
                        });
                        this.listData.push(newItem);
                        bhqdlArr.push({ value: res.properties.BHQDL, label: res.properties.BHQDL });
                        bhhdlArr.push({ value: res.properties.BHHDL, label: res.properties.BHHDL });

                        const currentCounty = res.properties.XZQ; // 假设 res.properties.XZQ 是当前要处理的行政区名称
                        const existingItem = this.countyData.find((item) => item.county === currentCounty); // 查找数组中是否已存在该行政区
                        if (existingItem) {
                            // 如果已存在，则数量加1
                            existingItem.countyCount += 1;
                        } else {
                            // 如果不存在，则添加新项，数量初始化为1
                            this.countyData.push({
                                county: currentCounty,
                                countyCount: 1
                            });
                        }
                    });
                    this.bhqdlOptions = this.unique3(bhqdlArr);
                    this.bhhdlOptions = this.unique3(bhhdlArr);
                    this.countyData.forEach((item) => {
                        this.selectOptions.push({
                            value: item.county,
                            label: item.county
                        });
                    });
                    let newItem = Object.assign(this.countyData[0], { key: 1 });
                    this.tableData.tableRegion.dataSource.push(newItem);

                    this.tableData.tableType.dataSource = this.unique(tempArr).sort((a, b) => {
                        return a.BHQDL > b.BHQDL ? 1 : -1;
                    });
                    this.tableData.tableType.dataSource.forEach((item) => {
                        item.IDs = [];
                        this.mapData.geojson.features.forEach((item1) => {
                            if (item.BHQDL === item1.properties.BHQDL && item.BHHDL === item1.properties.BHHDL) {
                                item.IDs.push(item1.properties.SMID);
                            }
                        });
                    });
                    for (let i = 0; i < this.tableData.tableType.dataSource.length; i++) {
                        this.tableData.tableType.dataSource[i].key = i + 1;
                    }
                    this.typeTableData = JSON.parse(JSON.stringify(this.tableData.tableType.dataSource));
                    this.judgeCount();
                    this.initSuperMap();
                });
                this.getSMID();
            } else {
                this.$message.error(res.msg);
            }
        },
        judgeCount() {
            let changeNum = 0;
            this.countyData.forEach((item) => {
                changeNum += item.countyCount;
            });
            // if (this.mapData.count === changeNum) {
            //     this.loading = false;
            // } else {
            //     this.loading = true;
            // }
        }
    }
};
</script>

<style scoped>
.all-polygon-container {
    width: 100%;
    height: 100%;
    display: flex;
}

/*右侧*/
.details-right {
    flex: 1;
    z-index: 1;
    position: relative;
}

.ai-banner-title {
    position: absolute;
    /* top: 2rem; */
    bottom: 0.6rem;
    background-color: rgba(50, 50, 50, 0.9);
    color: white;
    padding: 0.5rem 1rem;
    border-radius: 0.2rem;
    font-size: 1rem;
    z-index: 999;
}

.title-prev {
    /* left: calc(50% - 20px); */
    left: 0.8rem;
    /* transform: translateX(-100%); */
}

.title-next {
    /* left: calc(50% + 20px); */
    right: 0.8rem;
}

/*end*/
/*左侧*/
.details-left {
    width: 320px;
    padding: 0.5rem 0.5rem 1rem 0.5rem;
    position: relative;
    border-right: 0.1rem solid rgb(200, 200, 200);
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #050e1f;
}

.details-left-title {
    height: 2.5rem;
    min-height: 2.5rem;
    font-size: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.title-text i {
    color: blue;
    font-size: 1.3rem;
}

.title-text span {
    font-size: 1rem;
    font-weight: 600;
    margin-left: 0.5rem;
    color: white;
}

.back-btn {
    border: 0.1rem solid rgb(200, 200, 200);
    border-radius: 0.2rem;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 0.3rem;
    font-size: 0.8rem;
    color: white;
}

.back-btn:hover {
    cursor: pointer;
    font-weight: 600;
    transition: all 200ms linear;
}

.details-left-item {
    position: relative;
    width: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/*总体分析*/
.header-border {
    width: 100%;
    height: 1.4rem;
    background-color: #52a9f1;
    border: 0.4rem solid #137ce3;
}

.header-content {
    background-color: #2d56a0;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 94%;
    padding: 0.2rem 0.5rem 1.2rem 0.5rem;
    position: relative;
}

.header-item:nth-child(1) {
    width: 100%;
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    margin: 0.5rem 0;
}

.header-item:nth-child(1) span {
    margin: 0 0.8rem;
    font-size: 1rem;
    color: white;
    font-weight: 600;
}

.divider {
    flex: 1;
    min-width: 20%;
    margin: 0;
}

.header-item:nth-child(2) {
    font-size: 0.95rem;
    color: white;
}

.text-bold {
    font-size: 1rem;
    font-weight: 600;
    color: #ffb961;
    margin: 0 0.3rem;
    text-decoration: underline;
}

.text-bold:hover {
    cursor: pointer;
}

.divider1 {
    margin: 0.8rem 0;
}

.header-item:nth-child(4) {
    width: 100%;
    color: #dcdcdc;
    font-size: 0.95rem;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.header-item:nth-child(4) span:nth-child(3) {
    margin: 0 1rem;
}

.header-item:nth-child(4) span:nth-child(2) {
    margin-left: 0.5rem;
}

.header-item:nth-child(4) span:nth-child(4) {
    margin-right: 0.5rem;
}

.item-title {
    width: 100%;
    height: 2rem;
    display: flex;
    align-items: center;
    font-size: 1rem;
    padding: 0.2rem 0;
    background-image: url('@/assets/images/bg-tittle.png');
    background-repeat: no-repeat;
}

.regional-analysis {
    justify-content: space-between;
}

.item-title span {
    margin-right: 0.5rem;
    color: white;
    font-size: 1rem;
}

/*表格*/
.table-region {
    margin-bottom: 0.7rem;
    flex: 0 1 auto;
    overflow: auto;
    min-height: 145px;
    margin-top: 0.7rem;
}

.table-type {
    flex: 1 1 auto;
    overflow: auto;
}

.my-table {
    width: 100%;
    height: calc(100% - 2rem);
    overflow: auto;
}

::v-deep(.my-table tr) {
    height: 1rem !important;
}

::v-deep(.my-table tr td),
::v-deep(.my-table tr th) {
    padding-top: 0.4rem;
    padding-bottom: 0.4rem;
}

::v-deep(.my-table tr td) {
    cursor: pointer;
}

/*工具条*/
.tool-container {
    position: absolute;
    top: 2rem;
    right: 2rem;
    z-index: 2;
    background-color: white;
    border: 2px solid rgba(0, 0, 0, 0.2);
    background-clip: padding-box;
    border-radius: 10px;
}

.tool-item {
    float: left;
    cursor: pointer;
    width: 50px;
    height: 40px;
    text-align: center;
    line-height: 40px;
}

.tool-container .tool-item:nth-child(5) {
    width: 78px;
}

.tool-container .tool-item:nth-child(7) {
    width: 76px;
}

.tool-item:hover {
    color: #137ce3 !important;
}

.division {
    float: left;
    height: 40px;
    line-height: 40px;
}

.iconfont {
    cursor: pointer;
    font-size: 20px !important;
}

.toolbox .iconfont {
    color: #000 !important;
}

.arcgis-toolbox .iconfont {
    color: #7f7f7f !important;
}

.iconfont:hover {
    color: #137ce3 !important;
}

.toolbox {
    position: absolute;
    top: 80px;
    left: 410px;
    z-index: 2;
    background-color: #ffffff;
    border: 2px solid rgba(0, 0, 0, 0.2);
    background-clip: padding-box;
    border-radius: 4px;
}

.toolbox li {
    list-style: none;
    width: 30px;
    height: 30px;
    text-align: center;
}

.toolbox li:nth-child(2),
.arcgis-toolbox li:nth-child(2) {
    border-top: 1px solid #cccccc;
    border-bottom: 1px solid #cccccc;
}

.toolbox li:nth-child(3),
.arcgis-toolbox li:nth-child(3) {
    border-bottom: 1px solid #cccccc;
}

.arcgis-toolbox {
    position: absolute;
    top: 87px;
    left: 415px;
    z-index: 2;
    background-color: #ffffff;
    box-shadow: 0 1px 2px rgb(0 0 0 / 30%);
}

.arcgis-toolbox li {
    list-style: none;
    width: 32px;
    height: 32px;
    text-align: center;
}

.layer-dialog {
    position: absolute;
    background-color: white;
    top: 6rem;
    right: 6rem;
    z-index: 2;
    border-radius: 0.5rem;
    padding-bottom: 10px;
    max-height: 400px;
    overflow: auto;
}

.container-title {
    font-size: 15px;
    background-color: #3989ca;
    color: white;
    width: 100%;
    padding: 0.4rem;
    border-radius: 0.5rem 0.5rem 0 0;
    margin-bottom: 0.5rem;
}

.ant-checkbox-wrapper {
    display: block;
    margin: 0 16px;
}

::v-deep .el-input--small .el-input__inner {
    height: 1.6rem;
    line-height: 1.6rem;
}
::v-deep .ant-table {
    color: #fff;
}
::v-deep .ant-table-thead > tr > th {
    color: #fff;
    background: #243148;
}
::v-deep .ant-table-tbody > tr:hover:not(.ant-table-expanded-row):not(.ant-table-row-selected) > td {
    background: #e6f7ff2e;
}
</style>
