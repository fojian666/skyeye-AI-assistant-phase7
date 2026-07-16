<template>
    <div class="content">
        <div class="item">
            <div class="bread-crumb">
                <el-breadcrumb separator-class="el-icon-arrow-right">
                    <el-breadcrumb-item style="font-size: 16px" :to="{ path: '/algorithm-mall' }">算法列表</el-breadcrumb-item>
                    <el-breadcrumb-item style="font-size: 16px">算法详情</el-breadcrumb-item>
                </el-breadcrumb>
            </div>
            <div class="header">
                <div class="left-item">
                    <div class="title">
                        {{ modelDetail.name }}
                    </div>
                    <div class="des">
                        {{ modelDetail.note }}
                    </div>
                    <div class="tag">
                        <span class="tag1 item1">{{ modelDetail.scene }}</span>
                    </div>
                    <div class="btn">
                        <!--                        <el-row>-->
                        <!--                            <el-button>在线咨询</el-button>-->
                        <!--                            <el-button >申请试用</el-button>-->
                        <!--                        </el-row>-->
                    </div>
                </div>
                <div class="right-item">
                    <img :src="baseUrl + modelDetail.thumbnail" alt="" />
                </div>
            </div>
        </div>
        <div class="model-des">
            <div class="tit">应用场景</div>
            <el-row :gutter="20">
                <el-col :span="8" v-for="(item, index) in modelDes" :key="index">
                    <h2>
                        <i class="fa el-icon-caret-right"></i>
                        <!-- 使用i标签作为图标 -->
                        {{ item.title }}
                    </h2>
                    <p style="line-height: 1.6; padding: 10px">{{ item.des }}</p>
                </el-col>
            </el-row>
        </div>
        <div class="model-des">
            <div class="tit">常见问题</div>
            <el-row :gutter="20">
                <el-col :span="8" v-for="(item, index) in modelQues" :key="index">
                    <h2>
                        <i class="fa el-icon-caret-right"></i>
                        <!-- 使用i标签作为图标 -->
                        {{ item.title }}
                    </h2>
                    <p style="line-height: 1.6; padding: 10px">{{ item.des }}</p>
                </el-col>
            </el-row>
        </div>
        <div class="model-recom">
            <div class="title-recom">相关算法推荐</div>
            <el-row :gutter="20">
                <el-col :span="6" v-for="(item, index) in algorithms" :key="index">
                    <div class="card">
                        <img :src="baseUrl + item.image" alt="" class="card-image" />
                        <div class="card-content">
                            <span v-if="item.tag" class="tag">{{ item.tag }}</span>
                            <h3>{{ item.title }}</h3>
                            <p class="description">{{ item.description }}</p>
                        </div>
                    </div>
                </el-col>
            </el-row>
        </div>
    </div>
</template>

<script>
import { getModelDetail } from '@/api/commonApi.js';
export default {
    name: 'AlgorithmDetail',
    data() {
        return {
            modelDes: [
                {
                    title: '城市道路',
                    des: '自动识别城市道路特定时段渣土车行驶情况，实时反馈给交管人员，高效执法'
                },
                {
                    title: '无人机',
                    des: '无人机视角渣土车，且图像为红外热成像图片，识别到区域内有渣土车，则产生报警'
                },
                {
                    title: '工业作业区',
                    des: '在工地作业区域内，自动识别是否有渣土车驶入，如检测到渣土车，及时报警提醒并反馈给工作人员，有效提高了人工巡检的效率，减少人工成本'
                },
                {
                    title: '工业作业区',
                    des: '在工地作业区域内，自动识别是否有渣土车驶入，如检测到渣土车，及时报警提醒并反馈给工作人员，有效提高了人工巡检的效率，减少人工成本'
                },
                {
                    title: '工业作业区',
                    des: '在工地作业区域内，自动识别是否有渣土车驶入，如检测到渣土车，及时报警提醒并反馈给工作人员，有效提高了人工巡检的效率，减少人工成本'
                }
            ],
            modelQues: [
                {
                    title: '算法怎么使用',
                    des: '算法支持本地服务器/边缘端/云服务器等部署方式，边缘端部署可兼容华为昇腾/算能/瑞芯微/英伟达等边缘计算盒子，开箱即用'
                },
                {
                    title: '算法怎么收费',
                    des: '算法按付方式灵活，可根据实际需求和规模进行评估，主要有按路数授权/服务器授权/年包授权'
                },
                {
                    title: '算法如何定制',
                    des: '算法按付方式灵活，可根据实际需求和规模进行评估，主要有按路数授权/服务器授权/年包授权'
                }
            ],
            algorithms: [
                {
                    id: 0,
                    image: require('@/assets/images/algorithm-mall/bg1.jpg'),
                    tag: '',
                    title: '反光衣识别',
                    description: '智慧交通 智慧城管 建筑地产'
                },
                {
                    id: 1,
                    image: require('@/assets/images/algorithm-mall/bg1.jpg'),
                    tag: '新品',
                    title: '渣土车识别',
                    description: '智慧工业 建筑地产'
                },
                {
                    id: 2,
                    image: require('@/assets/images/algorithm-mall/bg1.jpg'),
                    tag: '热门',
                    title: '反光衣识别',
                    description: '智慧交通 智慧城管 建筑地产'
                },
                { id: 3, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' }
            ],
            modelDetail: [],
            baseUrl: process.env.VUE_APP_API_URL
        };
    },
    methods: {
        async getModelContent() {
            try {
                let res = await getModelDetail(this.$route.query.id);
                if (res && res.data) {
                    this.modelDetail = res.data;
                }
            } catch (error) {
                console.log('获取模型内容错误', error);
            }
        }
    },
    mounted() {
        this.getModelContent();
    }
};
</script>

<style scoped>
.content {
    .item {
        padding-top: 10px;
        width: 100%;
        background-image: url('@/assets/images/algorithm-mall/bg3.jpg');

        .bread-crumb {
            width: 80%;
            line-height: 40px;
            height: 40px;
            /*background-color: #fff;*/
            margin: 0 auto;
            margin-bottom: 10px;

            padding-left: 5px;
            padding-top: 10px;
        }

        .header {
            width: 80%;
            height: 320px;
            /*background-color: #99a9bf;*/
            margin: 0 auto;

            .left-item {
                width: 40%;
                float: left;
                margin-left: 10px;
                padding-top: 40px;

                .title {
                    color: #333;
                    font-size: 28px;
                    font-weight: bold;
                    padding-bottom: 10px;
                }

                .des {
                    font-size: 16px;
                    padding-bottom: 20px;
                    line-height: 2;
                }

                .tag {
                    .tag1 {
                        margin-right: 10px;
                    }

                    .item1 {
                        border-left: 1px solid #3d3d3d;
                        padding-left: 10px;
                    }
                }

                .btn {
                    margin-top: 30px;
                }
            }

            .right-item {
                width: 30%;
                float: right;
                img {
                    margin-right: 10px;
                    width: 100%;
                    height: auto;
                }
            }
        }
    }
    .model-des {
        width: 80%;
        margin: 0 auto;
        /*background-color: #99a9bf;*/
        .tit {
            color: #333;
            font-size: 28px;
            font-weight: bold;
            padding: 10px;
        }
    }
    .model-recom {
        width: 80%;
        margin: 0 auto;
        .title-recom {
            padding: 10px;
            color: #333;
            font-size: 28px;
            font-weight: bold;
        }
        .card {
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 100%;
            margin-bottom: 20px;
            position: relative;
        }

        .card-image {
            width: 100%;
            height: 180px;
            object-fit: cover;
        }

        .card-content {
            padding: 10px;
        }

        .tag {
            background-color: #ff4d4f;
            color: white;
            padding: 2px 4px;
            border-radius: 2px;
            font-size: 12px;
            position: absolute;
            top: 158px;
            left: 0;
            z-index: 999;
        }

        .card h3 {
            font-size: 18px;
            margin: 10px 0;
        }

        .description {
            color: #888;
            font-size: 14px;
        }
    }
}
</style>
