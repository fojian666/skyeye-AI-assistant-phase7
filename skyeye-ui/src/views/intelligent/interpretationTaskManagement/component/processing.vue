<template>
    <el-dialog
        id="interpreting-processing-dialog"
        title="进度信息"
        :close-on-click-modal="false"
        :visible.sync="detailVisible"
        width="90%"
        height="90%">
        <div class="se-container">
            <!-- 任务完成进度和硬件信息 -->
            <div class="se-container-header">
                <el-row :gutter="20">
                    <el-col :span="4">
                        <div class="grid-content bg-purple">
                            <div class="gt-card-header">
                                <i class="el-icon-s-management"></i>
                                <span>任务完成进度及使用时间</span>
                            </div>
                            <el-progress type="circle" :percentage="current_status" style="padding: 20px 0"></el-progress>
                            <div>累计耗时：{{ elapsedHour }}:{{ elapsedMinute }}:{{ elapsedSecond }}</div>
                        </div>
                    </el-col>
                    <el-col :span="20">
                        <div class="grid-content bg-purple-light" @mouseout="mouseout" @mouseover="mouseover">
                            <div class="gt-card-header">
                                <i class="el-icon-s-management"></i>
                                <span>节点硬件信息</span>
                            </div>
                            <el-table
                                :data="tableData"
                                height="200"
                                border
                                :cell-style="styleBack"
                                style="width: 100%; background-color: white; border: gray">
                                <el-table-column prop="node_type" label="节点类型" width="100"> </el-table-column>
                                <el-table-column prop="name" label="节点IP" width="150"> </el-table-column>
                                <el-table-column prop="cpu" label="CPU" width="80"> </el-table-column>
                                <el-table-column prop="gpu" label="GPU"> </el-table-column>
                                <el-table-column prop="memory" label="内存" width="100"> </el-table-column>
                                <el-table-column prop="cpu_percent" label="CPU利用率" width="110"> </el-table-column>
                                <el-table-column prop="gpu_percent" label="GPU利用率" width="110"> </el-table-column>
                                <el-table-column prop="memory_percent" label="内存利用率" width="110"> </el-table-column>
                            </el-table>
                        </div>
                    </el-col>
                </el-row>
            </div>
            <!-- 节点信息 -->
            <div class="se-container-main">
                <el-row v-for="(node_data, index) in nodes_data" :key="index">
                    <el-col :span="24">
                        <p style="text-align: left">
                            {{ node_data.ip_message.node_message }}：{{ node_data.ip_message.ip_computer }} 正在处理影像： {{ node_data.node_image }}
                        </p>
                        <el-steps :active="node_data.node_information_all_step" align-center>
                            <el-step
                                :title="step.node_name"
                                v-for="(step, index) in node_data.node_information"
                                :key="index"
                                :process-status="getStatus(step.status)"></el-step>
                        </el-steps>
                    </el-col>
                </el-row>
            </div>
            <!-- 日志和报错信息 -->
            <div class="se-container-footer">
                <el-tabs type="border-card" style="height: 100%">
                    <el-tab-pane>
                        <span slot="label"><i class="el-icon-date"></i> 日志信息</span>
                        <div class="gt-message">
                            <p style="color: green" v-for="(context, index) in runtime_log_info" :key="index">{{ context }}</p>
                        </div>
                    </el-tab-pane>
                    <el-tab-pane label="报错提示">
                        <span slot="label"><i class="el-icon-error"></i>报错提示</span>
                        <div class="gt-message">
                            <p style="color: red" v-for="(context, index) in error_log_info" :key="index">{{ context }}</p>
                        </div>
                    </el-tab-pane>
                </el-tabs>
            </div>
        </div>
    </el-dialog>
</template>

<script>
import axios from 'axios';
import { nextTick } from 'vue';
import { getProcessStatusApi } from '@/api/commonApi';
export default {
    name: 'processing',
    data() {
        return {
            // 处理类型
            detection_type: '遥感解译',
            // 节点表滚动定时器
            timer: null,
            // 后台请求定时器
            requestTimer: null,
            // 运行时间定时器
            SODTimer: null,

            // 组件显示
            detailVisible: false,

            // 运行时间
            elapsedTime: 0,
            elapsedHour: '00',
            elapsedMinute: '00',
            elapsedSecond: '00',

            // Task ID
            tasks_id: [],
            // Project ID
            project_id: '',
            // 当前状态
            current_status: 0,
            // 节点数据
            nodes_data: [],
            // 节点硬件表
            tableData: [],
            // 运行日志
            runtime_log_info: [],
            error_log_info: [],
            error_count: 0,
            success_count: 0
        };
    },
    watch: {
        detailVisible() {
            if (!this.detailVisible) {
                // 销毁组件
                this.$emit('closeDialog');
            }
        },
        current_status() {
            //判断解译是否结束
            if (Math.abs(this.current_status - 100) <= 0.00001 && this.detailVisible) {
                this.tasksProgressInfo(this.project_id);
                this.$nextTick(() => this.allOverDialog());
            }
        }
    },
    methods: {
        //点击开始解译，父组件获取响应数据，在子组件显示并初始化
        init(data, detection_type) {
            this.detailVisible = true;
            // 解译类型
            this.detection_type = detection_type;
            // 项目 ID
            this.project_id = data.id;
            // 记录 Tasks ID
            // this.tasks_id.push(...data.data.task_id.map(task_info => {
            //   return task_info.task_id
            // }));
            this.tasksProgressInfo(data.id, true);
        },
        //节点硬件信息回调，根据使用率调整背景颜色
        styleBack({ row, column, rowIndex, columnIndex }) {
            let cpu_percent = row.cpu_percent.slice(0, -1);
            if (columnIndex === 5 && cpu_percent > 70) {
                return { backgroundColor: 'red' };
            } else if (columnIndex === 5) {
                return { backgroundColor: '#FDD56A' };
            }
            let gpu_percent = row.gpu_percent.slice(0, -1);
            if (columnIndex === 6 && gpu_percent > 70) {
                return { backgroundColor: 'red' };
            } else if (columnIndex === 6) {
                return { backgroundColor: '#FDD56A' };
            }
            let memory_percent = row.memory_percent.slice(0, -1);
            if (columnIndex === 7 && memory_percent > 70) {
                return { backgroundColor: 'red' };
            } else if (columnIndex === 7) {
                return { backgroundColor: '#FDD56A' };
            }
        },
        //鼠标移入节点硬件信息，清除定时
        mouseover() {
            clearInterval(this.timer);
        },
        //鼠标移出，节点自动滚动以便展示多个机器的硬件信息
        mouseout() {
            this.autoScroll(false);
        },
        //使用定时器使硬件信息自动滚动
        autoScroll(init) {
            this.$nextTick(() => {
                const t = 50;
                const box = this.$el.querySelector('.el-table__body-wrapper');
                const content = this.$el.querySelector('.el-table__body');
                //是否从头开始
                if (init) box.scrollTop = 0;
                // set
                this.timer = setInterval(() => {
                    this.rollStart(box, content);
                }, t);
            });
        },
        //开始滚动
        rollStart(box, content) {
            if (box.scrollTop >= content.scrollHeight - box.offsetHeight) {
                box.scrollTop = 0;
            } else {
                box.scrollTop++;
            }
        },
        // 请求后台正在运行任务信息
        async tasksProgressInfo(id, initialize = false) {
            const res = await getProcessStatusApi(id);
            if (res.code == 0) {
                if (res.data.data.length !== 0) {
                    // 更新 节点硬件信息
                    this.tableData = res.data.data.map((node_ip) => {
                        // 更新 日志
                        let log_context = node_ip.ip_message.ip_computer + ':' + node_ip.current_process;
                        log_context = log_context.slice(0, log_context.length);
                        if (node_ip.current_process.includes('ERROR')) {
                            if (log_context !== this.error_log_info[0]) {
                                this.error_log_info.unshift(log_context);
                            }
                        } else {
                            if (log_context !== this.runtime_log_info[0]) {
                                this.runtime_log_info.unshift(log_context);
                            }
                        }
                        return {
                            node_type: node_ip.ip_message.node_message,
                            name: node_ip.ip_message.ip_computer,
                            cpu: node_ip.ip_message.cpu_info.split('核数')[1],
                            gpu: node_ip.ip_message.gpu_info,
                            memory: node_ip.ip_message.total_memory,
                            cpu_percent: node_ip.ip_message.used_cpu,
                            gpu_percent: node_ip.ip_message.used_gpu,
                            memory_percent: node_ip.ip_message.used_memory
                        };
                    });
                    // 更新 节点显示
                    this.nodes_data = res.data.data;
                    // 更新 处理进度
                    this.current_status = res.data.current_status;
                    this.error_count = res.data.error_count;
                    this.success_count = res.data.success_count;
                }
            }
        },
        // 取消任务
        // cancelTasks(tasksID) {
        //   console.log('@@@@@@@@@@cancelcancelcancelcancel')
        //   // 请求
        //   axios.post('/api/apps/cancel_celery_tasks', {
        //     tasks_id: tasksID,
        //   })
        //     .then(response => {
        //       if (this.current_status < 100) {
        //         this.$message.success(response.data.msg);
        //       }
        //     })
        //     .catch(error => {
        //       this.detailVisible = false;
        //       this.$message.error('取消解译失败！');
        //       console.error('取消解译失败:', error);
        //     });
        // },
        // 秒转时分秒
        // 取消任务
        cancelTasks() {
            if (this.current_status === 100) {
            } else {
                this.$alert('任务正在进行，离开此页面，后台仍会继续执行影像解译处理模块哦!!', '提示', {
                    confirmButtonText: '确定',
                    callback: (action) => {
                        this.detailVisible = false;
                    }
                });
            }
        },
        //时间秒转时-分-秒
        secondToDate(sod) {
            let h = Math.floor(sod / 3600);
            let m = Math.floor((sod / 60) % 60);
            let s = Math.floor(sod % 60);
            this.elapsedHour = h < 100 ? h.toString().padStart(2, '0') : h.toString();
            this.elapsedMinute = m.toString().padStart(2, '0');
            this.elapsedSecond = s.toString().padStart(2, '0');
        },
        // 重置时分秒
        resetHMS() {
            this.elapsedHour = '00';
            this.elapsedMinute = '00';
            this.elapsedSecond = '00';
        },
        // 设置定时器
        setRequestTimer() {
            this.$nextTick(() => {
                if (this.requestTimer === null) {
                    this.requestTimer = setInterval(() => {
                        this.tasksProgressInfo(this.project_id);
                    }, 5000);
                }
            });
        },
        // 日积秒定时器
        setSODTimer() {
            this.$nextTick(() => {
                if (this.SODTimer === null) {
                    this.SODTimer = setInterval(() => {
                        // 更新时间
                        this.elapsedTime += 1;
                        this.secondToDate(this.elapsedTime);
                    }, 1000);
                }
            });
        },
        // 完成解译提示框
        allOverDialog() {
            this.$alert(this.detection_type + '已完成!!' + '成功：' + this.success_count + '失败：' + this.error_count, '遥感解译', {
                confirmButtonText: '确定',
                callback: (action) => {
                    //点击确定，清除定时器，停止请求
                    clearInterval(this.requestTimer);
                    clearInterval(this.SODTimer);
                }
            });
        },
        getStatus(status) {
            if (status === 0) {
                return 'wait';
            } else if (status === 1) {
                return 'success';
            } else if (status === 2) {
                return 'error';
            } else {
                return 'wait'; // 默认状态为等待
            }
        }
    },
    mounted() {
        // 每次进入界面时，先清除之前的所有定时器，然后启动新的定时器
        clearInterval(this.requestTimer);
        clearInterval(this.SODTimer);
        this.requestTimer = null;
        this.SODTimer = null;
        this.setSODTimer();
        this.setRequestTimer();
    },
    beforeDestroy: function () {
        // 每次离开当前界面时，清除定时器
        // 取消任务
        this.cancelTasks();
        // 清除定时器
        clearInterval(this.requestTimer);
        this.requestTimer = null;
        clearInterval(this.SODTimer);
        this.SODTimer = null;
        this.resetHMS();
    }
};
</script>

<style scoped lang="scss">
#interpreting-processing-dialog {
    overflow-y: auto;

    .el-dialog__header {
        line-height: 10px;
        padding: 10px 10px 10px;

        .el-dialog__title {
            font-size: 22px;
        }

        .el-row .el-table {
            height: 300px !important;
        }

        .el-row .el-col .grid-content .el-progress {
            padding-top: 20px !important;
            padding-bottom: 0 !important;
        }
    }

    ::v-deep .el-dialog__body {
        overflow-y: scroll;
        height: 80%;
        max-height: 70vh;
        padding: 0;
    }

    .el-row {
        margin-bottom: 20px;

        &:last-child {
            margin-bottom: 0;
        }
    }

    .se-container {
        display: flex;
        flex-direction: column;
        height: 90%;
    }

    .gt-message {
        flex: 1;
        text-align: left;
        height: 30vh;
        overflow-y: scroll;
        line-height: 20px;
    }

    .se-container-header {
        flex: 0 0 auto;
        display: inline-block;
        padding: 10px;
        margin-right: 10px;
    }

    .se-container-footer {
        flex: 0 0 auto;
        margin-top: 10px;
        margin-right: 10px;
        padding: 0;
    }

    .se-container-main {
        flex: 0 0 auto;
        margin-top: 10px;
        margin-right: 10px;
        padding: 0;
        height: 20vh;
        border: 1px solid #e5e9f2;
        overflow-y: scroll;

        .el-col p {
            line-height: 30px;
            padding-left: 20px;
        }
    }

    .gt-card-header {
        text-align: left;
        padding: 10px;
        background-color: #e5e9f2;
    }

    .el-col {
        border-radius: 4px;
    }

    .bg-purple {
        background: #fff;
    }

    .bg-purple-light {
        background: #e5e9f2;
    }

    .grid-content {
        border-radius: 4px;
        min-height: 100px;
        text-align: center;
    }

    .row-bg {
        padding: 10px 0;
        background-color: #f9fafc;
    }
}
::v-deep .el-table th.el-table__cell {
    background: #fafafa !important;
    color: black !important;
}
::v-deep .el-table tbody tr:nth-child(odd) td.el-table__cell {
    background-color: #fafafa !important;
    color: black;
}
</style>
