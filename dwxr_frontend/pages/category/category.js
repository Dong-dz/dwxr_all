/*
 * @Author: Dong-dz 505403623@qq.com
 * @Date: 2025-05-05 22:41:14
 * @LastEditors: Dong-dz 505403623@qq.com
 * @LastEditTime: 2025-07-27 22:02:10
 * @FilePath: \打窝仙人\pages\category\category.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
// /Users/bytedance/Desktop/codelabs-miniprogram-template/miniprogram-templates/templates/microapp/javascript/group-buy-industry/group-buy-industry/pages/category/category.js
import {
  getShopList
} from "../../api/common";
const app = getApp()

Page({
  data: {
    sortList: ['热榜', '探索', '抽奖'],
    current: 0,
    shopList: [],
    swiperHeight: 0,
  },
  async onLoad () {
    const res = await getShopList();
    console.log('Welcome to Mini Code', res)
    this.setData({
      shopList: res?.products
    })
    console.log('Welcome to Mini Code', this.data.shopList)
  },
  onReady () {
    this.getHeight();
  },
  onShow () {
    const { category, tittle } = app.globalData?.category
    if (category) {
      this.setData({
        current: category
      })
    }
  },
  handleTabbarChange (event) {
    const current = event.detail.current
    this.setData({
      current: current
    });
    this.getHeight();
  },
  switchTap (e) {
    const { current } = e.detail;
    console.log(current);
    this.setData({
      current,
    });
    this.getHeight();
  },
  getHeight () {
    let that = this;
    tt.createSelectorQuery().select('#card').boundingClientRect(function (rect) {
    }).exec(res => {
      console.log(res);
      that.setData({
        swiperHeight: res[0].height + ''
      })
    });
  },

})
