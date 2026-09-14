<template>
    <div class="dashboard">
        <h1>Wireguard VPN Dashboard</h1>
        <!-- Header section-->
        <nav class="nav">
            <button @click="currentTab = 'systemInfo'">Server Info</button>
            <button @click="currentTab = 'peers'">Peers</button>
            <button @click="currentTab = 'addDevice'">Add Device</button>
        </nav>

        <!-- Main content section-->
        <main>
            <div v-if="currentTab === 'systemInfo'">
                <h2>Server Info</h2>
                <div v-if="systemInfo" class="tab">
                    <p><b>Uptime:</b> {{ formatUptime(systemInfo.uptime) }}</p>
                    <p><b>CPU Usage:</b> {{ systemInfo.cpu_usage }}%</p>
                    <p><b>Memory Usage:</b> {{ systemInfo.memory.percent }}%</p>
                    <p><b>Disk Usage:</b> {{ systemInfo.disk.percent }}%</p>
                    <p><b>Free Space:</b> {{ (systemInfo.disk.free / (1024 * 1024 * 1024)).toFixed(2) }} GB</p>
                </div>
                <div v-else>
                    <p>Failed to load system information...</p>
                </div>
            </div>

            <div v-if="currentTab === 'peers'">
                <h2>Peers</h2>
                <div v-if="peers.length === 0">
                    <p>No peers connected.</p>
                </div>
                <div v-else class="tab">
                    <div v-for="peer in peers">
                        <p><b>Public Key:</b> {{ peer.public_key }}</p>
                        <p><b>IP Address:</b> {{ peer.ip }}</p>
                        <p><b>Endpoint:</b> {{ peer.endpoint ? peer.endpoint : 'N/A' }}</p>
                        <p><b>Latest Handshake:</b> {{ formatHandshake(peer.latest_handshake) }}</p>
                        <p><b>Data Sent:</b> {{ formatBytes(peer.rx_bytes) }}</p>
                        <p><b>Data Received:</b> {{ formatBytes(peer.tx_bytes) }}</p>
                        <hr>    <!-- Separator line -->
                    </div>
                </div>
            </div>

            <div v-if="currentTab === 'addDevice'">
                <h2>Add Device</h2>
            </div>  

        </main>

    </div>

</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue'


const currentTab = ref('systemInfo')
const peers = ref([])
const systemInfo = ref(null)

// const API_URL = 'http://localhost:8000'
const API_URL = '/api'

let systemInfoInterval = null
let peersInterval = null

function formatUptime(seconds) {
    const days = Math.floor(seconds / (3600 * 24))
    const hours = Math.floor((seconds % (3600 * 24)) / 3600)
    const mins = Math.floor((seconds % 3600) / 60)
    // const secs = Math.floor(seconds % 60)
    return `${days}d ${hours}h ${mins}mins`
}

function formatHandshake(timestamp) {
    if (timestamp === 0) // unix timestamp
        return 'Never'
    const date = new Date(timestamp * 1000)

    const options = {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        month: 'short',
        day: '2-digit',
        year: 'numeric',
    }
    return date.toLocaleString(undefined, options)
}

function formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) 
        return '0 Byte'
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)))
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i]
}

async function fetchSystemInfo() {
    try {
        const response = await fetch(`${API_URL}/system/info`)
        systemInfo.value = await response.json()
    } catch (error) {
        console.error('Error fetching status:', error)
    }
}

async function fetchPeers() {
    try {
        const response = await fetch(`${API_URL}/wg/peers`)
        const data = await response.json()
        if (data.status === 'success') {
            peers.value = data.data
        }
    } catch (error) {
        console.error('Error fetching peers:', error)
    }
}

function startFetching() {
    clearInterval(systemInfoInterval)
    clearInterval(peersInterval)

    if (currentTab.value === 'systemInfo') {
        fetchSystemInfo()
        systemInfoInterval = setInterval(fetchSystemInfo, 1000)
    } else if (currentTab.value === 'peers') {
        fetchPeers()
        peersInterval = setInterval(fetchPeers, 1000)
    }

}

// Watch for tab changes
watch(currentTab, () => {
    startFetching()
})

onMounted(() => {
    startFetching()
})

onUnmounted(() => {
    clearInterval(systemInfoInterval)
    clearInterval(peersInterval)
})
</script>

<style scoped>
.tab {
    text-align: left;
}

</style>