<template>
    <div class="list-card-container">
        <template v-for="(item, index) in listCardConfig.data">
            <div class="list-card">
                <div class="card-top">
                    <span class="latest-label" v-if="item.id == listCardConfig.latestID">最新</span>
                    <span :title="item.name" class="task-name">任务名称：{{ item.name }}</span>
                </div>
                <template v-if="item.taskType === '地类变化'">
                    <div class="card-left" @click="viewDetails(item.id, item.appendTime, item.taskType)">
                        <img :src="`${item.nextImage.url}/entireImage.png`" />
                        <!--              <img :src="thumbnailCache[`${item.nextImage.collectId}_${item.nextImage.tifId}`]" alt="缩略图"/>-->
                    </div>
                    <div class="card-right">
                        <p :title="item.prevImage.appendTime">
                            <i class="list-card-icon iconfont icon-shijian"></i>前景时间：
                            <span style="color: #00f1f3">{{ item.prevImage.appendTime }}</span>
                        </p>
                        <p :title="item.nextImage.appendTime">
                            <i class="list-card-icon iconfont icon-shijian"></i>后景时间：<span style="color: #00f1f3">{{
                                item.nextImage.appendTime
                            }}</span>
                        </p>
                        <p :title="item.county">
                            <i class="list-card-icon iconfont icon-weizhi"></i>检测区域：<span style="color: #00f1f3">{{ item.county }}</span>
                        </p>
                        <p :title="item.createTime.split(' ')[0]">
                            <i class="list-card-icon iconfont icon-shijian"></i>预警时间：<span style="color: #00f1f3">{{
                                item.createTime.split(' ')[0]
                            }}</span>
                        </p>
                        <!--             <p :title="item.prev_image.service_type">-->
                        <!--              <i class="list-card-icon iconfont icon-weizhi"></i>服务类别：<span style="color: #00f1f3">{{-->
                        <!--                item.prev_image.service_type-->
                        <!--                 }}</span>-->
                        <!--            </p>-->
                        <p :title="item.taskType">
                            <i class="list-card-icon iconfont icon-weizhi"></i>检测类型：<span style="color: #00f1f3">{{ item.taskType }}</span>
                        </p>
                    </div>
                </template>
                <template v-else>
                    <div class="card-left" @click="viewDetails(item.id, item.appendTime, item.taskTypeTag)">
                        <!--            <img  :src="collectionIdDic[item.path.name]" alt="暂无此图"/>-->
                        <img :src="thumbnailCache[`${item.path.collectId}_${item.path.tifId}`]" alt="缩略图" />
                    </div>
                    <div class="card-right">
                        <p :title="item.path.appendTime">
                            <i class="list-card-icon iconfont icon-shijian"></i>影像时间：<span style="color: #00f1f3">{{
                                item.path.appendTime
                            }}</span>
                        </p>
                        <p :title="item.county">
                            <i class="list-card-icon iconfont icon-weizhi"></i>检测区域：<span style="color: #00f1f3">{{ item.county }}</span>
                        </p>
                        <p :title="item.createTime">
                            <i class="list-card-icon iconfont icon-shijian"></i>预警时间：<span style="color: #00f1f3">{{ item.createTime }}</span>
                        </p>
                        <!--            <p :title="item.path.dataType">-->
                        <!--              <i class="list-card-icon iconfont icon-model"></i>数据类型：<span style="color: #00f1f3">{{-->
                        <!--                item.path.dataType-->
                        <!--                }}</span>-->
                        <!--            </p>-->
                        <!--            <p :title="item.path.service_type">-->
                        <!--              <i class="list-card-icon iconfont icon-weizhi"></i>服务类别：<span style="color: #00f1f3">{{-->
                        <!--                item.path.service_type-->
                        <!--                }}</span>-->
                        <!--            </p>-->
                        <p :title="item.taskType">
                            <i class="list-card-icon iconfont icon-weizhi"></i>检测类型：<span style="color: #00f1f3">{{ item.taskType }}</span>
                        </p>
                    </div>
                </template>
            </div>
        </template>
    </div>
</template>

<script>
// import {ImageService} from "@supermap/iclient-leaflet/services/ImageService";
import codeNode from 'three/addons/nodes/code/CodeNode';
export default {
    name: 'ListCard',

    props: {
        listCardConfig: {
            type: Object,
            requred: true
        },
        parentMethod: {
            type: Function
        }
    },
    data() {
        return {
            flag: false,
            collectionIdDic: {},
            thumbnailCache: {}
        };
    },
    async created() {
        this.listCardConfig.detailPath == '/intelligent/land-change/land-change-details' ? (this.flag = true) : (this.flag = false);
        await this.loadAllThumbnails();
    },
    async mounted() {
        // await this.ImageSearchService();
        // await this.loadAllThumbnails()
    },

    methods: {
        viewDetails(id, append_time, task_type_tag) {
            /*这里需要判断哪个页面的详情页*/
            if (task_type_tag === '地类变化') {
                this.$router.push(`${this.listCardConfig.detailPath}?id=${id}&time=${append_time}`);
            } else {
                this.$router.push(`${this.listCardConfig.segdetailPath}?id=${id}&time=${append_time}`);
            }
        },
        async fankui(id) {
            let params = new URLSearchParams();
            params.append('task_id', id);
            const { data: res } = await this.$http.post(config.BASE_URL + 'common/retroaction', params);
            this.$message.success(res.msg);
            this.parentMethod();
        },
        ImageSearchService() {
            var service = new ImageService(window.config.iserverAdress);
            service.getCollections(this.getCollectionsCompleted);
            service.search({}, this.getSearchProcessCompleted);
        },
        getSearchProcessCompleted(res) {
            var result = res.result;
            if (result && result.features) {
                //id不能重复，否则相同id会被覆盖，显示不正确。重新设置id
                result.features.forEach(function (feature) {
                    feature.id = feature.collection + '.' + feature.id;
                });
            }
            const features = (result && result.features) || [];
            features.forEach((feature) => {
                const filename = feature.properties.smfilename.split('.')[0];
                this.$set(this.collectionIdDic, filename, feature.assets.thumbnail.href); // 确保触发视图更新
            });
        },
        getCollectionsCompleted(res) {
            var collectionsInfo = res.result || [];
            const collections = [];
            collectionsInfo.forEach(function (collection) {
                var split = collection['extent']['spatial']['crs'].split('/');
                var EPSGCode = split[split.length - 1];
                collections.push({
                    id: collection['id'],
                    title: collection['title'],
                    value: collection['id'],
                    extent: collection['extent']['spatial']['bbox'][0],
                    EPSG: EPSGCode
                });
            });
        },

        async loadAllThumbnails() {
            this.loadingThumbnails = true;
            // 使用 Promise.all 并行请求，提升加载速度
            await Promise.all(
                this.listCardConfig.data.map(async (item) => {
                    if (item.taskType === '地类变化') {
                        const cacheKey = `${item.nextImage.collectId}_${item.nextImage.tifId}`;
                        // 如果缓存中已有，则跳过
                        if (this.thumbnailCache[cacheKey]) return;
                        try {
                            const res = await this.axios.get(
                                `${item.nextImage.url}/collections/${item.nextImage.collectId}/items/${item.nextImage.tifId}.json`,
                                { withCredentials: false }
                            );
                            // 存储到缓存
                            this.$set(this.thumbnailCache, cacheKey, res.data.assets.thumbnail.href);
                        } catch (error) {
                            console.error(`加载缩略图 ${cacheKey} 失败:`, error);
                            this.$set(this.thumbnailCache, cacheKey, 'default-thumbnail.jpg'); // 降级处理
                        }
                    } else if (item.taskType === '地类分割') {
                        const cacheKey = `${item.path.collectId}_${item.path.tifId}`;
                        // 如果缓存中已有，则跳过
                        if (this.thumbnailCache[cacheKey]) return;
                        try {
                            const res = await this.axios.get(`${item.path.url}/collections/${item.path.collectId}/items/${item.path.tifId}.json`, {
                                withCredentials: false
                            });
                            // 存储到缓存
                            this.$set(this.thumbnailCache, cacheKey, res.data.assets.thumbnail.href);
                        } catch (error) {
                            this.$set(this.thumbnailCache, cacheKey, 'default-thumbnail.jpg'); // 降级处理
                        }
                    }
                })
            );
            this.loadingThumbnails = false;
        }
    }
};
</script>

<style scoped>
.list-card-container {
    height: calc(100% - 7rem);
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    align-content: flex-start;
    padding: 0;
    overflow: auto;
}

.list-card {
    border: 0.1rem solid rgb(9 82 149);
    box-sizing: border-box;
    border-radius: 0.3rem;
    width: calc(calc(100% / 3) - 0.5rem);
    margin: 0.25rem;
    padding: 3.5rem 0.5rem 0.5rem 0.5rem;
    display: flex;
    align-items: center;
    height: calc(calc(100% / 3) - 0.3rem);
    overflow: hidden;
    position: relative;
    color: white;
}

.list-card:hover {
    cursor: pointer;
    transform: scale(1.01, 1.01);
    transition: all 200ms linear;
}

.card-top {
    width: calc(100% - 1rem);
    height: 20%;
    position: absolute;
    top: 0;
    font-size: 1rem;
    border-bottom: 0.15rem solid #095295;
    display: flex;
    justify-content: start;
    align-items: center;
}

.task-name {
    display: inline-block;
    max-width: 100%;
    align-items: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.latest-label {
    height: 1.6rem;
    width: 4rem;
    background-color: #e65f40;
    transform: skew(-15deg, 0);
    border-radius: 0.3rem;
    text-align: center;
    line-height: 1.6rem;
    color: white;
    margin-right: 1rem;
    font-size: 1rem;
    font-weight: 400;
}

.card-left {
    width: 50%;
    height: 100%;
    display: inline-block;
    padding-right: 0.5rem;
}

.card-left img {
    height: 100%;
    width: 100%;
    object-fit: fill;
}

.card-right {
    width: 50%;
    display: inline-block;
}

.card-right p {
    margin-bottom: 0;
    padding: 0.2rem 0;
    font-size: 0.9rem;
    color: white;
    width: 100%;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.list-card-icon {
    margin-right: 0.5rem;
    font-weight: 600;
}
</style>
