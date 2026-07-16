<template>
    <div class="se-container">
        <div class="se-container-left">
            <ul class="isp_type" style="vertical-align: middle">
                <li :class="visibleNav === 'qjrh' ? 'isp_type_check' : 'isp_type_unchecked'" @click="changeNav('qjrh')">
                    <span>全景融合</span>
                </li>
                <li :class="visibleNav === 'tpjc' ? 'isp_type_check' : 'isp_type_unchecked'" @click="changeNav('tpjc')">
                    <span>图片检测</span>
                </li>
                <li :class="visibleNav === 'spjc' ? 'isp_type_check' : 'isp_type_unchecked'" @click="changeNav('spjc')">
                    <span>视频检测</span>
                </li>
                <li :class="visibleNav === 'hpjc' ? 'isp_type_check' : 'isp_type_unchecked'" @click="changeNav('hpjc')">
                    <span>航片检测</span>
                </li>
            </ul>
        </div>
        <div class="se-container-right">
            <od-index v-if="visibleNav === 'tpjc'"></od-index>
            <panorama-index v-else-if="visibleNav === 'qjrh'"></panorama-index>
            <video-index v-else-if="visibleNav === 'spjc'"></video-index>
            <changeDetectionInfo v-else></changeDetectionInfo>
        </div>
    </div>
</template>

<script>
import OdIndex from './objectDetection';
import PanoramaIndex from './panoramicStitch';
import VideoIndex from './videoDetection';
import changeDetectionInfo from './satelliteDetection';
export default {
    name: 'IntelligentMonitoring',
    data() {
        return {
            visibleNav: 'qjrh'
        };
    },
    components: {
        OdIndex,
        PanoramaIndex,
        VideoIndex,
        changeDetectionInfo
    },
    methods: {
        changeNav(current_nav) {
            this.visibleNav = current_nav;
        }
    }
};
</script>

<style scoped>
.se-container {
    display: flex;
    z-index: 9;
    position: relative;
}
.se-container-right {
    flex: 1;
}
.se-container-left {
    width: 40px;
    height: 100%;
    background-color: #030e24d9;
}

.isp_module_Content {
    width: 100%;
    height: 100%;
    display: flex;
    margin: 0 0 0 40px;
}

.isp_module_Content iframe {
    width: 100%;
    height: 100%;
    background-color: #061a3fd9;
}

body {
    overflow: hidden;
    font-size: 16px !important;
    font-weight: 400 !important;
}

/* 左边影像分割和变化检测切换css*/
.isp_type li {
    width: 30px;
    text-align: center;
    color: #fff;
    list-style: none;
    font-weight: 600;
    font-size: 16px;
    margin: 12px 0 0 10px;
    height: 175px;
    padding-top: 45px;
}

.isp_type li:hover {
    cursor: pointer;
}

.isp_type_check {
    background: url('@/assets/images/mb-tab-c.png');
    opacity: 1;
}

.isp_type_unchecked {
    background: url('@/assets/images/mb-tab-w.png');
    opacity: 0.8;
}
</style>
