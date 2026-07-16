<template>
    <div id="mapContainer" class="mapContainer"></div>
</template>

<script>
import { TiledMapLayer } from '@supermap/iclient-leaflet';
import { queryCluesDataApi, getMapInfoApi } from '@/api/commonApi';

export default {
    name: 'mapScreenshot',
    data() {
        return {
            mapService: '',
            gengdiService: '',
            gisServiceType: '1',
            dataSetsName: '',
            dataSourceName: '',
            map: {},
            clue_id: 0,
            currentObj: {},
            customIcon: L.icon({
                iconUrl: '../../static/marker-icon-red.png',
                iconSize: [32, 32],
                iconAnchor: [16, 32],
                popupAnchor: [0, -32]
            }),
            circleRadius: window.config.circleRadius
        };
    },
    methods: {
        //初始化天地图
        initMap() {
            // if (process.env.NODE_ENV === "production"){
            this.map = L.map('mapContainer', {
                crs: L.CRS.EPSG4326,
                center: [this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], //中心坐标
                zoom: 15, //缩放级别
                zoomControl: false, //缩放组件
                attributionControl: false //去掉右下角logo
            });
            const layer = L.tileLayer
                .wms(this.mapService, {
                    layers: `${this.dataSourceName}:${this.dataSetsName}`, // 图层名称
                    format: 'image/png',
                    transparent: true,
                    attribution: 'Your Attribution'
                })
                .addTo(this.map);
            this.gengdiLayer = new TiledMapLayer(this.gengdiService);
            // }else{
            //     this.map = L.map('mapContainer',{zoomControl: false}).setView([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], 15);
            //     // 添加天地图瓦片图层
            //     const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
            //     this.gengdiLayer = new TiledMapLayer(this.gengdiService)
            // }

            //换成红色图标
            this.redIcon = L.icon({
                // iconUrl: '../../static/marker-icon-red.png', // 替换为红色图标的路径
                iconUrl: '../../static/iconred.png', // 替换为红色图标的路径
                iconSize: [32, 32],
                iconAnchor: [16, 32],
                popupAnchor: [0, -32]
            });
            const marker = L.marker([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], { icon: this.redIcon }).addTo(this.map);
            this.currentViewPoint = L.marker([this.currentObj.latitude, this.currentObj.longitude], { icon: this.customIcon }).addTo(this.map);
            //绘制圆形范围
            const circle = L.circle([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], {
                color: 'yellow', // 圆圈边框颜色
                fillColor: 'red', // 圆圈填充颜色
                fillOpacity: 0, // 圆圈透明度
                radius: this.circleRadius, // 半径（以米为单位）
                weight: 1
            });
            circle.addTo(this.map);
        },
        async fetchData() {
            const pathArray = window.location.pathname.split('/').filter(Boolean);
            this.clue_id = pathArray[pathArray.length - 1];

            const res = await queryCluesDataApi(this.clue_id);
            if (res.code === 0) {
                this.currentObj = res.data;
                this.initMap();
            }
        }
    },
    async mounted() {
        const res = await getMapInfoApi();
        if (res.code === 0) {
            this.mapService = res.data.map_service;
            this.center = res.data.center;
            this.gridService = res.data.grid_service;
            this.gridDatasourceName = res.data.grid_datasource_name;
            this.gengdiService = res.data.gengdi_service;
            this.gisServiceType = res.data.gis_service_type;
            this.dataSetsName = res.data.datasets_name;
            this.dataSourceName = res.data.datasource_name;
            this.fetchData();
        }
    }
};
</script>

<style scoped>
#mapContainer {
    position: absolute;
    width: 100%;
    height: 100%;
    top: 0;
    z-index: 99999;
}

/deep/ .home-header {
    display: none !important;
}
</style>
