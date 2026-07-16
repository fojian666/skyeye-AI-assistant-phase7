<template>
    <div class="home">
        <div class="bg" v-if="$route.name == 'AlgorithmMall'">
            <div class="main-text">
                <h1 class="title">AI算法知识库</h1>
                <p class="text">
                    开创AI视觉算法商城，算法「多快好省」，累计成熟图像视频识别算法100+，
                    覆盖行业100+，落地项目100+，平均准确率≥95%，全新行业算法定制仅需6-8周， 助力人工智能+全场景落地
                </p>
                <div class="search-name">
                    <el-input prefix-icon="el-icon-search" v-model="name" placeholder="搜索算法" size="large"></el-input>
                    <!--                    <el-button type="primary" @click="handleSearch"> <el-icon class="el-icon-search"></el-icon></el-button>-->
                </div>
            </div>
        </div>
        <div class="filter" v-if="$route.name == 'AlgorithmMall'">
            <el-card>
                <div class="filter-category" v-for="category in categories" :key="category.name">
                    <span class="filter-title">{{ category.name }}</span>
                    <div class="filter-options">
                        <el-button
                            v-for="option in category.options"
                            :key="option"
                            type="text"
                            :class="{ 'active-option': selectedOptions[category.name] === option }"
                            @click="selectOption(category.name, option)">
                            {{ option }}
                        </el-button>
                    </div>
                </div>
            </el-card>
        </div>
        <div class="card-item" v-if="$route.name == 'AlgorithmMall'">
            <el-row :gutter="20">
                <el-col :span="6" v-for="(item, index) in paginatedItems" :key="index">
                    <div class="card">
                        <router-link :to="{ path: '/algorithm-mall/algorithm-detail', query: { id: item.id } }">
                            <img :src="baseUrl + item.thumbnail" alt="" class="card-image" />
                        </router-link>
                        <div class="card-content">
                            <span v-if="item.tag" class="tag">{{ item.tag }}</span>
                            <h3>{{ item.name }}</h3>
                            <p class="description">{{ item.scene }}</p>
                        </div>
                    </div>
                </el-col>
            </el-row>
            <div class="pagination-container">
                <el-pagination
                    layout="prev, pager, next"
                    :total="modelLists.length"
                    :page-size="pageSize"
                    @current-change="handlePageChange"
                    class="pagination">
                </el-pagination>
                <div class="text-[#8c8c8c] text-[14px]">共{{ modelLists.length }}条数据</div>
            </div>
        </div>
        <router-view></router-view>
    </div>
</template>

<script>
import { getEnumOptionApi, getModelLists } from '@/api/commonApi.js';
export default {
    name: 'AlgorithmMall',
    data() {
        return {
            name: '',
            baseUrl: process.env.VUE_APP_API_URL,
            categories: [],
            selectedOptions: {},
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
                { id: 3, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' },
                { id: 4, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' },
                { id: 5, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' },
                { id: 6, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' },
                { id: 7, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' },
                { id: 8, image: require('@/assets/images/algorithm-mall/bg1.jpg'), tag: '', title: '渣土车识别', description: '智慧工业 建筑地产' }
            ],
            currentPage: 1,
            pageSize: 8,
            industry: [],
            scene: [],
            modelLists: []
        };
    },
    computed: {
        paginatedItems() {
            const start = (this.currentPage - 1) * this.pageSize;
            const end = this.currentPage * this.pageSize;
            return this.modelLists.slice(start, end);
        }
    },
    methods: {
        setDefaultSelection() {
            // 设置默认选中“全部”选项
            this.categories.forEach((category) => {
                this.$set(this.selectedOptions, category.name, '全部'); // “全部”是第一个选项，索引为 0
            });
        },
        selectOption(categoryName, option) {
            this.$set(this.selectedOptions, categoryName, option);
            // 你可以在这里添加更多的逻辑
        },
        handlePageChange(page) {
            this.currentPage = page;
        },
        //获取枚举数据
        async getEnumData(params) {
            try {
                let res = await getEnumOptionApi(params);
                if (res && res.data) {
                    this.industry = res.data.Industry;
                    this.scene = res.data.Scene;
                    const formattedCategories = [
                        {
                            name: '行业',
                            options: this.formatOptions(this.industry) // 转换数据
                        },
                        {
                            name: '场景',
                            options: this.formatOptions(this.scene) // 转换数据
                        },
                        {
                            name: '其他',
                            options: ['全部', '图片类', '视频类']
                        }
                    ];
                    this.categories = formattedCategories;
                    this.setDefaultSelection();
                }
            } catch (error) {
                console.error('获取枚举数据失败:', error);
            }
        },
        //转换获取到后台数据的格式
        formatOptions(data) {
            const options = ['全部'].concat(data.map((item) => item.name));
            return options;
        },
        //获取模型列表数据
        async getmodelList(params) {
            try {
                let res = await getModelLists(params);
                if (res && res.data) {
                    this.modelLists = res.data;
                }
            } catch (error) {
                console.log('获取模型列表错误', error);
            }
        },
        //搜索框
        async handleSearch() {
            const params1 = {
                page: this.currentPage,
                limit: this.pageSize,
                name: this.name
            };
            await this.getmodelList(params1);
        }
    },
    mounted() {
        this.getEnumData('Industry,Scene'),
            this.getmodelList({
                page: this.currentPage,
                limit: this.pageSize,
                query: ''
            });
        // this.handleSearch()
    },
    watch: {
        name(newValue) {
            this.getmodelList({
                page: this.currentPage,
                limit: this.pageSize,
                name: this.name
            });
        }
    }
};
</script>

<style scoped lang="scss">
.home {
    width: 100%;
    min-height: auto;
    background-color: #fff;
    overflow-y: scroll;

    .bg {
        width: 100%;
        height: 500px;
        background-image: url('@/assets/images/algorithm-mall/bg.jpg');
        background-repeat: no-repeat;
        background-size: cover;
        position: relative;
        margin-bottom: 15px;

        .main-text {
            position: absolute;
            margin-top: 5%;
            margin-left: 10%;
            color: #ffffff;

            .title {
                color: #ffffff;
                font-size: 38px;
            }

            .text {
                width: 40%;
                padding-top: 20px;
                color: #ffffff99;
                font-size: 16px;
            }

            .search-name {
                margin-top: 30px;
                width: 40%;
                display: flex;
            }
        }
    }

    .filter {
        width: 80%;
        height: 170px;
        margin: auto;
        border-radius: 4px;
        display: flex;
        flex-direction: column;

        .filter-category {
            display: flex;
            align-items: center;
            justify-items: center;
            padding-left: 80px;
            padding-bottom: 10px;
            .filter-title {
                font-size: 20px;
                font-weight: bold;
                margin-right: 30px;
            }

            .filter-options {
                .el-button {
                    margin-right: 20px;
                    color: #0c0d0e;
                    font-size: 16px;
                }

                .active-option {
                    border: 1px solid #42b4f2;
                    color: #42b4f2;
                    padding: 3px 3px;
                }
            }
        }
    }

    .card-item {
        padding-top: 20px;
        width: 80%;
        margin: 0 auto;
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

    .pagination-container {
        padding-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }
}
</style>
