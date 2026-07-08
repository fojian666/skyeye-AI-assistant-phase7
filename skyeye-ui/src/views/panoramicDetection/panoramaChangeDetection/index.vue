<template>
  <div class="panorama-detect">
    <!-- 主内容区 -->
    <main class="main">
      <div class="container">
        <!-- 介绍部分 -->
        <section class="intro-section">
          <h2 class="section-title">多期全景变化检测</h2>
          <p class="section-desc">
            上传两期不同时间的全景图像，系统将通过AI算法自动检测并标记出场景中的变化区域，
            提供精准的变化分析和可视化展示，助力环境监测、城市规划和工程管理。
          </p>
        </section>

        <!-- 顶部独立上传按钮区域 -->
        <section class="upload-btn-section">
          <div class="upload-btn-wrap">
            <el-button
              type="primary"
              icon="el-icon-upload"
              size="medium"
              @click="triggerFileInput('left')"
              class="single-upload-btn"
            >
              上传第一期全景图（前景）
            </el-button>
            <el-button
              type="success"
              icon="el-icon-upload"
              size="medium"
              @click="triggerFileInput('right')"
              class="single-upload-btn"
            >
              上传第二期全景图（后景）
            </el-button>
          </div>
          <!-- 隐藏的文件输入框 -->
          <input
            type="file"
            id="panorama1-upload-top"
            accept="image/*"
            class="hidden-upload-input"
            @change="handleFileChange($event, 'left')"
          />
          <input
            type="file"
            id="panorama2-upload-top"
            accept="image/*"
            class="hidden-upload-input"
            @change="handleFileChange($event, 'right')"
          />
        </section>

        <!-- 全景图展示区域 -->
        <section class="upload-section">
          <!-- 第一期全景图（仅展示） -->
          <div class="upload-card">
            <div class="card-header">
              <h3 class="card-title">第一期全景图（前景）</h3>
              <el-tag type="primary" class="card-badge">已加载: {{ uploadedImages.left?.file?.name || '默认图' }}</el-tag>
            </div>

            <div id="panorama1-container" class="upload-container"
                 @dragover="handleDragOver($event, 'left')"
                 @dragleave="handleDragLeave($event, 'left')"
                 @drop="handleDrop($event, 'left')">
              <div id="panorama1-viewer" class="panorama-viewer" :class="{ active: uploadedImages.left || isDefaultImg === '1' }"></div>

              <!-- 加载层 -->
              <div class="loading-overlay" :class="{ active: loadingStatus.left }">
                <el-icon class="loading-icon">
                  <i class="el-icon-loading"></i>
                </el-icon>
                <p class="loading-text">加载中...</p>
              </div>
            </div>

            <!-- 文件信息 & 移除按钮 -->
            <div class="file-info" :class="{ active: uploadedImages.left }">
              <div class="file-details">
                <p class="file-name">{{ uploadedImages.left?.file?.name || '' }}</p>
                <p class="file-dimensions">
                  {{ uploadedImages.left?.width }} × {{ uploadedImages.left?.height }} px |
                  {{ uploadedImages.left?.file ? (uploadedImages.left.file.size / 1024 / 1024).toFixed(2) : 0 }} MB
                </p>
              </div>
              <el-button type="danger" icon="el-icon-delete" size="mini" @click="resetPanorama('left')">
                移除
              </el-button>
            </div>
          </div>

          <!-- 第二期全景图（仅展示） -->
          <div class="upload-card">
            <div class="card-header">
              <h3 class="card-title">第二期全景图（后景）</h3>
              <el-tag type="success" class="card-badge contrast">已加载: {{ uploadedImages.right?.file?.name || '默认图' }}</el-tag>
            </div>

            <div id="panorama2-container" class="upload-container"
                 @dragover="handleDragOver($event, 'right')"
                 @dragleave="handleDragLeave($event, 'right')"
                 @drop="handleDrop($event, 'right')">
              <div id="panorama2-viewer" class="panorama-viewer" :class="{ active: uploadedImages.right || isDefaultImg === '1' }"></div>

              <!-- 加载层 -->
              <div class="loading-overlay" :class="{ active: loadingStatus.right }">
                <el-icon class="loading-icon">
                  <i class="el-icon-loading"></i>
                </el-icon>
                <p class="loading-text">加载中...</p>
              </div>
            </div>

            <!-- 文件信息 & 移除按钮 -->
            <div class="file-info" :class="{ active: uploadedImages.right }">
              <div class="file-details">
                <p class="file-name">{{ uploadedImages.right?.file?.name || '' }}</p>
                <p class="file-dimensions">
                  {{ uploadedImages.right?.width }} × {{ uploadedImages.right?.height }} px |
                  {{ uploadedImages.right?.file ? (uploadedImages.right.file.size / 1024 / 1024).toFixed(2) : 0 }} MB
                </p>
              </div>
              <el-button type="danger" icon="el-icon-delete" size="mini" @click="resetPanorama('right')">
                移除
              </el-button>
            </div>
          </div>
        </section>

        <!-- 检测按钮 -->
        <section class="detect-section">
          <el-button type="primary" icon="el-icon-search" size="large" @click="handleDetect" :disabled="!isBothUploaded">
            {{ detectBtnText }}
          </el-button>
          <el-button type="warning" icon="el-icon-refresh" size="large" @click="handleResetDetection" style="margin-left: 10px;">
            重新检测
          </el-button>
          <p class="detect-hint" v-show="!isBothUploaded">
            请先上传两期全景图像
          </p>
        </section>

        <!-- 检测结果区域 -->
        <section class="result-section" v-show="showResult">
          <div class="result-header">
            <h3 class="result-title">变化检测结果</h3>
            <el-tag type="success" class="confidence-badge">
              <i class="el-icon-check-circle confidence-icon"></i> 检测完成
            </el-tag>
          </div>
          <div class="result-img" v-html="resultHtml"></div>
        </section>
      </div>
    </main>
  </div>
</template>

<script>
// 关键修改1：组件内局部引入 axios（若已全局挂载，可省略此句，直接使用 this.$axios）
import axios from 'axios'

export default {
  name: 'PanoramaDetect',
  data() {
    return {
      // 上传信息存储
      uploadedImages: {
        left: null,  // 第一期
        right: null  // 第二期
      },
      // 全景图实例
      viewerInstance: {
        left: null,
        right: null
      },
      // 加载状态
      loadingStatus: {
        left: false,
        right: false,
        global: false
      },
      // 同步控制变量
      syncMode: 'both',
      updating: false,
      isDefaultImg: '1',
      // 检测按钮状态
      detectBtnText: '开始检测',
      showResult: false,
      resultHtml: '',
      globalLoading: false
    }
  },
  computed: {
    // 计算属性：判断两期是否都上传完成
    isBothUploaded() {
      return !!this.uploadedImages.left && !!this.uploadedImages.right
    }
  },
  mounted() {
    // 页面挂载后初始化默认全景图
    this.initDefaultViewers()
  },
  destroyed() {
    // 组件销毁时销毁全景图实例
    this.destroyAllViewers()
  },
  methods: {
    // -------------------------- 顶部按钮触发文件选择 --------------------------
    triggerFileInput(type) {
      const inputId = `panorama${type === 'left' ? 1 : 2}-upload-top`
      document.getElementById(inputId).click()
    },

    // -------------------------- 拖拽事件处理 --------------------------
    handleDragOver(e, type) {
      e.preventDefault()
      const container = document.getElementById(`panorama${type === 'left' ? 1 : 2}-container`)
      container.style.borderColor = '#00e5ff'
      container.style.backgroundColor = 'rgba(17, 25, 40, 0.8)'
    },
    handleDragLeave(e, type) {
      e.preventDefault()
      const container = document.getElementById(`panorama${type === 'left' ? 1 : 2}-container`)
      container.style.borderColor = '#00e5ff'
      container.style.backgroundColor = 'rgba(17, 25, 40, 0.5)'
    },
    handleDrop(e, type) {
      e.preventDefault()
      const container = document.getElementById(`panorama${type === 'left' ? 1 : 2}-container`)
      container.style.borderColor = '#00e5ff'
      container.style.backgroundColor = 'rgba(17, 25, 40, 0.5)'
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        this.handleFileUpload(e.dataTransfer.files[0], type)
      }
    },

    // -------------------------- 文件选择与上传 --------------------------
    handleFileChange(e, type) {
      if (e.target.files && e.target.files[0]) {
        this.handleFileUpload(e.target.files[0], type)
        // 重置input值，确保同一文件可重复上传
        e.target.value = ''
      }
    },
    handleFileUpload(file, type) {
      // 开启对应加载状态
      this.loadingStatus[type] = true
      this.isDefaultImg = '0'

      const reader = new FileReader()
      reader.onload = (e) => {
        const img = new Image()
        img.onload = () => {
          // 关闭加载状态
          this.loadingStatus[type] = false

          // 存储上传信息
          this.uploadedImages[type] = {
            file: file,
            url: e.target.result,
            width: img.width,
            height: img.height
          }

          // 初始化对应全景图
          if (type === 'left') {
            this.initLeftViewer(e.target.result)
          } else {
            this.initRightViewer(e.target.result)
            // 绑定右侧全景图同步事件
            this.viewerInstance.right.on('mousedown', () => this.startSync('viewer2'))
            this.viewerInstance.right.on('mouseup', () => this.syncViewers('viewer2'))
          }

          // 绑定左侧鼠标移动事件（十字光标同步）
          this.bindLeftMouseMove()
        }
        img.src = e.target.result
      }
      reader.readAsDataURL(file)
    },

    // -------------------------- 全景图初始化 --------------------------
    initDefaultViewers() {
      // 初始化默认全景图（对应原测试数据）
      const leftUrl = '/panoramaUrl/static/1.JPG'
      const rightUrl = '/panoramaUrl/static/2.JPG'
      this.initLeftViewer(leftUrl)
      this.initRightViewer(rightUrl)
    },
    initLeftViewer(url) {
      // 销毁原有实例
      if (this.viewerInstance.left) {
        this.viewerInstance.left.destroy()
      }
      // 初始化新实例
      this.viewerInstance.left = window.pannellum?.viewer('panorama1-viewer', {
        type: "equirectangular",
        panorama: url,
        autoLoad: true,
        minHfov: 30,
        maxHfov: 120,
        compass: true,
        autoRotate: false,
        showControls: true,
        responsive: true,
        resize: true
      })
      // 绑定事件
      if (this.viewerInstance.left) {
        this.viewerInstance.left.on('mousedown', () => this.startSync('viewer1'))
        this.viewerInstance.left.on('mouseup', () => this.syncViewers('viewer1'))
        this.viewerInstance.left.on('load', () => console.log('第一期全景图加载完成'))
        this.viewerInstance.left.on('error', (err) => {
          console.error('第一期全景图加载错误：', err)
          this.$message?.error('全景图加载失败，请尝试更换图片格式或尺寸')
        })
      }
    },
    initRightViewer(url) {
      // 销毁原有实例
      if (this.viewerInstance.right) {
        this.viewerInstance.right.destroy()
      }
      // 初始化新实例
      this.viewerInstance.right = window.pannellum?.viewer('panorama2-viewer', {
        type: "equirectangular",
        panorama: url,
        autoLoad: true,
        minHfov: 30,
        maxHfov: 120,
        compass: true,
        autoRotate: false,
        showControls: true,
        responsive: true,
        resize: true
      })
      // 绑定事件
      if (this.viewerInstance.right) {
        this.viewerInstance.right.on('load', () => console.log('第二期全景图加载完成'))
        this.viewerInstance.right.on('error', (err) => {
          console.error('第二期全景图加载错误：', err)
          this.$message?.error('全景图加载失败，请尝试更换图片格式或尺寸')
        })
      }
    },

    // -------------------------- 十字光标同步 --------------------------
    bindLeftMouseMove() {
      const panorama1Viewer = document.getElementById('panorama1-viewer')
      if (!panorama1Viewer) return
      // 鼠标移动：同步右侧十字光标
      panorama1Viewer.addEventListener('mousemove', (e) => {
        if (!this.viewerInstance.left || !this.viewerInstance.right || !this.uploadedImages.right) {
          return
        }
        const leftCoords = this.viewerInstance.left.mouseEventToCoords(e)
        if (!leftCoords) return
        this.viewerInstance.right.removeHotSpot('123456')
        this.viewerInstance.right.addHotSpot({
          id: '123456',
          pitch: leftCoords[0],
          yaw: leftCoords[1],
          text: '',
          type: 'info',
          cssClass: 'crosshair'
        })
      })
      // 鼠标离开：移除右侧十字光标
      panorama1Viewer.addEventListener('mouseleave', () => {
        if (this.viewerInstance.right) {
          this.viewerInstance.right.removeHotSpot('123456')
        }
      })
    },

    // -------------------------- 全景图视角同步 --------------------------
    startSync(source) {
      if (this.syncMode === 'none') return
      if (this.syncMode === 'both' ||
        (this.syncMode === 'leftToRight' && source === 'viewer1') ||
        (this.syncMode === 'rightToLeft' && source === 'viewer2')) {
        this.updating = true
      }
    },
    syncViewers(source) {
      if (!this.updating) return
      if (!this.viewerInstance.left || !this.viewerInstance.right) {
        this.updating = false
        return
      }

      if (this.syncMode === 'both') {
        const pitch = source === 'viewer1' ? this.viewerInstance.left.getPitch() : this.viewerInstance.right.getPitch()
        const yaw = source === 'viewer1' ? this.viewerInstance.left.getYaw() : this.viewerInstance.right.getYaw()
        const hfov = source === 'viewer1' ? this.viewerInstance.left.getHfov() : this.viewerInstance.right.getHfov()

        if (source !== 'viewer1') {
          this.viewerInstance.left.setPitch(pitch)
          this.viewerInstance.left.setYaw(yaw)
          this.viewerInstance.left.setHfov(hfov)
        }
        if (source !== 'viewer2') {
          this.viewerInstance.right.setPitch(pitch)
          this.viewerInstance.right.setYaw(yaw)
          this.viewerInstance.right.setHfov(hfov)
        }
      } else if (this.syncMode === 'leftToRight' && source === 'viewer1') {
        this.viewerInstance.right.setPitch(this.viewerInstance.left.getPitch())
        this.viewerInstance.right.setYaw(this.viewerInstance.left.getYaw())
        this.viewerInstance.right.setHfov(this.viewerInstance.left.getHfov())
      } else if (this.syncMode === 'rightToLeft' && source === 'viewer2') {
        this.viewerInstance.left.setPitch(this.viewerInstance.right.getPitch())
        this.viewerInstance.left.setYaw(this.viewerInstance.right.getYaw())
        this.viewerInstance.left.setHfov(this.viewerInstance.right.getHfov())
      }

      this.updating = false
    },

    // -------------------------- 重置全景图 --------------------------
    resetPanorama(type) {
      // 清空上传信息
      this.uploadedImages[type] = null
      // 销毁对应全景图实例
      if (this.viewerInstance[type]) {
        this.viewerInstance[type].destroy()
        this.viewerInstance[type] = null
      }
      // 重置input值（顶部隐藏input）
      document.getElementById(`panorama${type === 'left' ? 1 : 2}-upload-top`).value = ''
      // 恢复默认图
      const defaultUrl = type === 'left' ? '/panoramaUrl/static/1.JPG' : '/panoramaUrl/static/2.JPG'
      type === 'left' ? this.initLeftViewer(defaultUrl) : this.initRightViewer(defaultUrl)
      this.isDefaultImg = '1'
      // 隐藏结果区域
      this.showResult = false
    },
    destroyAllViewers() {
      this.resetPanorama('left')
      this.resetPanorama('right')
    },

    // -------------------------- 检测与重置（核心修改：AJAX 替换为 axios） --------------------------
    handleDetect() {
      if (!this.isBothUploaded) {
        this.$message?.warning('请先上传两期全景图像')
        return
      }

      // 初始化状态
      this.showResult = true
      this.detectBtnText = '检测中...'
      this.globalLoading = true

      // 构建 FormData（原有逻辑不变）
      const formData = new FormData()
      if (this.isDefaultImg !== '1') {
        formData.append('panorama1', this.uploadedImages.left.file, this.uploadedImages.left.file.name)
        formData.append('panorama2', this.uploadedImages.right.file, this.uploadedImages.right.file.name)
      }
      formData.append('isDefaultImg', this.isDefaultImg)

      // 关键修改2：替换 jQuery AJAX 为 axios
      axios.post('/api/panorama/change-detection', formData, {
        // axios 配置：对应 jQuery 的 processData: false、contentType: false
        transformRequest: [data => data], // 禁止 axios 转换 FormData 格式
        contentType: false, // 禁止 axios 设置默认 Content-Type
        timeout: 600000 // 超时时间与原 AJAX 保持一致（10 分钟）
      })
        .then((response) => {
          // 对应 jQuery 的 success 回调
          const res = response.data // axios 响应结果在 data 中
          if (res.code === 0 && res.data && res.data.length > 0) {
            // 更新全景图与结果 HTML
            this.initLeftViewer(res.finalImg)
            let html = ''
            res.data.forEach(item => {
              html += `<div class="result-grid">
              <div class="result-card">
                  <h4 class="result-card-title">前景</h4>
                  <div class="result-img-container">
                      <div class="original-comparison">
                          <img src="${item.file1}" class="original-img" alt="前景"/>
                      </div>
                  </div>
              </div>
              <div class="result-card">
                  <h4 class="result-card-title">后景</h4>
                  <div class="result-img-container">
                      <img src="${item.file2}" class="result-img" alt="后景"/>
                  </div>
              </div>
          </div>`
              html += `<div class="result-grid2">
              <div class="result-card">
                  <h4 class="result-card-title">前景</h4>
                  <div class="result-img-container">
                      <div class="original-comparison">
                          <img src="${item.file1}" class="original-img" alt="前景"/>
                      </div>
                  </div>
              </div>
              <div class="result-card">
                  <h4 class="result-card-title">后景+mask</h4>
                  <div class="result-img-container">
                      <img src="${item.file3}" class="result-img" alt="后景"/>
                  </div>
              </div>
          </div>`
            })
            this.resultHtml = html
            this.$message?.success('检测完成！')
          } else {
            this.$message?.error(`检测失败：${res.msg || '未知错误'}`)
          }
        })
        .catch((error) => {
          // 对应 jQuery 的 error 回调
          console.error('检测请求失败：', error)
          if (error.code === 'ECONNABORTED') {
            // 超时错误判断
            this.$message?.error('检测超时，请重试（建议压缩图片或检查网络）')
          } else {
            // 其他错误信息提取
            const errorMsg = error.response?.data?.msg || error.message || '未知请求错误'
            this.$message?.error(`检测请求失败：${errorMsg}`)
          }
        })
        .finally(() => {
          // 对应 jQuery 的 complete 回调
          // 恢复状态
          this.detectBtnText = '开始检测'
          this.globalLoading = false
        })
    },
    handleResetDetection() {
      // 重置所有状态
      this.destroyAllViewers()
      this.uploadedImages = { left: null, right: null }
      this.showResult = false
      this.resultHtml = ''
      this.isDefaultImg = '1'
      // 滚动到顶部
      window.scrollTo({ top: 0, behavior: 'smooth' })
      // 重新初始化默认全景图
      this.initDefaultViewers()
    }
  }
}
</script>

<style scoped>
@import '@/css/pannellum.css';
@import '@/assets/css/pannellumCommon.css';
.panorama-detect {
  width: 100%;
  height: 100%;
  overflow-y: auto;
  background-color: #f5f7fa;
}

nav ul {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
}

nav ul li a {
  color: #666;
  text-decoration: none;
  font-size: 14px;
}

.menu-toggle {
  border: none;
  background: none;
  color: #00e5ff;
  font-size: 20px;
  cursor: pointer;
}

/* 主内容区 */
.main {
  padding: 30px 0;
}

.container {
  width: 98%;
  margin: 0 auto;
}

.intro-section {
  margin-bottom: 20px;
  text-align: center;
}

.section-title {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.section-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
}

/* 顶部上传按钮区域样式 */
.upload-btn-section {
  text-align: center;
  margin-bottom: 20px;
  padding: 15px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.upload-btn-wrap {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.single-upload-btn {
  padding: 8px 24px;
}

/* 隐藏的文件输入框 */
.hidden-upload-input {
  display: none;
}

/* 全景图展示区域 */
.upload-section {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.upload-card {
  flex: 1;
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.card-title {
  font-size: 16px;
  color: #333;
  margin: 0;
}

.card-badge {
  font-size: 12px;
  white-space: nowrap;
}

/* 全景图容器（仅展示） */
.upload-container {
  position: relative;
  width: 100%;
  height: 600px;
  border: 2px dashed #00e5ff;
  border-radius: 8px;
  background-color: rgba(17, 25, 40, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  overflow: hidden;
  cursor: pointer;
}

/* 全景图容器 */
.panorama-viewer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: none;
  z-index: 10;
}

.panorama-viewer.active {
  display: block;
}

/* 加载层 */
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(17, 25, 40, 0.8);
  display: none;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  z-index: 20;
}

.loading-overlay.active {
  display: flex;
}

.loading-text {
  color: #fff;
  margin-top: 10px;
  font-size: 14px;
}

/* 文件信息 */
.file-info {
  margin-top: 16px;
  padding: 12px;
  background-color: rgba(17, 25, 40, 0.3);
  border-radius: 6px;
  display: none;
  align-items: center;
  justify-content: space-between;
}

.file-info.active {
  display: flex;
}

.file-details {
  flex: 1;
}

.file-name {
  font-size: 14px;
  color: #333;
  margin: 0 0 5px 0;
}

.file-dimensions {
  font-size: 12px;
  color: #666;
  margin: 0;
}

/* 检测按钮区域 */
.detect-section {
  text-align: center;
  margin-bottom: 30px;
}

.detect-hint {
  font-size: 14px;
  color: #999;
  margin-top: 10px;
}

/* 结果区域 */
.result-section {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}

.result-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.result-title {
  font-size: 16px;
  color: #333;
  margin: 0;
}

.result-img {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.result-grid, .result-grid2 {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  width: 100%;
}

.result-card {
  flex: 1;
}

.result-card-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 10px;
}

.result-img-container {
  width: 100%;
  height: 300px;
  overflow: hidden;
  border-radius: 4px;
}

.result-img-container img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 页脚 */
.footer {
  padding: 20px 0;
  text-align: center;
  border-top: 1px solid #eee;
  margin-top: 50px;
}

.copyright {
  font-size: 12px;
  color: #999;
}

/* 十字光标 */
.crosshair {
  width: 30px;
  height: 30px;
  background-size: 100% 100%;
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 999;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .upload-section {
    flex-direction: column;
  }

  .result-grid, .result-grid2 {
    flex-direction: column;
  }

  .upload-btn-wrap {
    flex-direction: column;
    gap: 10px;
  }
}
</style>