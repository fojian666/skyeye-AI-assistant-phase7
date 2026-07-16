<template>
    <div class="one-polygon-container">
        <div class="details-left">
            <div class="details-left-title">
                <span class="title-text">
                    <i class="iconfont icon-zhuzhuangtu"></i>
                    <span>地类分割详情</span>
                </span>
                <span class="back-btn" @click="goBack">
                    <i class="iconfont icon-fanhui"></i>
                    <span>返回</span>
                </span>
            </div>
            <VirtualList :listData="listData" @changePolygon="changePolygon"></VirtualList>
        </div>
        <div class="details-right" id="myMap" ref="myMap"></div>
    </div>
</template>

<script>
import { calcResolution } from '@/utils/utils';
import { TiledMapLayer, FeatureService, ImageTileLayer } from '@supermap/iclient-leaflet';
export default {
    name: 'SpotView',
    data() {
        return {
            mapObj: {
                map: null,
                geojsonLayer: null
            },
            crs: {},
            zoom: 18,
            coordinate_system: '',
            proj: '',
            info: {},
            listData: [],
            map: null,
            featureLayer: null,
            view: null,
            tileLayer: null,
            highlight: null,
            FID0: 0,
            projectedPoints: null
        };
    },
    mounted() {
        this.info = this.$route.query.component.info;
        this.listData = this.$route.query.component.listData;
        this.initSuperMap();
    },
    methods: {
        initSuperMap() {
            this.coordinate_system = this.info.imagePath.coordinateSystem;
            this.proj = this.info.imagePath.proj;
            // this.axios.get(this.info.imagePath.url + '.json',{ withCredentials: false })
            this.axios
                .get(this.info.imagePath.url + `/collections/${this.info.imagePath.collectId}/items/${this.info.imagePath.tifId}` + '.json', {
                    withCredentials: false
                })
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
                    if (this.coordinate_system === '4326' || this.coordinate_system === '4490') {
                        this.crs = L.CRS.EPSG4326;
                    } else if (this.coordinate_system === '3857') {
                        this.crs = L.Proj.CRS('EPSG:3857', {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)]
                        });
                    } else {
                        const EPSG = 'EPSG:' + this.coordinate_system;
                        proj4.defs(EPSG, this.proj);
                        this.crs = L.Proj.CRS(EPSG, {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)]
                        });
                    }

                    this.mapObj.map = L.map('myMap', {
                        crs: this.crs,
                        maxZoom: 23,
                        minZoom: 10,
                        zoom: this.zoom,
                        attributionControl: false,
                        logoControl: false,
                        trackResize: false,
                        zoomControl: true
                    });
                    // const currentLayer =  L.supermap.tiledMapLayer(this.info.imagePath.url);
                    // currentLayer.options.minZoom = 10;
                    // currentLayer.options.maxZoom = 22;
                    // currentLayer.options.maxNativeZoom = 22;
                    // currentLayer.addTo(this.mapObj.map);
                    var currentLayer = new ImageTileLayer(this.info.imagePath.url, {
                        collectionId: this.info.imagePath.collectId,
                        names: [this.info.imagePath.tifName],
                        maxZoom: 24 //设置最大级别
                    }).addTo(this.mapObj.map);

                    let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                        queryParameter: {
                            name: this.info.dataSource,
                            attributeFilter: `SMID=${this.info.SmID}`
                        },
                        datasetNames: [`${this.info.dataSource}:${this.info.dataSets}`],
                        toIndex: 100000,
                        maxFeatures: 100000
                    });
                    new FeatureService(this.info.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                        const center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0]);
                        const transCenter1 = this.crs.unproject(L.point(center[1], center[0]));
                        const center1 = [transCenter1.lat, transCenter1.lng];
                        this.mapObj.map.setView(center1, this.zoom);
                        this.mapObj.geojsonLayer = L.geoJSON(serverResult.result.features, {
                            coordsToLatLng: (coords) => {
                                return this.crs.unproject(L.point(coords[0], coords[1]));
                            },
                            style: () => {
                                return { color: 'red' };
                            }
                        }).addTo(this.mapObj.map);
                    });
                });
        },
        changePolygon(SmID) {
            this.superChangePolygon(SmID);
        },
        superChangePolygon(SmID) {
            let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                queryParameter: {
                    attributeFilter: `SMID=${SmID}`
                },
                datasetNames: [`${this.info.dataSource}:${this.info.dataSets}`],
                toIndex: -1
            });
            new FeatureService(this.info.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                const center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0]);
                const transCenter1 = this.crs.unproject(L.point(center[1], center[0]));
                this.mapObj.map.setView([transCenter1.lat, transCenter1.lng], this.zoom);
                this.mapObj.map.removeLayer(this.mapObj.geojsonLayer);
                this.mapObj.geojsonLayer = L.geoJSON(serverResult.result.features, {
                    coordsToLatLng: (coords) => {
                        return this.crs.unproject(L.point(coords[0], coords[1]));
                    },
                    style: () => {
                        return { color: 'red' };
                    }
                }).addTo(this.mapObj.map);
            });
        },
        goBack() {
            this.$router.go(-1);
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
        }
    },
    components: {
        VirtualList: () => import('@/components/virtual-list')
    }
};
</script>

<style scoped>
.one-polygon-container {
    width: 100%;
    height: 100%;
    display: flex;
    background: #0b1a39;
}

/*左侧*/
.details-left {
    width: 20rem;
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
    cursor: pointer;
}

.back-btn:hover {
    cursor: pointer;
    font-weight: 600;
    transition: all 200ms linear;
}

/*右侧*/
.details-right {
    flex: 1;
    max-width: calc(100% - 20rem);
    display: flex;
    flex-direction: column;
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
.ant-list-item:hover .title-sole {
    cursor: pointer;
    color: black !important;
}

.data-item-active .title-sole {
    color: black;
}
</style>
