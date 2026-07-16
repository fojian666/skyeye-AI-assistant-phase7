<template>
    <div class="gtp-container">
        <el-card class="box-card" style="width: 100%; height: 100%; position: relative">
            <div slot="header" class="clearfix">
                <span>编码标识——{{ data.bsm }}</span>
            </div>
            <div class="body">
                <p>地类名称：{{ data.name }}</p>
                <p>权属单位：{{ data.unit_name }}</p>
                <!--                <div class="verify-result">-->
                <!--                    <p>是否占用耕地：</p>-->
                <!--                    <el-radio :value="is_occupy" @change="handleUserSelect('1')" label="1">未占用</el-radio>-->
                <!--                    <el-radio :value="is_occupy" @change="handleUserSelect('2')" label="2">占用</el-radio>-->
                <!--                    <el-button type="text" size="medium" @click="handleBtnClick" :disabled="is_show" class="btn">核实结论</el-button>-->
                <!--                </div>-->
            </div>
        </el-card>
        <el-dialog title="核实结论" :visible.sync="dialogVisible" style="margin-top: 20vh" width="30%" :modal-append-to-body="false">
            <div class="verify-item">
                <span>编码标识：</span>
                <el-input v-model="data.bsm" :disabled="true"></el-input>
            </div>
            <div class="verify-item">
                <span>核实结论：</span>
                <el-input type="textarea" v-model="verifyResult"></el-input>
            </div>
            <span slot="footer" class="dialog-footer">
                <el-button @click="dialogVisible = false">取 消</el-button>
                <el-button type="primary" @click="handelConfirmSubmit">提 交</el-button>
            </span>
        </el-dialog>
    </div>
</template>

<script>
import { modifyPatternConclusionApi, modifyPatternStatusApi } from '@/api/commonApi';

export default {
    name: 'CardsComponent',
    props: {
        data: {
            type: Object,
            required: true
        }
    },
    data() {
        return {
            is_occupy: '',
            is_show: true,
            dialogVisible: false,
            verifyResult: '',
            isInitialized: false
        };
    },
    computed: {
        status() {
            //线索状态标签css的类
            return {
                'status-checked': this.data.status === 0,
                'status-unchecked': this.data.status === 1
            };
        },
        currentStatus() {
            //当前线索状态
            if (this.data.status === 0) {
                return '待核实';
            } else {
                return '已核实';
            }
        },
        // 动态计算按钮样式
        buttonStyle() {
            if (this.is_occupy === '2') {
                return { color: 'blue' }; // 等于 '2' 时字体为灰色
            } else {
                return { color: 'grey' }; // 其他情况下字体为蓝色
            }
        }
    },
    watch: {
        is_occupy(val, oldVal) {
            // 只有当值变化且是用户操作时才发送请求
            if (val !== null && oldVal !== null) {
                if (val === '2') {
                    //占用
                    this.is_show = false;
                    if (this.isFromUser) {
                        this.handlePolygonStatus();
                    }
                } else if (val === '1') {
                    //未占用
                    this.is_show = true;
                    if (this.isFromUser) {
                        this.handlePolygonStatus();
                    }
                }
            }
            this.isFromUser = false; // 重置标志
        }
    },
    methods: {
        confirmRadioStatus() {
            //0还未做核实  1占用 2未占用
            if (this.data.status === 0) {
                this.is_occupy = '';
            } else if (this.data.status === 1) {
                this.is_occupy = '1';
            } else {
                this.is_occupy = '2';
                this.verifyResult = this.data.verify_conclusion;
            }
        },
        handleBtnClick() {
            this.dialogVisible = true;
        },
        async handelConfirmSubmit() {
            const para = {
                polygonDataId: this.data.id,
                verifyConclusion: this.verifyResult
            };
            const res = await modifyPatternConclusionApi(para);
            if (res.code === 0) {
                this.$message.success('提交成功');
                this.dialogVisible = false;
            } else {
                this.$message.error(res.msg);
            }
        },
        async handlePolygonStatus() {
            const para = {
                polygonDataId: this.data.id,
                polygonDataStatus: this.is_occupy
            };
            const res = await modifyPatternStatusApi(para);
            if (res.code !== 0) {
                this.$message.error(res.msg);
            }
        },
        // 新增方法处理用户选择
        handleUserSelect(val) {
            this.isFromUser = true;
            this.is_occupy = val;
        }
    },
    mounted() {
        this.confirmRadioStatus();
    },
    created() {}
};
</script>

<style lang="scss" scoped>
.gtp-container {
    width: 100%;
    height: 100%;
    padding-right: 5px;
    cursor: pointer;
}

::v-deep .el-card__header,
::v-deep .el-card__body {
    padding: 5px 20px;
}
.clearfix span {
    white-space: nowrap; /* 不换行 */
    text-overflow: ellipsis; /* 超出部分显示省略号 */
    font-size: 16px;
}
.body {
    white-space: nowrap; /* 不换行 */
    text-overflow: ellipsis; /* 超出部分显示省略号 */
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-around;
}
.body p {
    font-size: 14px;
}
.status {
    position: absolute;
    right: 10px;
    top: 30px;
    width: 60px;
    height: 25px;
    line-height: 25px;
    text-align: center;
    color: #fff;
    font-size: 14px;
    border-radius: 10px;
}
.status-checked {
    background: #27be82;
}
.status-unchecked {
    background: #ff6452;
}
.status-process {
    background: #2db6f4;
}
::v-deep .el-card .el-card__header {
    height: 25%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    margin-top: 5px;
}

::v-deep .el-card__body {
    padding: 10px 20px;
}

@media (max-height: 900px) {
    .clearfix span {
        font-size: 13px;
    }
    .body p {
        font-size: 12px;
    }
    .verify-result p {
        font-size: 10px;
    }
}
.verify-result {
    display: flex;
    flex-direction: row;
    margin-top: 5px;
    align-items: center;
}
.verify-result p {
    font-size: 12px;
    margin-top: 0px;
}
.el-radio {
    line-height: 0px;
    margin-right: 5px;
    padding-top: 3px;
}
::v-deep .el-radio__label {
    font-size: 10px;
}
.verify-item {
    margin-bottom: 10px;
    display: flex;
    flex-direction: row;
    align-items: center;
}
.verify-item span {
    width: 100px;
}

::v-deep .el-card__header {
    height: 20px;
    display: flex;
}

::v-deep .el-card {
    border-radius: 4px;
    border: 1px solid #fff;
    overflow: hidden;
    transition: 0.3s;
}
::v-deep .btn {
    &.is-disabled {
        color: gray !important;
        opacity: 1;
        cursor: not-allowed;
    }
    &:not(.is-disabled) {
        color: blue;
    }
}
</style>
