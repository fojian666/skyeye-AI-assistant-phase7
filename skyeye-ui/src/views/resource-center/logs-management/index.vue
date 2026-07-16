<template>
    <div class="configEdit">
        <div class="gt-breadcrumb-box">
            <i class="iconfont icon-geoai-landChange"></i>
            <span class="gt-current-position">航线管理</span>
            <a-breadcrumb separator=">" style="display: contents">
                <a-breadcrumb-item style="font-size: 12px">日志管理</a-breadcrumb-item>
                <a-breadcrumb-item style="font-size: 12px">航线规划</a-breadcrumb-item>
            </a-breadcrumb>
        </div>
        <div class="content-tab">
            <el-tabs v-model="activeName" @tab-click="handleClick">
                <el-tab-pane label="航线规划" name="航线规划"></el-tab-pane>
                <el-tab-pane label="全景融合" name="全景融合"></el-tab-pane>
                <el-tab-pane label="线索推送" name="线索推送"></el-tab-pane>
                <el-tab-pane label="运维中心" name="运维中心"></el-tab-pane>
                <el-tab-pane label="模型日志" name="模型日志"></el-tab-pane>
                <el-tab-pane label="体验中心" name="体验中心"></el-tab-pane>
                <el-tab-pane label="系统日志" name="系统日志"></el-tab-pane>
            </el-tabs>
        </div>
        <div class="gt-breadcrumb-cnt">
            <el-row :gutter="20" class="add">
                <el-col :span="7">
                    <el-input v-model="searchParams.text" placeholder="请输入查询文本" class="gt-query-item"></el-input>
                </el-col>
                <el-col :span="17">
                    <el-button @click="filterCode" type="primary" icon="el-icon-search">查询</el-button>
                    <el-button type="info" icon="el-icon-delete" @click="handleReset">重置</el-button>
                    <el-button type="primary" icon="el-icon-download" @click="handelDownLoadLog">下载日志</el-button>
                    <span style="float: right; font-weight: bold; padding-top: 8px">当前日志仅展示最新400行信息，如需查看更多信息，请下载日志</span>
                </el-col>
            </el-row>
            <editor
                ref="aceEditor"
                :value="logTxt"
                @init="editorInit"
                :options="options"
                lang="json"
                theme="chrome"
                width="100%"
                height="70vh"
                style="margin-top: 15px; border: gray dashed 1px" />
        </div>
    </div>
</template>

<script>
import Editor from 'vue2-ace-editor';
import axios from 'axios';
import { getDownloadFileApi, getLogsInfoApi } from '@/api/commonApi';
import 'brace/ext/searchbox'; // 引入搜索扩展
export default {
    name: 'configEdit',
    components: {
        Editor
    },
    data() {
        return {
            logTxt: '', //配置文件代码
            options: {
                tabSize: 4, // tab默认大小
                showPrintMargin: false, // 去除编辑器里的竖线
                fontSize: 15, // 字体大小

                highlightActiveLine: true,
                showGutter: true
            },
            searchParams: {
                text: '' //查询文本
            },
            activeName: '航线规划'
        };
    },
    mounted() {
        this.handleOpen();
    },

    methods: {
        // 代码块初始化
        editorInit() {
            require('brace/ext/language_tools'); // language extension prerequsite...
            require('brace/mode/python'); // 语言
            require('brace/theme/chrome'); // 主题
            require('brace/ext/language_tools'); //language extension prerequsite...
            require('brace/mode/yaml');
            require('brace/mode/json');
            require('brace/mode/less');
            require('brace/snippets/json');

            const editor = this.$refs.aceEditor.editor;
            editor.setOptions({
                // 启用搜索框
                enableCodeFolding: false,
                showLineNumbers: true,
                useWorker: false
            });
        },

        //获取代码
        async handleClick(tab, event) {
            const res = await getLogsInfoApi({ search_type: tab.name });
            if (res.code === '0') {
                this.logTxt = res.logs_txt;
                this.$nextTick(() => {
                    this.highlightErrors(); // 加载文本后高亮搜索
                });
            } else {
                this.logTxt = '';
                this.$message.error(res.msg);
            }
        },
        //代码查询
        filterCode() {
            const editor = this.$refs.aceEditor.editor;
            const range = editor.find(this.searchParams.text);
            if (!range) {
                this.$message.warning('文本为空或查询不到，请重新输入！');
            }
        },
        handleReset() {
            this.searchParams.text = '';
        },
        async handleOpen() {
            const res = await getLogsInfoApi({ search_type: this.activeName, tag: 'view' });
            if (res.code === '0') {
                this.logTxt = res.logs_txt;
                this.$nextTick(() => {
                    this.highlightErrors(); // 加载文本后高亮搜索
                });
            } else {
                this.$message.error(res.msg);
            }
        },
        async handelDownLoadLog() {
            try {
                const response = await getLogsInfoApi({ search_type: this.activeName, tag: 'download' });
                // 创建一个临时的a标签来模拟下载
                const url = window.URL.createObjectURL(new Blob([response]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', this.activeName); // 假设文件路径的最后一部分是文件名
                document.body.appendChild(link);
                link.click();
                // 清理
                window.URL.revokeObjectURL(url);
                document.body.removeChild(link);
            } catch (error) {
                if (error.response && error.response.status === 404) {
                    this.$message.error('文件未找到');
                } else {
                    this.$message.error('下载文件时发生错误');
                }
            }
        },
        highlightErrors() {
            const editor = this.$refs.aceEditor.editor;
            editor.find('ERROR', {
                regExp: true,
                wholeWord: false,
                caseSensitive: false,
                wrap: true,
                range: null,
                preserveCase: false,
                showButtons: false
            });
        }
    }
};
</script>

<style lang="scss" scoped>
* {
    font-size: 14px;
}
.error {
    color: red; /* 文本颜色 */
    background-color: #ff0000; /* 背景颜色 */
    display: inline-block; /* 使背景颜色仅应用于匹配的文本 */
}
/*  组件布局*/
.configEdit {
    margin: 0;
    padding: 0;
    background-color: #edf0f7 !important;
    color: #333;
    font-size: 14px;
    line-height: 1.5;
    display: flex;
    flex-direction: column;
}

/*  表头面包屑*/
.gt-breadcrumb-box {
    height: 40px;
    line-height: 40px;
    background-color: #fff;
    box-sizing: border-box;
    padding: 0 16px;
    border-left: 1px solid #dcdcdc;
}

.content-tab {
    height: 40px;
    line-height: 40px;
    background-color: #fff;
    box-sizing: border-box;
    padding: 0 16px;
    margin-top: 10px;
}

.gt-breadcrumb-box .icon-geoai-landChange {
    font-size: 20px;
    color: rgb(43, 179, 244);
}

.gt-current-position {
    margin-left: 5px;
    margin-right: 10px;
    font-size: 18px;
    font-weight: 700;
}
.gt-current-position span {
    margin: 0 10px;
    color: #999;
}

/*  内容*/
.gt-breadcrumb-cnt {
    padding: 10px;
    width: 100%;
    background-color: #fff;
    flex: 1;
}

.add {
    background-color: #f3f3f3;
    height: 45px;
    display: flex;
    align-items: center;
}
</style>
