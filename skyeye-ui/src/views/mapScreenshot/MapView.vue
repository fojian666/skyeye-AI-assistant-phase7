<template>
    <div id="mapContainer"></div>
</template>

<script>
    import {TiledMapLayer, FeatureService} from '@supermap/iclient-leaflet';
    import {queryCluesDataApi,getMapInfoNoLoginApi} from "@/api/commonApi";
    export default {
        name: "mapViewScreenshot",
        data(){
            return {
                mapService:'',
                gengdiService: '',
                map:{},
                currentMarker:null,
                clue_id:0,
                currentObj:{},
                customIcon : L.icon({
                    iconUrl: '../../static/marker-icon-red.png',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32],
                }),
                circleRadius: window.config.circleRadius
            }
        },
        methods:{
            //初始化天地图
            initMap() {
                //if (process.env.NODE_ENV === "production"){
                    this.map = L.map('mapContainer',
                        {
                            crs: L.CRS.EPSG4326,
                            center: [this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon],//中心坐标
                            zoom: 16,//缩放级别
                            zoomControl: false, //缩放组件
                            attributionControl: false, //去掉右下角logo
                        });
                    const layer = new TiledMapLayer(this.mapService).addTo(this.map)
                    this.gengdiLayer = new TiledMapLayer(this.gengdiService)
                // }else{
                //     this.map = L.map('mapContainer',{zoomControl: false}).setView([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], 14);
                //     // 添加天地图瓦片图层
                //     const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
                //     this.gengdiLayer = new TiledMapLayer(this.gengdiService);
                // }

                //换成红色图标
                this.redIcon = L.icon({
                    // iconUrl: '../../static/marker-icon-red.png', // 替换为红色图标的路径
                    iconUrl: '../../static/iconred.png', // 替换为红色图标的路径
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32],
                });
                const marker = L.marker([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], {icon: this.redIcon}).addTo(this.map);
                this.currentViewPoint = L.marker([this.currentObj.latitude, this.currentObj.longitude], {icon: this.customIcon}).addTo(this.map);
                //绘制圆形范围
                const circle = L.circle([this.currentObj.panorama_image_lat, this.currentObj.panorama_image_lon], {
                    color: 'yellow',         // 圆圈边框颜色
                    fillColor: 'red',     // 圆圈填充颜色
                    fillOpacity: 0,      // 圆圈透明度
                    radius: this.circleRadius,            // 半径（以米为单位）
                    weight: 1
                })
                circle.addTo(this.map);

                this.gengdiLayer.addTo(this.map);
                const lat = this.currentObj.panorama_image_lat;
                const lon = this.currentObj.panorama_image_lon;
                // 创建自定义图标
                const customIcon = L.icon({
                    iconUrl: '../../static/iconblue.png',
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32],
                });
                //换成红色图标
                this.redIcon = L.icon({
                    iconUrl: '../../static/iconred.png', // 替换为红色图标的路径
                    iconSize: [32, 32],
                    iconAnchor: [16, 32],
                    popupAnchor: [0, -32],
                });
                const marker1 = L.marker([this.currentObj.latitude, this.currentObj.longitude], {icon: customIcon})
                // 初始不创建扇形，点击时再绘制
                const markerData = {
                    marker1,
                    sector: null,
                    lat,
                    lon,
                    customIcon,
                    redIcon: this.redIcon,
                    image_id: this.currentObj.task_id
                };
                var yawRad = (this.currentObj.center_x / 14400) * 2 * Math.PI - Math.PI;
                // 将弧度转换为角度
                var yaw = yawRad * 180 / Math.PI;
                this.drawSector(lat,lon,markerData,marker1);
                this.updateSector(yaw);
            },
            drawSector(lat, lon, markerData, marker) {

                // 绘制当前标记的扇形
                const radius = this.circleRadius;
                const startAngle = -30;
                const endAngle = 30;
                const numberOfPoints = 50;
                const latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
                latlngs.push([lat, lon]);
                const sector = L.polygon(latlngs, {
                    color: 'blue',
                    fillColor: '#30f',
                    fillOpacity: 0.2
                }).addTo(this.map);

                // 设置当前点击的标记图标为红色
                marker.setIcon(this.redIcon);
                this.currentMarker = {marker, sector, lat, lon};
                // 更新当前标记的扇形数据
                markerData.sector = sector;

            },
            //绘制扇形
            getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints) {
                const latlngs = [];
                const angleStep = (endAngle - startAngle) / numberOfPoints;
                for (let i = 0; i <= numberOfPoints; i++) {
                    const angle = (startAngle + i * angleStep) * Math.PI / 180; // 转换为弧度
                    const pointLat = lat + (radius / 111320) * Math.cos(angle); // 111320是大约的米/纬度度转换系数
                    const pointLon = lon + (radius / (111320 * Math.cos(lat * Math.PI / 180))) * Math.sin(angle);
                    latlngs.push([pointLat, pointLon]);
                }
                return latlngs;
            },
            //更新扇形
            updateSector(yaw) {
                if (!this.currentMarker) return;
                const {marker, sector, lat, lon} = this.currentMarker;
                const radius = this.circleRadius;
                const startAngle = yaw + this.currentObj.yaw_degree - 30;
                const endAngle = yaw + this.currentObj.yaw_degree + 30;
                const numberOfPoints = 50;
                // 更新扇形坐标
                let latlngs = this.getSectorCoordinates(lat, lon, radius, startAngle, endAngle, numberOfPoints);
                latlngs.push([lat, lon]);
                // 更新地图上的扇形
                sector.setLatLngs(latlngs);
                sector.addTo(this.map)
            },
            async fetchData() {
                const pathArray = window.location.pathname.split('/').filter(Boolean);
                this.clue_id = pathArray[pathArray.length - 1];

                const res = await queryCluesDataApi(this.clue_id);
                if (res.code === 0) {
                    this.currentObj = res.data;
                    this.initMap()
                }
            }
        },
        async mounted() {
            const res = await getMapInfoNoLoginApi();
            if (res.code === 0) {
                this.mapService = res.data.map_service;
                this.center = res.data.center;
                this.gridService = res.data.grid_service;
                this.gridDatasourceName = res.data.grid_datasource_name;
                this.gengdiService = res.data.gengdi_service;
                this.fetchData();
            }

        },
    }
</script>

<style scoped>
    #mapContainer{
        position: absolute;
        width: 100%;
        height: 100%;
        top:0;
        z-index: 99999;
    }
    /deep/.home-header{
        display: none!important;
    }
</style>