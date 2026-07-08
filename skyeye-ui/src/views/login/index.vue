<template>
  <div class="se-container-login">
    <div class="head">
      <h1 class="ai-banner-title">{{ title }}</h1>
    </div>
    <div class="main">
      <div class="down">
        <div class="login-form">
          <div class="yuanzhu">
            <div class="yuanzhuli"></div>
          </div>
          <div class="login-content">
            <span>用户登录</span>
            <div class="xiahuaxian"></div>
            <div class="login-input">
              <el-form
                :rules="rules"
                :model="formFields"
                ref="LoginForm">
                <el-form-item prop="username" class="form-item">
                  <el-input
                    class="username"
                    type="text"
                    placeholder="账户"
                    v-model="formFields.username"
                    prefix-icon="el-icon-user"
                  >
                  </el-input>
                </el-form-item>
                <!-- 2：密码 -->
                <el-form-item prop="password" class="form-item">
                  <el-input
                    placeholder="密码"
                    v-model="formFields.password"
                    prefix-icon="el-icon-lock"
                    @keyup.enter.native="loginBtnClick('LoginForm')"
                    show-password
                  >
                  </el-input>
                </el-form-item>

                <el-form-item>
                  <!--  3: 记住密码 -->
                  <el-checkbox
                    v-model="formFields.rememberPass"
                    class="remember-pass"
                    @change="rememberPassListener"
                  >
                    记住密码
                  </el-checkbox>

                  <!-- 4:自动登录 -->
                  <el-checkbox
                    v-model="formFields.autoLogin"
                    class="remember-me"
                    @change="autoLoginListener"
                  >
                    7日内自动登录
                  </el-checkbox>
                </el-form-item>

                <!-- 5: 登录按钮 -->
                <el-form-item class="button-item">
                  <el-button
                    type=""
                    class="login-btn"
                    @click="loginBtnClick('LoginForm')"
                  >
                    登录
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
          </div>
        </div>
      </div>

    </div>
    <div class="foot">
      版权所有：©空间感知与优化计算研究所.

    </div>


  </div>
</template>

<script>
import {setCookie, getCookie, removeCookie} from '@/utils/utils';

const Base64 = require('js-base64').Base64;
import {getLoginCheckApi, getPublicKeyApi} from "@/api/commonApi";
import {JSEncrypt} from "jsencrypt";

export default {
  name: 'LoginForm',
  components: {},
  data() {
    // 检查用户名
    let checkUsername = (rule, value, callback) => {
      if (!value || value.trim() == '')
        return callback(new Error('用户名不能为空'));
      if (value.trim().length > 16)
        return callback(new Error('用户名长度不能超过16位'));
      callback();
    };

    // 检查密码
    let checkPassword = (rule, value, callback) => {
      if (!value || value.trim() == '') {
        return callback(new Error('密码不能为空'));
      }
      callback();
    };

    return {
      // 表单属性
      formFields: {
        username: '',
        password: '',
        rememberPass: false, // 记住密码, 保存在cookie中
        autoLogin: false // 自动登录
      },
      // 表单校验规则
      rules: {
        username: [{validator: checkUsername, trigger: onblur}],
        password: [{validator: checkPassword, trigger: onblur}]
      },
      title: window.config.system_name,
      publicKey: ''
    };
  },
  // watch
  watch: {
    'formFields.username': function (newVal, oldVal) {
      if (oldVal !== "") {
        // 清空 password
        this.formFields.password = '';
      }
    }
  },

  // ==================================================================
  // computed
  computed: {
    getUsername() {
      return this.formFields.username;
    },
    getPassword() {
      return this.formFields.password;
    }
  },

  created() {
    let username = getCookie('username');
    // 如果存在赋值给表单，并且将记住密码勾选
    if (username) {
      let password = Base64.decode(getCookie('password'));
      this.formFields.username = username;
      this.formFields.password = password;
      this.formFields.rememberPass = true;
    }
  },


  // ==================================================================
  // methods
  methods: {
    /**
     * 1: 监听"登录"点击事件
     * @param formName 表单的名字和 ref 中的值要相同
     */
    loginBtnClick(formName) {
      // 表单用户名、密码 校验成功~
      if (this.formFields.rememberPass) {
        let password = Base64.encode(this.formFields.password); // base64加密
        // 字符串拼接cookie
        setCookie('username', this.formFields.username);
        setCookie('password', password);
      } else {
        removeCookie('username');
        removeCookie('password');
      }
      const params = {
        username: this.formFields.username,
        password: this.encodePwd(this.formFields.password)
      }
      this.login(params)
    },
    async getPublicKey() {
      const res = await getPublicKeyApi();
      this.publicKey = res.data.public_key;
    },
    /**
     * 2: 监听 "7日自动登录" checkbox 点击事件
     * @param val checkbox 绑定的值。选中：true; 未选中: false。
     */
    autoLoginListener(val) {
      if (val === true) this.formFields.rememberPass = true;
    },

    /**
     * 3: 监听 "记住密码" checkbox 点击事件
     * @param val checkbox 绑定的值。选中：true; 未选中: false。
     */
    rememberPassListener(val) {
      if (val === false) this.formFields.autoLogin = false;
    },


    /**
     * cookie的操作
     * @param fields 表单内容(JSON对象)
     */
    cookieOps(fields) {
      if (fields.rememberPass)
        // "记住密码"选中状态 ==> 当登录成功的时候保存
        setCookie('vue-remember-username-password', JSON.stringify(fields), {
          expires: 7,
          path: '/'
        });
      // 记住密码未选中 ===> 登录成功的时候移除cookie
      else removeCookie('vue-remember-username-password', {path: '/'});
    },

    /**
     * 关联系统登录免验证
     * @param username(URLSearchParams)
     */
    checkLogin() {
      let username = this.getQueryString("username")
      let token = this.getQueryString("token")
      // 判断口令是否为“gtmap”
      if (token == null) {
        return true;
      } else if (token == "gtmap") {
        username == null ? username = "admin" : "";
        // 后台请求
        let params = new URLSearchParams();
        params.append('username', username);
        params.append('token', token);
        this.login(params)
      } else {
        this.$message.warning("关联系统登录的口令不正确！")
        localStorage.clear();
        return false;
      }

    },
    // 原生JS 自定义加密
    encodePwd(plainText, offset = 18) {
      let result = "";
      // 1. 拼接密钥混淆
      let mixStr = plainText + "|" + this.publicKey;
      // 2. 字符编码偏移
      for (let i = 0; i < mixStr.length; i++) {
        let code = mixStr.charCodeAt(i);
        result += String.fromCharCode(code + offset);
      }
      // 3. 简单反转
      result = result.split("").reverse().join("");
      // 4. base64 包装（避免特殊字符）
      return btoa(result);
    },

    /**
     * 登录后台验证
     * @param params(url)
     * @param token(url)
     */
    async login(params) {
      let then = this;
      try {
        const res = await getLoginCheckApi(params);
        if (res.code === 0) {
          // 登录成功设置cookie
          localStorage.setItem('username', params["username"]);
          // 设置登录用户角色
          localStorage.setItem('role', res.role);
          localStorage.setItem('tokens', res.tokens); // 存储 JWT 令牌
          then.cookieOps(params);
          //记录点击时间
          localStorage.setItem("lastClickTime", new Date().getTime());
          const path = localStorage.getItem('path')
          then.$message.success('登录成功！');
          setTimeout(function () {
            // 路由跳转
            if (path) {
              then.$router.push(path);
            } else {
              // 设置session和路由跳转不要放反
              if (res.role === 3) {
                then.$router.push('/data-management/one-map');
              } else {
                then.$router.push('/data-management/one-map');
              }
            }
          }, 1000)

        } else {
          then.$message.warning(res.msg);
          removeCookie('username');
          removeCookie('password');
        }
      } catch (e) {
        then.$message.warning("后台服务尚未加载完成，请稍后重试！");
      }

    },

    getQueryString(name) {
      var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
      var r = window.location.search.substr(1).match(reg);
      if (r != null) {
        return unescape(r[2]);
      }
      return null;
    }

  },
  async mounted() {
    await this.getPublicKey();
    //this.checkLogin();
    let flag = navigator.userAgent.match(/(phone|pad|pod|iPhone|iPod|ios|iPad|Android|Mobile|BlackBerry|IEMobile|MQQBrowser|JUC|Fennec|wOSBrowser|BrowserNG|WebOS|Symbian|Windows Phone)/i)
    if (flag) {
      document.getElementById("formLogin").style.width = '80%'
      document.getElementsByClassName('left_img')[0].style.display = 'none'
    } else {
      //document.getElementById("formLogin").style.width = '20%'
    }
  },
};
</script>

<style scoped>
.se-container-login {
  height: 100%;
  width: 100%;
  flex-direction: column;
  justify-content: space-between;
}

.head {
  height: 10%;
  display: flex;
  display: -webkit-flex;
  padding: 10px;
  margin-left: 3%
}

.main {
  height: 85%;
  display: flex;
  flex-direction: column;
  position: relative;
  background-image: url('@/assets/images/login-bg.jpg');
  background-repeat: no-repeat;
  background-size: cover;

}

.foot {
  height: 5%;
  line-height: 5%;
  color: black;
  display: none;
  justify-content: center;
  align-items: center; /* 垂直居中 */
  text-align: center;
}

.ai-login-logo {
  height: 70%;
  margin-top: 5px;
}

.ai-banner-title {
  color: #1a4396;
  font-size: 2.3em;
  font-weight: bold;
  margin-left: 8px;
  margin-top: 5px;
  font-family: Microsoft YaHei, Microsoft YaHei-Regular;
}

.down {
  flex: 1;
  margin-bottom: 15px;
}

.login-bj {
  position: absolute;
  top: 50px;
  z-index: 10;
  width: 100%;
  height: 80%;
  display: block;
}

.login-form {
  height: 60%;
  width: 25%;
  min-width: 400px;
  z-index: 2000;
  position: absolute;
  right: 5%;
  /* padding: 50px; */
  top: 15%;
  justify-content: center;
  align-items: center; /* 垂直居中 */
}

.yuanzhu {
  height: 25px;
  width: 90%;
  margin: 5px auto;
  background-color: #8bb8e7;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: center;
  align-items: center; /* 垂直居中 */
}

.yuanzhuli {
  height: 15px;
  width: 95%;
  margin: 0px auto;
  background-color: #225ca1;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.login-content {
  height: 85%;
  width: 80%;
  background: linear-gradient(to bottom, rgb(211, 239, 255), rgb(234, 252, 255));
  position: absolute;
  top: 19px;
  left: 20px;
  left: 10%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.xiahuaxian {
  height: 5px;
  width: 100px;
  background-color: #42b4f2;
  border-radius: 15px;
  margin-top: 15px;
}

.login-content span {
  color: #42b4f2;
  font-size: 2.2em;
  font-weight: bold;
  padding-top: 30px;
}

.login-input {
  width: 85%;
  flex: 1;
  margin-top: 10px;
}

.remember-me,
.remember-pass {
  color: black;
}

.login-btn {
  width: 100%;
  transition: background-color 0.3s;
  -moz-transition: background-color 0.3s; /* Firefox 4 */
  -webkit-transition: background-color 0.3s; /* Safari 和 Chrome */
  -o-transition: background-color 0.3s; /* Opera */
  background-color: #3786ec;
  border-color: #3786ec;
  color: #ffffff;
  letter-spacing: 4px;
  height: 38px;
  font-size: 1rem;
  font-weight: bold;
}

::v-deep .el-input--small .el-input__inner {
  height: 38px;
  line-height: 32px;
}
::v-deep .el-input__inner{
  color:black!important;
}
</style>