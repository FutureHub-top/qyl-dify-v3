<template>

    <div class="home-container">
        <el-row class="row-bg" :gutter="11">
            <el-col>
                <div style="padding-top: 4px;">
                    <el-button type="primary" :icon="Plus" @click="openInvite">
                        邀请进入空间
                    </el-button>
                </div>
            </el-col>
            <el-col :span="24">
                <el-table :data="tableData" style="width: 100%">
                    <el-table-column prop="email" label="邮箱地址" min-width="200" />
                    <el-table-column prop="invite_link" label="邀请链接" min-width="200">
                        <template #default="scope">
                            <div @click="handleCopy(scope.row.invite_link, $event)">点击复制：{{ scope.row.invite_link }}
                            </div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="remark" label="备注" width="120" />
                    <el-table-column prop="invited_by" label="邀请人" width="120" />
                    <el-table-column prop="role" label="邀请角色" width="120">
                        <template #default="scope">
                            <div>{{ scope.row.role == "owner" ? "空间所有者" : scope.row.role == "admin" ? "空间管理员" :
                                "尊享会员"
                                }}
                            </div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="created_at" label="创建时间" width="120">
                        <template #default="scope">
                            <div>{{ formatTime(scope.row.created_at, "") }}</div>
                        </template>
                    </el-table-column>
                    <!-- <el-table-column prop="last_login_at" label="最后登录时间" width="150">
                        <template #default="scope">
                            <div>{{ scope.row.last_login_at == null ? "无登录" : formatTime(scope.row.last_login_at, "") }}
                            </div>
                        </template>
</el-table-column> -->


                    <!-- <el-table-column label="操作" fixed="right" width="180">
                        <template #default="scope">
                            <el-button type="primary">编辑</el-button>
                            <el-button type="danger">删除</el-button>
                        </template>
                    </el-table-column> -->
                </el-table>
            </el-col>
            <el-col>
                <div style="padding: 15px ; background-color: #fff;">
                    <el-pagination v-model:current-page="PageInfo.page" v-model:page-size="PageInfo.limit" background
                        :total="PageInfo.total" @current-change="handleCurrentChange" />
                </div>
            </el-col>
        </el-row>

    </div>

    <el-dialog v-model="inviteDialog" title="邀请进入空间" width="500" align-center>
        <el-row>
            <el-col style="margin-bottom:20px">
                <span>输入被邀请人邮箱，如空则只生成邀请链接</span>
            </el-col>
        </el-row>
        <el-row v-if="roles.some(item => item !== 'superAdmin')" style="margin-bottom: 20px;">
            <el-select v-model="workspaceRole">
                <el-option v-for="item in rolesList" :key="item.key" :label="item.value" :value="item.key"
                    :disabled="(roles[0] != 'owner' && item.key == 'admin')" />
            </el-select>
        </el-row>
        <el-row>
            <el-col style="margin-bottom:20px">
                <div>
                    <el-input v-model="invitText" style="width: 240px" placeholder="邮箱地址 " clearable />
                </div>

            </el-col>
        </el-row>
        <el-row>
            <el-col>
                <div>
                    <el-input v-model="remarkText" type="textarea" style="width: 240px" placeholder="备注 " clearable />
                </div>

            </el-col>
        </el-row>
        <el-row>
            <el-col>
                <div v-if="invitUrl" style="border:#c9c9c9 2px dashed ; padding:5px;margin-top:5px"
                    @click="handleCopy(invitUrl, $event)">
                    点击复制邀请链接
                    <p>邀请链接：{{ invitUrl }}</p>
                </div>
            </el-col>
        </el-row>
        <template #footer>
            <div class="dialog-footer">
                <el-button @click="centerDialogVisible">取消</el-button>
                <el-button type="primary" @click="sendInvite" :disabled="buttonStatus">
                    发出邀请
                </el-button>
            </div>
        </template>
    </el-dialog>
</template>

<script lang="ts" setup>
import { ref, onMounted } from "vue"
import { Plus } from '@element-plus/icons-vue'

import { ElMessage } from "element-plus"
import { useRouter } from "vue-router"
import { getAuthList, inviteUser, memberInvites } from "@/api/api"
import clip from "@/utils/clipboard"
import { formatTime } from "@/utils"
import { useUserStore } from "@/store/modules/user"
const rolesList = ref([
    { key: "admin", value: "空间管理员" },
    { key: "normal", value: "尊享会员" }
])
const { token, roles } = useUserStore()
const workspaceRole = ref("")

const router = useRouter()
const tableData = ref([])
const inviteDialog = ref(false)
const invitText = ref("")
const remarkText = ref("")
const invitUrl = ref("")
const PageInfo = ref({
    "page": 1,
    "limit": 10,
    "total": 0
})
const buttonStatus = ref(false)
const handleCopy = (text, event) => {
    clip(text, event)
}

function handleCurrentChange() {
    AuthList()
}

function openInvite() {
    inviteDialog.value = true
    buttonStatus.value = false
    invitUrl.value = ""
}
function centerDialogVisible() {
    invitText.value = ""
    inviteDialog.value = false
}
function AuthList() {
    getAuthList(PageInfo.value).then(res => {
        let { code, msg, data } = res.data

        if (code == 0) {
            tableData.value = data.data
            PageInfo.value.total = data.total
            PageInfo.value.page = data.page
            PageInfo.value.limit = data.limit
        } else {

            ElMessage({
                message: msg,
                type: "error",
                duration: 3000,
            })
        }


    })
}

function getMemberInvites() {
    let data = {
        tenant_id: localStorage.getItem("tenant_id") || ""
    }
    memberInvites(data).then(res => {
        let { code, msg, data } = res.data
        if (code == 0) {
            tableData.value = data
        } else {

            ElMessage({
                message: msg,
                type: "error",
                duration: 3000,
            })
        }
    })
}
function sendInvite() {

    if (workspaceRole.value == "") {
        ElMessage({
            message: "请选择邀请角色!",
            type: "error",
            duration: 3000,
        })
        return
    }

    inviteUser({
        email: invitText.value,
        domain: "racio.chat",
        role: workspaceRole.value,
        tenant_id: localStorage.getItem("tenant_id") || "",
        remark: remarkText.value

    })
        .then(res => {
            let { code, data, msg } = res.data
            if (code == 0) {
                invitUrl.value = data.url
                buttonStatus.value = true
            } else {
                ElMessage({
                    message: msg,
                    type: "error",
                    duration: 3000,
                })
            }
        })
        .catch(error => {
            ElMessage({
                message: error.message,
                type: "error",
                duration: 3000,
            })
        })
        .finally(() => {
            getMemberInvites()
        })
}
onMounted(async () => {

    getMemberInvites()

    if (roles[0] == "owner") {
        workspaceRole.value = "admin"
    } else {
        workspaceRole.value = "normal"
    }
})
</script>
<style lang="scss" scoped>
.home-container {
    width: 98%;
    margin: 32px;
}

@import "./index.scss";
</style>
