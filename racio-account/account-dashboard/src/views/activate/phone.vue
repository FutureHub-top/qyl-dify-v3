<template>
    <div class="login-container">
        <div class="login-box">
            <div class="login-form">
                <el-row :gutter="5" style="padding-bottom: 10px;">
                    <el-col>
                        <h3>{{ roleTypes == "owner" ? "创建空间" : "加入空间" }}</h3>
                    </el-col>
                    <el-col :span="24">
                        <el-tooltip :visible="checkWorkSpaceBtn.tips" class="box-item" effect="light"
                            :content="checkWorkSpaceBtn.tipstext ? checkWorkSpaceBtn.tipstext : '长度3-12个字符'"
                            placement="top-end">
                            <el-input placeholder="请输入用户名/空间名" v-model.trim="workspace_name" minlength="8"
                                maxlength="30" clearable @input="isWorkspace"
                                :disabled="invitTokenInfo.role !== 'owner'" />
                        </el-tooltip>
                    </el-col>

                </el-row>
                <el-row :gutter="15" style="padding-bottom: 10px;" v-if="showVerify">
                    <el-col>
                        <h3>绑定手机号</h3>
                    </el-col>
                    <el-col :span="18">
                        <div>
                            <el-input maxlength="11" clearable v-model.number="phoneNum" @input="isPhone"
                                placeholder="输入需要绑定的手机号码" :disabled="!showVerify" />
                        </div>
                    </el-col>
                    <el-col :span="4">
                        <div class="check-code">
                            <el-button :disabled="!showVerify" :loading="checkCodeBtn.loading" type="primary"
                                @click="getCheckCode"> {{
                                    checkCodeBtn.text }}
                            </el-button>
                        </div>
                    </el-col>
                </el-row>

                <el-row :gutter="24" :justify="'start'" style="padding-bottom: 10px;" v-if="showVerify">
                    <el-col :span="24">
                        <div>
                            <el-input maxlength="4" clearable v-model.number="verifyCode" placeholder="请输入验证码"
                                :disabled="!showVerify" />
                        </div>
                    </el-col>
                </el-row>
                <el-row>
                    <el-col :span="24" style="text-align:center">
                        <div>
                            <el-button size="large" :width="100" type="primary" @click="activateAccount">{{
                                invitTokenInfo.role == "owner" ? "关联并创建空间" : "关联工作空间"
                                }}</el-button>
                        </div>
                    </el-col>
                </el-row>
                <el-row>
                    <el-col>

                    </el-col>
                </el-row>

            </div>
        </div>
        <Footer />
    </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue"
import Footer from "@/components/Footer/index.vue"
import { ElMessage, ElMessageBox } from "element-plus"
import { getWxInfo, sendSms, activate, checkOpenId, checkInvitToken, hasOwnerTenant, getJwtToken, tenantSwitch } from "@/api/api"
import { getQueryObject } from "@/utils/index"
import { useRouter } from "vue-router"
import { useUserStore } from "@/store/modules/user"
const router = useRouter()
const phoneNum = ref("")
const phoneStatus = ref(false)
const verifyPhoneNum = ref("")
const verifyCode = ref("")
const openId = ref("")
const workspace_name = ref("")
const accessToken = ref("")
const showWorkspace = ref(false)
const showVerify = ref(false)
const UserStore = useUserStore()
const dify_url = ref("")
const tenant_id = ref("")
const currentRole = ref("normal")
const urlQuery = getQueryObject(null)
const { token, code } = getQueryObject(null)

const invitTokenInfo = ref({
    is_valid: "",
    workspace_name: "",
    role: ""
})
const roleTypes = ref("")

function isPhone(value: string) {
    const reg = /^1[3456789]\d{9}$/
    if (reg.test(value)) {
        checkCodeBtn.value.disabled = false
        phoneStatus.value = true
    }
}
function isWorkspace() {
    const reg = /^[a-zA-Z0-9_\u4e00-\u9fa5]{3,12}$/i

    if (!reg.test(workspace_name.value)) {
        checkWorkSpaceBtn.value.tips = true
    } else {
        checkWorkSpaceBtn.value.tips = false
    }
}

function WxInfo() {
    getWxInfo({ code: code })
        .then(res => {
            let { code, msg, data } = res.data
            if (code == 0) {
                accessToken.value = data
                localStorage.setItem("access_token", data)
                hasTenant()
                // check(data)
            }

        })
        .catch(err => {
            ElMessage({
                message: "微信扫码异常，请重新扫码",
                type: 'error',
                duration: 5000,
            })
            setTimeout(() => {
                router.back()
            }, 5000);
        })


}
function goTo(uri) {
    console.log(uri, "localStorage.DIFY_TOKEN");

    if (uri.indexOf("http") != -1) {
        window.open(uri, '_blank')
    } else {
        router.replace(uri)
    }
}

function hasTenant() {

    hasOwnerTenant({
        token: token,
        access_token: accessToken.value
    })
        .then((result) => {

            let { data } = result.data
            workspace_name.value = data.tenant_name
            tenant_id.value = data.tenant_id

            invitTokenInfo.value.role = data.account_role
            if (data.is_joined_tenant) {
                getJwtToken({ "access_token": accessToken.value })
                    .then(res => {
                        let { code, data, msg } = res.data
                        if (code == 0) {
                            swtichTenant(tenant_id.value)
                            if (data.tenant_id == "" && data.current_role != "super_admin") {
                                ElMessageBox.alert('该Racio尚未找到您的关联帐号，请联系管理员（微信：dukexls）申请试用', '提示', {
                                    confirmButtonText: '知道了',
                                })
                                return
                            }
                            let userInfo = {
                                token: data.token,
                                access_token: accessToken.value,
                                roles: [data.current_role],
                                workspace_name: data.tenant_name,
                                workspace_id: data.tenant_id,
                                username: data.name
                            }


                            currentRole.value = data.current_role
                            UserStore.login(userInfo)


                            dify_url.value = import.meta.env.VITE_APP_DIFY_URL ? `${import.meta.env.VITE_APP_DIFY_URL}?console_token=${data.token}` : `${window.globalVariable.DIFY_URL}?console_token=${data.token}`
                            localStorage.setItem("DIFY_TOKEN", data.token)

                            if (urlQuery.state == "index") {

                                location.href = dify_url.value
                            } else if (urlQuery.state == "auth") {
                                router.replace("/workspace")
                            } else {
                                ElMessageBox.alert('您已加入该空间，点击【好的】直接进入体验', '提示', {
                                    // if you want to disable its autofocus
                                    // autofocus: false,
                                    confirmButtonText: '好的',
                                    callback: (action) => {
                                        goTo(dify_url.value)
                                    },
                                })
                            }

                        }
                    })
            }
            else if (data.has_owner_tenant) {
                ElMessageBox.alert(`该微信帐号已经创建空间，请更换微信帐号完成绑定操作`, '提示', {
                    confirmButtonText: '知道了',
                    dangerouslyUseHTMLString: true,
                    callback: () => {
                        router.back()
                    },
                })
            } else if (data.is_valid_invitation == false) {

                ElMessageBox.alert(`此邀请链接已经失效，请联系${workspace_name.value == "" ? "管理员（微信：dukexls）" : workspace_name.value + '的[管理员]'}获得新的邀请链接`, '提示', {
                    confirmButtonText: '知道了',
                    dangerouslyUseHTMLString: true,
                    callback: () => {
                        router.back()
                    },
                })
            } else {
                check(accessToken.value)
            }

        }).catch((err) => {
            ElMessageBox.alert(`${err}`, '提示', {
                confirmButtonText: '知道了',
                dangerouslyUseHTMLString: true,
                callback: () => {
                    router.back()
                },
            })
        });
}

// 检查是否已经绑定微信
function check(access_token) {
    checkOpenId({
        "access_token": access_token,
    })
        .then(res => {
            let { code, msg, data } = res.data
            if (code == 0) {
                if (data) {
                    showVerify.value = false

                } else {
                    showVerify.value = true
                }
            }

        })
}

function activateAccount() {
    if (accessToken.value == "") {
        ElMessage({
            message: '请先完成微信授权',
            type: 'warning',
            duration: 5000,
        })
        setTimeout(() => {
            router.back()
        }, 5000);
        return
    } else if (token == "") {
        ElMessageBox.alert(`此邀请链接已经失效，请联系${workspace_name.value == "" ? "管理员（微信：dukexls）" : workspace_name.value + '的[管理员]'}获得新的邀请链接`, '提示', {
            confirmButtonText: '知道了',
            dangerouslyUseHTMLString: true,
            callback: () => {
                router.back()
            },
        })
        return
    }
    activate({
        "token": token,
        "phone": `${verifyPhoneNum.value}`,
        "code": `${verifyCode.value}`,
        "access_token": accessToken.value,
        "tenant_name": workspace_name.value, //长度30个字符
    })
        .then(res => {
            let { code, msg, data } = res.data
            if (code == 0) {
                let userInfo = {
                    access_token: accessToken.value,
                    token: data.token,
                    roles: [data.account_role],
                    workspace_name: data.tenant_name,
                    name: data.name,
                    tenant_id: data.tenant_id
                }
                UserStore.login(userInfo)
                ElMessage({
                    message: '绑定成功',
                    type: 'success',
                    duration: 3000,
                })
                setTimeout(() => {
                    router.replace({
                        path: '/invitSuccess',
                        query: {
                            roleTypes: data.account_role,
                            workspace_name: data.tenant_name,
                            name: data.name
                        }
                    })
                }, 3000);
            } else if (code != 0 && msg == '不能重复加入同一个空间') {
                ElMessageBox.alert('您已加入该空间，点击【好的】直接进入体验', '提示', {
                    confirmButtonText: '好的',
                    callback: (action) => {
                        ElMessage({
                            type: 'info',
                            message: `action: ${action}`,
                        })
                    },
                })

            } else {

                ElMessage({
                    message: msg,
                    type: 'error',
                })
            }
        })
}
function sendmsm() {
    sendSms({ token: token, phone: phoneNum.value })
        .then(res => {
            let { code, msg, data } = res.data
            if (code == 0) {
                verifyPhoneNum.value = phoneNum.value
                ElMessage({
                    message: '验证码发送成功',
                    type: 'success',
                })
                // 清除掉定时器
                checkCodeBtn.value.timer && clearInterval(checkCodeBtn.value.timer)
                // 开启定时器
                checkCodeBtn.value.timer = setInterval(() => {
                    const tmp = checkCodeBtn.value.duration--
                    checkCodeBtn.value.text = `${tmp}秒`
                    if (tmp <= 0) {
                        // 清除掉定时器
                        clearInterval(checkCodeBtn.value.timer)
                        checkCodeBtn.value.duration = 60
                        checkCodeBtn.value.text = '重新获取'
                        // 设置按钮可以单击
                        checkCodeBtn.value.disabled = false
                    }
                }, 1000)
            } else {
                ElMessage({
                    message: msg,
                    type: 'error',
                })
            }
        })

}

let checkWorkSpaceBtn = ref({
    text: '检查是否可用',
    loading: false,
    tips: false,
    duration: 60,
    tipstext: ""
})
let checkCodeBtn = ref({
    text: '获取验证码',
    loading: false,
    disabled: true,
    duration: 60,
    timer: null
})

function swtichTenant(tenant_id) {
    let data = {
        tenant_id: tenant_id
    }
    tenantSwitch(data)
        .then(res => {
            let { code, data, msg } = res.data

        })
}

const getCheckCode = () => {
    if (!phoneStatus.value) {
        ElMessage({
            message: '请输入手机号',
            type: 'warning',
            duration: 5000,

        })
        return
    }
    // 倒计时期间按钮不能单击
    if (checkCodeBtn.value.duration !== 60) {
        checkCodeBtn.value.disabled = true

    } else {
        sendmsm() //调用发送短信接口
    }

}

onMounted(() => {
    WxInfo()
})

</script>
<style lang="scss" scoped>
.check-code {
    line-height: 42px;
    font-size: 12px;
    cursor: pointer
}

@import "./phone";

.login-box {
    height: 80%
}

.login-container {
    display: block;
}
</style>
