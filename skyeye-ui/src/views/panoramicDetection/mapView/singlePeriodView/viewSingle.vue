<template>
  <div class="container">
      <div class="card-detail-title">
          <span class="el-icon-close" @click="closeDiv" style="cursor: pointer"></span>
      </div>
    <div class="rm-main">
      <singlePannelView v-if="pannellumDialogVisible"
                            :key="uniquekey" :currentObj="singleObj"
                        @skipMulti="skipMulti"
      >
      </singlePannelView>
    </div>
  </div>

</template>

<script >

import singlePannelView from "@/views/panoramicDetection/mapView/singlePeriodView/singlePannelView.vue";

  export default {
    name: 'viewSingle',
    components: {singlePannelView,},
    props: {
      singleObj:Object
    },
    data() {
      return {
        pannellumDialogVisible: true,
        uniquekey: 1,
      }
    },
    methods:{
      closeDiv(){
        this.$emit('closeDiv',false)
      },
        skipMulti(){
          this.$emit('skipMulti')
        },
    },

    watch: {
      singleObj: {
        handler(newVal,oldVal){
          this.singleObj = newVal
        }
      }
    },
    created() {
    },

  }

</script>



<style scoped>

.container{
  height: 100%;
  width: 100%;
}
.card-detail-title {
    position: absolute;
    top: 0;
    right: 0;
    height: 30px;
    z-index: 9999999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    color: black;
    padding: 8px;
}
.rm-main{
  height: 100%;
  display: flex;
  flex-direction: row;
  justify-content: space-between;
}


</style>