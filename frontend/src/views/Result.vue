<template>
  <div class="result-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="result-heading"><a-button class="back-button" @click="goBack">← 返回首页</a-button><div v-if="tripPlan"><h1>{{ tripPlan.city }}旅行计划</h1><p class="result-subtitle">{{ tripPlan.start_date }} — {{ tripPlan.end_date }} · {{ tripPlan.days.length }} 天行程 <span v-if="tripPlan.traveler_count">· {{ tripPlan.traveler_count }} 人</span></p></div></div>
      <a-space size="middle">
        <a-button v-if="!editMode" @click="toggleEditMode" type="default" :disabled="replanning !== null || routeLoading !== null">
          编辑行程
        </a-button>
        <a-button v-else @click="saveChanges" type="primary">
          保存修改
        </a-button>
        <a-button v-if="editMode" @click="cancelEdit" type="default">
          取消编辑
        </a-button>

        <!-- 导出按钮 -->
        <a-dropdown v-if="!editMode">
          <template #overlay>
            <a-menu>
              <a-menu-item key="image" @click="exportAsImage">
                导出为图片
              </a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">
                导出为 PDF
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="default">
            导出行程 <DownOutlined />
          </a-button>
        </a-dropdown>
      </a-space>
    </div>

    <div v-if="tripPlan" class="content-wrapper">
      <!-- 侧边导航 -->
      <div class="side-nav">
        <a-affix :offset-top="80">
          <a-menu mode="inline" :selected-keys="[activeSection]" @click="scrollToSection">
            <a-menu-item key="overview">
              <span>行程概览</span>
            </a-menu-item>
            <a-menu-item key="budget" v-if="tripPlan.budget">
              <span>预算明细</span>
            </a-menu-item>
            <a-menu-item key="map">
              <span>景点地图</span>
            </a-menu-item>
            <a-sub-menu key="days" title="每日行程">
              <a-menu-item v-for="(day, index) in tripPlan.days" :key="`day-${index}`">
                第{{ day.day_index + 1 }}天
              </a-menu-item>
            </a-sub-menu>
            <a-menu-item key="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0">
              <span>天气信息</span>
            </a-menu-item>
          </a-menu>
        </a-affix>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <a-alert type="info" show-icon message="景点位置来自地图查询；费用为估算，未提供的费用按 0 计算，出行前请核实。" style="margin-bottom: 16px" />
        <a-alert v-for="warning in tripPlan.warnings || []" :key="warning" type="warning" show-icon :message="warning" style="margin-bottom: 12px" />
        <!-- 顶部信息区:左侧概览+预算,右侧地图 -->
        <div class="top-info-section">
          <!-- 左侧:行程概览和预算明细 -->
          <div class="left-info">
            <!-- 行程概览 -->
            <a-card id="overview" title="行程概览" :bordered="false" class="overview-card">
              <div class="overview-content">
                <div class="info-item">
                  <span class="info-label">日期</span>
                  <span class="info-value">{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">旅行建议</span>
                  <span class="info-value">{{ tripPlan.overall_suggestions }}</span>
                </div>
              </div>
            </a-card>

            <!-- 预算明细 -->
            <a-card id="budget" v-if="tripPlan.budget" title="预算明细（估算）" :bordered="false" class="budget-card">
              <div class="budget-grid">
                <div class="budget-item">
                  <div class="budget-label">景点门票</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_attractions }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">酒店住宿</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_hotels }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">餐饮费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_meals }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">交通费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_transportation }}</div>
                </div>
              </div>
              <div class="budget-total">
                <span class="total-label">预估总费用</span>
                <span class="total-value">¥{{ tripPlan.budget.total }}</span>
              </div>
            </a-card>
          </div>

          <!-- 右侧:地图 -->
          <div class="right-map">
            <a-card id="map" title="景点地图" :bordered="false" class="map-card">
              <div id="amap-container" class="map-container"></div>
              <p>地图连线仅表示景点顺序；实际道路与耗时可在每日行程查询。</p>
            </a-card>
          </div>
        </div>

        <!-- 每日行程:可折叠 -->
        <a-card title="每日行程" :bordered="false" class="days-card">
          <a-collapse v-model:activeKey="activeDays" accordion>
            <a-collapse-panel
              v-for="(day, index) in tripPlan.days"
              :key="index"
              :id="`day-${index}`"
            >
              <template #header>
                <div class="day-header">
                  <span class="day-title">第{{ day.day_index + 1 }}天</span>
                  <span class="day-date">{{ day.date }}</span>
                </div>
              </template>

              <!-- 行程基本信息 -->
              <div class="day-info">
                <div class="info-row">
                  <span class="label">行程概述</span>
                  <span class="value">{{ day.description }}</span>
                </div>
                <div class="info-row">
                  <span class="label">交通方式</span>
                  <span class="value">{{ day.transportation }}</span>
                </div>
                <div class="info-row">
                  <span class="label">住宿偏好</span>
                  <span class="value">{{ day.accommodation }}</span>
                </div>
              </div>

              <a-space direction="vertical" style="width: 100%; margin: 12px 0">
                <label class="adjust-label" :for="`adjust-${index}`">调整当天行程</label>
                <a-input :id="`adjust-${index}`" v-model:value="instructions[index]" placeholder="输入景点关键词，例如：博物馆" :disabled="editMode || replanning !== null || routeLoading !== null" />
                <a-space wrap>
                  <a-button :loading="replanning === index" :disabled="editMode || replanning !== null || routeLoading !== null || !instructions[index]?.trim()" @click="replanDay(index)">调整这一天</a-button>
                  <a-button :loading="routeLoading === index" :disabled="editMode || replanning !== null || routeLoading !== null || day.attractions.length < 2" @click="loadRoutes(index)">查询实际交通耗时</a-button>
                </a-space>
                <div v-for="route in routes[index] || []" :key="route.label">{{ route.label }}：{{ route.text }}</div>
              </a-space>
              <!-- 景点安排 -->
              <a-divider orientation="left">景点安排</a-divider>
              <a-list
                :data-source="day.attractions"
                :grid="{ gutter: 16, xs: 1, sm: 2, column: 2 }"
              >
                <template #renderItem="{ item, index }">
                  <a-list-item>
                    <a-card :title="item.name" size="small" class="attraction-card">
                      <!-- 编辑模式下的操作按钮 -->
                      <template #extra v-if="editMode">
                        <a-space>
                          <a-button
                            size="small"
                            aria-label="向前移动景点"
                            @click="moveAttraction(day.day_index, index, 'up')"
                            :disabled="index === 0"
                          >
                            ↑
                          </a-button>
                          <a-button
                            size="small"
                            aria-label="向后移动景点"
                            @click="moveAttraction(day.day_index, index, 'down')"
                            :disabled="index === day.attractions.length - 1"
                          >
                            ↓
                          </a-button>
                          <a-button
                            size="small"
                            danger
                            aria-label="删除景点"
                            @click="deleteAttraction(day.day_index, index)"
                          >
                            删除
                          </a-button>
                        </a-space>
                      </template>

                      <!-- 景点图片 -->
                      <div class="attraction-image-wrapper">
                        <img
                          :src="getAttractionImage(item.name, index)"
                          :alt="item.name"
                          class="attraction-image"
                          @error="handleImageError"
                        />
                        <div class="attraction-badge">
                          <span class="badge-number">{{ index + 1 }}</span>
                        </div>
                        <div v-if="item.ticket_price" class="price-tag">
                          ¥{{ item.ticket_price }}
                        </div>
                      </div>

                      <!-- 编辑模式下可编辑的字段 -->
                      <div v-if="editMode">
                        <p><strong>地址：</strong>{{ item.address }} <span class="edit-hint">（来自地图查询）</span></p>

                        <p><strong>游览时长(分钟):</strong></p>
                        <a-input-number :aria-label="`${item.name} 游览时长（分钟）`" v-model:value="item.visit_duration" :min="10" :max="480" size="small" style="width: 100%; margin-bottom: 8px" />

                        <p><strong>描述:</strong></p>
                        <a-textarea :aria-label="`${item.name} 描述`" v-model:value="item.description" :rows="2" size="small" style="margin-bottom: 8px" />
                      </div>

                      <!-- 查看模式 -->
                      <div v-else>
                        <p><strong>地址:</strong> {{ item.address }}</p>
                        <p><strong>游览时长:</strong> {{ item.visit_duration }}分钟</p>
                        <p><strong>描述:</strong> {{ item.description }}</p>
                        <p v-if="item.rating"><strong>评分:</strong> {{ item.rating }} / 5</p>
                      </div>
                    </a-card>
                  </a-list-item>
                </template>
              </a-list>

              <!-- 酒店推荐 -->
              <a-divider v-if="day.hotel" orientation="left">住宿推荐</a-divider>
              <a-card v-if="day.hotel" size="small" class="hotel-card">
                <template #title>
                  <span class="hotel-title">{{ day.hotel.name }}</span>
                </template>
                <a-descriptions :column="2" size="small">
                  <a-descriptions-item label="地址">{{ day.hotel.address }}</a-descriptions-item>
                  <a-descriptions-item label="类型">{{ day.hotel.type }}</a-descriptions-item>
                  <a-descriptions-item label="价格范围">{{ day.hotel.price_range }}</a-descriptions-item>
                  <a-descriptions-item label="评分">{{ day.hotel.rating || "暂无评分" }}</a-descriptions-item>
                  <a-descriptions-item label="距离" :span="2">{{ day.hotel.distance }}</a-descriptions-item>
                </a-descriptions>
              </a-card>

              <!-- 餐饮安排 -->
              <a-divider orientation="left">餐饮安排</a-divider>
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item
                  v-for="meal in day.meals"
                  :key="meal.type"
                  :label="getMealLabel(meal.type)"
                >
                  {{ meal.name }}
                  <span v-if="meal.description"> - {{ meal.description }}</span>
                </a-descriptions-item>
              </a-descriptions>
            </a-collapse-panel>
          </a-collapse>
        </a-card>

        <a-card id="weather" title="天气信息（仅显示已有预报）" style="margin-top: 20px" :bordered="false">
        <p v-if="tripPlan.weather_info.length < tripPlan.days.length">部分日期暂无天气预报，请临近出发时查询。</p>
        <a-list
          :data-source="tripPlan.weather_info"
          :grid="{ gutter: 16, xs: 1, sm: 2, lg: 3, column: 3 }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card size="small" class="weather-card">
                <div class="weather-date">{{ item.date }}</div>
                <div class="weather-info-row">
                  <span class="weather-icon">日</span>
                  <div>
                    <div class="weather-label">白天</div>
                    <div class="weather-value">{{ item.day_weather }} {{ item.day_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-info-row">
                  <span class="weather-icon">夜</span>
                  <div>
                    <div class="weather-label">夜间</div>
                    <div class="weather-value">{{ item.night_weather }} {{ item.night_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-wind">
                  风向 {{ item.wind_direction }} {{ item.wind_power }}
                </div>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
        </a-card>
      </div>
    </div>

    <a-empty v-else description="没有找到旅行计划数据">
      <template #image>
        <div class="empty-icon" aria-hidden="true">行程</div>
      </template>
      <template #description>
        <span style="color: #999;">暂无旅行计划数据,请先创建行程</span>
      </template>
      <a-button type="primary" @click="goBack">返回首页创建行程</a-button>
    </a-empty>

    <!-- 回到顶部按钮 -->
    <a-back-top :visibility-height="300">
      <div class="back-top-button">
        ↑
      </div>
    </a-back-top>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import type { TripPlan } from '@/types'
import apiClient from '@/services/api'
import { saveTrip } from '@/services/history'

const router = useRouter()
const tripPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const attractionPhotos = ref<Record<string, string>>({})
const activeSection = ref('overview')
const activeDays = ref<number[]>([0]) // 默认展开第一天
const instructions = ref<Record<number, string>>({})
const replanning = ref<number | null>(null)
const routeLoading = ref<number | null>(null)
const routes = ref<Record<number, { label: string; text: string; minutes: number }[]>>({})
let map: any = null

onMounted(async () => {
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
    // 加载景点图片
    loadAttractionPhotos()
    // 等待DOM渲染完成后初始化地图
    await nextTick()
    initMap()
  }
})

onBeforeUnmount(() => {
  if (map) map.destroy()
})

const goBack = () => {
  router.push('/')
}

// 滚动到指定区域
const scrollToSection = async ({ key }: { key: string }) => {
  activeSection.value = key
  if (key.startsWith('day-')) {
    activeDays.value = [Number(key.slice(4))]
    await nextTick()
  }
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 切换编辑模式
const toggleEditMode = () => {
  editMode.value = true
  // 保存原始数据用于取消编辑
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  message.info('进入编辑模式')
}

// 保存修改
const saveChanges = () => {
  editMode.value = false
  // 更新sessionStorage
  if (tripPlan.value) {
    if (tripPlan.value.budget) {
      const budget = tripPlan.value.budget
      budget.total_attractions = tripPlan.value.days.flatMap(day => day.attractions).reduce((total, item) => total + (item.ticket_price || 0), 0)
      budget.total_hotels = tripPlan.value.days.reduce((total, day) => total + (day.hotel?.estimated_cost || 0), 0)
      budget.total_meals = tripPlan.value.days.flatMap(day => day.meals).reduce((total, meal) => total + (meal.estimated_cost || 0), 0)
      budget.total = budget.total_attractions + budget.total_hotels + budget.total_meals + budget.total_transportation
      const budgetWarning = '估算费用超过预算上限，请调整行程或预算'
      const timeWarning = '部分日期的景点游览时间已超过每日活动时间，尚未计入交通与休息'
      const warnings = (tripPlan.value.warnings || []).filter(item => item !== budgetWarning && item !== timeWarning)
      if (tripPlan.value.budget_limit && budget.total > tripPlan.value.budget_limit) warnings.push(budgetWarning)
      if (tripPlan.value.days.some(day => day.attractions.reduce((sum, item) => sum + item.visit_duration, 0) > (tripPlan.value!.daily_hours || 8) * 60)) warnings.push(timeWarning)
      tripPlan.value.warnings = warnings
    }
    routes.value = {}
    saveTrip(tripPlan.value, sessionStorage.getItem('tripPlanId') || undefined)
  }
  message.success('修改已保存')

  // 重新初始化地图以反映更改
  if (map) {
    map.destroy()
  }
  nextTick(() => {
    initMap()
  })
}

// 取消编辑
const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
  }
  editMode.value = false
  message.info('已取消编辑')
}

// 删除景点
const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  if (day.attractions.length <= 1) {
    message.warning('每天至少需要保留一个景点')
    return
  }

  day.attractions.splice(attrIndex, 1)
  message.success('景点已删除')
}

// 移动景点顺序
const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  const attractions = day.attractions

  if (direction === 'up' && attrIndex > 0) {
    [attractions[attrIndex], attractions[attrIndex - 1]] = [attractions[attrIndex - 1], attractions[attrIndex]]
  } else if (direction === 'down' && attrIndex < attractions.length - 1) {
    [attractions[attrIndex], attractions[attrIndex + 1]] = [attractions[attrIndex + 1], attractions[attrIndex]]
  }
}

const getMealLabel = (type: string): string => {
  const labels: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃'
  }
  return labels[type] || type
}

// 调整指定日期，后端会保留其他日期和原酒店。
const replanDay = async (index: number) => {
  if (!tripPlan.value) return
  replanning.value = index
  try {
    const response = await apiClient.post('/api/trip/replan-day', {
      plan: tripPlan.value, day_index: index, instruction: instructions.value[index]
    }, { timeout: 600000 })
    tripPlan.value = response.data.data
    saveTrip(tripPlan.value!, sessionStorage.getItem('tripPlanId') || undefined)
    routes.value = {}
    loadAttractionPhotos()
    if (map) map.destroy()
    await nextTick()
    await initMap()
    message.success('当天行程已调整')
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '调整失败')
  } finally {
    replanning.value = null
  }
}

// 按景点顺序查询地图服务返回的实际距离和耗时。
const loadRoutes = async (index: number) => {
  if (!tripPlan.value) return
  routeLoading.value = index
  const day = tripPlan.value.days[index]
  const routeType = day.transportation.includes('自驾') ? 'driving' : day.transportation.includes('公共交通') || day.transportation.includes('地铁') ? 'transit' : 'walking'
  try {
    const results: { label: string; text: string; minutes: number }[] = []
    for (const [i, destination] of day.attractions.slice(1).entries()) {
      const origin = day.attractions[i]
      const response = await apiClient.post('/api/map/route', {
        origin_address: origin.address || origin.name,
        destination_address: destination.address || destination.name,
        origin_city: tripPlan.value!.city, destination_city: tripPlan.value!.city,
        route_type: routeType
      })
      const route = response.data.data
      const minutes = Math.ceil(route.duration / 60)
      results.push({ label: `${origin.name} → ${destination.name}`,
        text: `${(route.distance / 1000).toFixed(1)} 公里，约 ${minutes} 分钟`, minutes })
      routes.value[index] = [...results]
    }
    routes.value[index] = results
    const visitMinutes = day.attractions.reduce((sum, item) => sum + item.visit_duration, 0)
    const routeMinutes = results.reduce((sum, item) => sum + item.minutes, 0)
    if (visitMinutes + routeMinutes > (tripPlan.value.daily_hours || 8) * 60) message.warning('当天游览与交通预计超过每日活动时间，建议调整行程')
  } catch (error: any) {
    message.error(error.response?.data?.detail || error.message || '路线查询失败')
  } finally {
    routeLoading.value = null
  }
}

// 加载所有景点图片
const loadAttractionPhotos = async () => {
  if (!tripPlan.value) return

  const promises: Promise<void>[] = []

  tripPlan.value.days.forEach(day => {
    day.attractions.forEach(attraction => {
      const promise = apiClient.get('/api/poi/photo', { params: { name: attraction.name } })
        .then(res => res.data)
        .then(data => {
          if (data.success && data.data.photo_url) {
            attractionPhotos.value[attraction.name] = data.data.photo_url
          }
        })
        .catch(err => {
          console.error(`获取${attraction.name}图片失败:`, err)
        })

      promises.push(promise)
    })
  })

  await Promise.all(promises)
}

// 获取景点图片
const getAttractionImage = (name: string, index: number): string => {
  // 如果已加载真实图片,返回真实图片
  if (attractionPhotos.value[name]) {
    return attractionPhotos.value[name]
  }

  // 返回一个纯色占位图(避免跨域问题)
  const colors = [
    { start: '#315e5b', end: '#8cb2a3' },
    { start: '#b07658', end: '#ddbe9d' },
    { start: '#577e86', end: '#b8d1c9' },
    { start: '#758a6e', end: '#ced8b7' },
    { start: '#7f7870', end: '#c6b5a2' }
  ]
  const colorIndex = index % colors.length
  const { start, end } = colors[colorIndex]

  // 使用base64编码避免中文问题
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <defs>
      <linearGradient id="grad${index}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${start};stop-opacity:1" />
        <stop offset="100%" style="stop-color:${end};stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="400" height="300" fill="url(#grad${index})"/>
    <circle cx="200" cy="150" r="34" fill="none" stroke="white" stroke-opacity="0.65" stroke-width="2" />
    <path d="M200 126v48M176 150h48" fill="none" stroke="white" stroke-opacity="0.75" stroke-width="2" />
  </svg>`

  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

// 图片加载失败时的处理
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 使用灰色占位图
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="18" fill="%23999"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}



// 导出为图片
const exportAsImage = async () => {
  try {
    message.loading({ content: '正在生成图片...', key: 'export', duration: 0 })
    const { default: html2canvas } = await import('html2canvas')

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f7f6f0'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = '' // 移除所有类
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#184f50')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#184f50')
      }
      (card as HTMLElement).style.setProperty('background-color', '#edf4eb')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#f1f5ef')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#184f50')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f7f6f0')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f7f6f0',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    // 转换为图片并下载
    const link = document.createElement('a')
    link.download = `旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    message.success({ content: '图片导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出图片失败:', error)
    message.error({ content: `导出图片失败: ${error.message}`, key: 'export' })
  }
}

// 导出为PDF
const exportAsPDF = async () => {
  try {
    message.loading({ content: '正在生成PDF...', key: 'export', duration: 0 })
    const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([import('html2canvas'), import('jspdf')])

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f7f6f0'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = ''
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#184f50')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#184f50')
      }
      (card as HTMLElement).style.setProperty('background-color', '#edf4eb')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#f1f5ef')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#184f50')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f7f6f0')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f7f6f0',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const imgWidth = 210 // A4宽度(mm)
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    // 如果内容高度超过一页,分页处理
    let heightLeft = imgHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= 297 // A4高度

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= 297
    }

    pdf.save(`旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.pdf`)

    message.success({ content: 'PDF导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出PDF失败:', error)
    message.error({ content: `导出PDF失败: ${error.message}`, key: 'export' })
  }
}

// 初始化地图
const initMap = async () => {
  try {
    const mapServiceHost = import.meta.env.DEV
      ? `${window.location.origin}/_AMapService`
      : import.meta.env.VITE_AMAP_SERVICE_HOST
    if (mapServiceHost) {
      window._AMapSecurityConfig = { serviceHost: mapServiceHost }
    }
    const AMap = await AMapLoader.load({
      key: import.meta.env.VITE_AMAP_WEB_JS_KEY,  // 高德地图Web端(JS API) Key
      version: '2.0',
      plugins: ['AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']
    })

    // 创建地图实例
    map = new AMap.Map('amap-container', {
      zoom: 12,
      center: [116.397128, 39.916527], // 默认中心点(北京)
      viewMode: '3D'
    })

    // 添加景点标记
    addAttractionMarkers(AMap)

    message.success('地图加载成功')
  } catch (error) {
    console.error('地图加载失败:', error)
    message.error('地图加载失败')
  }
}

// 添加景点标记
const addAttractionMarkers = (AMap: any) => {
  if (!tripPlan.value) return

  const markers: any[] = []
  const allAttractions: any[] = []

  // 收集所有景点
  tripPlan.value.days.forEach((day, dayIndex) => {
    day.attractions.forEach((attraction, attrIndex) => {
      if (attraction.location && attraction.location.longitude && attraction.location.latitude) {
        allAttractions.push({
          ...attraction,
          dayIndex,
          attrIndex
        })
      }
    })
  })

  // 创建标记
  allAttractions.forEach((attraction, index) => {
    const marker = new AMap.Marker({
      position: [attraction.location.longitude, attraction.location.latitude],
      title: attraction.name,
      label: {
        content: `<div style="background: #184f50; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">${index + 1}</div>`,
        offset: new AMap.Pixel(0, -30)
      }
    })

    // 使用文本节点，避免外部景点描述被当作 HTML 执行。
    const infoContent = document.createElement('div')
    infoContent.style.padding = '10px'
    const title = document.createElement('h4')
    title.textContent = attraction.name
    infoContent.appendChild(title)
    for (const line of [
      `地址：${attraction.address}`,
      `游览时长：${attraction.visit_duration} 分钟`,
      `描述：${attraction.description}`,
      `第 ${attraction.dayIndex + 1} 天 · 景点 ${attraction.attrIndex + 1}`
    ]) {
      const paragraph = document.createElement('p')
      paragraph.textContent = line
      infoContent.appendChild(paragraph)
    }
    const infoWindow = new AMap.InfoWindow({
      content: infoContent,
      offset: new AMap.Pixel(0, -30)
    })

    // 点击标记显示信息窗口
    marker.on('click', () => {
      infoWindow.open(map, marker.getPosition())
    })

    markers.push(marker)
  })

  // 添加标记到地图
  map.add(markers)

  // 自动调整视野以包含所有标记
  if (allAttractions.length > 0) {
    map.setFitView(markers)
  }

  // 绘制路线
  drawRoutes(AMap, allAttractions)
}

// 绘制路线
const drawRoutes = (AMap: any, attractions: any[]) => {
  if (attractions.length < 2) return

  // 按天分组绘制路线
  const dayGroups: any = {}
  attractions.forEach(attr => {
    if (!dayGroups[attr.dayIndex]) {
      dayGroups[attr.dayIndex] = []
    }
    dayGroups[attr.dayIndex].push(attr)
  })

  // 为每天的景点绘制路线
  Object.values(dayGroups).forEach((dayAttractions: any) => {
    if (dayAttractions.length < 2) return

    const path = dayAttractions.map((attr: any) => [
      attr.location.longitude,
      attr.location.latitude
    ])

    const polyline = new AMap.Polyline({
      path: path,
      strokeColor: '#184f50',
      strokeWeight: 4,
      strokeOpacity: 0.8,
      strokeStyle: 'solid',
      showDir: true // 显示方向箭头
    })

    map.add(polyline)
  })
}
</script>

<style scoped>
.result-container { min-height:75vh; padding:24px 48px 72px; background:var(--paper); color:var(--ink); }
.page-header { max-width:1320px; margin:0 auto 30px; display:flex; justify-content:space-between; align-items:end; gap:24px; }.result-heading h1 { margin:10px 0; color:var(--ink); font-size:clamp(28px,2.5vw,36px); line-height:1.3; letter-spacing:-.02em; }.result-subtitle { margin:0; color:var(--ink-soft); font-size:14px; }
.back-button { padding:0; border:0; background:transparent; color:var(--ink-soft); box-shadow:none; }.page-header :deep(.ant-btn:not(.back-button)) { height:42px; border-radius:8px; border-color:#d5e1d8; color:var(--primary); background:var(--surface); font-weight:600; }.page-header :deep(.ant-btn-primary) { background:var(--primary); border-color:var(--primary); color:white; }
.content-wrapper { max-width:1320px; margin:auto; display:flex; gap:22px; align-items:flex-start; }.side-nav { width:190px; flex-shrink:0; }.side-nav :deep(.ant-menu) { padding:12px 4px; border:1px solid var(--line); border-radius:14px; background:var(--surface); color:var(--ink-soft); }.side-nav :deep(.ant-menu-item),.side-nav :deep(.ant-menu-submenu-title) { border-radius:8px; font-size:14px; }.side-nav :deep(.ant-menu-item-selected) { color:var(--primary); background:var(--soft); font-weight:700; }.main-content { flex:1; min-width:0; }
:deep(.ant-card) { border:1px solid var(--line) !important; border-radius:10px; background:var(--surface); box-shadow:none; overflow:hidden; }:deep(.ant-card-head) { min-height:60px; padding:0 22px; border-bottom:1px solid var(--line); background:var(--surface); }:deep(.ant-card-head-title) { color:var(--ink); font-size:16px; font-weight:700; }:deep(.ant-card-body) { padding:21px 22px; }:deep(.ant-btn) { border-radius:8px; cursor:pointer; }:deep(.ant-btn-primary) { background:var(--primary); border-color:var(--primary); }:deep(.ant-alert) { border-radius:10px; }
.top-info-section { display:grid; grid-template-columns:minmax(260px,.88fr) minmax(0,1.12fr); gap:18px; margin-bottom:18px; }.left-info { display:flex; flex-direction:column; gap:18px; }.right-map { min-width:0; }.overview-content { display:grid; gap:17px; }.info-item { display:grid; gap:6px; }.info-label { color:var(--muted); font-size:14px; font-weight:600; }.info-value { color:var(--ink-soft); font-size:15px; line-height:1.8; }
.budget-grid { display:grid; grid-template-columns:repeat(2,1fr); gap:0; margin-bottom:12px; }.budget-item { padding:12px 0; border-bottom:1px solid var(--line); }.budget-label { color:var(--muted); font-size:14px; }.budget-value { margin-top:6px; color:var(--ink); font-size:20px; font-weight:600; font-variant-numeric:tabular-nums; }.budget-total { display:flex; justify-content:space-between; align-items:center; padding:14px 0 0; color:var(--ink); }.total-label { font-size:15px; font-weight:600; }.total-value { font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; }
.map-card { height:100%; display:flex; flex-direction:column; }.map-card :deep(.ant-card-body) { padding:12px; flex:1; display:flex; flex-direction:column; }.map-container { width:100%; flex:1; min-height:390px; border-radius:9px; overflow:hidden; background:#eaf0e8; }.map-card p { color:var(--muted); font-size:12px; margin:11px 3px 1px; line-height:1.6; }
.days-card { margin-top:18px; }.day-header { display:flex; justify-content:space-between; gap:12px; width:100%; }.day-title { color:var(--primary); font-size:15px; font-weight:700; }.day-date { color:var(--muted); font-size:13px; }.day-info { display:grid; gap:12px; padding:0 0 16px; border-bottom:1px solid var(--line); }.info-row { display:flex; gap:12px; color:var(--ink-soft); font-size:14px; }.info-row .label { color:var(--muted); flex-shrink:0; }.info-row .value { line-height:1.7; }.adjust-label { color:var(--ink); font-size:14px; font-weight:600; }.edit-hint { color:var(--muted); font-size:12px; }
:deep(.ant-collapse) { border:0; background:transparent; }:deep(.ant-collapse-item) { overflow:hidden; border:1px solid var(--line) !important; border-radius:10px !important; margin-bottom:12px; }:deep(.ant-collapse-header) { background:#f7f9f5; }:deep(.ant-collapse-content) { border-color:var(--line); }
.attraction-image-wrapper { position:relative; overflow:hidden; border-radius:9px; margin-bottom:14px; }.attraction-image { width:100%; height:180px; object-fit:cover; display:block; }.attraction-badge { position:absolute; top:10px; left:10px; display:grid; place-items:center; width:31px; height:31px; border-radius:50%; color:white; background:var(--primary); font-weight:700; }.price-tag { position:absolute; top:10px; right:10px; padding:5px 10px; border-radius:7px; background:var(--surface); color:var(--accent); font-weight:700; font-size:12px; }.attraction-card { height:100%; }.attraction-card :deep(.ant-card-head) { min-height:46px; }.attraction-card :deep(.ant-card-head-title) { font-size:15px; }.attraction-card p { color:var(--ink-soft); font-size:14px; line-height:1.7; }.attraction-card p strong { color:var(--ink); }
.hotel-card { background:var(--surface); }.hotel-card :deep(.ant-card-head) { background:var(--surface); }.hotel-title { color:var(--primary); font-weight:700; }.weather-card { background:var(--surface); box-shadow:none !important; }.weather-date { color:var(--primary); font-weight:700; margin-bottom:12px; }.weather-info-row { display:flex; gap:10px; align-items:center; margin:10px 0; }.weather-icon { display:grid; place-items:center; width:30px; height:30px; border-radius:50%; background:#e4ede3; color:var(--primary); font-size:12px; }.weather-label { color:var(--muted); font-size:12px; }.weather-value { color:var(--ink-soft); font-size:14px; }.weather-wind { color:var(--muted); margin-top:10px; padding-top:10px; border-top:1px solid var(--line); font-size:12px; }
.empty-icon { display:grid; place-items:center; margin:auto; width:76px; height:76px; border-radius:50%; color:var(--primary); background:var(--soft); font-size:18px; font-weight:600; }.back-top-button { display:grid; place-items:center; width:44px; height:44px; border-radius:50%; color:white; background:var(--primary); font-size:20px; box-shadow:0 5px 20px #1b51443b; }
@media (max-width:1050px) { .side-nav { width:160px; }.top-info-section { grid-template-columns:1fr; }.map-container { flex:none; min-height:0; height:340px; } }
@media (max-width:760px) { .result-container { padding:25px 16px 48px; }.page-header { align-items:start; flex-direction:column; }.content-wrapper { display:block; }.side-nav { width:auto; margin-bottom:14px; }.side-nav :deep(.ant-menu) { display:flex; flex-wrap:wrap; }.side-nav :deep(.ant-menu-item),.side-nav :deep(.ant-menu-submenu) { width:auto; }.map-container { height:300px; }.page-header :deep(.ant-space) { flex-wrap:wrap; } }
@media (max-width:400px) { :deep(.ant-card-body) { padding:16px; }.budget-grid { gap:7px; }.info-row { flex-direction:column; gap:3px; } }
</style>
