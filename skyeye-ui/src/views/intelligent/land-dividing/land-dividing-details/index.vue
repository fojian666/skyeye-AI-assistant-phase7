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
                    <span>地类分割</span>
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
                        {{ mapData.county }}，{{ mapData.path.appendTime }}，地类分割图斑发现{{ mapData.count }}处<span
                            class="text-bold"
                            @click="openOnePolygon"
                            >[查看]</span
                        >。
                    </div>
                </div>
            </div>
            <div class="details-left-item">
                <div class="item-title">
                    <span>|</span>
                    <span>区域分析</span>
                </div>
                <a-table class="qy-table" :columns="tableData.columns" :dataSource="tableData.dataSource" bordered :pagination="false"></a-table>
            </div>
            <div class="details-left-item">
                <div class="item-title">
                    <span>|</span>
                    <span>图斑分析</span>
                </div>
                <a-table
                    class="qy-table"
                    :columns="tableData2.columns"
                    :dataSource="tableData2.dataSource"
                    bordered
                    :customRow="polygonRowClick"
                    :pagination="false"></a-table>
            </div>
        </div>
        <div
            class="details-right"
            id="details-map"
            v-loading="shpLoading"
            element-loading-text="推送shp中，请等候……"
            element-loading-spinner="el-icon-loading"
            element-loading-background="rgba(255,255,255,0.5)"></div>

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
            <!--            <div class="tool-item push-shp" @click="pushShp">-->
            <!--                <span>推送结果</span>-->
            <!--            </div>-->
        </div>
        <div class="layer-dialog" v-show="flag">
            <div class="container-title">请选择叠加图层</div>
            <a-checkbox @change="selectLayer($event, item)" v-for="(item, index) in layerOptions" :key="index">
                {{ item.label }}
            </a-checkbox>
        </div>
        <DownloadOption v-show="false"></DownloadOption>
    </div>
</template>

<script>
import DownloadOption from '@/components/download-option';
// import "leaflet.markercluster/dist/MarkerCluster.css";
// import "leaflet.markercluster/dist/MarkerCluster.Default.css";
// import "leaflet.markercluster";
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';
import { calcResolution, projectionToGeography, drawPoint, measureDistance, measureArea, clearGraphical } from '@/utils/utils';
import { TiledMapLayer, FeatureService, ImageTileLayer, GetFeaturesBySQLParameters } from '@supermap/iclient-leaflet';
import { getDetailResultApi, getOneMapApi } from '@/api/commonApi';
//聚合图层和geojson图层
// let markerClusterGroup = L.markerClusterGroup({
//     spiderfyOnMaxZoom: false,
//     showCoverageOnHover: false,
//     zoomToBoundsOnClick: false
// });
let geojsonLayer = null;

//表格列的配置
const columns = [
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
        title: '分割数量(处)',
        dataIndex: 'count',
        key: 'count',
        align: 'center'
    }
];
const columns2 = [
    {
        title: '序号',
        dataIndex: 'key',
        key: 'key',
        width: '4rem',
        align: 'center'
    },
    {
        title: '分割类型',
        dataIndex: 'type',
        key: 'type',
        align: 'center'
    },
    {
        title: '数量',
        dataIndex: 'count',
        key: 'count',
        align: 'center'
    }
];
let layer = [];
export default {
    name: 'landChangeDetails',
    components: {
        DownloadOption
    },
    data() {
        return {
            map: null, //地图容器
            mapData: null, //地图数据
            geojson: {},
            marker: {},
            isLoaded: false, //后台请求状态
            tableData: {
                columns: Object.freeze(columns),
                dataSource: []
            }, //表格数据
            tableData2: {
                columns: Object.freeze(columns2),
                dataSource: []
            }, //表格数据
            tempArr: [],
            tempArr1: [],
            tempArr2: [],
            tempArr3: [],
            tempArr4: [],
            listData: [], //查看页列表数据
            coordinate_system: '',
            proj: '',
            flag: false,
            layerOptions: [],
            polygonZoom: 16,
            polygonRowClick: (record) => ({
                // 事件
                on: {
                    click: () => {
                        // 点击改行时要做的事情
                        // this.polygonAnalysis(record);
                    }
                }
            }),
            center: null,
            zoom: 16,
            crs: {},
            view: null,
            polygonGraphicArr: null,
            highlight: null,
            serviceType: '',
            loading: false,
            shpLoading: false,
            data: [
                { label: '基础地理数据', children: [] },
                { label: '资源调查数据', children: [] },
                { label: '低空业务数据', children: [] }
            ]
        };
    },
    async mounted() {
        this.getinitData();
        await this.getSourceRelatedBussiness();
    },
    methods: {
        //初始化地图
        initMap(mapData) {
            this.axios
                // .get(mapData.path.url + ".json", {withCredentials: false})
                .get(mapData.path.url + `/collections/${mapData.path.collectId}/items/${mapData.path.tifId}` + '.json', { withCredentials: false })
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
                        this.crs.resolutions = [
                            0.7031249999891485, 0.35156250000645817, 0.17578124999134512, 0.08789062499567256, 0.04394531250972024,
                            0.02197265625486012, 0.01098632812743006, 0.00549316406371503, 0.002746582031857515, 0.0013732910159287575,
                            6.866454960804162e-4, 3.4332275992417075e-4, 1.7166136807812276e-4, 8.583068403906138e-5, 4.291534201953069e-5,
                            2.1457682893727956e-5, 1.0728841446863978e-5, 5.364420723431989e-6, 2.6822103617159945e-6, 1.3411051808579973e-6,
                            6.705407064663857e-7, 3.3527035323319285e-7, 1.6763517661659642e-7
                        ];
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
                        let EPSG = 'EPSG:' + this.coordinate_system;
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

                    this.map = L.map('details-map', {
                        crs: this.crs,
                        center: this.center,
                        maxZoom: 23,
                        zoom: this.zoom,
                        attributionControl: false,
                        logoControl: false,
                        trackResize: false
                    });
                    L.control.scale().addTo(this.map);
                    // var currentLayer = new TiledMapLayer(mapData.path.url);
                    // currentLayer.options.minZoom = 10;
                    // currentLayer.options.maxZoom = 22;
                    // currentLayer.options.maxNativeZoom = 22;
                    // currentLayer.addTo(this.map);

                    var currentLayer = new ImageTileLayer(mapData.path.url, {
                        collectionId: mapData.path.collectId,
                        names: [mapData.path.tifName],
                        maxZoom: 24 //设置最大级别
                    }).addTo(this.map);

                    this.map.on('zoomend', this.updateZoomLevel);
                    this.loadGeoJSONLayer(this.map, this.mapData);
                    // if (mapData.count < 400) {
                    //     // this.loadMarkerCluster(this.map, this.mapData);
                    //     this.map.on("zoomend", () => {
                    //         if (this.map.getZoom() > 15) {
                    //             this.map.removeLayer(markerClusterGroup);
                    //             this.loadGeoJSONLayer(this.map, this.mapData);
                    //         } else {
                    //             this.geoJSONLayer && this.map.removeLayer(this.geoJSONLayer);
                    //             // this.loadMarkerCluster(this.map, this.mapData);
                    //         }
                    //     });
                    // } else {
                    //     this.loadMap(this.map, this.mapData);
                    // }
                });
        },
        updateZoomLevel() {
            // 更新当前缩放级别
            this.currentZoom = this.map.getZoom();
        },
        // 画点，显示经纬度
        drawPoint() {
            drawPoint(this.map);
        },
        //画线，测量距离
        measureLength() {
            measureDistance(this.map);
        },
        // 画面，测量面积
        startDrawPolygon() {
            measureArea(this.map);
        },
        clearDraw() {
            clearGraphical(this.map);
        },

        loadMap(map, mapData) {
            let layerInfo = {};
            // let newLayer = new L.supermap.tiledMapLayer(mapData.map_url).addTo(map);
            let newLayer = new ImageTileLayer(mapData.path.url, {
                collectionId: mapData.path.collectId,
                names: [mapData.path.tifName],
                maxZoom: 24 //设置最大级别
            }).addTo(map);
            layerInfo = {
                layer: newLayer
            };
            layer.push(layerInfo);
        },
        //加载聚合图层
        loadMarkerCluster(map, mapData) {
            let DefaultIcon = L.icon({
                iconUrl: icon,
                shadowUrl: iconShadow
            });
            L.Marker.prototype.options.icon = DefaultIcon;
            let getFeatureBySQLParams = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: new SuperMap.FilterParameter({
                    name: `${mapData.datasetsName}@${mapData.datasourceName}`,
                    attributeFilter: `SmID>0 and SmID <= ${mapData.count}`
                }),
                datasetNames: [`${mapData.datasourceName}:${mapData.datasetsName}`],
                toIndex: mapData.count,
                fromIndex: 0,
                maxFeatures: mapData.count
            });
            L.supermap.featureService(mapData.dataPath).getFeaturesBySQL(getFeatureBySQLParams, (serviceResult) => {
                let result = serviceResult.result.features;
                if (!result || !result.features || result.features.length < 1) {
                    return;
                }
                markerClusterGroup.clearLayers();
                result.features.map((feature) => {
                    let center = [];
                    center.push(parseFloat(feature.properties.ZXDY));
                    center.push(parseFloat(feature.properties.ZXDX));
                    markerClusterGroup.addLayer(L.marker(center));
                });
                markerClusterGroup.addTo(map);
                this.markerClusterGroup = markerClusterGroup;
            });
        },
        //加载geojson图层
        loadGeoJSONLayer(map, mapData) {
            this.geoJSONLayer && this.map.removeLayer(this.geoJSONLayer);
            let leftTop = Object.values(map.getBounds().getNorthWest());
            let rightTop = Object.values(map.getBounds().getNorthEast());
            let rightBottom = Object.values(map.getBounds().getSouthEast());
            let leftBottom = Object.values(map.getBounds().getSouthWest());
            let polygon = L.polygon([leftTop, rightTop, rightBottom, leftBottom], {
                color: 'red'
            });
            let boundsParam = new SuperMap.GetFeaturesByBoundsParameters({
                datasetNames: [`${mapData.datasourceName}:${mapData.datasetsName}`],
                bounds: polygon.getBounds(),
                toIndex: 100000,
                maxFeatures: 100000
            });
            L.supermap.featureService(mapData.dataPath).getFeaturesByBounds(boundsParam, (serviceResult) => {
                let result = serviceResult.result.features;
                if (!result || !result.features || result.features.length < 1) {
                    return;
                }
                this.geoJSONLayer = L.geoJSON(result, {
                    style: () => {
                        return { color: 'red' };
                    }
                }).addTo(map);
            });
        },
        queryFeatures(DLFGLB) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    // attributeFilter: `DLFGLB='${DLFGLB}'`
                },
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1,
                maxFeatures: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                serverResult.result.features.features.forEach((item) => {
                    this.tempArr.push({
                        count: serverResult.result.totalCount,
                        // data_type: DLFGLB,
                        data_type: item.properties.DLFGLB,
                        SmID: item.properties.SMID
                    });
                });
                const dataTypeList = [];
                for (let j = 0; j < this.tempArr.length; j++) {
                    let newItem = {
                        id: j,
                        title: this.mapData.county + '--' + this.tempArr[j].data_type,
                        SmID: this.tempArr[j].SmID,
                        imagePath: this.mapData.path,
                        dataSource: this.mapData.datasourceName,
                        dataSets: this.mapData.datasetsName,
                        dataPath: this.mapData.dataPath,
                        selected: !j
                    };
                    this.listData.push(newItem);

                    const existingItem = dataTypeList.find((item) => item.type === this.tempArr[j].data_type); // 查找数组中是否已存在该行政区
                    if (existingItem) {
                        // 如果已存在，则数量加1
                        existingItem.count += 1;
                    } else {
                        // 如果不存在，则添加新项，数量初始化为1
                        dataTypeList.push({
                            type: this.tempArr[j].data_type,
                            count: 1
                        });
                    }
                    dataTypeList.forEach((item, index) => {
                        item.key = index + 1;
                    });

                    this.tableData2.dataSource = dataTypeList;
                }
            });
        },
        queryFeatures1(DLFGLB) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    attributeFilter: `DLFGLB='${DLFGLB}'`
                },
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1,
                maxFeatures: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                serverResult.result.features.features.forEach((item) => {
                    this.tempArr1.push({
                        count: serverResult.result.totalCount,
                        data_type: DLFGLB,
                        SmID: item.properties.SMID
                    });
                });
                for (let j = 0; j < this.tempArr1.length; j++) {
                    let newItem = {
                        id: j,
                        title: this.mapData.county + '--' + this.tempArr1[j].data_type,
                        SmID: this.tempArr1[j].SmID,
                        imagePath: this.mapData.path,
                        dataSource: this.mapData.datasourceName,
                        dataSets: this.mapData.datasetsName,
                        dataPath: this.mapData.dataPath,
                        selected: !j
                    };
                    this.listData.push(newItem);
                }
            });
        },
        queryFeatures2(DLFGLB) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    attributeFilter: `DLFGLB='${DLFGLB}'`
                },
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1,
                maxFeatures: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                serverResult.result.features.features.forEach((item) => {
                    this.tempArr2.push({
                        count: serverResult.result.totalCount,
                        data_type: DLFGLB,
                        SmID: item.properties.SMID
                    });
                });
                for (let j = 0; j < this.tempArr2.length; j++) {
                    let newItem = {
                        id: j,
                        title: this.mapData.county + '--' + this.tempArr2[j].data_type,
                        SmID: this.tempArr2[j].SmID,
                        imagePath: this.mapData.path,
                        dataSource: this.mapData.datasourceName,
                        dataSets: this.mapData.datasetsName,
                        dataPath: this.mapData.dataNath,
                        selected: !j
                    };
                    this.listData.push(newItem);
                }
            });
        },
        queryFeatures3(DLFGLB) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    attributeFilter: `DLFGLB='${DLFGLB}'`
                },
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1,
                maxFeatures: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                serverResult.result.features.features.forEach((item) => {
                    this.tempArr3.push({
                        count: serverResult.result.totalCount,
                        data_type: DLFGLB,
                        SmID: item.properties.SMID
                    });
                });
                for (let j = 0; j < this.tempArr3.length; j++) {
                    let newItem = {
                        id: j,
                        title: this.mapData.county + '--' + this.tempArr3[j].data_type,
                        SmID: this.tempArr3[j].SmID,
                        imagePath: this.mapData.path,
                        dataSource: this.mapData.datasourceName,
                        dataSets: this.mapData.datasetsName,
                        dataPath: this.mapData.dataPath,
                        selected: !j
                    };
                    this.listData.push(newItem);
                }
            });
        },
        queryFeatures4(DLFGLB) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    attributeFilter: `DLFGLB='${DLFGLB}'`
                },
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`],
                toIndex: -1,
                maxFeatures: -1
            });
            new FeatureService(this.mapData.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                serverResult.result.features.features.forEach((item) => {
                    this.tempArr4.push({
                        count: serverResult.result.totalCount,
                        data_type: DLFGLB,
                        SmID: item.properties.SMID
                    });
                });
                for (let j = 0; j < this.tempArr4.length; j++) {
                    let newItem = {
                        id: j,
                        title: this.mapData.county + '--' + this.tempArr4[j].data_type,
                        SmID: this.tempArr4[j].SmID,
                        imagePath: this.mapData.path,
                        dataSource: this.mapData.datasourceName,
                        dataSets: this.mapData.datasetsName,
                        dataPath: this.mapData.dataPath,
                        selected: !j
                    };
                    this.listData.push(newItem);
                }
            });
        },
        // 对数组中的项去重，并统计每一项的个数
        unique(arr) {
            let hash = [];
            for (let i = 0; i < arr.length; i++) {
                for (let j = i + 1; j < arr.length; j++) {
                    if (arr[i].data_type === arr[j].data_type) {
                        ++i;
                        j = i;
                    }
                }
                hash.push(arr[i]);
            }
            hash.forEach((item, index) => {
                item.key = index + 1;
            });
            return hash;
        },
        // 对数组中的项去重，并统计每一项的个数
        unique2(arr) {
            let hash = [];
            for (let i = 0; i < arr.length; i++) {
                for (let j = i + 1; j < arr.length; j++) {
                    if (arr[i].county === arr[j].county) {
                        ++i;
                        j = i;
                    }
                }
                arr[i].count = 0;
                hash.push(arr[i]);
            }
            hash.forEach((item, index) => {
                arr.forEach((item1) => {
                    if (item.county === item1.county) {
                        item.count++;
                    }
                });
            });
            return hash;
        },
        // 对数组中的项去重，并统计每一项的个数
        unique3(arr) {
            let hash = [];
            for (let i = 0; i < arr.length; i++) {
                for (let j = i + 1; j < arr.length; j++) {
                    if (arr[i].type === arr[j].type) {
                        ++i;
                        j = i;
                    }
                }
                arr[i].count = 0;
                hash.push(arr[i]);
            }
            hash.forEach((item, index) => {
                arr.forEach((item1) => {
                    if (item.type === item1.type) {
                        item.count++;
                    }
                });
            });
            return hash;
        },
        //回返上个页面
        goBack() {
            // this.$router.push("/intelligent/land-dividing");
            this.$router.push('/intelligent/land-change');
        },
        //全图
        flyToFull() {
            if (this.mapData.path.url && this.mapData.path.url.includes('arcgis')) {
                projectionToGeography(40388053.97, 3585501.13, this.view.spatialReference.wkid, 4326, this.view, 12);
            } else {
                this.map.flyTo(this.center, 9);
            }
        },
        //查看
        openOnePolygon() {
            if (this.mapData.dataPath && this.mapData.dataPath.includes('arcgis')) {
                this.$router.push({
                    path: '/intelligent/land-dividing/land-dividing-details/spot-view',
                    query: {
                        data_path: this.mapData.dataPath,
                        path_url: this.mapData.path.url
                    }
                });
            } else {
                for (let i = 0; i < this.listData.length; i++) {
                    this.listData[i].title = i + 1 + '.' + this.listData[i].title;
                }
                let component = {
                    name: 'OnePolygon',
                    info: this.listData[0],
                    listData: this.listData
                };
                this.$router.push({
                    path: '/intelligent/land-dividing/land-dividing-details/spot-view',
                    query: { component }
                });
            }
        },
        layerDialog() {
            if (this.layerOptions.length === 0) return this.$message.warning('没有叠加的图层！');
            this.flag = !this.flag;
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
        onChange(e, url, datasetsName, datasourceName) {
            this.axios(`${url}/datasources/${datasourceName}/datasets/${datasetsName}/features.json`).then((res) => {
                this.overlayLayer(e, url, res.data.startIndex, res.data.featureCount, datasets_name, datasource_name);
            });
        },
        overlayLayer(e, url, startIndex, featureCount, datasetsName, datasourceName) {
            this.axios(
                `${url}/datasources/${datasourceName}/datasets/${datasetsName}/features.geojson?fromIndex=${startIndex}&toIndex=${featureCount}`,
                { withCredentials: false }
            ).then((res) => {
                if (e.target.checked) {
                    layer = L.geoJSON(res.data, {
                        style: () => {
                            return { fillColor: 'transparent', color: 'red' };
                        }
                    }).addTo(this.map);
                } else {
                    this.map.removeLayer(layer);
                }
            });
        },
        //选择图层
        async selectLayer(e, item) {
            let layerInfo = {};
            let checked = e.target.checked;
            if (checked) {
                let newLayer = null;
                if (item.datasource_name && item.datasets_name) {
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
        polygonAnalysis(record) {
            this.map.removeLayer(this.geojson);
            let idsParam = new SuperMap.GetFeaturesByIDsParameters({
                IDs: record.IDs,
                datasetNames: [`${this.mapData.datasourceName}:${this.mapData.datasetsName}`]
            });
            L.supermap.featureService(this.mapData.dataPath).getFeaturesByIDs(idsParam, (serverResult) => {
                let center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0]);
                const transCenter1 = this.crs.unproject(L.point(center[1], center[0]));
                this.map.setView([transCenter1.lat, transCenter1.lng], this.polygonZoom);
                this.geojson = L.geoJSON(serverResult.result.features, {
                    coordsToLatLng: (coords) => {
                        return this.crs.unproject(L.point(coords[0], coords[1]));
                    },
                    style: () => {
                        return { color: '#2AC2E7', fillColor: 'transparent' };
                    }
                });
                this.geojson.addTo(this.map);
            });
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
        async getinitData() {
            this.loading = true;
            const taskId = this.$route.query.id;
            const res = await getDetailResultApi(taskId);
            // const res = {
            //     'data': {
            //         "source_related_bussiness": [
            //             {
            //                 "name": "试点街道耕地",
            //                 "url": "http://192.168.60.42:8090/iserver/services/map-ugcv5-njsdgdnjsdgd/rest/maps/njsdgd%40njsdgd",
            //                 "owner": "admin",
            //                 "sourceType": "业务数据服务",
            //                 "coordinateSystem": "4490",
            //                 "center": "[29.40961700911636, 106.28435372154246]",
            //                 "dataType": "",
            //                 "datasetsName": "",
            //                 "datasourceName": "",
            //                 "createTime": "2024-09-07",
            //                 "appendTime": "2024-09",
            //                 "count": 1
            //             }
            //         ],
            //         "name": "高淳检测",
            //         "path": {
            //             "name": "Gc_20250601",
            //             "appendTime": "2024-09",
            //             "url": "http://192.168.60.42:8090/iserver/services/imageservice-njimagetest/restjsr",
            //             "collectId":'imagetestdk',
            //             "tifName":'Gc_20250601.tif',
            //             "tifId":3,
            //             "coordinateSystem": "4490",
            //             "proj": "+proj=longlat +ellps=GRS80 +no_defs +type=crs"
            //         },
            //         "prevImage": {},
            //         "nextImage": {},
            //         "center": "[31.38094708595064, 118.99396342874518]",
            //         "taskType": "地类分割",
            //         "createTime": "2024-09-07 15:27:22",
            //         "dataPath": "http://192.168.60.42:8090/iserver/services/data-hpjy/rest/data",
            //         "county": "高淳",
            //         "dataTypeList": [
            //             {
            //                 "type": "耕地",
            //                 "count": "36"
            //             }
            //         ],
            //         "countyData": [],
            //         "count": 41,
            //         "datasourceName": "hpjyi",
            //         "datasetsName": "dwfl",
            //         "dataType": "耕地",
            //         "owner": "admin",
            //         "desc": "",
            //         // "map_url": "http://192.168.60.51:8090/iserver/services/map-ugcv5-DLHGYJIANGJING/rest/maps/DLHGY%40JIANGJING",
            //         "status": true
            //     },
            //     'code': 0
            // }

            if (res.code == 0) {
                this.mapData = res.data;
                this.isLoaded = true;
                this.serviceType = 'iserver';
                this.center = this.mapData.path.center.split(',').map(Number) ? this.mapData.path.center.split(',').map(Number) : [0, 0];
                this.coordinate_system = this.mapData.path.coordinateSystem;
                this.proj = this.mapData.path.proj;
                this.tableData.dataSource.push({
                    key: 1,
                    county: this.mapData.county,
                    count: this.mapData.count
                });
                let changeNum = 0;
                this.tableData.dataSource.forEach((item) => {
                    changeNum += item.count;
                });
                if (this.mapData.count === changeNum) {
                    this.loading = false;
                } else {
                    this.loading = true;
                }
                this.loading = false;

                this.$nextTick(() => {
                    this.initMap(this.mapData);
                });
                const FGArr = this.mapData.dataType;
                this.queryFeatures(FGArr);
                // const FGArr = this.mapData.dataType.split(",") ? this.mapData.dataType.split(",") : [];
                // if (FGArr.length === 1) {
                //     let num = 0;
                //     for (let j = 0; j < this.mapData.count; j++) {
                //         num++;
                //         let newItem = {
                //             id: num - 1,
                //             title: this.mapData.county + "--" + this.mapData.dataType,
                //             SmID: num,
                //             imagePath: this.mapData.path,
                //             dataSource: this.mapData.datasourceName,
                //             dataSets: this.mapData.datasetsName,
                //             dataPath: this.mapData.dataPath,
                //             selected: !(num - 1)
                //         };
                //         this.listData.push(newItem);
                //     }
                // } else {
                //     this.queryFeatures(FGArr[FGArr.length - 5]);
                //     this.queryFeatures1(FGArr[FGArr.length - 4]);
                //     this.queryFeatures2(FGArr[FGArr.length - 3]);
                //     this.queryFeatures3(FGArr[FGArr.length - 2]);
                //     this.queryFeatures4(FGArr[FGArr.length - 1]);
                // }
                // this.layerOptions = res.data.source_related_bussiness;
            } else {
                this.$message.error(res.msg);
            }
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
                this.$message.error('加载矢量数据错误！');
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
        }
    }
};
</script>

<style scoped lang="scss">
.all-polygon-container {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: space-between;
    background: #0b1a39;
}

/*右侧*/
.details-right {
    flex: 1;
    height: 100%;
}

/*end*/
/*左侧*/
.details-left {
    width: 320px;
    height: 100%;
    padding: 0.5rem;
    position: relative;
    border-right: 0.1rem solid rgb(200, 200, 200);
}

.details-left-title {
    height: 2.5rem;
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
    margin-bottom: 2rem;
    flex-direction: column;
    align-items: center;
}

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
    top: -0.3rem;
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
    font-weight: 600;
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

.item-title span {
    margin-right: 0.5rem;
    font-size: 1rem;
    color: white;
}

/*表格*/
.qy-table {
    width: 100%;
}

::v-deep(.qy-table tr) {
    height: 1rem !important;
}

::v-deep(.qy-table tr td),
::v-deep(.qy-table tr th) {
    padding-top: 0.4rem;
    padding-bottom: 0.4rem;
}

::v-deep(.qy-table tr td) {
    cursor: pointer;
}

/*工具条*/
.tool-container {
    position: absolute;
    top: 2rem;
    right: 2rem;
    z-index: 999;
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

.push-shp {
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
    z-index: 999;
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
    left: 335px;
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

/*列表*/
.left-list {
    position: absolute;
    left: 20rem;
    top: 50%;
    transform: translateY(-50%);
    background-color: white;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    padding-bottom: 1rem;
    padding-top: 1.5rem;
    z-index: 999;
}

.close-btn {
    position: absolute;
    top: 0.3rem;
    right: 0.5rem;
    font-size: 1.5rem;
}

.location-icon {
    color: #3989ca;
    font-size: 1.5rem;
}

::v-deep(.ant-list-item-meta) {
    align-items: center;
}

::v-deep(.ant-list-item-meta-title) {
    margin-bottom: 0;
}

::v-deep(.ant-avatar-circle) {
    color: blue;
    background-color: rgba(1, 1, 1, 0);
    font-size: 1.2rem;
}

::v-deep(.ant-list-item) {
    padding: 0.6rem 0;
    display: flex;
    align-items: center;
}

.compare-btn {
    height: 2rem;
    width: 2rem;
    margin-left: 0.5rem;
}

.compare-btn:hover {
    cursor: pointer;
}

.layer-dialog {
    position: absolute;
    background-color: white;
    top: 6rem;
    right: 3rem;
    z-index: 9999;
    border-radius: 0.5rem;
    padding-bottom: 10px;
    max-height: 400px;
    overflow: auto;
}

::v-deep(.ant-checkbox-wrapper) {
    display: block;
    margin-left: 20px;
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
    margin: 0 12px;
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
