<template>
  <el-dialog id="verify-dialog" title="数据校验" :visible.sync="detailVisible" :close-on-click-modal="false" width="50vw">
    <el-row :gutter="20">
      <el-col :span="16" class="step-context" v-loading="isLoading">
        <el-main>
          <h3>{{allStep[currentStep].title}}</h3>
          <p v-for="item in allStep[currentStep].text">{{item}}</p>
        </el-main>
        <el-footer>
          <el-button type="info" @click="handleCancel">取消</el-button>
          <el-button type="primary" @click="handleContinue">继续</el-button>
        </el-footer>
      </el-col>
      <el-col :span="8" class="step-menus">
        <a-steps direction="vertical" :current="currentStep">
          <a-step :title="status[0]" :description="allStep[0].description" />
          <a-step :title="status[1]" :description="allStep[1].description" />
          <a-step :title="status[2]" :description="allStep[2].description" />
          <a-step :title="status[3]" :description="allStep[3].description" />
        </a-steps>
      </el-col>
    </el-row>
  </el-dialog>
</template>

<script>
import axios from "axios";
import {nextTick} from "vue";
import {dataVerifyApi, getGpuFreeMemoryApi, getRedisCountApi} from "@/api/commonApi";
// import config from "@/config/config";

export default {
  name: "verify",
  props:{
    form:Object,
    resultPaths:Array,
  },
  data() {
    return {
      taskIsEmpty:false,
      isLoading:false,
      detailVisible:true,
      allStep:[
        {title:'',text:[],description:'校验文件夹'},
        {title:'',text:[],description:'校验redis'},
        {title:'',text:[],description:'校验内存'},
        {title:'',text:[],description:'校验影像'},
      ],
      currentStep:0,
    }
  },
  watch:{
    detailVisible() {
      if (!this.detailVisible) {
        // 销毁组件
        this.$emit('closeDialog');
      }
    },

  },
  computed:{
    // 根据当前步骤计算并返回所有的步骤完成情况
    status: function (){
      if (this.currentStep===0)
        return ['In Progress','Waiting','Waiting','Waiting']
      else if (this.currentStep===1)
        return ['Finished','In Progress','Waiting','Waiting']
      else if (this.currentStep===2)
        return ['Finished','Finished','In Progress','Waiting']
      else if (this.currentStep===3)
        return ['Finished','Finished','Finished','In Progress']
    }
  },
  mounted() {
    this.isLoading = true
    setTimeout(()=>{this.isLoading=false;this.checkFileName()},1500)
  },
  methods:{
    handleContinue(){
      if (this.currentStep===0){
        this.currentStep += 1
        this.isLoading = true
        setTimeout(() => {this.isLoading = false;this.checkTask()}, 1500)
      }else if (this.currentStep===1){
        this.currentStep += 1
        this.isLoading = true
        setTimeout(()=>{this.isLoading=false;this.checkMemory()},1500)
      }else if (this.currentStep===2){
        this.currentStep += 1
        this.isLoading = true
        setTimeout(()=>{this.isLoading=false;this.data_verify()},1500)
      }else if (this.currentStep===3){
        this.isLoading = true
        setTimeout(()=>{this.detailVisible=false;this.$emit('continueTranslation',this.taskIsEmpty)},1500)
      }
    },
    handleCancel(){
      this.detailVisible = false
      this.$emit('closeDialog');
    },

    checkFileName() {
      //判断文件夹是否重重，给用户提示！
      if (this.resultPaths.includes(this.form.savedPath)) {
        this.allStep[0].title = '文件夹名称重复'
        this.allStep[0].text.push('保存的文件夹名称已经存在，继续执行将覆盖原有数据，是否继续?')
      } else {
        this.handleContinue()
      }
    },

    //判断redis是否有正在运行的项目
    async checkTask(){
      let isEmpty = true
      await getRedisCountApi()
        .then(async response=>{
          if(response.data.error){
            this.$message.error(response.data.msg)
            isEmpty = false
          } else if(response.data.count === 0) {
            isEmpty = true
          } else {
            isEmpty = false
            this.allStep[1].title = '有其他项目在执行'
            this.allStep[1].text.push('redis中存在其他正在运行的项目，继续执行新建的项目，不会打开解译窗口，需要等待其他项目的任务执行完毕后在任务管理中的才能查看解译窗口，是否继续？')
          }
        })
        .catch(error=>{
          this.$message.error(error)
          isEmpty = false
        })
      if (isEmpty){
        this.taskIsEmpty = true
        this.handleContinue()
      }
    },

    //判断所有机器显存是否大于5GB
    async checkMemory(){
      let isEnoughMemory = true
      //请求数据，返回显存小于5GB的ip地址和容量
      await getGpuFreeMemoryApi()
        .then(async response=>{
          if(response.data.error){
            this.$message.error(response.data.msg)
            isEnoughMemory = false
          } else if(response.data.length === 0) {
            isEnoughMemory = true
          } else {
            isEnoughMemory = false
            let messageList = response.data
            this.allStep[2].title = '硬件内存不足'
            this.allStep[2].text.push('请确保GPU剩余显存大于5GB，剩余物理内存大于20GB并且CPU利用率小于50%，检测到下列ip地址的硬件没有满足条件，继续运行任务会失败，是否继续？')
            messageList.forEach(message => {
              this.allStep[2].text.push(`ip地址：${message.ip_address}；剩余显存："${message.gpu_free_memory}"；剩余内存："${message.available_memory}"；CPU利用率："${message.used_cpu}"`);
            });
          }
        })
        .catch(error=>{
          this.$message.error(error)
          isEnoughMemory = false
        })
      if (isEnoughMemory){
        this.handleContinue()
      }
    },

    //检验数据
    async data_verify(){
      let isQualify = true
      const para = {
          'inputPath':this.form.inputPath,
          'inputPathPrev':this.form.inputPathPrev,
          'inputPathNext':this.form.inputNextPath,
      }
      await dataVerifyApi(para)
        .then(async response => {
          if (response.data.status==="success"){
            if (response.data.largedataCount !== 0 || response.data.errorEpsgcount !== 0){
              isQualify = false
              const messageList = response.data.datainfo;
              const dataSize = response.data.dataSize   // 配置文件中的dataSize
              this.allStep[3].title = '影像格式错误'
              this.allStep[3].text.push(`数据中存在大范围数据或错误epsg数据，坐标系请转换为WGS_84或者CGCS2000坐标系;部分数据长宽大于${dataSize}，鉴定为大数据量，检测结果可能会出现内存溢出问题，导致检测失败，是否继续？`)
              messageList.forEach(message => {
                this.allStep[3].text.push(`${message.dataMessage}；坐标系："${message.epsg}"；长度："${message.rasterXSize}"；宽度："${message.rasterYSize}"`);
              });
            }
          }else{
            this.$message.error("数据校验失败，不执行检测，请查看接口是否有误!!!")
            isQualify = false
          }
        })
        .catch(error=>{
          this.$message.error(error)
          isQualify = false
        })
      if (isQualify){
        this.handleContinue()
      }
    },
  },
}
</script>

<style scoped>
.el-main {
  height: 200px;

  h3{
    text-align: center;
    color: red;
    font-weight: bolder;
    margin-bottom: 20px;
  }
  p:first-of-type{
    color: red;
  }
}

.el-footer{
  display: flex;
  align-items: center;
  justify-content: center;
}

</style>
