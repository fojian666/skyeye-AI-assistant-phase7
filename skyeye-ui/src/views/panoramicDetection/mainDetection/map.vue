<template>
    <div class="gtp-container">
        <div id="mapContainer" style="height: 100%; border: 1px solid lightgray"></div>
    </div>
</template>

<script>
import { FeatureService, GetFeaturesBySQLParameters, TiledMapLayer } from '@supermap/iclient-leaflet';
import { getUploadPoint, getMapInfoApi, getMapInfoApi1 } from '@/api/commonApi';

export default {
    name: 'MapComponent',
    props: {
        activeRow: {
            type: Object,
            required: true
        }
    },
    watch: {
        async activeRow(newValue, oldValue) {
            //根据选中的表格数据更新全景点位
            if (this.drawGeometry && this.drawCircles.length !== 0) {
                this.drawCircles.forEach((item) => {
                    item.circle.remove();
                });
                this.drawGeometry.remove();
                this.drawCircles = [];
                this.drawGeometry = null;
            }
            if (newValue.batch_id) {
                await this.getGridGeometry();
                await this.getPanoramaPoint(newValue.batch_id);
                await this.addPointGeometry();

            } else {
                if (this.center != '' && this.map) {
                    this.map.setView(this.center, 8);
                }
            }
        }
    },
    data() {
        return {
            map: null,
            mapService: '',
            center: '',
            crs: L.CRS.EPSG4326,
            gridService: '',
            layerName:'',
            gridDatasourceName: '',
            gridDatasetsName: '',
            dataSourceName:'',
            datasetsName:'',
            maxZoom:22,
            gisServiceType:'',
            panoramaPoint: [], //全景点坐标
            gridGeometry: [], //网格多边形
            gridCenter: [], //网格中心点
            drawCircles: [], //在地图上加载的所有全景点集合
            drawGeometry: null, //地图上的网格多边形
            gridDataSources: [] //所有的网格数据源
        };
    },
    computed: {},

    methods: {
        initMap() {
          let resolutions = [
            1.40625,
            0.703125,
            0.3515625,
            0.17578125,
            0.087890625,
            0.0439453125,
            0.02197265625,
            0.010986328125,
            0.0054931640625,
            0.00274658203125,
            0.001373291015625,
            0.0006866455078125,
            0.00034332275390625,
            0.000171661376953125,
            0.0000858306884765625,
            0.00004291534423828125,
            0.000021457672119140625,
            0.000010728836059570312,
            0.000005364418029785156
          ];

          let mapCrs = L.Proj.CRS('EPSG:4326', {
            bounds: L.bounds([-180, -90], [180, 90]),
            origin: [-180, 90],
            resolutions: resolutions
          })
            //初始化地图
            this.map = L.map('mapContainer', {
                crs: mapCrs,
                center: this.center, //中心坐标
                zoom: 8, //缩放级别
                zoomControl: false, //缩放组件
                attributionControl: false //去掉右下角logo
            });
            //加载全景点
            if(this.gisServiceType === '1'){
               var layer = new TiledMapLayer(this.mapService, {
                    maxZoom: this.maxZoom,       // 允许地图缩放到 22 级
                    maxNativeZoom: this.maxZoom, // 瓦片服务实际支持的最高级别
                    reuseTiles: false,  // 关键参数：禁止复用旧瓦片
                    updateWhenIdle: true,
                    updateInterval: 200,
                    keepBuffer: 1,      // 仅保留1屏缓冲
                    noWrap: true        // 禁止瓦片重复
                }).addTo(this.map);
            }else if(this.gisServiceType === '2'){

            }else if(this.gisServiceType === '3'){
                //天地图服务
              // 矩阵集id, 决定了在每一级该去请求哪一个identifier对应的切片，如果只有个别几级需要处理minZoom， maxZoom
              let identifier = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
              let matrixIds = [];
              for (var i = 0; i < identifier.length; i++) {
                matrixIds.push({
                  identifier: identifier[i]
                })
              }
              var layer = new L.supermap.WMTSLayer(this.mapService, {
                layer: "img",
                style: "default",
                tilematrixSet: "c",
                format: "tiles",
                matrixIds: matrixIds,
                maxZoom: identifier.length - 1,
              }).addTo(this.map)
              this.map.setView(this.center,13)
            }else {
                var layer = L.tileLayer.wms(this.mapService, {
                    layers: `${this.dataSourceName}:${this.datasetsName}`, // 图层名称
                    format: 'image/png',
                    transparent: true,
                    attribution: "Your Attribution"
                }).addTo(this.map);
            }
        },
        async getPanoramaPoint(batch_id) {
            //获取全景点坐标和上传状态
            const res = await getUploadPoint(batch_id);
            if (res.code !== 0) {
                this.$message.error(res.msg);
                return;
            }
            this.panoramaPoint = res.data;
            this.gridCenter = [this.panoramaPoint[0].latitude, this.panoramaPoint[0].longitude];
            if (this.gridCenter.length !== 0) {
                this.map.setView(this.gridCenter, 10);
            }
        },
        async getGridGeometry() {
            //获取网格数据多边形坐标

            var sqlParam = new GetFeaturesBySQLParameters({
                queryParameter: {
                    name: `${this.gridDatasetsName}@${this.gridDatasourceName}`,
                    attributeFilter: '1=1'
                },
                datasetNames: [`${this.gridDatasourceName}:${this.gridDatasetsName}`]
            });
            const featureService = await new FeatureService(this.gridService);
            const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
            serviceResult.features.features.forEach((item) => {
                this.gridGeometry.push(item);
            });
        },
        addPointGeometry() {
            this.drawCircles = [];
            this.panoramaPoint.forEach((item) => {
                if (item.status === 0) {
                    const circle = L.circle([item.latitude, item.longitude], 80, {
                        color: 'orange',
                        fillColor: 'orange',
                        fillOpacity: 1,
                        weight: 2
                    }).addTo(this.map);
                    circle.bindPopup(item.point_name);
                    this.drawCircles.push({ point_id: item.point_id, circle: circle }); //添加circle对象
                } else {
                    const circle = L.circle([item.latitude, item.longitude], 80, {
                        color: '#32CD32',
                        fillColor: '#32CD32',
                        fillOpacity: 1,
                        weight: 2
                    }).addTo(this.map);
                    circle.bindPopup(item.point_name);
                    this.drawCircles.push({ point_id: item.point_id, circle: circle }); //添加circle对象
                }
            });
            if (this.gridGeometry.length > 0) {
                const geojsonFeature = {
                    type: 'FeatureCollection',
                    features: this.gridGeometry
                };
                this.drawGeometry = L.geoJSON(geojsonFeature, {
                    style: {
                        color: 'red',
                        weight: 2,
                        opacity: 1,
                        fillColor: '#ffeb3b',
                        fillOpacity: 0
                    }
                }).addTo(this.map);
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
    },
    async mounted() {
        const res = await getMapInfoApi();
        if (res.code === 0) {
            this.mapService = res.data.map_service;
            this.center = res.data.center;
            this.gisServiceType=res.data.gis_service_type;
            this.datasetsName = res.data.datasets_name;
            this.dataSourceName = res.data.datasource_name;
            this.gridService = res.data.grid_service;
            this.gridDatasourceName = res.data.grid_datasource_name;
            this.gridDatasetsName = res.data.grid_datasets_name;
            if(this.gridService !==""){
              await this.getGridGeometry();
            }

            await this.initMap();
            await this.addPointGeometry();
        }
    }
};
</script>

<style lang="scss" scoped>
.gtp-container {
    height: 100%;
    width: 100%;
    position: relative;
}
#mapContainer {
    background-color: white; //地图背景颜色
}
.image {
    position: absolute;
    width: 400px;
    height: 250px;
    right: 0;
    bottom: 0;
    z-index: 1000;
    overflow: auto;
}
img {
    width: 100%;
    height: 100%;
    object-fit: fill;
}
</style>
