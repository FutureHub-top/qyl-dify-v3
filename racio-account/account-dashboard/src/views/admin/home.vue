<template>

    <div class="home-container">
        <el-row class="row-bg" :gutter="11">

            <el-col :span="24">
                <el-table :data="tableData" style="width: 100%">
                    <el-table-column type="index" prop="date" label="编号" width="60" />
                    <el-table-column prop="tenant_names" label="空间名" min-width="80" />
                    <el-table-column prop="name" label="创建者" width="180" />
                    <el-table-column prop="" label="管理员配额" width="100" />
                    <el-table-column prop="" label="应用构建配额" width="120" />
                    <el-table-column prop="" label="普通用户数" width="120" />
                    <el-table-column prop="" label="本周访客数" width="120" />
                    <el-table-column prop="created_at" label="创建时间" width="180">
                        <template #default="scope">
                            <div>{{ parseTime(scope.row.created_at, "") }}</div>
                        </template>
                    </el-table-column>
                    <el-table-column prop="overtime_at" label="到期时间" width="180" />

                    <el-table-column label="操作" fixed="right" width="180">
                        <template #default="scope">
                            <el-button type="primary">暂停</el-button>
                            <el-button type="danger">移除</el-button>
                        </template>
                    </el-table-column>
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

    <el-dialog v-model="inviteDialog" title="邀请开通空间" width="500" align-center>
        <el-row>
            <el-col style="margin-bottom:20px">
                <span>输入被邀请人邮箱，如空则只生成邀请链接</span>
            </el-col>
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
import { parseTime } from "@/utils"


const router = useRouter()
const tableData = ref([])
const inviteDialog = ref(false)
const invitText = ref("")
const remarkText = ref("")
const invitUrl = ref("")
const PageInfo = ref({
    "page": 1,
    "limit": 10,
    "total": 0,
    "keyword": ""
})
const handleCopy = (text, event) => {
    clip(text, event)
}

function handleCurrentChange() {
    AuthList()
}

function openInvite() {
    inviteDialog.value = true
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
        }
    })
}
function sendInvite() {
    inviteUser({
        email: invitText.value,
        domain: "racio.chat",
        role: "owner",
        tenant_id: localStorage.getItem("tenant_id") || "",
        remark: remarkText.value

    })
        .then(res => {
            let { code, data, msg } = res.data
            if (code == 0) {
                invitUrl.value = data.url
            }
        })
        .catch(error => {
            ElMessage({
                message: error.message,
                type: "error",
                duration: 3000,
            })
        })
}
onMounted(async () => {
    AuthList()
    // getMemberInvites()
})
</script>
<style lang="scss" scoped>
.home-container {
    width: 98%;
    margin: 32px;
}

@import "./index.scss";
</style>
