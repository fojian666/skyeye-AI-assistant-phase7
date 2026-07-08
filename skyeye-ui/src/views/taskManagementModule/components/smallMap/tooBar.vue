<template>
    <div>
        <div class="toolbar" :style="targetDivStyle" v-if="activeToolIndex === 2">
            <div @click="drawPoint" :class="{ baractive: activeToolBarIndex === 2 }" title="经纬度">
                <span class="icon iconfont icon-position icon-toolbar"></span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="measureLength" :class="{ baractive: activeToolBarIndex === 3 }" title="测距">
                <span class="icon iconfont icon-icon-line-graph icon-toolbar"></span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="startDrawPolygon" :class="{ baractive: activeToolBarIndex === 4 }" title="测面积">
                <span class="icon iconfont icon-duobianxing icon-toolbar"></span>
            </div>
            <span style="color: #cccccc">|</span>
            <div @click="clearDraw" title="清除">
                <span class="icon iconfont icon-qingchu icon-toolbar"></span>
            </div>
        </div>
        <div class="mark-content" v-if="activeToolIndex === 1 "
             :style="{
                left: position.left + 'px',
                top: position.top + 'px',
            }"
             @mousedown="startDrag"
        >
            <div class="mark-top">
                <img src="@/assets/images/mapbar/ditu2.png"/><span class="toolbar-text1">标记</span>
                <span class="isCollapsed-span">
                    <i class="el-icon-arrow-down" title="收起" @click="handleIsCollapsed" v-if="!isCollapsed"></i>
                    <i class="el-icon-caret-right" title="展开" @click="handleIsCollapsed" v-else></i>
                </span>
                <i class="el-icon-close" title="关闭" @click="handleDrawDivClose"></i>
            </div>
            <div :style="{display: !isCollapsed ? 'block' : 'none'}">
                <div class="mark-tool-content">
                    <div class="mark-tool" title="添加点" style="cursor: not-allowed"><img src="@/assets/images/mapbar/marker.png"/></div>
                    <div class="mark-tool" title="添加线" style="cursor: not-allowed"><img src="@/assets/images/mapbar/line.png"/></div>
                    <div class="mark-tool" title="添加面" :class="{ drawbaractive: drawIndex === 3 }" @click="handleDrawPolygon"><img src="@/assets/images/mapbar/polygon.png"/></div>
                    <div class="mark-tool" title="面显隐" :class="{ drawbaractive: drawIndex === 4 }" @click="handleOneClickHiddenOrDisplay">
                        <img src="@/assets/images/mapbar/isshow.png" v-if="onClickHiddenBool"/>
                        <img src="@/assets/images/mapbar/isnotshow.png" v-else/>
                    </div>
                </div>
                <div class="layer-style-setting" >
                    <div class="mark-top2">
                        <span class="toolbar-text1">图层样式</span>
                        <span class="isCollapsed-span">
                            <i class="el-icon-caret-bottom" title="收起" @click="handleLayerIsCollapsed" v-if="!layerIsCollapsed"></i>
                            <i class="el-icon-caret-right" title="展开" @click="handleLayerIsCollapsed" v-else></i>
                        </span>
                    </div>
                    <div class="style-setting-panel" :style="{display: !layerIsCollapsed ? 'block' : 'none'}">
                        <!-- 透明度 -->
                        <div class="setting-item">
                            <label class="setting-label">透明度</label>
                            <el-slider
                                    v-model="shapeOption.fillOpacity"
                                    :min="0"
                                    :max="1"
                                    :step="0.1"
                                    style="flex: 1"
                            ></el-slider>
                        </div>
                        <!-- 颜色选择 -->
                        <div class="setting-item" style="z-index: 9999">
                            <label class="setting-label">颜色</label>
                            <div class="colordiv">
                                <div class="color-preview" :style="{ backgroundColor: shapeOption.fillColor }"></div>
                                <el-color-picker v-model="shapeOption.fillColor" popper-append-to-body="false"  class="custom-color-picker"/>
                            </div>

                        </div>
                        <div class="setting-item" style="z-index: 9999">
                            <label class="setting-label">边线颜色</label>
                            <div class="colordiv">
                                <div class="color-preview" :style="{ backgroundColor: shapeOption.color }"></div>
                                <el-color-picker v-model="shapeOption.color" popper-append-to-body="false"  class="custom-color-picker"/>
                            </div>

                        </div>
                        <!-- 边线透明度 -->
                        <div class="setting-item">
                            <label class="setting-label">边线透明度</label>
                            <el-slider
                                    v-model="shapeOption.opacity"
                                    :min="0"
                                    :max="1"
                                    :step="0.1"
                                    style="flex: 1"
                            ></el-slider>
                        </div>
                        <!-- 边线宽度 -->
                        <div class="setting-item">
                            <label class="setting-label">边线宽度</label>
                            <el-slider
                                    v-model="shapeOption.weight"
                                    :min="0"
                                    :max="20"
                                    :step="1"
                                    style="flex: 1"
                            ></el-slider>
                        </div>
                    </div>
                </div>

                <div class="mark-list">
                    <div class="mark-top-list">
                        <span class="toolbar-text1" >标注列表</span>
                        <span @click="handleIsZhankai">
                            <i class="el-icon-caret-bottom" v-if="isZhankai"></i>
                            <i class="el-icon-caret-right" v-else></i>
                        </span>
                    </div>

                    <div class="mark-list-container" v-if="isZhankai">
                        <div v-for="(item,index) in annotationList" :key="index" class="mark-list-item">
                            <div class="mark-item">
                                <div class="top-item">
                                    <div class="top-item-left">
                                        <img src="@/assets/images/mapbar/mian1.png">
                                        <span
                                              class="plot-name"
                                              @click="handlePylogonLocation(item,event)">{{item.plotName}}</span>
                                    </div>
                                    <div class="marker-edit">
                                        <el-switch
                                                v-model="item.show"
                                                active-color="#3f7ddd"
                                                inactive-color="#ff4949"
                                                @change="handleSwitchChange(item)"
                                        >
                                        </el-switch>
                                        <el-button type="info" icon="el-icon-edit" title="编辑" @click="handleEditPolygon(item)" class="confirm-btn"></el-button>
                                        <el-button type="info" icon="el-icon-delete" title="删除" class="confirm-btn" @click="handleDelete(item)"></el-button>
                                    </div>
                                </div>
                                <div class="bottom-item">
                                    <span><i class="el-icon-time"></i>{{item.createDate}}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                </div>
            </div>


        </div>
        <!-- 弹窗容器：通过 v-show 控制显示/隐藏 -->
        <div class="area-selector-popup" v-show="isShowCounty">
            <!-- 头部：标题 + 关闭按钮 -->
            <div class="popup-header">
                <h3><span class="icon iconfont icon-map-marker icon-toolbar"></span>区划定位</h3>
                <button class="close-btn" @click="closeCounty">×</button>
            </div>
            <!-- 内容区：定位提示 + 区域列表 -->
            <div class="popup-content">
                <div class="location-section">
                    <!-- 定位图标（可替换为 FontAwesome/本地图片） -->
                    <i class="location-icon"></i>
                    <span>当前城市</span>
                </div>
                <!-- 区域网格布局 -->
                <div class="areas-grid">
                    <div
                            v-for="(area, index) in areas"
                            :key="index"
                            class="area-item"
                            @click="selectArea(area)"
                    >
                        {{ area }}
                    </div>
                </div>
            </div>
        </div>
        <el-dialog
                title="编辑属性信息"
                :visible.sync="editLabelVisible"
                :modal="false"
                class="edit-label-dialog"
                :close-on-click-modal="false"
                @close="">
            <el-form class="form_class">
                <el-form-item label="名称:" style="display: flex">
                    <el-input v-model="currentEditObj.plotName" class="select-item"> </el-input>
                </el-form-item>
                <el-form-item label="备注:" style="display: flex">
                    <el-input v-model="currentEditObj.plotDesc" class="select-item"></el-input>
                </el-form-item>
                <el-form-item label="线索:" style="display: flex">
                    <el-select  v-model="currentEditObj.clueId">
                        <el-option
                                v-for="item in currentEditObj.currentRelateClueIdOptions"
                                :key="item.value"
                                :label="item.label"
                                :value="item.value">
                        </el-option>
                    </el-select>

                </el-form-item>
                <div class="btn-uploading">
                    <el-button type="primary" size="medium" @click="confirmEdit">确认 </el-button>
                    <el-button size="medium" @click="handleCancelBtn">取消</el-button>
                </div>
            </el-form>
        </el-dialog>
        <el-dialog
                title="添加面信息"
                :visible.sync="addPolygonVisible"
                :modal="false"
                class="edit-label-dialog"
                :close-on-click-modal="false"
                @close="handleCancelBtn">
            <el-form class="form_class"  :rules="formRules">
                <el-form-item
                        label="名称:"
                        style="display: flex"
                        prop="plotName"
                >
                <el-input v-model="currentAddPolygon.plotName" class="select-item"></el-input>
                </el-form-item>

                <el-form-item
                        label="备注:"
                        style="display: flex"
                        prop="plotDesc"
                >
                <el-input v-model="currentAddPolygon.plotDesc" class="select-item"></el-input>
                </el-form-item>

                <el-form-item
                        label="线索:"
                        style="display: flex"
                        prop="clueId"
                >
                <el-input v-model="currentAddPolygon.clueId" class="select-item" disabled>
                </el-input>
                </el-form-item>
                <div class="btn-uploading">
                    <el-button type="primary" size="medium" @click="confirmAddPolygon">确认 </el-button>
                    <el-button size="medium" @click="handleCancelBtn">取消</el-button>
                </div>
            </el-form>
        </el-dialog>
    </div>

</template>

<script >
import {clearGraphical, drawPoint, measureArea, measureDistance, drawPolygon, formatCurrentTime} from "@/utils/utils";
import {addPlotApi, deletePlotApi, getPlotByClueApi, getPlotByImageApi, updatePlotApi,getMapInfoApi} from "@/api/commonApi";
import {FeatureService, GetFeaturesBySQLParameters} from "@supermap/iclient-leaflet";

 export default {
     name:'taskMgmtToolBar',
     props: {
         map:{ type: Object, required: true },
         currentTask: { type: Object},
         isClueViewPage: { type: Boolean, default: false },
         activeItem: { type: Object, default: () => ({}) },
         oneMapSingle:{Boolean,default: false},
     },
     data(){
         return{
             // 表单验证规则
             formRules: {
                 plotName: [
                     { required: true, message: '名称不能为空', trigger: 'blur' }
                 ],
                 plotDesc: [
                     { required: true, message: '备注不能为空', trigger: 'blur' }
                 ],
             },
             countyService:"",
             datasource_name:"NJXZQ",
             datasets_name:'xzq_new',
             isShowCounty: false, // 控制弹窗显示
             areas: [
                 "鼓楼区", "玄武区", "秦淮区", "建邺区",
                 "栖霞区", "雨花台区", "浦口区", "江宁区",
                 "六合区", "溧水区", "高淳区", "江北新区",
             ], // 区域列表（可从接口动态获取）
             targetDivPosition: {x: 0}, // 初始 X 轴位置
             activeToolBarIndex: 0,
             activeToolIndex: 0,
           selectedClueId:'',//当前选中的线索点
             shapeOption:{
                 fillOpacity: 0.2,
                 color: '#F54124',
                 weight: 3,
                 opacity: 0.8,
                 fillColor:'#F54124',
                 clickable: true
             },
             isZhankai:false,
             isShowArea:false,
             annotationList:[],
             isShowPolygon:true,
             isShowBiaozhuDiv:false,
             editLabelVisible: false,
             currentEditObj: {},
             position: {
                 left: 10, // 初始right值（px）
                 top: 10 // 15vh换算值
             },
             drawIndex:0, //标记或者工具的索引值
             isCollapsed: false,
             addPolygonVisible:false, // 添加面信息弹出框
             currentAddPolygon:{plotName:'',plotDesc:'',clueId:''}, //记录当前添加面信息
             // addPolygonPointsList:[],
             currentViewPoint:null,
             currentRelateClueIdOptions:[],
             isCollapsedToolBar: false,
             onClickHiddenBool: true,
             tempAddlayer:null,
             resultLayer: L.layerGroup(),
             layerIsCollapsed:true,
             lastViewLayer:null
         }
     },
     methods:{
         openCounty() {
             this.isShowCounty = true; // 打开弹窗
         },
         closeCounty() {
             this.isShowCounty = false; // 关闭弹窗
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
         // 根据矩形大小计算缩放级别
         calculateZoomLevel(xmin, ymin, xmax, ymax) {
            // 计算矩形对角线的近似长度（使用简单的近似公式）
            const lngDiff = Math.abs(xmax - xmin);
            const latDiff = Math.abs(ymax - ymin);
            const diagonal = Math.sqrt(lngDiff * lngDiff + latDiff * latDiff);

            // 根据对角线长度计算缩放级别
            // 这是一个经验公式，可能需要根据实际情况调整
            if (diagonal > 10) return 6;
            if (diagonal > 5) return 7;
            if (diagonal > 2) return 8;
            if (diagonal > 1) return 9;
            if (diagonal > 0.5) return 10;
            if (diagonal > 0.2) return 11;
            if (diagonal > 0.1) return 12;
            if (diagonal > 0.05) return 13;
            if (diagonal > 0.02) return 14;
            if (diagonal > 0.01) return 15;
            return 16;
        },

        async selectArea(area) {
             this.resultLayer.clearLayers();
             var sqlParam = new GetFeaturesBySQLParameters({
                 queryParameter: {
                     name: `${this.datasets_name}@${this.datasource_name}`,
                     attributeFilter: `XZQMC='${area}'`
                 },
                 datasetNames: [`${this.datasource_name}:${this.datasets_name}`]
             });
             const vectorData = [];
             const featureService = await new FeatureService(this.countyService);
             const serviceResult = await this.getFeaturesBySQLAsync(featureService, sqlParam);
             serviceResult.features.features.forEach((item) => {
                 vectorData.push(item);
                 const xmin = parseFloat(item.properties.XMIN);
                 const xmax = parseFloat(item.properties.XMAX);
                 const ymin = parseFloat(item.properties.YMIN);
                 const ymax = parseFloat(item.properties.YMAX);
                 const centerLng = (xmin + xmax) / 2;
                 const centerLat = (ymin + ymax) / 2;
                 const zoom = this.calculateZoomLevel(xmin, ymin, xmax, ymax)
                 this.map.setView([centerLat, centerLng],zoom);

             });
             if (vectorData.length > 0) {
                 const geojsonFeature = {
                     type: 'FeatureCollection',
                     features: vectorData
                 };
                 var layer = L.geoJSON(geojsonFeature, {
                     style: {
                         color: 'red',
                         weight: 2,
                         opacity: 1,
                         fillColor: '#ffeb3b',
                         fillOpacity: 0
                     },
                 }).addTo(this.resultLayer);
             }
             this.map.addLayer(this.resultLayer)
         },
         // 画点，显示经纬度
         drawPoint() {
             this.map.off('mousedown');
             this.map.off('mousemove');
             this.map.off('dblclick');
             this.activeToolBarIndex = 2;
             drawPoint(this.map);
         },
         //画线，测量距离
         measureLength(map) {
             this.map.off('mousedown');
             this.map.off('mousemove');
             this.map.off('dblclick');
             this.map.off('contextmenu');
             this.activeToolBarIndex = 3;
             measureDistance(this.map);
         },
         // 画面，测量面积
         startDrawPolygon(map) {
             this.map.off('mousedown');
             this.map.off('mousemove');
             this.map.off('dblclick');
             this.map.off('contextmenu');

             this.activeToolBarIndex = 4;
             measureArea(this.map);
         },
         clearDraw(map) {
             this.activeToolBarIndex = 0;
             clearGraphical(this.map);
         },
         changeBarIndex(index){
            this.activeToolIndex = index;
            this.lastViewLayer = null
         },
         resetBar(){
             this.activeToolIndex = 0
             this.handleRemoveAllLayers()
         },
         handleIsZhankai(){
             this.isZhankai = !this.isZhankai
         },
         handleEditPolygon(item){
             // 解构 item，排除 layer 字段，其余属性全部保留
             const { layer, ...rest } = item;
             // 深拷贝其余属性（避免引用关系导致原数据被意外修改）
             this.currentEditObj = {
                 ...rest,
                 currentRelateClueIdOptions: item.clueId ? [{value:item.clueId,label:item.clueId}] : [],
             };
             this.editLabelVisible = true
         },
         handleCancelBtn(){
             this.editLabelVisible = false
             this.currentEditObj = {}
             this.addPolygonVisible = false
             if (this.currentAddPolygon.layer){
                 this.map.removeLayer(this.currentAddPolygon.layer)
             }
             if(this.tempAddlayer){
                 this.map.removeLayer(this.tempAddlayer)
             }
             this.currentAddPolygon = {}
         },
         async confirmEdit() {
             const res = await updatePlotApi(this.currentEditObj)
             if (res.code === 0){
                 // 找到原始 item 在 markerList 中的索引
                 const index = this.annotationList.findIndex(item => item.id === this.currentEditObj.id);
                 if (index !== -1) {
                     this.annotationList[index].plotName = this.currentEditObj.plotName;
                     this.annotationList[index].plotDesc = this.currentEditObj.plotDesc;
                     this.annotationList[index].clueId = this.currentEditObj.clueId;
                     // this.annotationList[index] = this.currentEditObj;
                 }
             }else{
                 this.$message.error(res.msg)
             }
             this.editLabelVisible = false; // 关闭对话框
             this.currentEditObj = {}
         },
         startDrag(e) {
             if (e.target.closest('.mark-top')) {
                 this.isDragging = true;
                 this.dragStartPos = {
                     x: e.clientX,
                     y: e.clientY
                 };
                 document.addEventListener('mousemove', this.handleDrag);
                 document.addEventListener('mouseup', this.stopDrag);
             }
         },

         handleDrag(e) {
             if (!this.isDragging) return;
             const dx = e.clientX - this.dragStartPos.x;
             const dy = e.clientY - this.dragStartPos.y;
             // this.position = {
             //     right: Math.max(10, this.position.right - dx), // 最小保留10px右边距
             //     top: Math.max(10, this.position.top + dy) // 最小保留10px上边距
             // };
             this.position = {
                 left: this.position.left + dx,
                 top: Math.max(10, this.position.top + dy)
             };
             this.dragStartPos = {
                 x: e.clientX,
                 y: e.clientY
             };
         },

         stopDrag() {
             this.isDragging = false;
             document.removeEventListener('mousemove', this.handleDrag);
             document.removeEventListener('mouseup', this.stopDrag);
         },
         handleIsCollapsed(){
             this.isCollapsed = !this.isCollapsed
         },
         handleLayerIsCollapsed(){
             this.layerIsCollapsed = !this.layerIsCollapsed
        },
         handleNoClue(){
             this.currentAddPolygon.clueId = null
             this.currentAddPolygon.clueName = null
             this.currentAddPolygon.imageId = null
             this.currentAddPolygon.pointName = null
             this.currentAddPolygon.pointId = null
         },
         hanldeSmallMapPageAddPolygon(){
             if (this.currentViewPoint != null && (this.currentViewPoint.clueStatus == 2 || this.currentViewPoint.clueStatus == 3))  {
                 const viewPointLatLng = L.latLng(
                     this.currentViewPoint.latitude, // 从 currentViewPoint 获取纬度
                     this.currentViewPoint.longitude // 获取经度
                 );
             }else{
                 this.handleNoClue()
             }
             const time = formatCurrentTime();
             // this.currentAddPolygon.time = time;
             this.currentAddPolygon.plotName = '多边形-' +  time.replace(/\D/g, '');
             this.addPolygonVisible = true; // 绘制完成后才开启显示
             this.currentAddPolygon.imageId = this.currentTask.imageId ? this.currentTask.imageId : null
         },
         handleClueViewPageAddPolygon(){
             if (this.activeItem != null && (this.activeItem.status == 2 || this.activeItem.status == 3))  {
                 const viewPointLatLng = L.latLng(
                     this.activeItem.latitude, // 从 currentViewPoint 获取纬度
                     this.activeItem.longitude // 获取经度
                 );
                 // 3. 判断点是否在多边形内
                 const isIntersect = this.isPointInPolygon(
                     this.tempAddlayer, // 多边形实例（DRAWPOLYGON）
                     viewPointLatLng // 转换后的查看点
                 );
                 // 4. 根据结果处理业务逻辑
                 if (isIntersect) {
                     this.currentRelateClueIdOptions.push({'value':this.activeItem.clue_id,'label':this.activeItem.clue_id})
                     this.currentAddPolygon.clueId = this.activeItem.clue_id
                     this.currentAddPolygon.clueName = this.activeItem.clue_name
                     // this.currentAddPolygon.pointName = this.activeItem.pointName
                     this.currentAddPolygon.pointId = this.activeItem.point_id
                 } else {
                     this.handleNoClue()
                     console.log("当前查看点与多边形不相交");
                 }
             }else{
                 this.handleNoClue()
             }
             const time = formatCurrentTime();
             this.currentAddPolygon.plotName = '多边形-' +  time.replace(/\D/g, '');
             this.addPolygonVisible = true; // 绘制完成后才开启显示
             this.currentAddPolygon.imageId = this.activeItem.panorama_image_id ? this.activeItem.panorama_image_id : null
         },


         handleDrawPolygon(){
             this.map.off('mousedown');
             this.map.off('mousemove');
             this.map.off('dblclick');
             this.map.off('contextmenu');
             this.drawIndex = 3;
             // 调用 drawPolygon，传入 onFinish 回调
             drawPolygon(
                 this.map,
                 this.shapeOption,
                 (finalPoints,DRAWPOLYGON,allArea) => {
                     // 绘制结束后执行：保存顶点列表 + 显示面板
                     // this.addPolygonPointsList = finalPoints;
                     this.currentAddPolygon.currentRelateClueIdOptions = []
                     this.tempAddlayer = DRAWPOLYGON
                     this.currentAddPolygon.geometry = finalPoints
                     this.currentAddPolygon.plotArea = allArea
                     this.currentAddPolygon.plotType = 'Plygon'
                     if (!DRAWPOLYGON) {
                         console.warn("多边形或查看点未定义");
                         return;
                     }
                     if (this.isClueViewPage){
                         this.handleClueViewPageAddPolygon()
                     }else{
                         this.hanldeSmallMapPageAddPolygon()
                     }

                 }
             );
         },
         async confirmAddPolygon(){
             const param = {
                 ...this.currentAddPolygon,
                 geometry: JSON.stringify(this.currentAddPolygon.geometry),
                 orderIndex: null,
                 color: this.shapeOption.fillColor,
                 transparent: this.shapeOption.fillOpacity,
                 lineColor: this.shapeOption.color,
                 lineWidth: this.shapeOption.weight,
             }
             if(this.currentAddPolygon.clueId === null){
                 this.$message.warning("请关联线索点！")
                 return
             }
             addPlotApi(param).then(res =>{
                 if (res.code == 0){
                     this.$message.success('添加成功')
                     const resPolygon = res.data
                     resPolygon.show = true
                     const layer = new  L.Polygon(JSON.parse(resPolygon.geometry), this.shapeOption)
                     this.map.addLayer(layer) //添加面
                     resPolygon.layer = layer
                     this.annotationList.unshift(resPolygon)
                 }else{
                     this.$message.error(res.msg)
                 }
                 this.map.removeLayer(this.tempAddlayer)
             }).catch(err => {
                 this.$message.error(err);
             });

             this.addPolygonVisible = false
             this.currentAddPolygon = {}
         },

         updataCurrentViewPoint(newVal){ //通过ref调用的函数
             const markerLatLng = newVal.getLatLng();
             const latitude = markerLatLng.lat;  // 纬度
             const longitude = markerLatLng.lng; // 经度
           this.currentAddPolygon.clueId = newVal.options.clueId;
           this.currentAddPolygon.clueName = newVal.options.clueName
           this.currentAddPolygon.pointName = newVal.options.pointName
           this.currentAddPolygon.pointId = newVal.options.pointId
           console.log(this.currentAddPolygon)
             this.currentViewPoint = {
                 latitude: latitude,
                 longitude: longitude,
                 clueId: newVal.options.clueId,
                 clueName: newVal.options.clueName,
                 imageId:newVal.options.imageId,
                 pointName: newVal.options.pointName,
                 pointId: newVal.options.pointId,
                 clueStatus: newVal.options.clueStatus,
             }
         },

         // 判断点是否在多边形内（相交）
         isPointInPolygon(polygon, pointLatLng) {
             if (!polygon || !pointLatLng) return false; // 处理空值
             // 使用 Leaflet 多边形的 contains 方法判断
             return polygon.getBounds().contains(pointLatLng);
         },
         handleSwitchChange(item) {
             // 确保图层实例存在
             if (!item.layer) {
                 console.warn("未找到多边形图层实例");
                 return;
             }
             // 根据开关状态显示/隐藏图层
             if (item.show) {
                 // 显示：添加到地图
                 item.layer.addTo(this.map); // this.map 是你的 Leaflet 地图实例
             } else {
                 // 隐藏：从地图移除
                 this.map.removeLayer(item.layer);
             }
         },

         // 可选：初始化时根据 show 状态设置图层显隐
         initMarkerLayers() {
             this.annotationList.forEach(item => {
                 if (item.show && item.layer) {
                     item.layer.addTo(this.map);
                 } else if (!item.show && item.layer) {
                     this.map.removeLayer(item.layer);
                 }
             });
         },
         handleIsCollapsedToolBar(){
             this.isCollapsedToolBar = !this.isCollapsedToolBar
         },
         handleRemoveAllLayers(){
             this.annotationList.forEach(item => {
                 item.show = false
                 if (item.layer){
                     this.map.removeLayer(item.layer);
                 }
             })
         },
         handleAddAllLayers(){
             this.annotationList.forEach(item => {
                 const layer = L.polygon(JSON.parse(item.geometry), this.shapeOption)
                 item.layer = layer
                 this.map.addLayer(layer)
                 item.show = true
             })
         },
         handleOneClickHiddenOrDisplay(){
             this.drawIndex = 4;
             this.onClickHiddenBool = !this.onClickHiddenBool
             if (!this.onClickHiddenBool){
                 this.handleRemoveAllLayers()
             }else{
                 this.handleAddAllLayers()
             }

         },
         handleDrawDivClose(){
             this.activeToolIndex = 0
             this.handleRemoveAllLayers()
             this.lastViewLayer = null
         },
         async initAnanotationList(){
             if (this.currentTask.imageId){
                 const res = await getPlotByImageApi(this.currentTask.imageId)
                 if (res.code == 0){
                     res.data.forEach(item => {
                         item.show = false
                         const layer = L.polygon(JSON.parse(item.geometry), this.shapeOption)
                         const center = layer.getBounds().getCenter();
                         item.layer = layer
                         item.center = center
                         this.annotationList.push(item)
                     })
                     this.judgeActiveToolIndex()
                 }else{
                     this.$message.error(res.msg)
                 }
             }
         },
         async handleDelete(item) {
             this.$confirm('此操作将永久删除该图斑, 是否继续?', '提示', {
                 confirmButtonText: '确定',
                 cancelButtonText: '取消',
             }).then(async () => {
                 try {
                     const params = {
                         plot_id:item.id
                     }
                     const res = await deletePlotApi(params);
                     if (res.code === 0) {
                         this.$message.success('删除成功');
                         this.annotationList = this.annotationList.filter(i => i.id !== item.id);
                         if (item.layer) {
                             this.map.removeLayer(item.layer);
                         }
                     } else {
                         this.$message.error(res.msg || '删除失败');
                     }
                 } catch (err) {
                     this.$message.error('删除接口调用失败：' + (err.message || err));
                 }
             }).catch(() => {
                 this.$message.info('已取消删除');
             });
         },
         judgeActiveToolIndex(){
             if (this.activeToolIndex === 1){
                 this.annotationList.forEach(item => {
                     const layer = L.polygon(JSON.parse(item.geometry), this.shapeOption)
                     item.layer = layer
                     this.map.addLayer(layer)
                     item.show = true
                 })
             }
         },
         async initClueViewPageAnnotationList() {
             const res = await getPlotByClueApi(this.activeItem.clue_id)
             if (res.code == 0){
                 res.data.forEach(item => {
                     item.show = false
                     const layer = L.polygon(JSON.parse(item.geometry), this.shapeOption)
                     const center = layer.getBounds().getCenter();
                     item.layer = layer
                     item.center = center
                     this.annotationList.push(item)
                 })
                 this.judgeActiveToolIndex()

             }else{
                 this.$message.error(res.msg)
             }
         },
         handlePylogonLocation(item) {
             // 确保图层实例存在
             if (!item.layer) {
                 console.warn("未找到多边形图层实例");
                 return;
             }
             if (item.show) {
                 document.querySelectorAll('.plot-name').forEach(el => {
                   el.style.color = '#fff'; // 恢复默认颜色
                 });
                 event.currentTarget.style.color = '#409EFF'; // 只设置当前点击的
                 if (this.lastViewLayer){
                     this.lastViewLayer.setStyle({
                         color: '#F54124',
                         fillColor:'#F54124',
                     })
                 }

                 this.map.setView(item.center,20)
                 item.layer.setStyle({
                     fillColor: '#00FF00',
                     color: '#00FF00',
                 });
                 this.lastViewLayer = item.layer;
             } else {
                 this.$message.warning('图斑隐藏，无法定位')
             }
         }

     },
     computed: {
         targetDivStyle() {
             return {
                 transform: `translateX(${-this.targetDivPosition.x}px)`
             };
         }
     },
     watch: {
         currentTask: {
             async handler(newVal) {
                 if (!newVal || !newVal.imageId) {
                     return;
                 }
                 this.handleRemoveAllLayers();
                 this.annotationList = [];
                 this.activeToolIndex = 0;
             }
         },
         activeItem: {
             async handler(newVal) {
                 if (!newVal || !newVal.clue_id) {
                     return;
                 }
                 this.handleRemoveAllLayers();
                 this.annotationList = [];
                 this.activeToolIndex = 0;
             }
         },
         activeToolIndex: {
             handler(newVal) {
                 if (newVal === 1){
                     this.annotationList.forEach(item => {
                         const layer = L.polygon(JSON.parse(item.geometry), this.shapeOption)
                         item.layer = layer
                         this.map.addLayer(layer)
                         item.show = true
                     })
                 }else{
                     this.annotationList.forEach(item => {
                         item.show = false
                         if (item.layer){
                             this.map.removeLayer(item.layer);
                         }
                     })
                 }
             },
             immediate: true
         }
     },
     async mounted() {
         const currentArea = window.config.projectCity
         if(currentArea === 'nanjing'){
             this.isShowArea = true;
         }
         const res = await getMapInfoApi();
         if (res.code === 0) {
             this.countyService = res.data.county_service;
             if(res.data.county_datasets_name) {
                 this.datasets_name = res.data.county_datasets_name;
                 this.datasource_name = res.data.county_datasource_name;
             }

         }

     }
 }
</script>

<style scoped>
    @import '@/assets/css/mapCommon.css';
    .color-preview {
        width: calc(100% - 35px);
        height: 30px;
        border: 1px solid #ddd;
        border-radius: 4px;
        margin-bottom: 8px; /* 与颜色选择器保持距离 */
        margin-right: 3px;
    }
    ::v-deep .el-button--info {
        color: #89f4f2;
        background-color: #0b1a39;
        margin-left: 5px;
    }
    ::v-deep .el-button {
        border: 1px solid #0b1a39;
    }


    ::v-deep .edit-label-dialog .el-dialog__body {
        height: auto;
        overflow-y: auto;
    }
    ::v-deep .el-dialog__header {
        padding: 5px 5px 5px;
    }
    ::v-deep .el-dialog__headerbtn {
        position: absolute;
        top: 7px;
        right: 20px;
        padding: 0;
        background: 0 0;
        border: none;
        outline: 0;
        cursor: pointer;
        font-size: 16px;
    }
    ::v-deep .el-icon-close:before {
        content: "\e6db";
        color: white;
    }
    ::v-deep .edit-label-dialog .el-form-item__label {
        color: #fff;
        width: 100px;
        text-align: left;
    }
    .btn-uploading{
        text-align: right;
    }
    ::v-deep .el-button--medium {
        padding: 5px 10px;
        font-size: 14px;
        border-radius: 4px;
    }
    .draw-content{
        display: flex;
    }
    ::v-deep .el-dialog__title {
        line-height: 24px;
        font-size: 18px;
        color: #fff;
    }
    ::v-deep .el-input__inner {
        color: #fff;
    }
    .confirm-btn{
        padding: 0 !important;
    }
    ::v-deep .el-dialog__header, [data-v-28f795ec] .el-dialog__header {
        text-align: center;
        font-weight: 700;
        border-bottom: 1px solid #fff;
    }

    /* 弹窗整体样式 */
    .area-selector-popup {
        position: absolute;
        top: 60px;
        right: 10px;
        width: 320px;
        border: 1px solid #ccc;
        border-radius: 6px;
        background-color: #ccc;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        z-index: 99999;
    }

    /* 头部样式 */
    .popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 4px 6px;
        background-color: #2985C4;
        border-bottom: 1px solid #e5e7eb;
    }

    .popup-header h3 {
        margin: 0;
        font-size: 14px;
        color:#fff;
        font-weight: bold;
    }

    .close-btn {
        background: transparent;
        border: none;
        font-size: 20px;
        cursor: pointer;
        color: #fff;
    }

    .close-btn:hover {
        color: #333;
    }

    /* 内容区样式 */
    .popup-content {
        padding: 8px;
    }

    /* 定位提示行 */
    .location-section {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
    }

    .location-icon {
        display: inline-block;
        width: 20px;
        height: 20px;
        margin-right: 8px;
        /* 替换为实际定位图标（示例用纯色模拟） */
        background-color: #3b82f6;
        mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z' /%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 11a3 3 0 11-6 0 3 3 0 016 0z' /%3E%3C/svg%3E");
        -webkit-mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='currentColor'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z' /%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M15 11a3 3 0 11-6 0 3 3 0 016 0z' /%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-size: contain;
    }

    /* 区域列表：网格布局 */
    .areas-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
    }

    .area-item {
        border-radius: 4px;
        cursor: pointer;
        flex: 0 0 calc(25% - 8px); /* 每行3个区域，自动换行 */
        text-align: center;
        font-size: 14px;
    }

    .area-item:hover {
        background-color: #e5e7eb;
    }
    .top-item-left{
        cursor: default
    }
    .plot-name{
        cursor: pointer;
    }
    .plot-name:hover{
        color: #409EFF;
    }
    .layer-style-setting{
        max-height: 210px;
        overflow-y: auto;
    }

</style>