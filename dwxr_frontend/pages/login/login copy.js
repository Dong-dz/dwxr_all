/*
 * @Author: Dong-dz 505403623@qq.com
 * @Date: 2025-07-10 21:20:55
 * @LastEditors: Dong-dz 505403623@qq.com
 * @LastEditTime: 2025-08-10 16:19:30
 * @FilePath: \打窝仙人\pages\login\login.js
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
 */
import { loginController } from '../../utils/login_impl';
Page({
  data: {
    unionid: '',
    username: '',
    // 抖音登录状态
    isLogin: false,
  },
  // async onLoad() {
  //   // 判断用户是否登录抖音主端
  //   const isDouyinLogin = await loginController.login(false);
  //   // setData设置抖音登录状态
  //   this.setData({
  //     isLogin: isDouyinLogin,
  //   });
  //   // 如果用户已登录开发者服务端，则在缓存中获取openid和unionid
  //   if (loginController.isDeveloperServerLogin()) {
  //     this.setData({
  //       openid: loginController.getOpenid(),
  //       unionid: loginController.getUnionid(),
  //     });
  //     tt.setNavigationBarColor({ frontColor: '#000000', backgroundColor: '#F2F2F2' });
  //   }
  // },
  /**
   * @description: 点击事件，若用户没登录抖音主端，则强制调取登录界面，并向开发者服务端进行登录
   * @return {*}
   */
  async onLoginTap () {
    console.log('点击登录');
    try {
      const isDouyinLogin = await loginController.login();
      if (!isDouyinLogin) {
        console.log('[onLoginTap] 登录失败');
        return;
      }else{
        const openid = loginController.getOpenid();
        console.log('openid', openid);
        this.setData({
          openid: openid,
          username: loginController.getUsername(),
          //unionid: loginController.getUnionid(),
          isLogin: isDouyinLogin,
        });
        // 设置全局openid
        const app = getApp();
        app.setGlobalData('openid', openid);
        console.log('[onLoginTap] ', isDouyinLogin);
        console.log('[onLoginTap] 登录成功');
      }
    } catch (err) {
      console.log('[onLoginTap] 点击登录异常',err);
    }
  },


  /**
   * @description: 退出登录事件，调用 loginController.logout 并清空页面数据
   * @return {*}
   */
  async onLogoutTap () {
    console.log('点击登录退出');
    await loginController.logout();
    this.setData({
      openid: '',
      unionid: '',
      isDeveloperServerLogin: false,
      isLogin: false,
    });
    tt.setNavigationBarColor({ frontColor: '#ffffff', backgroundColor: '#ffffff' });
  },
});
