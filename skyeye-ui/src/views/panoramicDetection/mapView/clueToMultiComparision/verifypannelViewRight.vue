<template>
  <div id="panoramaContainerl" style="position: relative">
    <div class="pannellum-layer" v-if="afterLoadPannellum">
    </div>
    <div class="show_jiaodu">
<!--      <div class="gongju_left">{{currentObjRight.imageId}}</div>-->
<!--      <div class="gongju_main">-->
<!--        <i class="el-icon-caret-top"></i>-->
<!--        <span>{{ direction}}</span>-->
<!--      </div>-->
      <div class="gongju_right">{{currentObjRight.batchName}}</div>
    </div>

  </div>
</template>

<script>
  import screenfull from 'screenfull'
  import {
    getOneQuanjingPointClueInfoApi
  } from "@/api/commonApi";

  export default {
    name: 'verifypannelViewRight',
    //接收父组件传递的数据
    props: {
      currentObjRight: Object,
      angleParms:Object,
        currentLeftObj: Object,
    },
    data() {
      return {
        // 图层显示
        afterLoadPannellum: false,
        yawDegree: 0,
        // 全景对象
        viewer: undefined,
        //是否全屏
        isScreenFull: false,
        pitch: 0,
        yaw: 0,
        listData: [],
        currentPitch:0, //当前倾斜角度,
        currentYaw:0,
        currenthfov:0,
        editFlag:false
      };
    },
    beforeDestroy() {
      if (this.viewer) {
        this.viewer.destroy(); // 调用Pannellum的销毁方法，清理资源
      }
      //window.removeEventListener('resize', this.adjustPanoramaSize);
    },
    methods: {
      async fetchData(image_id) {
        if (image_id) {
          const listres = await getOneQuanjingPointClueInfoApi(image_id);
          if (listres.code === 0) {
            this.width = listres.data.image_width;
            this.height = listres.data.image_height
            this.listData = listres.data.clue_list
            this.listData.forEach(item => {
              // 将像素坐标转换为弧度
              var yawRad = (item.center_x / this.width) * 2 * Math.PI - Math.PI;
              var pitchRad = Math.PI / 2 - (item.center_y / this.height) * Math.PI;
              // 将弧度转换为角度
              var yaw = yawRad * 180 / Math.PI;
              var pitch = pitchRad * 180 / Math.PI;
              this.viewer.addHotSpot({
                "id": item.clue_id,
                "pitch": pitch,
                "yaw": yaw,
                "text": item.label,
                "type": 'info',
                "cssClass": "custom-hotspot"
              });
            });
          }else {
            this.$message.error(listres.msg);
          }
        }

      },
      destroyExistingWebGLContext() {
        const canvases = document.querySelectorAll('canvas');
        canvases.forEach(canvas => {
          const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
          if (gl && gl.getExtension('WEBGL_lose_context')) {
            gl.getExtension('WEBGL_lose_context').loseContext();
          }
        });
      },
      //根据全景图路径切换全景图
      handleViewerChange(){
        this.currentPitch = this.angleParms.pitch
        this.currentYaw = this.angleParms.yaw
        this.currenthfov = this.angleParms.hfov
        // 全景图对象
        if (this.currentObjRight.imageId) {
          this.yawDegree = this.currentObjRight.yawDegree;

        this.viewer = pannellum.viewer('panoramaContainerl', {
            "type": "multires",
            "sceneFadeDuration": 1000,
            "autoLoad": true,
            //"compass":true,
            "hfov": 100, // 初始的水平视场角
            "minHfov": 10, // 最小水平视场角
            //"northOffset": 35,
            "yaw": -this.yawDegree,
            // "pitch":0,
            "maxHfov": 120, // 最大水平视场角
            "multiRes": {
                "basePath": '/panoramaUrl/static/layers/' + this.currentObjRight.batchId + '/' + this.currentObjRight.imageId,
                "path": "/%l/%s%y_%x",
                "fallbackPath": "/fallback/%s",
                "extension": "png",
                "tileResolution": this.currentObjRight.tileResolution ? this.currentObjRight.tileResolution : 512,
                "maxLevel": this.currentObjRight.maxLevel ? this.currentObjRight.maxLevel : 5,
                "cubeResolution": this.currentObjRight.cubeResolution ? this.currentObjRight.cubeResolution : 4576
            },
            'draggable': false,
            // "compass": true,// 添加指南针
            // 其他全景图配置...
        });

          // 设置初始的正北方向
          // this.viewer.on('mousedown', this.handleMouseDown);
          // 场景加载完成时添加图层选择节点
          this.viewer.on("load", () => {
            this.afterLoadPannellum = true
          })
          this.viewer.setYaw(this.yawDegree)
          //全程监听yaw的值
          // this.viewer.on('animatefinished', (event) => {
          //   const yaw = this.viewer.getYaw();
          //   const pitch = this.viewer.getPitch();
          //   const hfov = this.viewer.getHfov();
          //   this.currentPitch = pitch
          //   this.currentYaw = yaw
          //   this.currenthfov = hfov
          //   this.$emit('rightangleParm',{'yaw':this.currentYaw,'pitch':this.currentPitch,'hfov':this.currenthfov})
          //
          // })
        }
        // 监听窗口大小改变，screenfull.isFullscreen的值为是否全屏，若是则true，反之false
        window.onresize = () => {
          this.isScreenFull = screenfull.isFullscreen
        }
        this.fetchData(this.currentObjRight.imageId);
      },
        differenceValue() {
            const leftYaw = this.currentLeftObj.yawDegree
            const rightYaw = this.currentObjRight.yawDegree
            const chazhi = Math.abs(leftYaw - rightYaw)
            if (leftYaw>rightYaw){
                return chazhi
            } else{
                return -chazhi
            }
        }
    },
    async mounted() {
      this.handleViewerChange()

    },
    computed: {
      direction() {
        let yaw = parseFloat(this.currentYaw)+ this.yawDegree; // 确保 yaw 是一个数字
        let direction = '';
        // 由于 yaw 可以是 0-360 度，需要处理超过 270 度和小于 0 度的情况
        if (yaw >= 0 && yaw < 90) {
          direction = '东';
        } else if (yaw >= 90 && yaw < 180) {
          direction = '南';
        } else if (yaw >= 180 && yaw < 270) {
          direction = '西';
        } else if (yaw >= 270 && yaw < 360) {
          direction = '北';
        } else if (yaw < 0 || yaw >= 360) {
          // 处理 yaw 值大于 360 或小于 0 的情况
          yaw = (yaw % 360 + 360) % 360; // 确保 yaw 在 0-360 范围内
          if (yaw >= 0 && yaw < 90) {
            direction = '东';
          } else if (yaw >= 90 && yaw < 180) {
            direction = '南';
          } else if (yaw >= 180 && yaw < 270) {
            direction = '西';
          } else if (yaw >= 270) {
            direction = '北';
          }
        }
        // 使用 toFixed(2) 保留两位小数，并转换为字符串
        return direction + yaw.toFixed(2) + '度';
      }
    },
    watch: {
      currentObjRight: {
        handler(newVal) {
          // 假设 newVal 是一个对象，并且包含 task_id 属性
          this.handleViewerChange()
        },
        deep: true // 开启深度监听
      },
      // 监听 angleParms 对象中的每个属性
      angleParms: {
        handler(newVal) {
          if (this.viewer && newVal) {
            this.viewer.setYaw(newVal.yaw+ this.differenceValue());
            this.viewer.setPitch(newVal.pitch);
            this.viewer.setHfov(newVal.hfov);
              this.currentYaw = newVal.yaw + this.differenceValue();
              this.currentPitch = newVal.pitch
              this.currenthfov = newVal.hfov
          }
        },
        deep: true // 开启深度监听
      }
    }
  }
</script>

<style scoped >
  @import '@/css/pannellum.css';

  ::v-deep .transparent-dialog .el-dialog__headerbtn .el-icon-close:hover {
    background-color: transparent;
  }

  ::v-deep .transparent-dialog .el-dialog {
    background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;

  }

  ::v-deep .el-dialog {
    background-color: rgba(0, 0, 0, 0.4); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
    position: absolute;
    right: 50px;
    width: 300px;
  }

  ::v-deep .el-dialog__body {
    height: 500px;
    overflow-y: auto;
  }

  ::v-deep .el-table,  ::v-deep.el-table tr, ::v-deep .el-table th,  ::v-deep.el-table th.el-table__cell {
    background-color: rgba(0, 0, 0, 0.1); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;

  }

  ::v-deep .el-table__body tr:hover > td {
    background-color: rgba(0, 0, 0, 0.6) !important;
  }

  ::v-deep .el-dialog__header, ::v-deep .el-dialog__header {
    text-align: center;
    font-weight: 700;
    border-bottom: 1px solid #fff;
  }

  ::v-deep .el-dialog__title, ::v-deep .el-dialog__title {
    color: #fff;
    font-size: 16px;
  }

  ::v-deep .gt-od-list-data .el-dialog__body {
    padding: 10px; /* 根据需要调整内边距 */
    color: #fff;
  }

  ::v-deep .label-dialog .el-dialog {
    position: absolute;
    bottom: 4%;
    width: 400px;
    left: 50%;
    margin-left: -200px;
    background-color: rgba(0, 0, 0, 0.6); /* 半透明背景 */
    box-shadow: none; /* 可选，移除阴影 */
    z-index: 999;
    color: #fff;
  }

  ::v-deep .gt-toolbar-right {
    position: absolute;
    right: 10px;
    bottom: 20px;
    width: 40px;
    z-index: 99999;
    background-color: rgba(0, 0, 0, 0.5);
    border-radius: 10px;
    margin-bottom: -10px;
  }

  ::v-deep .gt-toolbar-right div {
    width: 40px;
    height: 40px;
    cursor: pointer;
    text-align: center;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  ::v-deep .gt-toolbar-right .gt-alarms-list img {
    width: 24px;
    height: 24px
  }

  ::v-deep .transparent-dialog .el-dialog__header, .label-dialog .el-dialog__header {
    text-align: center;
    font-weight: 700;
    border-bottom: 1px solid #fff;
  }

  ::v-deep .transparent-dialog .el-dialog__title, .label-dialog .el-dialog__title {
    color: #fff;
    font-size: 16px;
  }

  ::v-deep .transparent-dialog .el-dialog__body {
    padding: 10px; /* 根据需要调整内边距 */
    color: #fff;
  }

  ::v-deep .label-dialog .el-form-item__label {
    color: #fff;
    width: 80px;
  }

  ::v-deep .pannellum-layer {
    z-index: 9999;
    position: fixed;
    right: 3%;
    top: 3%;
  }

  ::v-deep .el-radio .el-radio__input .el-radio__inner {
    border-radius: 2px;
  }

  ::v-deep .custom-hotspot {
    width: 25px;
    height: 40px;
    background-image: url("@/assets/images/marker-icon-blue.png");
    background-size: 100% 100%;
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 999;
  }

  ::v-deep .custom-hotspot2 {
    width: 25px;
    height: 40px;
    background-image: url("@/assets/images/marker-icon-red.png");
    background-size: 100% 100%;
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 999;
  }

  ::v-deep .el-radio .el-radio__input.is-checked .el-radio__inner::after {
    box-sizing: content-box;
    content: "";
    transition: transform .15s ease-in .05s;
    transform-origin: center;
    transform: rotate(-45deg) scaleY(1);
    width: 6px;
    height: 3px;
    border: 2px solid white;
    border-top: transparent;
    border-right: transparent;
    text-align: center;
    display: block;
    position: absolute;
    top: 18%;
    left: 18%;
    vertical-align: middle;
    border-radius: 0;
    background: none;
  }


  ::v-deep .gt-img-desc {
    width: 100%;
    text-overflow: clip;
    overflow: hidden;
    height: 20px;
    line-height: 20px;
    white-space: nowrap;
    text-align: center;
    font-size: 10px;
    color: #fff;
    text-shadow: 3px 3px 3px #000;
  }

  ::v-deep div.pnlm-tooltip span {
    visibility: visible;
    width: 100px;
  }

  ::v-deep .map-container {
    position: absolute;
    bottom: 0; /* 距离底部10px */
    left: 0; /* 距离左侧10px */
    width: 400px; /* 设定宽度 */
    height: 300px; /* 设定高度 */
    z-index: 9999999;
    border: 1px solid #fff;
  }

  ::v-deep .leaflet-control-attribution {
    display: none !important;
  }

  .ctrllayers{
    position: absolute;
    left: 300px;
    bottom: 225px; /* 距离底部10px */
    z-index: 9999999;
    width: 90px;
    height: 70px;
    display: flex; /* 使用flex布局 */
    flex-direction: column; /* 子元素按列排列 */
    background: #fff;
    border-radius: 5px;
    box-shadow: 0 0 5px rgba(0,0,0,0.2);
  }
  .ctrllayers label {
    display: flex;
    align-items: center; /* 垂直居中对齐子元素 */
    padding: 5px; /* 移除默认的外边距 */
  }

  .layer-checkbox {
    margin-right: 8px;
  }
  ::v-deep .el-collapse-item__content {
    font-size: 13px;
    color: #303133;
    line-height: 1.769230769230769;
    margin-left: 5px;
  }
  ::v-deep .el-collapse-item__header {
    display: flex;
    align-items: center;
    height: 36px;
    line-height: 36px;
    background-color: #FFF;
    color: #303133;
    cursor: pointer;
    border-bottom: 1px solid #EBEEF5;
    font-size: 13px;
    font-weight: 500;
    transition: border-bottom-color .3s;
    outline: 0;
    margin-left: 10px;
  }
  .show_jiaodu{
    width: 100%;
    height: 60px;
    background-color: rgb(218 213 213 / 35%);
    z-index: 9999999;
    position: absolute;
    display: flex; /* 使用flex布局 */
    justify-content: space-between;
    color:black ;
  }
  .gongju_left{
    width: 30%;
    height: 100%;
    overflow-wrap: break-word; /* 允许在单词内换行 */
    word-break: break-word; /* 允许在单词内换行 */
  }
  .gongju_main{
    width: 30%;
    height: 100%;
    justify-content: space-between;
  }
  .gongju_right{
    width: 30%;
    height: 100%;
  }
  .gongju_main, .gongju_left, .gongju_right{
    display: flex; /* 启用 flexbox */
    justify-content: center; /* 水平居中 */
    align-items: center; /* 垂直居中 */
    overflow-wrap: break-word; /* 允许在单词内换行 */
  }
  ::v-deep div.pnlm-tooltip span {
      visibility: visible;
      width: 100px;
      background-color: rgba(0, 0, 0, 0);
  }
</style>
