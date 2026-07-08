<template>
    <div class="container">
        <!-- 左边显示图片 -->
        <div class="left-section">
            <h2 class="section-title">图片</h2>
            <div
                    ref="imageContainer"
                    class="image-container"
                    @wheel="handleWheel"
                    @mousedown="handleMouseDown"
                    @mousemove="handleMouseMove"
                    @mouseup="handleMouseUp">
                <img ref="image" :src="picurl" alt="Image" style="width: 100%;height: 100%"/>
            </div>
        </div>
        <!-- 右边显示Leaflet地图 -->
        <div class="right-section">
            <h2 class="section-title">地图</h2>
            <div id="leafletMap"></div>
            <!--			<div-->
            <!--					ref="imageContainer"-->
            <!--					class="image-container">-->
            <!--				<img style="width: 100%;height:100%" src="../../assets/images/UAV/detection_bev_video.gif" alt="Map" />-->
            <!--			</div>-->

        </div>
    </div>
</template>

<script>
    import axios from 'axios';
    import L from 'leaflet';


    export default {
        name: "ImageMap",
        props: {
            picture: {
                type: Object,
                required: true,
            },
        },
        data() {
            return {
                datas: [],//请求返回的数据
                url: 'points',
                map: null,
                isDragging: false,
                startX: 0,
                startY: 0,
                translateX: 0,
                translateY: 0,
                scale: 1,
                picurl: "",
                imageKey: ""
            };
        },
        created() {
            this.datas = this.picture.alarms;
            const apiBaseUrl = 'api';
            this.picurl = `/${apiBaseUrl}/${this.picture.result_path}`
        },
        mounted() {
            // 在mounted生命周期钩子中初始化Leaflet地图
            this.map = L.map('leafletMap',
                {
                    center: [32.502, 118.607],//中心坐标
                    zoom: 10,//缩放级别
                    minZoom: 6,
                    maxZoom: 20,
                    zoomControl: true, //缩放组件
                    attributionControl: false, //去掉右下角logo
                });
            //const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
            this.handleData()
        },
        methods: {
            handleData() {
                const customIcon = L.icon({
                    iconUrl: '../../static/marker-icon.png',
                    iconSize: [32, 40], // Adjust the size according to your icon
                    iconAnchor: [16, 32], // Adjust the anchor point of the icon
                    popupAnchor: [0, -32], // Adjust the popup anchor point
                });
                // 将点添加到地图中
                const marklist = []
                this.datas.forEach(point => {

                    if (point.location.length === 2) { // 确保 location 中有两个坐标值

                        var marker = L.marker([point.location[1], point.location[0]], {icon: customIcon}).addTo(this.map);
                        //const marker = L.marker([point.location[0],point.location[1]]).addTo(this.map);
                        marklist.push(marker.getLatLng())

                        marker.bindPopup(`疑似违法识别类别： ${point.class}`);

                    }
                });
                this.map.fitBounds(marklist);
            },
            handleWheel(event) {
                event.preventDefault();
                const delta = Math.sign(event.deltaY);
                const scaleIncrement = delta * 0.1;
                // 设置最小缩放值
                const minScale = 0.1;
                if (this.scale + scaleIncrement >= minScale) {
                    this.scale += scaleIncrement;
                    this.updateTransform();
                }
            },
            handleMouseDown(event) {
                event.preventDefault();
                this.isDragging = true;
                this.startX = event.clientX - this.translateX;
                this.startY = event.clientY - this.translateY;
            },
            handleMouseMove(event) {
                if (this.isDragging) {
                    this.translateX = event.clientX - this.startX;
                    this.translateY = event.clientY - this.startY;
                    this.updateTransform();
                }
            },
            handleMouseUp() {
                this.isDragging = false;
            },
            updateTransform() {
                const transformValue = `translate(${this.translateX}px, ${this.translateY}px) scale(${this.scale})`;
                this.$refs.image.style.transform = transformValue;
            },
        }
    }
</script>

<style scoped>
    .container {
        display: flex;
        height: 100%;
    }

    .left-section {
        width: 50%;
    }

    .image-container {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        user-select: none;
        border: 1px solid gray;
        height: 90%;
    }

    .right-section {
        flex: 1;
        height: 100%;
    }

    .section-title {
        font-size: 1.5em;
        /*text-align: center;*/
        padding-left: 3px;
        padding-bottom: 6px;
    }

    #leafletMap {
        height: 90%; /* 设置地图容器的高度 */
    }

</style>