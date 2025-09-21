// import {
//   getShopList
// } from "../../api/common";
import { biaodian } from '../../utils/biaodian_impl';

const app = getApp()
Page({
  data: {
    swiperHeight: 0,
    latitude: 39.907957, // 经度
    longitude: 116.397493, // 纬度
    scale: 15, //  缩放级别
    rotate: 10, //  旋转角度
    skew: 5, //  倾斜角度
    showLocation: true,
    includePoints: [], // 显示点
    showCompass: true, // 显示指南针
    enableOverlooking: true, // 显示俯视
    enableRotate: true, // 显示指南针
    showScale: true, // 显示比例尺
    enableZoom: true, // 显示缩放
    enableScroll: true, // 显示缩放
    enableSatellite: false, // 显示卫星
    enablePoi: true, // 显示 POI
    enableBuilding: false, // 显示楼块
    minScale: 3, //  最小缩放级别
    maxScale: 19, // 最大缩放级别
    markers: [{ // 样例字段
      id: 1,
      latitude: 40.907957,
      longitude: 110.397493,
      width: 30,
      height: 30,
      iconPath: '../../assets/zhusu.png',
      callout: {
        content: '这是一个标注',
        color: '#000',
        fontSize: 12,
        borderRadius: 5,
        bgColor: '#fff',
        padding: 5,
        display: 'ALWAYS'
      },
      label: {
        content: '标注',
        color: '#fff',
        fontSize: 12,
        borderRadius: 5,
        bgColor: '#000',
        padding: 5,
        display: 'ALWAYS'
      }
    }],
    showContent: false,
    // shopList: [], // 商品列表
    // loading: false, // 是否正在加载
    // noMoreData: false, // 是否没有更多数据
    // page: 1, // 当前页码
    // pageSize: 10 // 每页数据条数
    items: []
  },
  onReady () {
    this.mapCtx = tt.createMapContext('myMap');
  },
  /**  视图切换 */
  toggleContent () {
    this.setData({
      showContent: !this.data.showContent,
    });

    // 切换到列表视图时加载数据
    if (!this.data.showContent && this.data.shopList.length === 0) {
      this.loadShopList();
    }
  },
  /**  加载页面  */
  onLoad () {
    this.loadBiaoDianList();
    tt.getLocation({
      type: 'gcj02',
      success: (res) => {
        console.log('getLocation', res);
        this.setData({
          latitude: res.latitude,
          longitude: res.longitude,
          scale: 14
        });
      },
      fail: (err) => {
        console.log('getLocation', err);
      }
    })
  },
  // 加载标点
  // loadBiaoDianList() {
  //   this.setData({ loading: true });
  //   tt.request({
  //     url: 'https://api.example.com/products', // 你的后端接口地址
  //     method: 'GET',
  //     success: (res) => {
  //       if (res.statusCode === 200 && Array.isArray(res.data)) {
  //         this.setData({
  //           items: res.data,
  //           loading: false
  //         });
  //       } else {
  //         this.setData({ items: [], loading: false });
  //       }
  //     },
  //     fail: (err) => {
  //       console.error('接口请求失败', err);
  //       this.setData({ items: [], loading: false });
  //     }
  //   });
  // },
  async loadBiaoDianList () {
    console.log('[loadBiaoDianList] 获取标点数据');
    try {
      console.log('[loadBiaoDianList] 11111');
      // 从全局变量获取openid
      const app = getApp();
      const openid = app.getGlobalData('openid');

      if (!openid) {
        console.log('[loadBiaoDianList] 未获取到全局openid');
        // 如果全局变量中没有openid，则通过登录获取code
        // const loginRes = await new Promise((resolve, reject) => {
        //   tt.login({
        //     success: resolve,
        //     fail: reject
        //   });
        // });
        //const code = loginRes.code;
        //console.log('[loadBiaoDianList] 使用临时code:', code);
        const biaodianList = await biaodian.bd_list(openid);
        console.log('[loadBiaoDianList] 获取标点数据成功', biaodianList);
      } else {
        console.log('[loadBiaoDianList] 获取到全局openid:', openid);
        const biaodianList = await biaodian.bd_list(openid);
        console.log('[loadBiaoDianList] 获取标点数据成功', biaodianList);
      }
    } catch (err) {
      console.log('[loadBiaoDianList] 获取标点数据异常', err);
    }
  },









  /**  添加标点  */
  handleMapTap (e) {
    // 从点击事件直接获取坐标
    const {
      latitude,
      longitude
    } = e.detail;
    // 构造新标记对象
    const newMarker = {
      id: Date.now(),
      latitude,
      longitude,
      width: 20,
      height: 28,
      iconPath: '../../assets/travel_15692612.png',
      callout: {
        content: `标记点-${this.data.markers.length + 1}`,
        color: '#FF5722',
        fontSize: 14,
        borderRadius: 8,
        bgColor: '#FFFBE6',
        padding: 8,
        display: 'BYCLICK' // 优化显示方式
      }
    };
    // 只能添加5个
    if (this.data.markers.length >= 30) {
      tt.showToast({
        title: '当前最多添加30个标点',
        icon: 'none',
        duration: 2000,
      });
      return;
    }
    // 更新数据（保留历史标记）
    this.setData({
      markers: [...this.data.markers, newMarker],
      latitude,
      longitude
    });
    //console.log("添加标点")
  },

  // 加载商品列表数据
  // loadShopList() {
  //   // 如果正在加载或没有更多数据，则不执行加载操作
  //   if (this.data.loading || this.data.noMoreData) {
  //     return;
  //   }

  //   this.setData({
  //     loading: true
  //   });

  //   // 模拟异步加载数据
  //   setTimeout(() => {
  //     try {
  //       const res = getShopList();
  //       const newData = res.products || [];

  //       // 如果返回的数据少于页面大小，说明没有更多数据了
  //       const noMoreData = newData.length < this.data.pageSize;

  //       // 如果是第一页，直接设置数据；否则追加数据
  //       const shopList = this.data.page === 1 ? newData : [...this.data.shopList, ...newData];

  //       this.setData({
  //         shopList: shopList,
  //         loading: false,
  //         noMoreData: noMoreData,
  //         page: noMoreData ? this.data.page : this.data.page + 1
  //       });
  //     } catch (error) {
  //       console.error('加载商品列表失败:', error);
  //       this.setData({
  //         loading: false
  //       });
  //       tt.showToast({
  //         title: '加载失败',
  //         icon: 'none'
  //       });
  //     }
  //   }, 1000); // 模拟网络延迟
  // },

  // 触底加载更多
  onReachBottom () {
    if (!this.data.showContent) {
      this.loadShopList();
    }
  },

  // 列表项点击事件
  onItemTap (e) {
    const id = e.currentTarget.dataset.id;
    tt.showToast({
      title: `点击了商品: ${id}`,
      icon: 'none'
    });
  },

  // 页面显示时的处理
  onShow () {
    // 如果当前是列表视图且列表为空，则加载数据
    if (!this.data.showContent && this.data.shopList.length === 0) {
      this.loadShopList();
    }
  },

  /**  移动到当前定位点 */
  // moveToLocation() {
  //   this.mapCtx.moveToLocation({
  //     success(res) {
  //       console.log('move 成功: ', res);
  //     },
  //     fail(err) {
  //       console.log('move 失败: ', err);
  //     },
  //     complete(res) {
  //       console.log('move 完成', res);
  //     }

  /**  查看标点信息  */
  // handleMarkerTap(e) {
  //   const markerId = e.markerId;
  //   tt.showToast({
  //     title: '标点信息',
  //     icon: 'success'
  //   });
  //   console.log("查看标点信息")
  // },
  // 开启卫星地图
  // onSwitchEnableSatellite() {
  //   this.setData({
  //     enableSatellite: !this.data.enableSatellite
  //   });
  // },

  /**  删除标点  */
  // handleMarkerTap(e) {
  //   const markerId = e.markerId;
  //   this.setData({
  //     markers: this.data.markers.filter(marker => marker.id !== markerId)
  //   });
  //   // tt.showToast({
  //   //   title: '标点已删除',
  //   //   icon: 'success'
  //   // });
  //   console.log("删除标点")
  // },

  /** 切换显示内容 */
  // toggleDisplay() {
  //   this.setData({
  //     showMap: !this.data.showMap
  //   });
  //   console.log("切换视图，当前 showMap:", this.data.showMap); // 调试日志
  // },
});
