<template>
  <div class="main">
    <div class="left-content">
<!--        <div class="top">-->
<!--          <div class="left-tools">-->
<!--              <img src="@/assets/images/tubiao/quanping.png" class="tubiao" style="width: 30px;height: 30px">-->
<!--              <img src="@/assets/images/tubiao/qingchu.png" class="tubiao" style="width: 30px;height: 30px">-->
<!--          </div>-->
<!--          <div class="right-tools">-->
<!--              <img src="@/assets/images/tubiao/zhengfangxing.png" class="tubiao">-->
<!--              <img src="@/assets/images/tubiao/four.png" class="tubiao">-->
<!--              <img src="@/assets/images/tubiao/night.png" class="tubiao">-->
<!--          </div>-->
<!--        </div>-->
      <div class="tabs-container">
        <el-tabs v-model="activeName" @tab-click="handleVideo" style="width: 100%">
          <el-tab-pane label="全部" name="allVideo"></el-tab-pane>
          <el-tab-pane label="无人机" name="UVA"></el-tab-pane>
          <el-tab-pane label="方舱" name="shelter"></el-tab-pane>
        </el-tabs>
      </div>
      <div class="card-container">
        <!-- 根据当前页数和每页数量渲染视频 -->
        <div class="card" v-for="(video, index) in paginatedVideos" :key="index" @click="handleClickCard(video)">
          <div class="box-card">
            <div class="video-img">
              <img src="/static/video-icon.svg">
            </div>
            <div class="video-information">
              <div class="uavName">无人机名称：{{ video.uavName}}</div>
              <p class="recordId">飞行记录编号：{{ video.recordId }}</p>
              <p class="deptTime">时间：{{ video.deptName}}</p>
            </div>
          </div>
        </div>
        <div v-if="!showData" class="no-data">暂无数据</div>
        <!-- 分页组件 -->
        <div class="page">
          <el-pagination
              small
              background
              @current-change="handlePageChange"
              :current-page="currentPage"
              :page-size="pageSize"
              :total="filteredVideos.length"
              layout="total, prev, pager, next"
          />
        </div>
      </div>
    </div>
    <div class="right-content">
      <div class="right-box">
          <div class="tishi" v-if="isShowTishi">
              <img src="@/assets/images/tubiao/video.png">
              <span>请点击左侧卡片查看视频</span>
          </div>
          <div v-else class="tishi" >
              <video
                      class="video"
                      controls
                      id="videoElement"
                      ref = "videoElement" autoplay muted
              >
<!--                  <source :src='videourl' type="video/mp4">-->
<!--                  您的浏览器不支持视频标签。-->
              </video>
          </div>
      </div>
        <div class="map-track" id="map">

        </div>
    </div>
  </div>
</template>

<script>
import { getFlyHistoryTreeListApi, getFlyTraceApi } from '@/api/commonApi'
import VerifypannelViewLeft from "@/views/panoramicDetection/verifyClue/multiComparison/verifypannelViewLeft.vue";
import flvjs from 'flv.js'
export default {
    components: {VerifypannelViewLeft},
  data() {
    return {
      activeName: 'allVideo', // 默认选项是全部
      selectedVideoName: '派出所05',  // 存储选中的视频名称
      currentPage: 1, // 当前页数
      pageSize: 7, // 每页显示多少条数据
      url:'/static/video-icon.svg',
      videoList:[],
      videourl:'',
      isShowTishi: true,
      showData:true,
      pathCoordinates: [],// 飞行轨迹点
      currentPointIndex: 0, // 当前添加到的点的索引
      line: null, // 用于存储当前绘制的线
      intervalId: null, // 绘制轨迹线setInterval的ID，以便后续清除
      fetchInterval:null, // 获取飞行轨迹的定时器
      currentIndex: 0,  // 用来记录当前绘制到哪个坐标点
      currentItem: null, // 无人机id
      currentFlyCoordinates: [],
      currentPostCount:0
    };

  },
  computed: {
    filteredVideos() {
      if (this.activeName === 'allVideo') {
        return this.videoList;
      }
      return this.videoList.filter(video => video.category === this.activeName);
    },
    paginatedVideos() {
      const startIndex = (this.currentPage - 1) * this.pageSize;
      const endIndex = startIndex + this.pageSize;
      return this.filteredVideos.slice(startIndex, endIndex);
    }
  },
  methods: {
      handleVideo(tab, event) {
          this.activeName = tab.name;
      },
      showVideo(video) {
          this.selectedVideoName = video.name;
      },
      handlePageChange(page) {
          this.currentPage = page;
      },
      // 获取视频数据
      async fetchVideoData() {
          try {
              // const res = await axios.get('/api/polls/tests', {
              //     params: {
              //         pageNum: this.currentPage,  // 页码
              //         pageSize: this.pageSize,    // 每页大小
              //     },
              //     timeout: 20000  // 设置超时时间为10000毫秒（10秒）
              // });
              const res = await getFlyHistoryTreeListApi({pageNum: 1, pageSize: 10});
              if (res.code === '0') {
                  this.videoList = res.data;
                  // this.videourl = res.data.data[0].video_url.hls;
                  if (this.videoList.length === 0) {
                      this.showData = false
                  }
              } else {
                  this.$message.error(res.msg);
              }
          } catch (error) {
              if (error.code === 'ECONNABORTED') {
                  this.$message.error('请求超时，请稍后再试');
              } else {
                  this.$message.error('请求失败，请检查网络或联系管理员');
              }
          }
      },
      handleClickCard(item) {
          this.selectedVideoName = item.uav_name;
          this.currentItem = item
          this.videourl = item.play_flv
          this.isShowTishi = false
          // 等待 Vue 更新 DOM
          this.$nextTick(() => {
              this.playVideo('videoElement', this.videourl);
              // this.getFlyTrace()
              this.startFetchingData()
          });
      },

      playVideo(demos, url) {
          let demo = document.getElementById(demos);
          if (videoElement) {
              demo.muted = true
              demo.controls = true
              if (flvjs.isSupported()) {
                  var flvPlayer = flvjs.createPlayer({
                          type: 'flv',
                          hasAudio: false,
                          url: url
                      },
                      {
                          autoCleanupSourceBuffer: true,
                          enableWorker: false, //不启用分离线程
                          enableStashBuffer: true, //关闭IO隐藏缓冲区
                          isLive: true,
                          lazyLoad: false,
                      }
                  );
                  flvPlayer.attachMediaElement(demo);
                  flvPlayer.load(); //加载
              }
              demo.play();
          }
          // demo = document.getElementById(demo);
      },
      initMap() {
          // this.map = L.map('map').setView([32.13738861, 118.997949395], 14);
          this.map = L.map('map').setView([32.5750979, 119.9098536],14);
          // 添加天地图瓦片图层
          const tdtLayer = L.tileLayer('http://t0.tianditu.gov.cn/img_w/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=img&STYLE=default&TILEMATRIXSET=w&FORMAT=tiles&TILEMATRIX={z}&TILEROW={y}&TILECOL={x}&tk=d40cf3cbefc882d9a93de1dab6a5a48c').addTo(this.map);
      },
      addNewPoint(newPoint) {
        if (this.line) {
          // 如果已有line，向其中添加新的坐标点
          this.line.addLatLng(newPoint);
        } else {
          // 如果没有line，创建一个新的polyline对象（红色线条），并添加新的坐标点
          this.line = L.polyline([newPoint], { color: 'red' }).addTo(this.map);
        }

      },
    // 获取飞行轨迹数据
    async getFlyTrace() {
      const para = {
        'recordId': this.currentItem.recordId,
        'deptId': this.currentItem.deptId,
        // 'recordId': '1',
        // 'deptId': '1',
      };

      const res = await getFlyTraceApi(para);
      this.pathCoordinates = res.data.map(point => point.map(Number).reverse());

      // 检查 pathCoordinates 是否为空，且第一个数据存在
      if (this.pathCoordinates.length > 0 && this.pathCoordinates[0]) {
        // 如果是第一次请求
        if (this.currentPostCount === 0) {
          const customIcon = L.icon({
            iconUrl: '../../static/marker-icon.png',
            iconSize: [32, 32],
            iconAnchor: [16, 32],
            popupAnchor: [0, -32],
          });
          // 在 pathCoordinates[0] 绘制 marker
          const marker = L.marker(this.pathCoordinates[0], { icon: customIcon }).addTo(this.map);
          this.map.flyTo(this.pathCoordinates[0], 14);
          marker.on('click', () => {
            console.log('Marker clicked: ', this.pathCoordinates[0]);
          });

          // 遍历路径坐标点并添加
          this.pathCoordinates.forEach(point => {
            this.addNewPoint(point);
          });

          this.currentFlyCoordinates = this.pathCoordinates;
          this.currentPostCount += 1;
        } else {
          // 如果是第二次及以后请求
          const currentAddData = this.pathCoordinates.slice(this.currentFlyCoordinates.length, this.pathCoordinates.length);
          currentAddData.forEach(point => {
            this.addNewPoint(point);
          });
          this.currentFlyCoordinates = this.pathCoordinates;
          this.currentPostCount += 1;
        }
      } else {
        console.log('路径坐标数据为空或无效，无法绘制 marker');
      }
    },
    startFetchingData() {
      // 每隔5秒钟调用一次 getFlyTrace 方法
      this.fetchInterval = setInterval(this.getFlyTrace, 5000)
    },
    stopFetchingData() {
      // 停止定时器
      clearInterval(this.fetchInterval)
    }
  },
  mounted() {
    this.fetchVideoData(); // 组件挂载后立即发送请求
    this.initMap()
    // this.startFetchingData() // 每隔5秒钟获取无人机轨迹数据
  },
  beforeDestroy() {
    // 组件销毁时清除定时器
    this.stopFetchingData()
  },
};
</script>

<style scoped>
.main {
  display: flex; /* 使用 Flexbox 排列子元素 */
  width: 100%;
}
.left-content {
  width: 350px;
  overflow-y: auto;
  height: 100%; /* 填满父容器的高度 */
  position: relative; /* 使分页组件定位相对该容器 */
}
.tabs-container {
  display: flex;
  justify-content: space-around;
}
.box-card {
  display: flex;
  justify-content: space-around;
  margin-top: 5px;
  display: flex;
    cursor: pointer;
}
.card {
  width: 95%;
  height: auto;
  margin: 5px auto;
  border: 1.5px solid #ccc; /* 边框 */
  transition: box-shadow 0.3s ease; /* 为阴影添加过渡效果 */
  background-color: #f7faff;
}
.card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* 鼠标悬停时显示阴影 */
}
.video-img {
  flex-shrink: 0; /* 防止缩小 */
  width: 50px; /* 设置固定宽度 */
  height: 50px; /* 设置固定高度 */
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: 10px;
}

.video-img img {
  width: 100%;
  height: 100%;
  object-fit: cover; /* 图片填充容器 */
}

.video-information {
  flex-grow: 1; /* 让其占满剩余空间 */
  padding-left: 10px; /* 添加左侧间距 */
}
.right-content {
  flex: 1;
  height: 100%;
  display: flex; /* 使用 Flexbox */
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  flex-direction: row;
}
.right-box {
  flex: 1;
  height: 98%;
  background: #e5e9f2;
}
.page {
  position: absolute; /* 使分页组件定位在left-content的底部 */
  left: 0;
  bottom: 10px; /* 距离底部10px */
  width: 100%; /* 让分页组件占满left-content的宽度 */
}
.top{
    height: 30px;
    margin-top: 20px;
    margin-left: 10px;
    display: flex;
    align-items: center;
    justify-content: space-between;

}
.left-tools{
    width: 35%;
    height: 90%;
    background-color: #ebeef5a1;
}
.right-tools {
    width: 60%;
    height: 90%;
    background-color: #ebeef5a1;
}
.left-tools,.right-tools{
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.video{
    width: 100%;
    height: 100%;
}
.tubiao{
    height: 25px;
    width: 25px;
    margin-left: 5px;
    margin-right: 5px;
    cursor: pointer;
}
::v-deep .el-tabs__nav {
    left: 20%;
}
::v-deep .el-tabs__item {
    font-size: 16px;
    font-weight: bold;
}

.tishi{
    display: flex;
    font-size: 20px;
    font-weight: bold;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    flex-direction: column;
}
.tishi img{
    width: 90px;
    height: 90px;
}
.no-data{
    font-size: 18px;
    font-weight: bold;
    text-align: center;
}
.map-track{
    width: 40%;
    height: 98%;
    background-color: bisque;;
}
.uavName{
    font-size:16px;
    font-weight: bold;
}
.recordId,.deptTime{
    font-size:12px;
}
</style>
