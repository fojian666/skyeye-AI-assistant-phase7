<template>
    <div class="one-polygon-container">
        <div class="details-left">
            <div class="header-search">
                <div class="details-left-title">
          <span class="title-text">
            <i class="iconfont icon-zhuzhuangtu"></i>
            <span>搜索条件</span>
          </span>
                    <span class="back-btn" @click="goBack">
            <i class="iconfont icon-fanhui"></i>
            <span>返回</span>
          </span>
                </div>
                <el-form
                        :model="ruleForm"
                        :rules="rules"
                        ref="ruleForm"
                        label-width="100px"
                        label-position="left"
                >
                    <div class="form-content">
                        <el-form-item label="行政区:" prop="region">
                            <el-select
                                    v-model="ruleForm.region"
                                    clearable
                                    placeholder="请选择行政区"
                            >
                                <el-option
                                        v-for="item in regionOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                >
                                </el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="变化前地类:" prop="landTypeBeforeChange">
                            <el-select
                                    v-model="ruleForm.landTypeBeforeChange"
                                    clearable
                                    placeholder="请选择变化前地类"
                            >
                                <el-option
                                        v-for="item in landBeforeOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                >
                                </el-option>
                            </el-select>
                        </el-form-item>
                        <el-form-item label="变化后地类:" prop="landTypeAfterChange">
                            <el-select
                                    v-model="ruleForm.landTypeAfterChange"
                                    clearable
                                    placeholder="请选择变化前地类"
                            >
                                <el-option
                                        v-for="item in landAfterOptions"
                                        :key="item.value"
                                        :label="item.label"
                                        :value="item.value"
                                >
                                </el-option>
                            </el-select>
                        </el-form-item>
                    </div>
                    <div class="btn-content">
                        <el-form-item>
                            <el-button type="primary" size="mini" @click="submitForm"
                            >确定
                            </el-button
                            >
                            <el-button size="mini" class="reset" @click="resetForm"
                            >重置
                            </el-button
                            >
                        </el-form-item>
                    </div>
                </el-form>
            </div>
            <div class="title-text">
                <span>地类变化详情</span>
            </div>
            <div class="list-item">
                <div class="list-item-content">
                    <a-icon class="location-icon" type="environment"/>
                    <span class="list-item-active">{{currentData}}</span>
                </div>
                <a-divider/>
            </div>

            <VirtualList :cindex="this.currentSmid"
                         :listData="listData"
                         class="virtual-list"
                         @changePolygon="changePolygon"
            ></VirtualList>
        </div>
        <div class="details-right">
            <div class="map-container">
                <div id="map1" class="left-map">
                    <ul class="toolbox">
                        <li>
              <span
                      class="icon iconfont icon-gantanhao"
                      title="查属性"
                      @click="viewLeftProperty"
              ></span>
                        </li>
                    </ul>
                </div>
                <div id="map2" class="right-map">
                    <ul class="toolbox">
                        <li>
              <span
                      class="icon iconfont icon-gantanhao"
                      title="查属性"
                      @click="viewRightProperty"
              ></span>
                        </li>
                    </ul>
                </div>
                <div class="map-divider"></div>
                <div class="ai-banner-title title-prev">
                    前景时间：{{ imagesAppendTime[0] }}
                </div>
                <div class="ai-banner-title title-next">
                    后景时间：{{ imagesAppendTime[1] }}
                </div>
            </div>
            <div class="image-container">
                <div class="image-list" ref="imageList">
                    <template v-for="(item, index) in info.sourceCounty">
                        <div class="img" ref="img">
                            <img :src="thumbnailCache[`${item.collectId}_${item.tifId}`]" alt="缩略图"/>
                            <div class="img-info">
                                {{ item.append_time }}
                            </div>
                            <a-radio-group
                                    class="img-btn-container"
                                    :id="item.name"
                                    v-model="item.value"
                                    @change="changeImg($event.target.value, item, index)"
                            >
                                <a-radio :value="0" :disabled="item.disabled[0]"
                                >前景影像
                                </a-radio>
                                <!-- <div class="img-btn-diviver"></div> -->
                                <a-radio :value="1" :disabled="item.disabled[1]"
                                >后景影像
                                </a-radio>
                            </a-radio-group>
                        </div>
                    </template>
                </div>
                <div class="image-list-after"></div>
                <div class="image-list-before"></div>
            </div>
        </div>
<!--        <div class="layer-dialog" v-show="flag">-->
<!--            <div class="container-title">请选择叠加图层</div>-->
<!--            <a-checkbox-->
<!--                    @change="selectLayer($event, item)"-->
<!--                    v-for="item in layerOptions"-->
<!--                    :key="item.count"-->
<!--            >-->
<!--                {{ item.name }}-->
<!--            </a-checkbox>-->
<!--        </div>-->
    </div>
</template>

<script>
    import {calcResolution} from '@/utils/utils';
    import icon from 'leaflet/dist/images/marker-icon.png';
    import {FeatureService, ImageTileLayer, TiledMapLayer} from '@supermap/iclient-leaflet';

    let layer = [];
    export default {
        name: 'SpotView',
        data() {
            return {
                map1: null,//地图容器
                map2: null,
                currentSmid: null,
                currentData: '',
                mapArray: [],
                imageList: [],
                src: require('@/assets/images/LandChange.png'),
                lastImgInfo: {
                    prev: -1,
                    next: -1
                },
                flag: true,
                showTop: false,
                prevTime: 0,
                nextTime: 0,
                coordinate_system: '',
                proj: '',
                imagesAppendTime: [],
                crs: {},
                zoom: 18,
                layerOptions: [],
                front_time: '',
                back_time: '',
                info: {},
                listData: [],
                arcMapArr: [],
                ruleForm: {
                    region: '',
                    landTypeBeforeChange: '',
                    landTypeAfterChange: '',
                },
                rules: {
                    region: [
                        {required: true, message: '请选择行政区', trigger: 'change'}
                    ],
                    landTypeBeforeChange: [
                        {required: true, message: '请选择变化前地类', trigger: 'change'}
                    ],
                    landTypeAfterChange: [
                        {required: true, message: '请选择变化后地类', trigger: 'change'}
                    ]
                },
                regionOptions: [],
                landBeforeOptions: [],
                landAfterOptions: [],
                center: [],
                polygonArea: 0,
                latLng: '',
                leftLineMarker: null,
                rightLineMarker: null,
                thumbnailCache:{}
            }
        },
        async created() {
            this.info = this.$route.query.component.info;
            this.nextTime = this.info.sourceCounty.length - 6;
            this.front_time = this.info.image1.appendTime;
            this.back_time = this.info.image2.appendTime;
            // 设置默认选中的图层
            this.info.sourceCounty.forEach((item) => {
                this.$set(item, 'disabled', [false, false]);
                this.$set(item, 'value', 2);
                item.value = 2;
                if (item.appendTime === this.info.image1.appendTime) {
                    this.$set(item.disabled, 1, true);
                    item.value = 0;
                }
                if (item.appendTime === this.info.image2.appendTime) {
                    this.$set(item.disabled, 0, true);
                    item.value = 1;
                }
            });
            this.imagesAppendTime.push(this.info.image1.appendTime);
            this.imagesAppendTime.push(this.info.image2.appendTime);
            await this.loadAllThumbnails()
        },
        mounted() {
            this.currentSmid = this.$route.query.component.smid
            // this.regionOptions = [{'label': '佛山市顺德区', 'value': '佛山市顺德区'}];
            // this.regionOptions = this.$route.query.component.reginOptions;

            this.$route.query.component.listData.forEach((item) => {
                const xzq = (item.title.split('.')[1]).split('--')[0];
                if (!this.regionOptions.some(existing => existing.value === xzq)) {
                    this.regionOptions.push({label:xzq,value:xzq});
                }
            });
            this.landBeforeOptions = this.$route.query.component.bhqdlOptions;
            this.landAfterOptions = this.$route.query.component.bhhdlOptions;
            this.ruleForm.region = "";
            this.listData = this.$route.query.component.listData.filter((item) => {
                return item.title.includes(this.ruleForm.region);
            });
            this.initSuperMap();

            //叠加图层的，已注释掉
            // this.layerOptions = [
            //     {
            //         "name": "\u987a\u5fb7\u533a",
            //         "url": "http://192.168.60.42:8090/iserver/services/map-ugcv5-sdq20241sdq20241/rest/maps/sdq2024_1%40sdq2024_1",
            //         "owner": "admin",
            //         "source_type": "\u4e1a\u52a1\u6570\u636e\u670d\u52a1",
            //         "coordinate_system": "4326",
            //         "center": "[22.7476441730324, 113.30428774389964]",
            //         "data_type": "",
            //         "datasets_name": "",
            //         "datasource_name": "",
            //         "create_time": "2025-05-28",
            //         "append_time": "2025-05",
            //         "count": 1
            //     }
            // ]
        },
        methods: {
            createMap(mapID) {
                let map = L.map(mapID, {
                    crs: this.crs,
                    maxZoom: 18,
                    minZoom: 1,
                    attributionControl: false,
                    logoControl: false,
                    trackResize: false,
                    // zoomControl: false

                });
                if (mapID == 'map1') {
                    this.map1 = map
                } else {
                    this.map2 = map;
                }

                return map;
            },
            initSuperMap() {
                this.coordinate_system = this.info.image1.coordinateSystem
                this.proj = this.info.image1.proj;
                // this.axios.get(this.info.image1.url + '.json',{ withCredentials: false }).then(res => {
                //     const serveData = res.data;
                //     const minX = serveData.bounds.left.toFixed(2);
                //     const minY = serveData.bounds.bottom.toFixed(2);
                //     const maxX = serveData.bounds.right.toFixed(2);
                //     const maxY = serveData.bounds.top.toFixed(2);

                this.axios
                    .get(this.info.image1.url + `/collections/${this.info.image1.collectId}/items/${this.info.image1.tifId}`+'.json', {withCredentials: false})
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
                        this.crs = L.CRS.EPSG4326
                    }
                    else if (this.coordinate_system === '3857') {
                        this.crs = L.Proj.CRS('EPSG:3857', {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)],
                        })
                    }
                    else {
                        const EPSG = 'EPSG:' + this.coordinate_system;
                        proj4.defs(EPSG, this.proj)
                        this.crs = L.Proj.CRS(EPSG, {
                            resolutions: calcResolution(serveData.visibleScales),
                            bounds: L.bounds([parseFloat(minX), parseFloat(maxY)], [parseFloat(maxX), parseFloat(minY)]),
                            origin: [parseFloat(minX), parseFloat(minY)],
                        })
                    }
                    //判断是否携带SMID跳转，如果携带，就定位到对应的图斑
                    let sqlParam;
                    if (this.currentSmid) {
                        this.currentData = this.listData[this.currentSmid - 1].title
                        this.listData[this.currentSmid - 1].selected = true
                        this.listData[0].selected = false
                        sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                            queryParameter: {
                                name: this.info.dataSource,
                                attributeFilter: `SMID=${this.currentSmid}`
                            },
                            datasetNames: [`${this.info.dataSource}:${this.info.dataSets}`],
                            toIndex: -1
                        });
                    } else {
                        this.currentData = this.listData[0].title
                        sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                            queryParameter: {
                                name: this.info.dataSource,
                                attributeFilter: `SMID=${this.listData[0].SmID}`
                            },
                            datasetNames: [`${this.listData[0].dataSource}:${this.listData[0].dataSets}`],
                            toIndex: -1
                        });
                    }
                    new FeatureService(this.listData[0].dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                        this.center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0])
                        this.polygonArea = serverResult.result.features.features[0].properties.TBMJ
                        const transCenter1 = this.crs.unproject(L.point(this.center[1], this.center[0]))
                        this.latLng = parseFloat(this.center[0]).toFixed(3) + ', ' + parseFloat(this.center[1]).toFixed(3)
                        for (let i = 1; i < 3; i++) {
                            let map = this.createMap(`map${i}`)
                            let obj = {
                                map: null,
                                baseLayer: null,
                                geojsonLayer: null
                            }
                            // obj.baseLayer = L.supermap.tiledMapLayer(this.info[`image${i}`].url).addTo(map)
                            obj.baseLayer =  new ImageTileLayer(this.info[`image${i}`].url, {
                                collectionId:this.info[`image${i}`].collectId,
                                names: [this.info[`image${i}`].tifName],
                                maxZoom:24  //设置最大级别
                            }).addTo(map)

                            map.setView([transCenter1.lat, transCenter1.lng], this.zoom)
                            let geojson = L.geoJSON(serverResult.result.features, {
                                coordsToLatLng: (coords) => {
                                    return this.crs.unproject(L.point(coords[0], coords[1]));
                                },
                                style: () => {
                                    return {color: 'red'}
                                },
                            })
                            geojson.addTo(map)
                            obj.map = map
                            obj.geojsonLayer = geojson
                            this.mapArray.push(obj)
                        }
                        this.linkageZoom()
                    });
                });
            },
            changePolygon(SmID) {
                const currentPolygon = this.listData.filter(item => {
                    if (item.SmID === SmID) {
                        return item
                    }
                })
                this.currentData = currentPolygon[0].title
                this.superChangePolygon(SmID);

            },
            goBack() {
                this.$router.go(-1);
            },
            getCenter(arr) {
                let center = []
                let x = 0, y = 0
                arr.forEach(i => {
                    x += i[0]
                    y += i[1]
                })
                center.push(y / arr.length)
                center.push(x / arr.length)
                return center
            },
            linkageZoom() {
                //监听地图缩放和移动实现联动。
                this.mapArray.map((one) => {
                    //先做监听
                    one.map.on({
                        drag: () => {
                            //再做设置
                            this.mapArray.map((other) => {
                                other != one && other.map.setView([one.map.getCenter().lat, one.map.getCenter().lng])
                            })
                        }, zoom: () => {
                            this.mapArray.map((other) => {
                                other != one && other.map.setZoom(one.map.getZoom())
                            })
                        }
                    })
                })
            },
            //选择图层
            selectLayer(e, item) {
                let layerInfo = {}
                let layerInfo2 = {}

                let checked = e.target.checked
                if (checked) {
                    let newLayer = new L.supermap.tiledMapLayer(item.url).addTo(this.map1);
                    let newLayer2 = new L.supermap.tiledMapLayer(item.url).addTo(this.map2);
                    layerInfo = {
                        layer: newLayer,
                        layer2: newLayer2,
                        name: item.name
                    }
                    layer.push(layerInfo)
                } else {
                    layer.forEach((i, index) => {
                        if (item.name == i.name) {
                            this.map1.removeLayer(i.layer);
                            this.map2.removeLayer(i.layer2);
                            layer.splice(index, 1)
                        }
                    })
                }
            },
            changeImg(v, item, index) {
                let flag = v
                let cilckTime = Date.parse(item.append_time)
                let oldTime = Date.parse(this.imagesAppendTime[1 - parseInt(flag)])
                if (flag == '0') {
                    //前景
                    this.info.sourceCounty.forEach(item1 => {
                        if (item1.append_time !== item.append_time) {
                            this.$set(item1, 'disabled', [false, false]);
                            this.$set(item1, 'value', 2);
                        }
                        if (item1.append_time === this.back_time) {
                            this.$set(item1.disabled, 0, true)
                            item1.value = 1
                        }
                    })
                    this.front_time = item.append_time;
                    if (index !== this.lastImgInfo.prev) {
                        if (cilckTime >= oldTime) {
                            this.info.sourceCounty[index].value = 2
                            this.$message.warning('前景时间需小于后景时间！')
                            return
                        }
                        //判断是不是第一次点击前景
                        if (this.lastImgInfo.prev >= 0) {
                            this.$set(this.info.sourceCounty[index].disabled, 1, true)
                            this.$set(this.info.sourceCounty[this.lastImgInfo.prev].disabled, 1, false)
                            this.info.sourceCounty[index].value = 0
                            this.lastImgInfo.prev = index
                        } else {
                            this.$set(this.info.sourceCounty[index].disabled, 1, true)
                            this.lastImgInfo.prev = index
                        }
                    }
                } else {
                    //后景
                    this.info.sourceCounty.forEach(item1 => {
                        if (item1.append_time !== item.append_time) {
                            this.$set(item1, 'disabled', [false, false]);
                            this.$set(item1, 'value', 2);
                        }
                        if (item1.append_time === this.front_time) {
                            this.$set(item1.disabled, 1, true)
                            item1.value = 0
                        }
                    })
                    this.back_time = item.append_time;
                    if (index !== this.lastImgInfo.next) {
                        if (cilckTime <= oldTime) {
                            this.info.sourceCounty[index].value = 2
                            this.$message.warning('后景影像时间需大于前景影像时间！')
                            return
                        }
                        if (this.lastImgInfo.next >= 0) {
                            this.$set(this.info.sourceCounty[index].disabled, 0, true)
                            this.$set(this.info.sourceCounty[this.lastImgInfo.next].disabled, 0, false)
                            this.info.sourceCounty[index].value = 1
                            this.lastImgInfo.next = index
                        } else {
                            this.$set(this.info.sourceCounty[index].disabled, 0, true)
                            this.lastImgInfo.next = index
                        }
                    }
                }
                let i = parseInt(flag)

                this.mapArray[i].map.removeLayer(this.mapArray[i].baseLayer)
                new TiledMapLayer(item.url).addTo(this.mapArray[i].map)

                this.imagesAppendTime[i] = item.append_time
            },
            superChangePolygon(SmID) {
                if (this.leftLineMarker) {
                    this.mapArray[0].map.removeLayer(this.leftLineMarker)
                }
                if (this.rightLineMarker) {
                    this.mapArray[1].map.removeLayer(this.rightLineMarker)
                }
                let sqlParam = new SuperMap.GetFeaturesBySQLParameters({
                    queryParameter: {
                        attributeFilter: `SMID=${SmID}`
                    },
                    datasetNames: [`${this.info.dataSource}:${this.info.dataSets}`],
                    toIndex: -1
                });
                new FeatureService(this.info.dataPath).getFeaturesBySQL(sqlParam, (serverResult) => {
                    this.center = this.getCenter(serverResult.result.features.features[0].geometry.coordinates[0][0])
                    const transCenter1 = this.crs.unproject(L.point(this.center[1], this.center[0]))
                    for (let i = 0; i < 2; i++) {
                        this.mapArray[i].map.setView([transCenter1.lat, transCenter1.lng], this.zoom)
                        let geojson = L.geoJSON(serverResult.result.features, {
                            coordsToLatLng: (coords) => {
                                return this.crs.unproject(L.point(coords[0], coords[1]));
                            },
                            style: () => {
                                return {color: 'red'}
                            },
                        })
                        geojson.addTo(this.mapArray[i].map)
                        this.mapArray[i].geojsonLayer && this.mapArray[i].map.removeLayer(this.mapArray[i].geojsonLayer)
                        this.mapArray[i].geojsonLayer = geojson
                    }
                })
            },
            submitForm() {
                this.$refs.ruleForm.validate((valid) => {
                    if (!valid) return false
                    if (this.ruleForm.landTypeBeforeChange === this.ruleForm.landTypeAfterChange) {
                        return this.$message.warning('变化前地类和变化后地类不能一样');
                    }
                    const landChangeArr = this.$route.query.component.listData.filter((item) => {
                        return item.title.includes(this.ruleForm.region) && item.title.includes(this.ruleForm.landTypeBeforeChange, item.title.indexOf('--') + 1) && item.title.includes(this.ruleForm.landTypeAfterChange, item.title.indexOf('>'))
                    })
                    if (landChangeArr.length == 0) return this.$message.warning('没有这种变化类型');
                    this.listData = landChangeArr;
                });
            },
            resetForm() {
                this.$refs.ruleForm.resetFields();
                this.listData = this.$route.query.component.listData;
                this.ruleForm.region = this.$route.query.component.defaultRegion;
            },
            viewLeftProperty() {
                //添加一个标记
                this.leftLineMarker = new L.Marker(L.latLng(...this.center), {
                    draggable: false,
                    icon: L.icon({
                        iconUrl: icon,
                        iconSize: [20, 30],// 图片大小
                    })
                });
                //地图上添加标记
                this.mapArray[0].map.addLayer(this.leftLineMarker);
                //标记绑定弹窗显示
                this.leftLineMarker.bindPopup('<div>面积：' + parseFloat(this.polygonArea).toFixed(3) + ' ㎡</div>' + '<div>经纬度：' + this.latLng + '</div>').openPopup();
            },
            viewRightProperty() {
                //添加一个标记
                this.rightLineMarker = new L.Marker(L.latLng(...this.center), {
                    draggable: false,
                    icon: L.icon({
                        iconUrl: icon,
                        iconSize: [20, 30],// 图片大小
                    })
                });
                //地图上添加标记
                this.mapArray[1].map.addLayer(this.rightLineMarker);
                //标记绑定弹窗显示
                this.rightLineMarker.bindPopup('<div>面积：' + parseFloat(this.polygonArea).toFixed(3) + ' ㎡</div>' + '<div>经纬度：' + this.latLng + '</div>').openPopup();
            },
            imgData(){
                this.info.sourceCounty.forEach(item => {
                     this.axios.get(item.url + `/collections/${item.collectId}/items/${item.tifId}`+'.json', {withCredentials: false}).then(res => {
                        const serveData = res.data;
                        return serveData.assets.thumbnail.href
                    })
                })


            },
            async loadAllThumbnails() {
                this.loadingThumbnails = true;
                // 使用 Promise.all 并行请求，提升加载速度
                await Promise.all(
                    this.info.sourceCounty.map(async (item) => {
                        const cacheKey = `${item.collectId}_${item.tifId}`;
                        // 如果缓存中已有，则跳过
                        if (this.thumbnailCache[cacheKey]) return;
                        try {
                            const res = await this.axios.get(
                                `${item.url}/collections/${item.collectId}/items/${item.tifId}.json`,
                                { withCredentials: false }
                            );
                            // 存储到缓存
                            this.$set(this.thumbnailCache, cacheKey, res.data.assets.thumbnail.href);
                        } catch (error) {
                            console.error(`加载缩略图 ${cacheKey} 失败:`, error);
                            this.$set(this.thumbnailCache, cacheKey, "default-thumbnail.jpg"); // 降级处理
                        }
                    })
                );
                this.loadingThumbnails = false;
            },

            // 单个获取缩略图（备用，如果动态新增图片）
            async getThumbnail(url, collectionId, tifId) {
                const cacheKey = `${collectionId}_${tifId}`;

                // 如果缓存存在，直接返回
                if (this.thumbnailCache[cacheKey]) {
                    return this.thumbnailCache[cacheKey];
                }

                try {
                    const res = await this.axios.get(
                        `${url}/collections/${collectionId}/items/${tifId}.json`,
                        { withCredentials: false }
                    );
                    const thumbnailUrl = res.data.assets.thumbnail.href;

                    // 存储到缓存
                    this.$set(this.thumbnailCache, cacheKey, thumbnailUrl);
                    return thumbnailUrl;
                } catch (error) {
                    console.error("获取缩略图失败:", error);
                    return "default-thumbnail.jpg"; // 返回默认图
                }
            },
        },
        components: {
            VirtualList: () => import('@/components/virtual-list')
        },
        computed: {

        }
    }

</script>

<style scoped>
    .one-polygon-container {
        width: 100%;
        height: 100%;
        display: flex;
        background: #0b1a39;
        color: white;
    }

    /*左侧*/
    .details-left {
        width: 20rem;
        padding: 0.5rem;
        position: relative;
        border-right: 0.1rem solid rgb(200, 200, 200);
    }

    .header-search {
        height: 10rem;
        width: 100%;
    }

    .details-left-title {
        height: 2.5rem;
        font-size: 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    .title-text {
        height: 1.4rem;
        margin: 0 0 0.5rem;
    }

    .title-text span {
        font-size: 1rem;
        font-weight: 600;
        margin-left: 0.5rem;
        color:white ;
    }

    .virtual-list {
        top: 15.4rem !important;
    }

    .back-btn {
        border: 0.1rem solid rgb(200, 200, 200);
        border-radius: 0.2rem;
        display: flex;
        justify-content: center;
        align-items: center;
        padding: 0 0.3rem;
        font-size: 0.8rem;
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

    .map-container {
        flex: 1;
        display: flex;
        position: relative;
    }

    #map1,
    #map2 {
        width: 50%;
        position: relative;
    }

    .map-divider {
        position: absolute;
        width: 0.2rem;
        height: 100%;
        background-color: red;
        z-index: 999;
        left: 50%;
        transform: translateX(-50%);
    }

    .ai-banner-title {
        position: absolute;
        top: 2rem;
        background-color: rgba(50, 50, 50, 0.9);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.2rem;
        font-size: 1rem;
        z-index: 999;
    }

    .title-prev {
        left: 50%;
        transform: translateX(-15rem);
    }

    .title-next {
        right: 50%;
        transform: translateX(15rem);
    }

    .image-container {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        height: 12rem;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        overflow: hidden;
    }

    .image-list {
        padding: 0 1rem;
        height: 100%;
        width: 100%;
        display: flex;
        flex-wrap: nowrap;
        position: absolute;
        overflow: auto;
    }

    .image-list-before {
        position: absolute;
        top: 0;
        left: 0;
        height: 100%;
        width: 1rem;
        background-color: white;
        z-index: 998;
    }

    .image-list-after {
        position: absolute;
        top: 0;
        right: 0;
        height: 100%;
        width: 1rem;
        background-color: white;
        z-index: 998;
    }

    .img {
        margin: 0 0.5rem;
        width: calc(100% / 6);
        min-width: calc(100% / 6);
        height: 100%;
        display: inline-flex;
        align-items: center;
        position: relative;
        border: 0.1rem solid rgb(230, 230, 230);
        overflow: hidden;
    }

    .img:hover {
        cursor: pointer;
    }

    .img img {
        width: 100%;
    }

    .img-info {
        position: absolute;
        top: 0.5rem;
        left: 50%;
        transform: translateX(-50%);
        background-color: rgba(50, 50, 50, 0.8);
        padding: 0.3rem 1rem;
        border-radius: 0.2rem;
        text-align: center;
        color: white;
    }

    .img-btn-container {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: rgba(23, 118, 193, 0.9);
        height: 2.5rem;
    }

    ::v-deep(.ant-radio-wrapper) {
        margin: 0 !important;
        color: white;
    }

    ::v-deep(.ant-radio-wrapper span) {
        padding: 0;
    }

    ::v-deep(.ant-radio-wrapper span:nth-child(2)) {
        margin-left: 0.5rem;
    }

    /* .img-btn-diviver {
      height: 50%;
      width: 0.1rem;
      background-color: white;
      margin: 0 1rem;
    } */

    .icon-icon_previous {
        position: absolute;
        top: 50%;
        left: 0;
        transform: translateY(-5%);
        z-index: 999;
    }

    .icon-icon_next {
        position: absolute;
        top: 50%;
        right: 0;
        transform: translateY(-5%);
        z-index: 999;
    }

    .icon-deactivate {
        color: rgba(5, 78, 179, 0.5);
    }

    .icon-icon_next,
    .icon-icon_previous {
        color: rgba(5, 78, 179, 0.9);
    }

    .icon-icon_next:hover,
    .icon-icon_previous:hover {
        cursor: pointer;
        color: rgba(5, 78, 179, 1);
        font-size: 1.1rem;
        transition: all 100ms linear;
    }

    ::-webkit-scrollbar {
        /* 滚动条整体样式 */
        height: 6px;
    }

    ::-webkit-scrollbar-thumb {
        /* 滚动条里的小方块 */
        border-radius: 3px;
        background: #99a9bf;
    }

    ::-webkit-scrollbar-track {
        /* 滚动条里面的轨道 */
        border-radius: 3px;
        background: #d3dce6;
    }

    ::v-deep .el-input--small .el-input__inner {
        height: 1.6rem;
        line-height: 1.6rem;
    }

    ::v-deep .el-form-item__content {
        margin-left: 0 !important;
    }

    .el-button {
        display: block;
    }

    .el-button--mini {
        padding: 3px 10px;
    }

    .el-button + .el-button {
        margin-left: 0;
    }

    .el-select {
        width: 140px;
    }

    .el-form-item--small.el-form-item {
        margin-bottom: 6px;
    }

    .form-content {
        width: 84%;
    }

    .btn-content {
        width: 16%;
        display: flex;
        align-items: flex-end;
    }

    .el-form {
        display: flex;
        justify-content: space-between;
        width: 100%;
    }

    .reset {
        margin-top: 0.4rem;
    }

    .iconfont {
        cursor: pointer;
        font-size: 20px !important;
        color: #000;
    }

    .left-map,
    .right-map {
        position: relative;
    }

    .toolbox {
        position: absolute;
        top: 80px;
        left: 12px;
        z-index: 999;
    }

    .toolbox li {
        list-style: none;
        width: 30px;
        height: 30px;
        border-radius: 15px;
        background-color: #ffffff;
        border: 2px solid rgba(0, 0, 0, 0.2);
        background-clip: padding-box;
        display: flex;
        justify-content: center;
        align-items: center;
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

    .layer-dialog {
        position: absolute;
        background-color: white;
        top: 4rem;
        right: 4rem;
        z-index: 999;
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

    .list-item-content {
        display: flex;
        align-items: center;
        margin-left: 0.5rem;
    }

    ::v-deep(.ant-divider) {
        margin: 1rem 0 !important;
    }

    .list-item-content i {
        color: #3989ca;
        font-size: 1.5rem;
    }

    .list-item-content span {
        font-size: 0.95rem;
        margin-left: 0.5rem;
    }

    .list-item:hover {
        cursor: pointer;
        color: black;
        font-weight: 600;
        transition: all 100ms linear;
    }

    .list-item-active {
        color: rgb(0, 241, 243);
        font-weight: 600;
    }
    ::v-deep .el-form-item--small .el-form-item__label {
        line-height: 32px;
        color: white;
    }
    ::v-deep .el-input--small .el-input__inner {
        color: white;
    }
</style>
