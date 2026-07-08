<template>
    <a-config-provider :locale="locale">
        <div id="app" class="se-main-container">
            <router-view />
        </div>
    </a-config-provider>
</template>

<script>
import zhCN from 'ant-design-vue/lib/locale-provider/zh_CN';

export default {
    data() {
        return {
            locale: zhCN,
            timer: null,
            times: 60 * 60 * 100000 //配置的是1小时
        };
    },
    methods: {
        isTimeOut() {
            // 使⽤定时器之前，要清除⼀下定时器
            clearInterval(this.timer);
            // 定时器
            this.timer = setInterval(() => {
                let lastClickTime = localStorage.getItem('lastClickTime') * 1; // 把上次点击时候的字符串时间转换成数字时间
                let nowTime = new Date().getTime(); // 获取当前时间
                // 当前时间减去上次点击时间超出配置的登出时间，就提⽰登录退出
                if (nowTime - lastClickTime > this.times) {
                    this.$message({ type: 'warning', message: '登录超时，已退出登录' });
                    // 这⾥要清除定时器，结束任务
                    clearInterval(this.timer);
                    localStorage.removeItem('username');
                    if (this.$route.path !== '/login') {
                        // 最后返回到登录页
                        this.$router.push('/login');
                    }
                }
            }, 1000);
        },
        changeTheme() {
            const theme = this.$store.state.theme;
            const head = document.head;
            // 遍历页面所有的link节点
            const links = document.getElementsByTagName('link');
            for (let i in links) {
                // 如果已有引入主题样式则删除
                if (links[i].href) {
                    if (links[i].href.indexOf('dark.css') !== -1 || links[i].href.indexOf('light.css') !== -1) {
                        head.removeChild(links[i]);
                    }
                }
            }
            // 创建新的主题节点插入head
            var link = document.createElement('link');
            link = Object.assign(link, {
                href: '/theme/' + theme + '.css',
                type: 'text/css',
                rel: 'stylesheet'
            });
            head.appendChild(link);
        }
    },
    mounted() {
        //在这执行定时器
        //this.isTimeOut();
        // 监听用户操作事件，更新上次操作时间
        document.addEventListener('click', function () {
            // 更新上次操作时间
            localStorage.setItem('lastClickTime', new Date().getTime());
        });
    },
    destroyed: function () {
        clearInterval(this.timer);
        window.removeEventListener('click', () => {}, true);
    },
    watch: {
        '$store.state.theme': {
            handler() {
                this.changeTheme();
            },
            immediate: true
        }
    }
};
</script>

<style lang="scss">
.el-pagination.is-background.el-pagination--small .btn-next,
.el-pagination.is-background.el-pagination--small .btn-prev,
.el-pagination.is-background.el-pagination--small .el-pager li {
    margin: 0 1px !important;
}

.se-main-container {
    width: 100%;
    height: 100%;
    overflow: hidden;
  position: relative;
  display: flex;
}
</style>
