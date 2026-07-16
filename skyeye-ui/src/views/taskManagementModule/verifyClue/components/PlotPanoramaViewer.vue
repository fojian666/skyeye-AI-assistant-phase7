<template>
    <div class="plot-panorama-viewer">
        <div id="plotPanoramaContainer" ref="panoramaContainer" class="panorama-container"></div>
        <div v-if="loading" class="panorama-loading-mask">
            <i class="el-icon-loading image-loading-spinner"></i>
        </div>
        <div v-else-if="!currentImage || !currentImage.imageId" class="empty-placeholder">暂无全景图</div>
    </div>
</template>

<script>
import { updateZoomButtonsState } from '@/utils/panoramaTools';

export default {
    name: 'PlotPanoramaViewer',
    props: {
        currentImage: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            viewer: null,
            loading: false,
            minHfov: 10,
            maxHfov: 120,
            yawDegree: 0,
            relativeYaw: 0
        };
    },
    watch: {
        currentImage: {
            immediate: true,
            deep: true,
            handler(val) {
                if (val && val.imageId) {
                    this.loadPanorama(val);
                } else {
                    this.destroyViewer();
                }
            }
        }
    },
    beforeDestroy() {
        this.destroyViewer();
        window.removeEventListener('resize', this.handleResize);
    },
    methods: {
        destroyExistingWebGLContext() {
            const canvases = document.querySelectorAll('#plotPanoramaContainer canvas');
            canvases.forEach((canvas) => {
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (gl && gl.getExtension('WEBGL_lose_context')) {
                    gl.getExtension('WEBGL_lose_context').loseContext();
                }
            });
        },
        destroyViewer() {
            if (this.viewer) {
                this.viewer.destroy();
                this.viewer = null;
            }
        },
        calcRelativeYaw(azimuth) {
            const yawDegree = this.yawDegree || 0;
            let relativeYaw = (azimuth - yawDegree + 360) % 360;
            if (relativeYaw > 360) {
                relativeYaw -= 360;
            }
            return relativeYaw;
        },
        emitYawChange() {
            if (!this.viewer) return;
            this.$emit('yaw-change', {
                yaw: this.viewer.getYaw(),
                pitch: this.viewer.getPitch(),
                hfov: this.viewer.getHfov(),
                originYaw: this.yawDegree
            });
        },
        handleResize() {
            if (!this.viewer) return;
            this.viewer.resize();
        },
        async loadPanorama(image) {
            if (!image || !image.imageId) return;
            this.loading = true;
            this.yawDegree = image.yawDegree || 0;
            this.relativeYaw = this.calcRelativeYaw(0);

            this.destroyViewer();
            this.destroyExistingWebGLContext();

            await this.$nextTick();

            const container = this.$refs.panoramaContainer;
            if (!container) {
                this.loading = false;
                return;
            }

            try {
                this.viewer = window.pannellum.viewer('plotPanoramaContainer', {
                    type: 'multires',
                    sceneFadeDuration: 1000,
                    autoLoad: true,
                    hfov: 100,
                    minHfov: this.minHfov,
                    maxHfov: this.maxHfov,
                    yaw: -this.yawDegree,
                    pitch: 0,
                    multiRes: {
                        basePath: `/panoramaUrl/static/layers/${image.batchId}/${image.imageId}`,
                        path: '/%l/%s%y_%x',
                        fallbackPath: '/fallback/%s',
                        extension: 'png',
                        tileResolution: image.tileResolution || 512,
                        maxLevel: image.maxLevel || 5,
                        cubeResolution: image.cubeResolution || 4576
                    },
                    autoRotate: 0,
                    autoRotateInactivityDelay: 0
                });

                this.viewer.on('load', () => {
                    this.loading = false;
                    this.emitYawChange();
                });
                this.viewer.on('animatefinished', () => {
                    this.emitYawChange();
                });
                this.viewer.on('rendercanvas', () => {
                    updateZoomButtonsState(this.viewer, this.minHfov, this.maxHfov);
                });

                window.removeEventListener('resize', this.handleResize);
                window.addEventListener('resize', this.handleResize);
            } catch (e) {
                console.warn('全景图加载失败', e);
                this.loading = false;
            }
        }
    }
};
</script>

<style scoped lang="scss">
@import '@/css/pannellum.css';

.plot-panorama-viewer {
    width: 100%;
    height: 100%;
    position: relative;
    overflow: hidden;
}

.panorama-container {
    width: 100%;
    height: 100%;
}

.panorama-loading-mask {
    position: absolute;
    inset: 0;
    z-index: 2;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 9, 45, 0.72);
}

.image-loading-spinner {
    font-size: 36px;
    color: #42b4f2;
}

.empty-placeholder {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #8c8c8c;
    font-size: 14px;
}
</style>
