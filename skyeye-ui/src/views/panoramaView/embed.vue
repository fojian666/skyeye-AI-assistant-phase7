<template>
    <div class="panorama-embed">
        <div v-if="loading" class="panorama-embed__status" v-loading="true" element-loading-text="正在加载最近全景点..."></div>
        <div v-else-if="error" class="panorama-embed__status panorama-embed__error">{{ error }}</div>
        <verifypannelViewer v-else-if="ready" embed-mode :current-obj="currentObj" :task-list="taskList" :batch-number="batchNumber" />
    </div>
</template>

<script>
import verifypannelViewer from './verifypannelViewer.vue';
import { getNearestPanoramaPointApi, getPanoramaImageApi, getPanoramaPointByCountryApi } from '@/api/commonApi';

function parseCoordinate(value) {
    if (value === undefined || value === null || value === '') {
        return NaN;
    }
    return Number(value);
}

function getDistance(lat1, lon1, lat2, lon2) {
    const toRad = (deg) => (deg * Math.PI) / 180;
    const dLat = toRad(lat2 - lat1);
    const dLon = toRad(lon2 - lon1);
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) + Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) * Math.sin(dLon / 2);
    return 6371000 * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export default {
    name: 'PanoramaEmbed',
    components: { verifypannelViewer },
    data() {
        return {
            loading: true,
            ready: false,
            error: '',
            currentObj: {},
            taskList: [],
            batchNumber: ''
        };
    },
    async mounted() {
        const longitude = parseCoordinate(this.$route.query.longitude || this.$route.query.lon || this.$route.query.lng);
        const latitude = parseCoordinate(this.$route.query.latitude || this.$route.query.lat);

        if (Number.isNaN(longitude) || Number.isNaN(latitude)) {
            this.loading = false;
            this.error = '请在 URL 中传入有效的经度（longitude/lon/lng）和纬度（latitude/lat）';
            return;
        }

        try {
            const nearestRes = await getNearestPanoramaPointApi({ longitude, latitude });
            if (nearestRes.code === 0 && nearestRes.data) {
                await this.initPanorama(nearestRes.data);
                return;
            }
            await this.initPanoramaByClient(longitude, latitude);
        } catch (err) {
            console.error(err);
            try {
                await this.initPanoramaByClient(longitude, latitude);
            } catch (fallbackErr) {
                console.error(fallbackErr);
                this.error = '加载全景失败，请稍后重试';
            }
        } finally {
            this.loading = false;
        }
    },
    methods: {
        async initPanoramaByClient(longitude, latitude) {
            const res = await getPanoramaPointByCountryApi({});
            if (res.code !== 0 || !Array.isArray(res.data) || !res.data.length) {
                this.error = res.msg || '未找到附近的全景点';
                return;
            }

            let nearest = null;
            let minDistance = Infinity;
            res.data.forEach((item) => {
                const itemLat = Number(item.latitude);
                const itemLon = Number(item.longitude);
                if (Number.isNaN(itemLat) || Number.isNaN(itemLon)) {
                    return;
                }
                const distance = getDistance(latitude, longitude, itemLat, itemLon);
                if (distance < minDistance) {
                    minDistance = distance;
                    nearest = item;
                }
            });

            if (!nearest) {
                this.error = '未找到附近的全景点';
                return;
            }

            await this.initPanorama(nearest);
        },
        async initPanorama(pointData) {
            const pointId = pointData.pointId || pointData.point_id || pointData.id;
            if (!pointId) {
                this.error = '最近全景点数据缺少 pointId';
                return;
            }

            const imageRes = await getPanoramaImageApi({ pointId });
            if (imageRes.code !== 0 || !Array.isArray(imageRes.data) || !imageRes.data.length) {
                this.error = imageRes.msg || '未查询到该全景点对应的全景图';
                return;
            }

            this.taskList = imageRes.data;
            const currentTask = this.taskList[0];
            this.batchNumber = String(currentTask.batchId || currentTask.batchNumber || pointData.batchId || pointData.batchNumber || '');
            this.currentObj = {
                imageId: currentTask.imageId,
                imageName: currentTask.imageName,
                pointName: pointData.pointName || currentTask.pointName || '',
                yawDegree: currentTask.yawDegree || 0,
                pointId,
                latitude: pointData.latitude || currentTask.latitude,
                longitude: pointData.longitude || currentTask.longitude
            };
            this.ready = true;
        }
    }
};
</script>

<style scoped>
.panorama-embed {
    width: 100%;
    height: 100vh;
    overflow: hidden;
    background: #000;
}

.panorama-embed__status {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 16px;
}

.panorama-embed__error {
    padding: 24px;
    text-align: center;
    line-height: 1.6;
}
</style>
