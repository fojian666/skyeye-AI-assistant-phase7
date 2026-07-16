<template>
    <div class="color-input-picker">
        <div class="color-preview" :style="{ backgroundColor: displayColor }"></div>
        <a-input class="color-input" :value="inputValue" placeholder="#FF0000 或 #F00" @input="handleInput" @blur="handleInputBlur" />
        <el-color-picker :value="pickerValue" :show-alpha="false" popper-append-to-body class="color-picker" @change="handlePickerChange" />
    </div>
</template>

<script>
import { isValidHexColor, normalizeHexColor } from '@/utils/colorHex';

export default {
    name: 'ColorInputPicker',
    props: {
        value: {
            type: String,
            default: '#FF0000'
        }
    },
    data() {
        return {
            inputValue: this.value || '#FF0000'
        };
    },
    computed: {
        pickerValue() {
            return normalizeHexColor(this.value) || '#FF0000';
        },
        displayColor() {
            return this.pickerValue;
        }
    },
    watch: {
        value(next) {
            this.inputValue = next || '';
        }
    },
    methods: {
        emitColor(color) {
            this.$emit('input', color);
            this.$emit('change', color);
        },
        handleInput(event) {
            this.inputValue = event.target.value;
        },
        handleInputBlur() {
            const trimmed = (this.inputValue || '').trim();
            if (!trimmed) {
                this.inputValue = this.value || '#FF0000';
                return;
            }
            if (!isValidHexColor(trimmed)) {
                this.$message.warning('请输入合法色值，如 #FF0000 或 #F00');
                this.inputValue = this.value || '#FF0000';
                return;
            }
            const normalized = normalizeHexColor(trimmed);
            this.inputValue = normalized;
            this.emitColor(normalized);
        },
        handlePickerChange(color) {
            if (!color) {
                return;
            }
            const normalized = normalizeHexColor(color);
            this.inputValue = normalized;
            this.emitColor(normalized);
        }
    }
};
</script>

<style scoped>
.color-input-picker {
    display: flex;
    align-items: center;
    gap: 8px;
}

.color-preview {
    width: 24px;
    height: 24px;
    border: 1px solid #d9d9d9;
    border-radius: 2px;
    flex-shrink: 0;
}

.color-input {
    flex: 1;
    min-width: 120px;
}

.color-picker {
    flex-shrink: 0;
}
</style>
