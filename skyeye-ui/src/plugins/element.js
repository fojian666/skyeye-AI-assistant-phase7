/**
 * 按需加载 element-ui 组件
 * @description
 * [参考官网 - 按需加载](https://element.eleme.cn/#/zh-CN/component/quickstart#an-xu-yin-ru)
 */
 import Vue from 'vue';
 import ElementUI from 'element-ui';
 import 'element-ui/lib/theme-chalk/index.css';
 import { Message, MessageBox } from 'element-ui';

 Vue.prototype.$message  = Message;
 Vue.prototype.$confirm = MessageBox.confirm;
 
 Vue.use(ElementUI, { size: 'small' });
 