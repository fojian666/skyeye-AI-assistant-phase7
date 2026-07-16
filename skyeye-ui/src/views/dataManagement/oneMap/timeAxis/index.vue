<template>
    <div class="main-container-time">
        <div class="year-show">
            <span class="label-span">时间</span>
            <div class="timeline">
                <i class="el-icon-arrow-left" @click="prevItem" :class="{ disabled: isFirstItemActive }"></i>
                <!-- 固定线条 -->
                <div class="line-container">
                    <!--                    <div class="line" ref="line"></div>-->
                </div>
                <!-- 可滚动的圆点 -->
                <div
                    class="circles-container"
                    ref="circlesContainer"
                    :class="{ 'justify-center': !needsScroll && centerWhenFew }"
                    @touchstart="handleTouchStart"
                    @touchend="handleTouchEnd"
                    @touchmove="handleTouchMove">
                    <!--                    @touchmove="handleTouchMove"-->
                    <div
                        v-for="(item, index) in allItems"
                        :key="item.key"
                        :class="{
                            circle: item.type === 'year',
                            smallcircle: item.type === 'month',
                            active: item.isActive,
                            hover: item.isHover
                        }"
                        :style="getItemStyle(index)"
                        @mouseover="hoverItem(index)"
                        @mouseout="unhoverItem(index)"
                        @click="activateItem(index)">
                        <div v-if="item.type === 'year'" class="circle-content">
                            {{ item.value }}
                        </div>
                        <div v-if="item.type === 'month' && (item.isHover || item.isActive)" class="month-content">
                            {{ item.value.split('-')[1] + '月' }}
                        </div>
                    </div>
                </div>
                <i class="el-icon-arrow-right" @click="nextItem" :class="{ disabled: isLastItemActive }" style="position: absolute; right: 20px"></i>
                <i class="el-icon-refresh refresh" @click="resetScroll"></i>
            </div>
        </div>
    </div>
</template>

<script>
import { getTimeAxisDataApi } from '@/api/commonApi';
import colorSpaceNode from 'three/addons/nodes/display/ColorSpaceNode';

export default {
    props: {},
    data() {
        return {
            rawTimelineItems: [],
            allItems: [],
            touchStartX: 0,
            isScrolling: false,
            activeIndex: -1,
            itemBaseWidth: 30, // 每个项目的基础占位宽度
            minSpacing: 20, // 最小间距
            needsScroll: false, // 是否需要滚动
            centerWhenFew: false, // 少量项目时是否居中(设为false表示均匀分布)
            currrentActivateData: '',
            containerWidth: 0
        };
    },
    computed: {
        isFirstItemActive() {
            return this.activeIndex === 0 || this.currrentActivateData === '';
        },
        isLastItemActive() {
            return this.activeIndex === this.allItems.length - 1;
        }
    },
    methods: {
        initTimelineItems() {
            this.allItems = this.rawTimelineItems.flatMap((item) => {
                const yearObj = {
                    type: 'year',
                    value: item.year,
                    isActive: false,
                    isHover: false
                    // key: `year-${item.year}`
                };

                const monthObjs = item.month_list.map((month) => ({
                    type: 'month',
                    value: `${item.year}-${month}`,
                    isActive: false,
                    isHover: false
                    // key: `month-${item.year}-${month}`
                }));

                return [yearObj, ...monthObjs];
            });
            // if (this.allItems.length > 0) {
            //     this.allItems[0].isActive = true;
            // }

            this.$nextTick(() => {
                this.calculateLayout();
                // 初始化后如果内容很少，自动居中
                if (!this.needsScroll && this.allItems.length < 5) {
                    this.centerWhenFew = true;
                }
            });
        },
        calculateLayout() {
            const container = this.$refs.circlesContainer;
            if (!container || !this.allItems.length) return;
            const containerWidth = container.clientWidth;
            this.containerWidth = containerWidth;
            // 计算所有项目需要的总宽度
            const totalContentWidth = this.allItems.length * this.itemBaseWidth;
            if (totalContentWidth > containerWidth) {
                this.needsScroll = true;
            } else {
                this.centerWhenFew = true;
            }

            // console.log('布局计算完成', {
            //     容器宽度: containerWidth,
            //     需要滚动: this.needsScroll,
            // });
        },

        getItemStyle(index) {
            if (this.needsScroll) {
                // 需要滚动时使用固定最小间距
                return {
                    margin: `0 ${this.minSpacing}px`
                };
            }
            // 不需要滚动时的均匀分布逻辑
            if (this.centerWhenFew) {
                const itemBaseWidth = 15;
                const remainingSpace = this.containerWidth - this.allItems.length * itemBaseWidth - 50;
                const rightDistance = remainingSpace / (this.allItems.length - 1);

                // 居中模式
                if (index === 0) {
                    return { margin: `0 ${rightDistance}px 0 25px` }; //上 右 下 左
                }
                if (index === this.allItems.length - 1) {
                    return { margin: `0 25px 0 0` };
                }
                return { margin: `0 ${rightDistance}px 0 0` };
            }
        },
        hoverItem(index) {
            this.allItems[index].isHover = true;
        },
        unhoverItem(index) {
            this.allItems[index].isHover = false;
        },
        activateItem(index) {
            if (index >= 0 && index < this.allItems.length && !this.allItems[index].isActive) {
                this.allItems.forEach((item) => (item.isActive = false));
                this.allItems[index].isActive = true;
                this.activeIndex = index;
                if (this.needsScroll) {
                    this.scrollToActiveItem();
                }
                this.currrentActivateData = this.allItems[index].value;
                this.$emit('handleDateChange', this.currrentActivateData);
            }
        },
        scrollToActiveItem() {
            // if (this.isScrolling || !this.needsScroll) return;
            this.isScrolling = true;

            const container = this.$refs.circlesContainer;
            const activeElement = container.querySelector('.active');
            if (!activeElement) return;

            const containerRect = container.getBoundingClientRect();
            const activeRect = activeElement.getBoundingClientRect();

            const targetPosition = container.scrollLeft + (activeRect.left - containerRect.left) - container.clientWidth / 2 + activeRect.width / 2;

            const maxScroll = container.scrollWidth - container.clientWidth;
            const finalPosition = Math.max(0, Math.min(targetPosition, maxScroll));

            container.scrollTo({
                left: finalPosition,
                behavior: 'smooth'
            });

            setTimeout(() => {
                this.isScrolling = false;
            }, 500);
        },
        prevItem() {
            if (this.activeIndex > 0) {
                this.activateItem(this.activeIndex - 1);
            }
        },
        nextItem() {
            if (this.activeIndex < this.allItems.length - 1) {
                this.activateItem(this.activeIndex + 1);
            }
        },
        resetScroll() {
            // this.activateItem(0);
            this.allItems.forEach((item) => (item.isActive = false));
            this.activeIndex = -1;

            if (this.needsScroll) {
                this.scrollToActiveItem();
            }
            this.currrentActivateData = '';
            this.$emit('handleDateChange', this.currrentActivateData);
        },
        handleTouchStart(e) {
            this.touchStartX = e.touches[0].clientX;
            this.startScrollLeft = this.$refs.circlesContainer.scrollLeft;
            this.isScrolling = true;
        },
        handleTouchMove(e) {
            if (!this.touchStartX || !this.needsScroll) return;
            const touchX = e.touches[0].clientX;
            const diff = this.touchStartX - touchX;
            if (Math.abs(diff) > 5) {
                this.$refs.circlesContainer.scrollLeft += diff;
                this.touchStartX = touchX;
            }
        },
        handleTouchEnd() {
            this.touchStartX = 0;
        },
        handleResize() {
            this.calculateLayout();
            // 如果当前有激活项，确保它在视图中
            if (this.activeIndex >= 0) {
                this.$nextTick(() => {
                    this.scrollToActiveItem();
                });
            }
        },
        async getTimeAxisData() {
            const res = await getTimeAxisDataApi();
            if (res.code === 0) {
                this.rawTimelineItems = res.data.rawTimelineItems;
            } else {
                this.$message.error(res.msg);
            }
        }
    },
    async mounted() {
        await this.getTimeAxisData();
        this.initTimelineItems();
        window.addEventListener('resize', this.handleResize);
    },
    beforeDestroy() {
        window.removeEventListener('resize', this.handleResize);
    },
    async created() {}
};
</script>

<style scoped>
.main-container-time {
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    color: black;
}

.year-show {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: row;
    padding: 0 6px;
    color: white;
}

.timeline {
    display: flex;
    //position: relative;
    //margin-left: 10px;
    width: calc(100% - 30px);
    overflow: hidden;
    font-size: 20px;
    justify-content: space-between;
}

.line-container {
    position: absolute;
    width: calc(100% - 90px);
    height: 2px;
    top: 19px;
    transform: translateY(-50%);
    z-index: 1;
    background-image: linear-gradient(to right, #f5f7fa, #c3cfe2, #c3cfe2, #f5f7fa);
    margin-left: 17px;
}

.line {
    height: 100%;
    min-width: 100%;
    margin-left: 10px;
}

.circles-container {
    display: flex;
    position: absolute;
    height: 100%;
    width: calc(100% - 90px);
    overflow-x: auto;
    //scroll-behavior: smooth;
    //scrollbar-width: none;
    -ms-overflow-style: none;
    z-index: 2;
    margin-left: 20px;
}

.circles-container.justify-center {
}

.circles-container::-webkit-scrollbar {
    display: none;
}

.circle,
.smallcircle {
    position: relative;
    flex-shrink: 0;
    width: 30px;
    transform: translateY(0);
    transition: all 0.3s;
}

.circle {
    width: 15px;
    height: 15px;
    background-color: #fff;
    border: 2px solid #1daf95;
    border-radius: 50%;
    top: 10px;
}

.smallcircle {
    width: 15px;
    height: 15px;
    background-color: #fff;
    border: 2px solid #1daf95;
    border-radius: 50%;
    top: 10px;
}

.circle.hover,
.smallcircle.hover {
    transform: translateY(-5px);
    cursor: pointer;
}

.circle.active,
.smallcircle.active {
    background-color: #1daf95;
    border-color: #1daf95;
    transform: translateY(-5px);
}

.circle-content,
.month-content {
    position: absolute;
    bottom: -25px;
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: 12px;
    color: #fff;
    font-weight: bold;
}

.label-span {
    width: 30px;
    display: flex;
    align-items: center;
    line-height: 50px;
}

.refresh {
    font-size: 20px;
    color: white;
    cursor: pointer;
}

i {
    cursor: pointer;
    flex-shrink: 0;
    z-index: 3;
    color: #2db6f4;
    font-weight: bold;
    margin-top: 10px;
}

i:hover:not(.disabled) {
    color: dodgerblue;
}

i.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    color: #524f4f;
}
</style>
