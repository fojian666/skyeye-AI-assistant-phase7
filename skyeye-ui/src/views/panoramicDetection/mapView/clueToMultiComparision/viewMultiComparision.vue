<template>
  <div class="container">
    <div class="multi-top">
      <el-tooltip class="item" effect="dark" content="关闭" placement="top">
        <el-button icon="el-icon-close" circle @click="closeMultiDiv"></el-button>
      </el-tooltip>
    </div>
    <div class="rm-main">
      <div class="rm_left">
        <verifypannelViewLeft v-if="pannellumDialogVisible"
                              :key="uniquekey" :currentObj="currentObj" @angleParm="handleRightAngleParm"
                              :leftangleParms="leftangleParms"
        >
        </verifypannelViewLeft>
      </div>
      <div class="rm_right">
        <verifypannelViewRight v-if="pannellumDialogVisibleRight"
                               :key="uniquekeyRight" :currentObjRight="currentObjRight"
                               :angleParms="angleParms"
                               @rightangleParm="handleLeftAngleParm"
                               :currentLeftObj="currentObj">

        </verifypannelViewRight>
      </div>
    </div>
  </div>

</template>

<script >

import verifypannelViewLeft from "@/views/panoramicDetection/mapView/clueToMultiComparision/verifypannelViewLeft.vue";
import verifypannelViewRight from "@/views/panoramicDetection/mapView/clueToMultiComparision/verifypannelViewRight.vue";

  export default {
    name: 'viewMultiComparision',
    components: {verifypannelViewLeft, verifypannelViewRight},
    props: {
      // listData:Array,
      rightObj:Object,
      leftObj:Object
    },
    data() {
      return {
        pannellumDialogVisible: true,
        pannellumDialogVisibleRight: true,
        uniquekey: 1,
        uniquekeyRight: 1,
        currentObj: {},
        currentObjRight: {},
        angleParms:{'yaw':0,'pitch':0,'hfov':0},
        leftangleParms:{'yaw':0,'pitch':0,'hfov':0},
      }
    },
    methods:{
      //接收左侧传的角度，更改到右侧
      handleRightAngleParm(data){
        this.angleParms = data
      },
      //接收左侧传的角度，更改到右侧
      handleLeftAngleParm(data){
        this.leftangleParms =data
      },

      //初始化数据
      initData(){
        this.currentObj = this.listData[0]
        this.currentObjRight = this.listData[1]
      },
      closeMultiDiv(){
        this.$emit('closeMultiDiv',false)
      }
    },

    watch: {
      rightObj: {
        handler(newVal, oldVal) {
          this.currentObjRight = newVal
        }
      },
      leftObj: {
        handler(newVal,oldVal){
          this.currentObj = newVal
        }
      }
    },
    created() {
      // console.log(this.rightObj !== null , this.leftObj !== null)
      // if (this.rightObj !== null || this.leftObj !== null){
      //   this.currentObj = this.leftObj
      //   this.currentObjRight = this.rightObj
      // }else {
      //   this.currentObj = this.listData[0]
      //   this.currentObjRight = this.listData[1]
      // }
      this.currentObj = this.leftObj
      this.currentObjRight = this.rightObj
    },
  }

</script>

<style scoped>

.container{
  height: 100%;
  width: 100%;
}
.multi-top{
  height: 5%;
  text-align: right;
  color: black;
}
.rm-main{
  height: 93%;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
  padding-top: 10px;
}
.rm_left{
  width: 49%;
  padding-left: 20px;
}
.rm_right{
  width: 49%;
  padding-right: 20px;
}
</style>